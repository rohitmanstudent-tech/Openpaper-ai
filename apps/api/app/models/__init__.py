import enum
from datetime import UTC, datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.MEMBER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    agents = relationship("Agent", back_populates="owner")
    chats = relationship("Chat", back_populates="user")
    tasks = relationship("Task", back_populates="assignee", foreign_keys="[Task.assigned_to]")
    refresh_tokens = relationship("RefreshToken", backref="user", cascade="all, delete-orphan")


from .hub_registry import (  # noqa: E402, F401
    PublisherKey,
    RegistryPackage,
    RegistryPackageVersion,
    RegistryRating,
    RegistrySyncLog,
)
from .marketplace import InstalledMarketplaceItem  # noqa: E402, F401
from .refresh_token import RefreshToken  # noqa: E402, F401
from .workflow import RunStatus, Workflow, WorkflowRun, WorkflowStatus  # noqa: E402, F401
