from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from ..crud import get_or_404, save, update_changes
from ..deps import SessionDep
from ..models import (
    Expense,
    ExpenseCategory,
    ExpenseCategoryCreate,
    ExpenseCategoryRead,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseRead,
    ExpenseUpdate,
)
from ..months import OptionalMonthParam, month_bounds

categories_router = APIRouter(prefix="/expense-categories", tags=["expenses"])
router = APIRouter(prefix="/expenses", tags=["expenses"])


# --- Categories ---------------------------------------------------------------


def _save_category(session: Session, category: ExpenseCategory) -> ExpenseCategory:
    try:
        return save(session, category)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"A category named '{category.name}' already exists"
        )


@categories_router.get("", response_model=list[ExpenseCategoryRead])
def list_categories(session: SessionDep) -> list[ExpenseCategory]:
    query = select(ExpenseCategory).order_by(ExpenseCategory.position, ExpenseCategory.name)
    return list(session.exec(query))


@categories_router.post("", response_model=ExpenseCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(body: ExpenseCategoryCreate, session: SessionDep) -> ExpenseCategory:
    last = session.exec(select(func.max(ExpenseCategory.position))).one()
    category = ExpenseCategory.model_validate(
        body, update={"name": body.name.strip(), "position": (last or 0) + 1}
    )
    return _save_category(session, category)


@categories_router.patch("/{category_id}", response_model=ExpenseCategoryRead)
def update_category(
    category_id: int, body: ExpenseCategoryUpdate, session: SessionDep
) -> ExpenseCategory:
    category = get_or_404(session, ExpenseCategory, category_id)
    changes = update_changes(body, required=("name",))
    if "name" in changes:
        changes["name"] = changes["name"].strip()
    category.sqlmodel_update(changes)
    return _save_category(session, category)


@categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, session: SessionDep) -> None:
    """Delete a category; its expenses become uncategorized (ON DELETE SET NULL)."""
    session.delete(get_or_404(session, ExpenseCategory, category_id))
    session.commit()


# --- Expenses -----------------------------------------------------------------


def _check_category(session: Session, category_id: int | None) -> None:
    if category_id is not None and session.get(ExpenseCategory, category_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown category")


@router.get("", response_model=list[ExpenseRead])
def list_expenses(
    session: SessionDep,
    month: OptionalMonthParam = None,
    start: date | None = None,
    end: date | None = None,
    category_id: int | None = None,
) -> list[Expense]:
    """Newest first. Filter by month (YYYY-MM) or an inclusive start/end date range."""
    query = select(Expense).order_by(col(Expense.spent_on).desc(), col(Expense.id).desc())
    if month:
        start, end_exclusive = month_bounds(month)
        query = query.where(Expense.spent_on >= start, Expense.spent_on < end_exclusive)
    else:
        if start:
            query = query.where(Expense.spent_on >= start)
        if end:
            query = query.where(Expense.spent_on <= end)
    if category_id is not None:
        query = query.where(Expense.category_id == category_id)
    return list(session.exec(query))


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(body: ExpenseCreate, session: SessionDep) -> Expense:
    _check_category(session, body.category_id)
    return save(session, Expense.model_validate(body))


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(expense_id: int, session: SessionDep) -> Expense:
    return get_or_404(session, Expense, expense_id)


@router.patch("/{expense_id}", response_model=ExpenseRead)
def update_expense(expense_id: int, body: ExpenseUpdate, session: SessionDep) -> Expense:
    expense = get_or_404(session, Expense, expense_id)
    changes = update_changes(body, required=("spent_on", "amount_cents", "description"))
    if "category_id" in changes:
        _check_category(session, changes["category_id"])
    expense.sqlmodel_update(changes)
    return save(session, expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, session: SessionDep) -> None:
    session.delete(get_or_404(session, Expense, expense_id))
    session.commit()
