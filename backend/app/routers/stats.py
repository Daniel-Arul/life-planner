from datetime import date, timedelta

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import select

from ..deps import SessionDep
from ..models import Expense, ExpenseCategory
from ..months import MonthParam, month_bounds, previous_month

router = APIRouter(prefix="/stats", tags=["stats"])


class CategoryTotal(BaseModel):
    id: int | None  # None = uncategorized
    name: str
    total_cents: int
    budget_cents: int | None


class DayTotal(BaseModel):
    date: date
    total_cents: int


class ExpenseStats(BaseModel):
    month: str
    total_cents: int
    previous_total_cents: int
    # Sum of category budgets; None when no category has a budget.
    budget_cents: int | None
    categories: list[CategoryTotal]
    daily: list[DayTotal]


def _total(session: SessionDep, start: date, end: date) -> int:
    query = select(func.coalesce(func.sum(Expense.amount_cents), 0)).where(
        Expense.spent_on >= start, Expense.spent_on < end
    )
    return session.exec(query).one()


@router.get("/expenses", response_model=ExpenseStats)
def expense_stats(month: MonthParam, session: SessionDep) -> ExpenseStats:
    start, end = month_bounds(month)
    in_month = (Expense.spent_on >= start, Expense.spent_on < end)

    by_category = dict(
        session.exec(
            select(Expense.category_id, func.sum(Expense.amount_cents))
            .where(*in_month)
            .group_by(Expense.category_id)
        ).all()
    )
    categories = [
        CategoryTotal(
            id=c.id,
            name=c.name,
            total_cents=by_category.get(c.id, 0),
            budget_cents=c.monthly_budget_cents,
        )
        for c in session.exec(select(ExpenseCategory))
        # Hide idle categories unless they carry a budget worth tracking.
        if by_category.get(c.id) or c.monthly_budget_cents
    ]
    if by_category.get(None):
        categories.append(
            CategoryTotal(id=None, name="Uncategorized", total_cents=by_category[None], budget_cents=None)
        )
    categories.sort(key=lambda c: (-c.total_cents, c.name))

    by_day = dict(
        session.exec(
            select(Expense.spent_on, func.sum(Expense.amount_cents))
            .where(*in_month)
            .group_by(Expense.spent_on)
        ).all()
    )
    days = (end - start).days
    daily = [
        DayTotal(date=day, total_cents=by_day.get(day, 0))
        for day in (start + timedelta(days=i) for i in range(days))
    ]

    budgets = [c.budget_cents for c in categories if c.budget_cents]
    return ExpenseStats(
        month=month,
        total_cents=sum(by_category.values()),
        previous_total_cents=_total(session, previous_month(start), start),
        budget_cents=sum(budgets) if budgets else None,
        categories=categories,
        daily=daily,
    )
