from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"
    assigned_to: int | None = None
    assigned_agent: int | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: int | None = None
    assigned_agent: int | None = None
    due_date: datetime | None = None
    result: str | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    status: str
    priority: str
    assigned_to: int | None = None
    assigned_agent: int | None = None
    created_by: int
    parent_task_id: int | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
