"""OpenPaper Hub — Pydantic schemas for registry API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PackageVersionResponse(BaseModel):
    version: str
    checksum_sha256: str
    signature: str | None = None
    signature_key_id: str | None = None
    dependencies: list[str] = []
    changelog: str | None = None
    published_at: datetime

    model_config = {"from_attributes": True}


class PackageDetailResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    package_type: str
    author: str
    current_version: str
    visibility: str = "public"
    downloads: int = 0
    average_rating: float = 0
    rating_count: int = 0
    verified_publisher: bool = False
    tags: list[str] = []
    homepage: str | None = None
    repository: str | None = None
    readme: str | None = None
    versions: list[PackageVersionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PackageSearchItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    package_type: str
    author: str
    current_version: str
    downloads: int = 0
    average_rating: float = 0
    rating_count: int = 0
    verified_publisher: bool = False
    tags: list[str] = []

    model_config = {"from_attributes": True}


class PackageSearchResponse(BaseModel):
    items: list[PackageSearchItem]
    total: int
    page: int = 1
    page_size: int = 20


class PublishManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    package_type: str = "tool"
    author: str = ""
    entrypoint: str = ""
    dependencies: list[str] = []
    permissions: list[str] = []
    hooks: list[str] = []
    config_schema: dict[str, Any] = {}
    homepage: str = ""
    repository: str = ""
    readme: str = ""
    tags: list[str] = []
    keywords: list[str] = []


class PublishRequest(BaseModel):
    manifest: PublishManifest
    source_archive: str = ""
    changelog: str = ""
    signature: str = ""
    signature_key_id: str = ""
    visibility: str = "public"


class PublishResponse(BaseModel):
    success: bool
    package_id: str
    version: str
    message: str = ""
    signature_verified: bool = False


class InstallResolution(BaseModel):
    package_id: str
    name: str
    version: str
    dependencies: list[str] = []
    manifest: dict[str, Any] = {}
    signature: str | None = None
    signature_key_id: str | None = None
    checksum_sha256: str = ""
    permissions_requested: list[str] = []


class ResolveResponse(BaseModel):
    success: bool
    package_id: str
    version: str
    resolution: InstallResolution
    dependency_chain: list[InstallResolution] = []


class RatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review: str = ""


class RatingResponse(BaseModel):
    success: bool
    new_average: float
    total_ratings: int


class SyncResponse(BaseModel):
    success: bool
    message: str = ""
    packages_synced: int = 0
    packages_added: int = 0
    packages_updated: int = 0
    errors: list[str] = []
