# OpenPaper AI — Workflow Guide

The Workflow Builder lets you create automated DAG pipelines using a visual
editor (React Flow) or API.

## Workflow Concepts

- **Nodes** — individual steps in the workflow (8 types available)
- **Edges** — directional connections between nodes
- **Trigger** — entry point that starts execution
- **Condition** — branching logic (true/false paths)
- **Run** — a single execution of a workflow with logs

## Node Types

| Type | Icon | Purpose | Output Handles |
|------|------|---------|----------------|
| **Trigger** | ⚡ | Starts workflow execution | 1 (source) |
| **Agent** | 🤖 | Executes a specialist agent | 1 (source) |
| **Knowledge Search** | 🔍 | Semantic search across documents | 1 (source) |
| **Condition** | 🔀 | Branch based on field comparison | 3 (true/false/error) |
| **Delay** | ⏱️ | Pause execution for N seconds | 1 (source) |
| **HTTP Request** | 🌐 | Call external API | 1 (source) |
| **Email** | ✉️ | Send notification | 1 (source) |
| **Memory Store** | 🧠 | Store data in agent memory | 1 (source) |

## Building a Workflow

### Using the Visual Editor

1. Go to `/workflows` and click **Create Workflow**
2. Enter a name and description
3. Drag nodes from the panel onto the canvas
4. Connect nodes by dragging between handles
5. Configure each node's properties
6. Click **Save** and then **Execute**

### Workflow Example: Lead Generation

```
[Trigger] → [Research Agent] → [Condition: buyers found?]
                                        │
                                   Yes /   \ No
                                      /     \
                          [Sales Agent]    [Email Alert]
                                     │
                          [Memory Store]
```

### Using the API

```python
import httpx

# Create workflow
resp = httpx.post("http://localhost:8000/api/v1/workflows", json={
    "name": "Lead Gen",
    "nodes": [
        {"id": "1", "type": "trigger", "data": {}, "position": {"x": 0, "y": 0}},
        {"id": "2", "type": "agent", "data": {"agent_type": "research"}, "position": {"x": 200, "y": 0}},
    ],
    "edges": [{"id": "e1-2", "source": "1", "target": "2"}],
})
workflow_id = resp.json()["id"]

# Execute
httpx.post(f"http://localhost:8000/api/v1/workflows/{workflow_id}/execute")
```

## Condition Branching

Conditions use JavaScript-like expression syntax:

```json
{
  "field": "leads_count",
  "operator": ">",
  "value": 10
}
```

Supported operators: `==`, `!=`, `>`, `>=`, `<`, `<=`, `contains`, `is_empty`

Each condition node has three output handles:
- **true** — followed when condition passes
- **false** — followed when condition fails
- **error** — followed on execution error

## Workflow Runs

Each execution creates a `WorkflowRun` with:

- **Status**: pending → running → completed/failed/cancelled
- **Logs**: per-node execution records with timestamps
- **Input/Output**: data passed through the pipeline

### Monitoring Runs

1. Go to `/workflows/runs` to view all runs
2. Click **View Logs** to see per-node execution details
3. Click **Cancel** to stop a running workflow

## Best Practices

1. **Keep nodes focused** — each node should do one thing well
2. **Use conditions** — branch based on data to handle edge cases
3. **Add delays** — respect rate limits on external APIs
4. **Store results** — use Memory Store nodes to persist intermediate data
5. **Test incrementally** — start with 2-3 nodes, then expand
