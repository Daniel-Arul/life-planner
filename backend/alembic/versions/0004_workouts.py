"""create exercise, workout and workout_entry tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "exercise",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=60), nullable=False, unique=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "workout",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("performed_on", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_workout_performed_on", "workout", ["performed_on"])

    op.create_table(
        "workout_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "workout_id",
            sa.Integer(),
            sa.ForeignKey("workout.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("distance", sa.Float(), nullable=True),
        sa.Column("duration_s", sa.Integer(), nullable=True),
    )
    op.create_index("ix_workout_entry_workout_id", "workout_entry", ["workout_id"])
    op.create_index("ix_workout_entry_exercise_id", "workout_entry", ["exercise_id"])


def downgrade() -> None:
    op.drop_index("ix_workout_entry_exercise_id", table_name="workout_entry")
    op.drop_index("ix_workout_entry_workout_id", table_name="workout_entry")
    op.drop_table("workout_entry")
    op.drop_index("ix_workout_performed_on", table_name="workout")
    op.drop_table("workout")
    op.drop_table("exercise")
