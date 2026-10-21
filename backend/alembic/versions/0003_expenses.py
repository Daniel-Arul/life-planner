"""create expense tables with starter categories

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-20
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STARTER_CATEGORIES = [
    "Groceries",
    "Eating out",
    "Transport",
    "Housing",
    "Bills",
    "Health",
    "Fun",
    "Shopping",
    "Other",
]


def upgrade() -> None:
    category = op.create_table(
        "expense_category",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=40), nullable=False, unique=True),
        sa.Column("monthly_budget_cents", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "expense",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("spent_on", sa.Date(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("expense_category.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_expense_spent_on", "expense", ["spent_on"])
    op.create_index("ix_expense_category_id", "expense", ["category_id"])

    now = datetime.now(UTC)
    op.bulk_insert(
        category,
        [
            {"name": name, "position": i, "created_at": now, "updated_at": now}
            for i, name in enumerate(STARTER_CATEGORIES, start=1)
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_expense_category_id", table_name="expense")
    op.drop_index("ix_expense_spent_on", table_name="expense")
    op.drop_table("expense")
    op.drop_table("expense_category")
