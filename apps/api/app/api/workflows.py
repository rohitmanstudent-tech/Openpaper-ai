from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.core.exceptions import NotFoundError
from app.core.security import get_current_user
from app.core.workflow_engine import execute_workflow
from app.database import get_db
from app.models import User
from app.models.workflow import RunStatus, Workflow, WorkflowRun
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowResponse,
    WorkflowRunResponse,
    WorkflowUpdate,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])

_orchestrator: AgentOrchestrator | None = None


def _get_orch() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


# ── Workflows CRUD ──────────────────────────────────────────────────

@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow)
        .where(Workflow.owner_id == current_user.id)
        .order_by(Workflow.updated_at.desc())
    )
    return [WorkflowResponse.model_validate(w) for w in result.scalars().all()]


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wf = Workflow(
        name=data.name,
        description=data.description,
        nodes=data.nodes,
        edges=data.edges,
        owner_id=current_user.id,
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return WorkflowResponse.model_validate(wf)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.owner_id == current_user.id)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise NotFoundError("Workflow not found")
    return WorkflowResponse.model_validate(wf)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.owner_id == current_user.id)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise NotFoundError("Workflow not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wf, field, value)
    wf.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(wf)
    return WorkflowResponse.model_validate(wf)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.owner_id == current_user.id)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise NotFoundError("Workflow not found")
    await db.delete(wf)
    await db.commit()


# ── Execution ───────────────────────────────────────────────────────

@router.post("/{workflow_id}/execute", response_model=WorkflowRunResponse)
async def execute_workflow_endpoint(
    workflow_id: int,
    body: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.owner_id == current_user.id)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise NotFoundError("Workflow not found")

    run = WorkflowRun(
        workflow_id=wf.id,
        trigger=body.trigger,
        input_data=body.input_data,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    try:
        await execute_workflow(wf, run, orchestrator=_get_orch())
    except Exception as e:
        run.status = RunStatus.FAILED
        run.error = str(e)
        run.completed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(run)
    return WorkflowRunResponse.model_validate(run)


# ── Runs ────────────────────────────────────────────────────────────

@router.get("/{workflow_id}/runs", response_model=list[WorkflowRunResponse])
async def list_runs(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.workflow_id == workflow_id)
        .order_by(WorkflowRun.created_at.desc())
        .limit(50)
    )
    return [WorkflowRunResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise NotFoundError("Run not found")
    return WorkflowRunResponse.model_validate(run)


@router.get("/runs", response_model=list[WorkflowRunResponse])
async def list_all_runs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkflowRun)
        .join(Workflow)
        .where(Workflow.owner_id == current_user.id)
        .order_by(WorkflowRun.created_at.desc())
        .limit(100)
    )
    return [WorkflowRunResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/runs/{run_id}/cancel", response_model=WorkflowRunResponse)
async def cancel_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise NotFoundError("Run not found")
    run.status = RunStatus.CANCELLED
    run.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(run)
    return WorkflowRunResponse.model_validate(run)
