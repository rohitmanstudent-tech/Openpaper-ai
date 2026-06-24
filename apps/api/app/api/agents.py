import json

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.core.exceptions import NotFoundError, ProviderError, ValidationError
from app.core.input_sanitizer import PromptInjectionError, sanitize_chat_input
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.models.agent import Agent, AgentType
from app.models.task import Task
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])
orchestrator = AgentOrchestrator()


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.owner_id == current_user.id).order_by(Agent.created_at.desc()))
    return [AgentResponse.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = Agent(
        name=data.name,
        agent_type=data.agent_type,
        description=data.description,
        model=data.model,
        provider=data.provider,
        system_prompt=data.system_prompt,
        temperature=data.temperature,
        owner_id=current_user.id,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.owner_id == current_user.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent not found")
    return AgentResponse.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.owner_id == current_user.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
    await db.commit()
    await db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.owner_id == current_user.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent not found")
    await db.delete(agent)
    await db.commit()


@router.post("/{agent_id}/execute")
async def execute_agent(
    agent_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.owner_id == current_user.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent not found")

    user_input = body.get("input", "")
    if not user_input:
        raise ValidationError("input is required")
    try:
        user_input = sanitize_chat_input(user_input)
    except PromptInjectionError:
        raise ValidationError("Input blocked: potential prompt injection detected") from None

    stream = body.get("stream", False)
    context = body.get("context")

    task = Task(
        title=f"Agent: {agent.name} — {user_input[:50]}",
        description=user_input,
        assigned_agent=agent.id,
        created_by=current_user.id,
        status="in_progress",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    try:
        agent_type = AgentType(agent.agent_type)

        if stream:

            async def generate():
                full_content = ""
                async for chunk in orchestrator.process_stream(
                    agent_type=agent_type,
                    user_input=user_input,
                    context=context,
                    provider=agent.provider,
                    model=agent.model,
                    temperature=agent.temperature,
                ):
                    full_content += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"

                task.status = "completed"
                task.result = full_content
                await db.commit()
                yield f"data: {json.dumps({'done': True, 'task_id': task.id})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            content = await orchestrator.process(
                agent_type=agent_type,
                user_input=user_input,
                context=context,
                provider=agent.provider,
                model=agent.model,
                temperature=agent.temperature,
            )
            task.status = "completed"
            task.result = content
            await db.commit()
            return {"result": content, "task_id": task.id}

    except Exception as e:
        task.status = "failed"
        task.result = str(e)
        await db.commit()
        raise ProviderError(f"Agent execution failed: {e}") from e


@router.post("/{agent_id}/delegate")
async def delegate_agent_task(
    agent_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.owner_id == current_user.id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent not found")

    target_agent_type = body.get("target_agent_type")
    if not target_agent_type:
        raise ValidationError("target_agent_type is required")

    user_input = body.get("input", "")
    if not user_input:
        raise ValidationError("input is required")

    task = Task(
        title=f"Delegation: {agent.name} -> {target_agent_type}: {user_input[:50]}",
        description=user_input,
        assigned_agent=agent.id,
        created_by=current_user.id,
        status="in_progress",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    try:
        target_type = AgentType(target_agent_type)
        content = await orchestrator.process(
            agent_type=target_type,
            user_input=user_input,
            provider=agent.provider,
            model=agent.model,
            temperature=agent.temperature,
        )
        task.status = "completed"
        task.result = content
        await db.commit()
        return {"result": content, "task_id": task.id, "delegated_to": target_agent_type}
    except Exception as e:
        task.status = "failed"
        task.result = str(e)
        await db.commit()
        raise ProviderError(f"Delegation failed: {e}") from e
