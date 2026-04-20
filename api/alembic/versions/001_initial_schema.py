"""Initial schema.

Revision ID: 001
Revises:
Create Date: 2024-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_users"),
        sa.UniqueConstraint("public_id", name="uq_app_users_public_id"),
        sa.UniqueConstraint("email", name="uq_app_users_email"),
    )
    op.create_index("ix_app_users_public_id", "app_users", ["public_id"])
    op.create_index("ix_app_users_email", "app_users", ["email"])

    op.create_table(
        "app_households",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_households"),
        sa.UniqueConstraint("public_id", name="uq_app_households_public_id"),
    )
    op.create_index("ix_app_households_public_id", "app_households", ["public_id"])

    op.create_table(
        "app_household_memberships",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("household_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", "household_id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_users.id"],
            ondelete="CASCADE",
            name="fk_app_household_memberships_user_id_app_users",
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["app_households.id"],
            ondelete="CASCADE",
            name="fk_app_household_memberships_household_id_app_households",
        ),
    )

    op.create_table(
        "app_household_members",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("household_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short", sa.String(8), nullable=False),
        sa.Column("color", sa.String(32), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False, server_default="adult"),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_household_members"),
        sa.UniqueConstraint("public_id", name="uq_app_household_members_public_id"),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["app_households.id"],
            ondelete="CASCADE",
            name="fk_app_household_members_household_id_app_households",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_users.id"],
            ondelete="SET NULL",
            name="fk_app_household_members_user_id_app_users",
        ),
    )
    op.create_index(
        "ix_app_household_members_public_id", "app_household_members", ["public_id"]
    )
    op.create_index(
        "ix_app_household_members_household_id", "app_household_members", ["household_id"]
    )
    op.create_index(
        "ix_app_household_members_user_id", "app_household_members", ["user_id"]
    )
    op.create_index(
        "ix_app_household_members_deleted_at", "app_household_members", ["deleted_at"]
    )
    op.create_index(
        "ix_app_household_members_household_id_updated_at",
        "app_household_members",
        ["household_id", "updated_at"],
    )

    op.create_table(
        "app_refresh_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_refresh_tokens"),
        sa.UniqueConstraint("public_id", name="uq_app_refresh_tokens_public_id"),
        sa.UniqueConstraint("token_hash", name="uq_app_refresh_tokens_token_hash"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_users.id"],
            ondelete="CASCADE",
            name="fk_app_refresh_tokens_user_id_app_users",
        ),
    )
    op.create_index("ix_app_refresh_tokens_user_id", "app_refresh_tokens", ["user_id"])
    op.create_index("ix_app_refresh_tokens_token_hash", "app_refresh_tokens", ["token_hash"])

    op.create_table(
        "app_areas",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("household_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("color", sa.String(32), nullable=False),
        sa.Column("slug", sa.String(32), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_areas"),
        sa.UniqueConstraint("public_id", name="uq_app_areas_public_id"),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["app_households.id"],
            ondelete="CASCADE",
            name="fk_app_areas_household_id_app_households",
        ),
    )
    op.create_index("ix_app_areas_public_id", "app_areas", ["public_id"])
    op.create_index("ix_app_areas_household_id", "app_areas", ["household_id"])
    op.create_index("ix_app_areas_deleted_at", "app_areas", ["deleted_at"])
    op.create_index(
        "ix_app_areas_household_id_updated_at", "app_areas", ["household_id", "updated_at"]
    )

    op.create_table(
        "app_projects",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("household_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("lead_member_id", sa.BigInteger(), nullable=False),
        sa.Column("for_member_id", sa.BigInteger(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_projects"),
        sa.UniqueConstraint("public_id", name="uq_app_projects_public_id"),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["app_households.id"],
            ondelete="CASCADE",
            name="fk_app_projects_household_id_app_households",
        ),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["app_areas.id"],
            ondelete="RESTRICT",
            name="fk_app_projects_area_id_app_areas",
        ),
        sa.ForeignKeyConstraint(
            ["lead_member_id"],
            ["app_household_members.id"],
            ondelete="RESTRICT",
            name="fk_app_projects_lead_member_id_app_household_members",
        ),
        sa.ForeignKeyConstraint(
            ["for_member_id"],
            ["app_household_members.id"],
            ondelete="SET NULL",
            name="fk_app_projects_for_member_id_app_household_members",
        ),
    )
    op.create_index("ix_app_projects_public_id", "app_projects", ["public_id"])
    op.create_index("ix_app_projects_household_id", "app_projects", ["household_id"])
    op.create_index("ix_app_projects_area_id", "app_projects", ["area_id"])
    op.create_index("ix_app_projects_lead_member_id", "app_projects", ["lead_member_id"])
    op.create_index("ix_app_projects_for_member_id", "app_projects", ["for_member_id"])
    op.create_index("ix_app_projects_deleted_at", "app_projects", ["deleted_at"])
    op.create_index(
        "ix_app_projects_household_id_updated_at",
        "app_projects",
        ["household_id", "updated_at"],
    )

    op.create_table(
        "app_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("household_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assignee_member_id", sa.BigInteger(), nullable=True),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("area_id", sa.BigInteger(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("is_event", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(16), nullable=False, server_default="todo"),
        sa.Column("priority", sa.String(16), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("updated_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_tasks"),
        sa.UniqueConstraint("public_id", name="uq_app_tasks_public_id"),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["app_households.id"],
            ondelete="CASCADE",
            name="fk_app_tasks_household_id_app_households",
        ),
        sa.ForeignKeyConstraint(
            ["assignee_member_id"],
            ["app_household_members.id"],
            ondelete="SET NULL",
            name="fk_app_tasks_assignee_member_id_app_household_members",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["app_projects.id"],
            ondelete="RESTRICT",
            name="fk_app_tasks_project_id_app_projects",
        ),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["app_areas.id"],
            ondelete="RESTRICT",
            name="fk_app_tasks_area_id_app_areas",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["app_users.id"],
            ondelete="RESTRICT",
            name="fk_app_tasks_created_by_user_id_app_users",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["app_users.id"],
            ondelete="RESTRICT",
            name="fk_app_tasks_updated_by_user_id_app_users",
        ),
    )
    op.create_index("ix_app_tasks_public_id", "app_tasks", ["public_id"])
    op.create_index("ix_app_tasks_household_id", "app_tasks", ["household_id"])
    op.create_index("ix_app_tasks_assignee_member_id", "app_tasks", ["assignee_member_id"])
    op.create_index("ix_app_tasks_project_id", "app_tasks", ["project_id"])
    op.create_index("ix_app_tasks_area_id", "app_tasks", ["area_id"])
    op.create_index("ix_app_tasks_due_date", "app_tasks", ["due_date"])
    op.create_index("ix_app_tasks_deleted_at", "app_tasks", ["deleted_at"])
    op.create_index(
        "ix_app_tasks_household_id_updated_at", "app_tasks", ["household_id", "updated_at"]
    )
    op.create_index(
        "ix_app_tasks_household_id_due_date", "app_tasks", ["household_id", "due_date"]
    )
    op.create_index(
        "ix_app_tasks_household_id_project_id", "app_tasks", ["household_id", "project_id"]
    )

    op.create_table(
        "app_task_comments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("author_user_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_task_comments"),
        sa.UniqueConstraint("public_id", name="uq_app_task_comments_public_id"),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["app_tasks.id"],
            ondelete="CASCADE",
            name="fk_app_task_comments_task_id_app_tasks",
        ),
        sa.ForeignKeyConstraint(
            ["author_user_id"],
            ["app_users.id"],
            ondelete="RESTRICT",
            name="fk_app_task_comments_author_user_id_app_users",
        ),
    )
    op.create_index("ix_app_task_comments_public_id", "app_task_comments", ["public_id"])
    op.create_index("ix_app_task_comments_task_id", "app_task_comments", ["task_id"])


def downgrade() -> None:
    op.drop_table("app_task_comments")
    op.drop_table("app_tasks")
    op.drop_table("app_projects")
    op.drop_table("app_areas")
    op.drop_table("app_refresh_tokens")
    op.drop_table("app_household_members")
    op.drop_table("app_household_memberships")
    op.drop_table("app_households")
    op.drop_table("app_users")
