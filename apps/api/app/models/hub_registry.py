"""OpenPaper Hub — remote registry models for package metadata,
versioning, signatures, downloads, and ratings."""

import enum
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PackageType(enum.StrEnum):
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    PROVIDER = "provider"


class PackageVisibility(enum.StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    ORGANIZATION = "organization"


class RegistryPackage(Base):
    __tablename__ = "hub_packages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    package_id: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    package_type: Mapped[PackageType] = mapped_column(SAEnum(PackageType), nullable=False)
    author: Mapped[str] = mapped_column(String(255), default="")
    publisher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    current_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    visibility: Mapped[PackageVisibility] = mapped_column(SAEnum(PackageVisibility), default=PackageVisibility.PUBLIC)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    rating_sum: Mapped[int] = mapped_column(Integer, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    verified_publisher: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    keywords: Mapped[dict] = mapped_column(JSON, default=list)
    homepage: Mapped[str] = mapped_column(String(500), nullable=True)
    repository: Mapped[str] = mapped_column(String(500), nullable=True)
    readme: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    versions = relationship("RegistryPackageVersion", back_populates="package", cascade="all, delete-orphan",
                            order_by="RegistryPackageVersion.created_at.desc()")
    ratings = relationship("RegistryRating", back_populates="package", cascade="all, delete-orphan")

    @property
    def average_rating(self) -> float:
        if self.rating_count == 0:
            return 0.0
        return round(self.rating_sum / self.rating_count, 2)


class RegistryPackageVersion(Base):
    __tablename__ = "hub_package_versions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("hub_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=True)
    signature_key_id: Mapped[str] = mapped_column(String(200), nullable=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    dependencies: Mapped[dict] = mapped_column(JSON, default=list)
    changelog: Mapped[str] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    package = relationship("RegistryPackage", back_populates="versions")


class RegistryRating(Base):
    __tablename__ = "hub_package_ratings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("hub_packages.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    package = relationship("RegistryPackage", back_populates="ratings")


class RegistrySyncLog(Base):
    __tablename__ = "hub_sync_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    packages_synced: Mapped[int] = mapped_column(Integer, default=0)
    packages_added: Mapped[int] = mapped_column(Integer, default=0)
    packages_updated: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[dict] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class PublisherKey(Base):
    __tablename__ = "hub_publisher_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    key_id: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), default="ed25519")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
