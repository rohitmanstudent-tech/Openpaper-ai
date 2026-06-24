"""add hub registry tables

Revision ID: 005_hub_registry
Revises: 004_marketplace
Create Date: 2024-01-05 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005_hub_registry"
down_revision: str | None = "004_marketplace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hub_packages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("package_id", sa.String(200), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("package_type", sa.Enum("agent", "workflow", "tool", "provider", name="packagetype"), nullable=False),
        sa.Column("author", sa.String(255), nullable=False, server_default=""),
        sa.Column("publisher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("current_version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column(
            "visibility",
            sa.Enum("public", "private", "organization", name="packagevisibility"),
            nullable=False,
            server_default="public",
        ),
        sa.Column("downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_sum", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_publisher", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("keywords", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("homepage", sa.String(500), nullable=True),
        sa.Column("repository", sa.String(500), nullable=True),
        sa.Column("readme", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hub_packages_id", "hub_packages", ["id"])
    op.create_index("ix_hub_packages_package_id", "hub_packages", ["package_id"])

    op.create_table(
        "hub_package_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("hub_packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("signature_key_id", sa.String(200), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("dependencies", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hub_package_versions_id", "hub_package_versions", ["id"])

    op.create_table(
        "hub_package_ratings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("hub_packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hub_package_ratings_id", "hub_package_ratings", ["id"])

    op.create_table(
        "hub_sync_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
        sa.Column("packages_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("packages_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("packages_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hub_sync_log_id", "hub_sync_log", ["id"])

    op.create_table(
        "hub_publisher_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key_id", sa.String(200), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.String(50), nullable=False, server_default="ed25519"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hub_publisher_keys_id", "hub_publisher_keys", ["id"])
    op.create_index("ix_hub_publisher_keys_key_id", "hub_publisher_keys", ["key_id"])


def downgrade() -> None:
    op.drop_table("hub_publisher_keys")
    op.drop_table("hub_sync_log")
    op.drop_table("hub_package_ratings")
    op.drop_table("hub_package_versions")
    op.drop_table("hub_packages")
    op.execute("DROP TYPE IF EXISTS packagetype")
    op.execute("DROP TYPE IF EXISTS packagevisibility")
