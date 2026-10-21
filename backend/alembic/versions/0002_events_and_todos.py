"""create event and todo tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("start", sa.DateTime(), nullable=False),
        sa.Column("end", sa.DateTime(), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False),
        sa.Column("rrule", sa.String(length=500), nullable=True),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_event_start", "event", ["start"])

    op.create_table(
        "todo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_todo_due_date", "todo", ["due_date"])
    op.create_index("ix_todo_status", "todo", ["status"])


def downgrade() -> None:
    op.drop_index("ix_todo_status", table_name="todo")
    op.drop_index("ix_todo_due_date", table_name="todo")
    op.drop_table("todo")
    op.drop_index("ix_event_start", table_name="event")
    op.drop_table("event")
