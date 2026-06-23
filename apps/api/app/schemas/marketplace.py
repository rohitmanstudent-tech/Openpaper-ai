from datetime import datetime
from typing import Any

from pydantic import BaseModel


class MarketplaceItemResponse(BaseModel):
    id: str
    name: str
    item_type: str
    version: str
    description: str
    author: str
    tags: list[str] = []
    downloads: int = 0
    rating: float = 0
    install_status: str = "not_installed"
    permissions: list[str] = []
    dependencies: list[str] = []
    config_schema: dict[str, Any] = {}
    readme: str = ""
    updated_at: str = ""

    model_config = {"from_attributes": True}


class MarketplaceListResponse(BaseModel):
    items: list[MarketplaceItemResponse]
    total: int
    categories: list[str]


class InstallRequest(BaseModel):
    item_id: str
    config: dict[str, Any] = {}


class InstallResponse(BaseModel):
    success: bool
    item_id: str
    status: str
    message: str = ""
    permissions_requested: list[str] = []


class InstalledItemResponse(BaseModel):
    id: int
    item_id: str
    name: str
    item_type: str
    version: str
    status: str
    author: str
    description: str | None = None
    permissions: list[str] = []
    dependencies: list[str] = []
    installed_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
