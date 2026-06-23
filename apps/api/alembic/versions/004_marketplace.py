"""add marketplace installs table

Revision ID: 004_marketplace
Revises: 003_workflows
Create Date: 2024-01-04 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_marketplace"
down_revision: str | None = "003_workflows"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "marketplace_installs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("item_type", sa.Enum("agent", "workflow", "tool", "provider", name="marketplaceitemtype"), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.Enum("not_installed", "installing", "installed", "update_available", "error", "uninstalled", name="installstatus"), nullable=False, server_default="installed"),
        sa.Column("author", sa.String(255), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("dependencies", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("install_path", sa.String(500), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", "user_id", name="uq_marketplace_item_user"),
    )
    op.create_index("ix_marketplace_installs_id", "marketplace_installs", ["id"])
    op.create_index("ix_marketplace_installs_item", "marketplace_installs", ["item_id"])
    op.create_index("ix_marketplace_installs_user", "marketplace_installs", ["user_id"])


def downgrade() -> None:
    op.drop_table("marketplace_installs")
    op.execute("DROP TYPE IF EXISTS marketplaceitemtype")
    op.execute("DROP TYPE IF EXISTS installstatus")
