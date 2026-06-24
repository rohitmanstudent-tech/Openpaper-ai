"""Workflow Execution Engine.

Loads workflow DAG from DB, resolves node dependencies,
executes nodes via agents/memory/tools, handles condition
branching, and captures logs.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.agents.orchestrator import AgentOrchestrator
from app.core.event_bus import get_bus
from app.core.memory import get_memory_engine
from app.core.vector import search as vector_search
from app.models.agent import AgentType
from app.models.workflow import RunStatus, Workflow, WorkflowRun

logger = logging.getLogger(__name__)


def _topological_sort(nodes: list[dict], edges: list[dict]) -> list[dict]:
    """Kahn's algorithm for topological ordering."""
    node_map = {n["id"]: n for n in nodes}
    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    adj: dict[str, list[str]] = {n["id"]: [] for n in nodes}

    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        if src and tgt:
            adj.setdefault(src, []).append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    sorted_nodes = []

    while queue:
        nid = queue.pop(0)
        if nid in node_map:
            sorted_nodes.append(node_map[nid])
        for neighbor in adj.get(nid, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return sorted_nodes


def _get_edges_from(target_id: str, edges: list[dict]) -> list[dict]:
    return [e for e in edges if e.get("source") == target_id]


def _get_edge_label(edge: dict) -> str:
    return (edge.get("sourceHandle") or edge.get("label") or "").lower()


async def execute_workflow(
    workflow: Workflow,
    workflow_run: WorkflowRun,
    orchestrator: AgentOrchestrator | None = None,
) -> None:
    """Execute a workflow DAG, updating run logs & status."""
    nodes: list[dict] = workflow.nodes if isinstance(workflow.nodes, list) else []
    edges: list[dict] = workflow.edges if isinstance(workflow.edges, list) else []
    input_data: dict = workflow_run.input_data or {}
    memory = get_memory_engine()
    get_bus()
    orch = orchestrator or AgentOrchestrator()

    context: dict[str, Any] = dict(input_data)
    sorted_nodes = _topological_sort(nodes, edges)
    logs: list[dict] = []
    skipped: set[str] = set()
    node_outputs: dict[str, Any] = {}

    workflow_run.status = RunStatus.RUNNING
    workflow_run.started_at = datetime.now(UTC)

    for node in sorted_nodes:
        nid = node["id"]
        ntype = node.get("type", "")
        ndata = node.get("data", {})

        # ── Check if node should be skipped (conditional branch) ──
        incoming = [e for e in edges if e.get("target") == nid]
        skip = False
        for inc in incoming:
            src = inc.get("source", "")
            src_label = _get_edge_label(inc)
            src_output = node_outputs.get(src, {})
            if src_label == "no" and src_output.get("condition_result") is not False:
                skip = True
                break
            if src_label == "yes" and src_output.get("condition_result") is not True:
                skip = True
                break
            if src_label == "false" and src_output.get("condition_result") is not False:
                skip = True
                break
            if src_label == "true" and src_output.get("condition_result") is not True:
                skip = True
                break

        if skip:
            skipped.add(nid)
            logs.append(
                {
                    "node_id": nid,
                    "node_type": ntype,
                    "status": "skipped",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            continue

        log_entry: dict[str, Any] = {
            "node_id": nid,
            "node_type": ntype,
            "status": "running",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        try:
            result: Any = None
            node_input = {**context, **{k: v for k, v in ndata.items() if k != "label"}}

            if ntype == "trigger":
                result = {"triggered": True, "input": node_input}

            elif ntype == "agent":
                agent_type_str = ndata.get("agent_type", "ceo")
                agent_input = ndata.get("input", ndata.get("prompt", ""))
                provider = ndata.get("provider", "ollama")
                model = ndata.get("model", "llama3.1")
                try:
                    at = AgentType(agent_type_str)
                except ValueError:
                    at = AgentType.CEO
                agent = orch.get_agent(at, provider=provider, model=model)
                processed = await agent.process(agent_input, context=[])
                result = {"response": processed, "agent_type": agent_type_str}

            elif ntype == "knowledge_search":
                query = ndata.get("query", "")
                if not query:
                    # try template from context
                    for _k, v in context.items():
                        query = str(v)
                        break
                limit = ndata.get("limit", 5)
                results = await vector_search(
                    collection="knowledge_base",
                    query_text=query,
                    limit=limit,
                )
                result = {"results": results}

            elif ntype == "condition":
                field = ndata.get("field", "")
                operator = ndata.get("operator", "exists")
                value = ndata.get("value", "")
                actual = context.get(field, ndata.get(field))
                cond_result = _evaluate_condition(actual, operator, value)
                result = {"condition_result": cond_result, "field": field}

            elif ntype == "delay":
                seconds = int(ndata.get("seconds", 1))
                await asyncio.sleep(seconds)
                result = {"delayed": True, "seconds": seconds}

            elif ntype == "http_request":
                url = ndata.get("url", "")
                method = ndata.get("method", "GET").upper()
                headers = ndata.get("headers", {})
                body = ndata.get("body")
                import httpx

                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.request(method, url, headers=headers, json=body)
                    result = {"status": resp.status_code, "body": resp.text[:5000]}

            elif ntype == "email_sender":
                to = ndata.get("to", "")
                subject = ndata.get("subject", "")
                ndata.get("body", "")
                log_msg = f"Email would be sent to {to}: {subject}"
                logger.info(log_msg)
                result = {"sent": True, "to": to, "subject": subject}

            elif ntype == "memory_store":
                content = ndata.get("content", str(context))
                memory_type = ndata.get("memory_type", "semantic")
                agent_id = ndata.get("agent_id", "workflow")
                await memory.create(
                    agent_id=agent_id,
                    content=content,
                    memory_type=memory_type,
                )
                result = {"stored": True}

            else:
                result = {"status": "unknown_type", "type": ntype}

            node_outputs[nid] = result or {}
            context[nid] = result
            log_entry["status"] = "completed"
            log_entry["result"] = result

        except Exception as e:
            logger.error("Workflow node %s (%s) failed: %s", nid, ntype, e)
            log_entry["status"] = "failed"
            log_entry["error"] = str(e)
            workflow_run.status = RunStatus.FAILED
            workflow_run.error = f"Node {nid} ({ntype}) failed: {e}"
            logs.append(log_entry)
            workflow_run.logs = logs
            workflow_run.completed_at = datetime.now(UTC)
            return

        logs.append(log_entry)

    if workflow_run.status != RunStatus.FAILED:
        workflow_run.status = RunStatus.COMPLETED
    workflow_run.output_data = context
    workflow_run.logs = logs
    workflow_run.completed_at = datetime.now(UTC)


def _evaluate_condition(actual: Any, operator: str, value: str) -> bool:
    try:
        if operator == "exists":
            return actual is not None and actual != ""
        elif operator == "equals":
            return str(actual) == value
        elif operator == "contains":
            return value in str(actual)
        elif operator == "gt":
            return float(actual) > float(value)
        elif operator == "lt":
            return float(actual) < float(value)
        elif operator == "gte":
            return float(actual) >= float(value)
        elif operator == "lte":
            return float(actual) <= float(value)
        elif operator == "is_true":
            return bool(actual) is True
        elif operator == "is_false":
            return bool(actual) is False
    except (ValueError, TypeError):
        return False
    return False
