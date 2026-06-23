from datetime import datetime
from typing import Any

from pydantic import BaseModel


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: str
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowRunCreate(BaseModel):
    workflow_id: int
    trigger: str = "manual"
    input_data: dict[str, Any] = {}


class WorkflowRunResponse(BaseModel):
    id: int
    workflow_id: int
    status: str
    trigger: str
    input_data: dict[str, Any] = {}
    output_data: dict[str, Any] | None = None
    logs: list[dict[str, Any]] = []
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowExecuteRequest(BaseModel):
    input_data: dict[str, Any] = {}
    trigger: str = "manual"
