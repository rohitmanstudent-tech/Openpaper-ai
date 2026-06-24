import enum
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MarketplaceItemType(enum.StrEnum):
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    PROVIDER = "provider"


class InstallStatus(enum.StrEnum):
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    UPDATE_AVAILABLE = "update_available"
    ERROR = "error"
    UNINSTALLED = "uninstalled"


class InstalledMarketplaceItem(Base):
    __tablename__ = "marketplace_installs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_type: Mapped[MarketplaceItemType] = mapped_column(SAEnum(MarketplaceItemType), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    status: Mapped[InstallStatus] = mapped_column(SAEnum(InstallStatus), default=InstallStatus.INSTALLED)
    author: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, nullable=True)
    permissions: Mapped[dict] = mapped_column(JSON, default=list)
    dependencies: Mapped[dict] = mapped_column(JSON, default=list)
    install_path: Mapped[str] = mapped_column(String(500), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
