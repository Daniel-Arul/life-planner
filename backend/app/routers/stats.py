from collections import defaultdict
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import col, select

from ..crud import get_or_404
from ..deps import SessionDep
from ..models import Exercise, Expense, ExpenseCategory, Workout, WorkoutEntry
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


# --- Workouts -----------------------------------------------------------------


class WeekTotal(BaseModel):
    week_start: date  # Monday
    workouts: int
    minutes: int
    # Strength volume: sum of sets x reps x weight.
    volume: float


class WorkoutStats(BaseModel):
    weeks: list[WeekTotal]
    this_week_workouts: int
    this_week_minutes: int
    # Consecutive weeks with at least one workout, ending this week (or last
    # week, if this week has none yet).
    streak_weeks: int


def _volume(entry: WorkoutEntry) -> float:
    return entry.sets * entry.reps * entry.weight if entry.reps and entry.weight else 0.0


@router.get("/workouts", response_model=WorkoutStats)
def workout_stats(
    session: SessionDep,
    weeks: Annotated[int, Query(ge=1, le=104)] = 12,
    # The browser's local date, so "this week" matches the user's calendar.
    today: date | None = None,
) -> WorkoutStats:
    today = today or date.today()
    this_monday = today - timedelta(days=today.weekday())
    first_monday = this_monday - timedelta(weeks=weeks - 1)

    counts: dict[date, int] = defaultdict(int)
    minutes: dict[date, int] = defaultdict(int)
    volume: dict[date, float] = defaultdict(float)
    workout_week: dict[int, date] = {}
    for workout in session.exec(
        select(Workout).where(Workout.performed_on >= first_monday, Workout.performed_on <= today)
    ):
        week = workout.performed_on - timedelta(days=workout.performed_on.weekday())
        workout_week[workout.id] = week
        counts[week] += 1
        minutes[week] += workout.duration_min or 0
    if workout_week:
        for entry in session.exec(
            select(WorkoutEntry).where(col(WorkoutEntry.workout_id).in_(list(workout_week)))
        ):
            volume[workout_week[entry.workout_id]] += _volume(entry)

    week_list = [first_monday + timedelta(weeks=i) for i in range(weeks)]

    # The streak can run back past the chart window, so count it from all workouts.
    active_weeks = {
        d - timedelta(days=d.weekday())
        for d in session.exec(select(Workout.performed_on).where(Workout.performed_on <= today))
    }
    streak = 0
    week = this_monday if this_monday in active_weeks else this_monday - timedelta(weeks=1)
    while week in active_weeks:
        streak += 1
        week -= timedelta(weeks=1)

    return WorkoutStats(
        weeks=[
            WeekTotal(week_start=w, workouts=counts[w], minutes=minutes[w], volume=round(volume[w], 2))
            for w in week_list
        ],
        this_week_workouts=counts[this_monday],
        this_week_minutes=minutes[this_monday],
        streak_weeks=streak,
    )


class ProgressPoint(BaseModel):
    date: date
    workout_id: int
    best_weight: float | None
    max_reps: int | None
    volume: float
    distance: float | None
    duration_s: int | None


@router.get("/exercises/{exercise_id}", response_model=list[ProgressPoint])
def exercise_progress(
    exercise_id: int, session: SessionDep, limit: Annotated[int, Query(ge=1, le=500)] = 100
) -> list[ProgressPoint]:
    """One point per workout that included the exercise, oldest first."""
    get_or_404(session, Exercise, exercise_id)
    rows = session.exec(
        select(WorkoutEntry, Workout.performed_on)
        .join(Workout, col(Workout.id) == WorkoutEntry.workout_id)
        .where(WorkoutEntry.exercise_id == exercise_id)
        .order_by(col(Workout.performed_on).desc(), col(Workout.id).desc())
    )
    by_workout: dict[int, list[WorkoutEntry]] = {}
    dates: dict[int, date] = {}
    for entry, performed_on in rows:
        if entry.workout_id not in by_workout and len(by_workout) >= limit:
            continue
        by_workout.setdefault(entry.workout_id, []).append(entry)
        dates[entry.workout_id] = performed_on

    def best(values):
        values = [v for v in values if v is not None]
        return max(values) if values else None

    def total(values):
        values = [v for v in values if v is not None]
        return sum(values) if values else None

    points = [
        ProgressPoint(
            date=dates[workout_id],
            workout_id=workout_id,
            best_weight=best(e.weight for e in entries),
            max_reps=best(e.reps for e in entries),
            volume=round(sum(_volume(e) for e in entries), 2),
            distance=total(e.distance for e in entries),
            duration_s=total(e.duration_s for e in entries),
        )
        for workout_id, entries in by_workout.items()
    ]
    points.sort(key=lambda p: (p.date, p.workout_id))
    return points
