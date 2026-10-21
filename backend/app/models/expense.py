from datetime import date, datetime

from sqlmodel import Field, SQLModel

from .base import TimestampMixin

# Money is always integer cents (minor units) to avoid float rounding.


class ExpenseCategoryBase(SQLModel):
    name: str = Field(min_length=1, max_length=40)
    monthly_budget_cents: int | None = Field(default=None, ge=0)


class ExpenseCategory(ExpenseCategoryBase, TimestampMixin, table=True):
    __tablename__ = "expense_category"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=40)
    position: int = 0


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategoryUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    monthly_budget_cents: int | None = Field(default=None, ge=0)


class ExpenseCategoryRead(ExpenseCategoryBase):
    id: int
    position: int


class ExpenseBase(SQLModel):
    spent_on: date = Field(index=True)
    amount_cents: int = Field(gt=0)
    category_id: int | None = Field(
        default=None, foreign_key="expense_category.id", ondelete="SET NULL", index=True
    )
    description: str = Field(default="", max_length=200)
    payment_method: str | None = Field(default=None, max_length=30)


class Expense(ExpenseBase, TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(SQLModel):
    spent_on: date | None = None
    amount_cents: int | None = Field(default=None, gt=0)
    category_id: int | None = None
    description: str | None = Field(default=None, max_length=200)
    payment_method: str | None = Field(default=None, max_length=30)


class ExpenseRead(ExpenseBase):
    id: int
    created_at: datetime
