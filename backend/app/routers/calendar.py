from datetime import datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, NaiveDatetime
from sqlalchemy import func
from sqlmodel import col, or_, select

from ..deps import SessionDep
from ..models import Event, Expense, Todo, Workout
from ..recurrence import occurrences

router = APIRouter(prefix="/calendar", tags=["calendar"])

MAX_RANGE = timedelta(days=400)

# Module accent colors, matching the frontend theme.
EVENT_COLOR = "lavender"
TODO_COLOR = "butter"
EXPENSE_COLOR = "peach"
WORKOUT_COLOR = "mint"


class CalendarItem(BaseModel):
    id: str
    kind: Literal["event", "todo", "expense", "workout"]
    source_id: int
    title: str
    start: NaiveDatetime
    end: NaiveDatetime
    all_day: bool
    color: str
    recurring: bool = False
    done: bool = False
    # Daily total, for kind == "expense".
    amount_cents: int | None = None


@router.get("", response_model=list[CalendarItem])
def calendar(
    start: NaiveDatetime, end: NaiveDatetime, session: SessionDep
) -> list[CalendarItem]:
    """Everything that belongs on the calendar between start and end (local time)."""
    if end <= start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "end must be after start")
    if end - start > MAX_RANGE:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "range is limited to 400 days")

    items = (
        _event_items(session, start, end)
        + _todo_items(session, start, end)
        + _expense_items(session, start, end)
        + _workout_items(session, start, end)
    )
    items.sort(key=lambda item: (item.start, not item.all_day, item.title))
    return items


def _event_items(session: SessionDep, start: datetime, end: datetime) -> list[CalendarItem]:
    events = session.exec(
        select(Event).where(
            Event.start < end,
            # One-off events must also end after the range starts; series are expanded below.
            or_(col(Event.rrule).is_not(None), Event.end >= start),
        )
    )
    items = []
    for event in events:
        for occ_start, occ_end in occurrences(event.start, event.end, event.rrule, start, end):
            item_id = f"event-{event.id}"
            if event.rrule:
                item_id += f"-{occ_start:%Y%m%dT%H%M}"
            items.append(
                CalendarItem(
                    id=item_id,
                    kind="event",
                    source_id=event.id,
                    title=event.title,
                    start=occ_start,
                    end=occ_end,
                    all_day=event.all_day,
                    color=event.color or EVENT_COLOR,
                    recurring=bool(event.rrule),
                )
            )
    return items


def _todo_items(session: SessionDep, start: datetime, end: datetime) -> list[CalendarItem]:
    todos = session.exec(
        select(Todo).where(
            col(Todo.due_date).is_not(None),
            Todo.due_date >= start.date(),
            Todo.due_date < end.date() + timedelta(days=1),
        )
    )
    items = []
    for todo in todos:
        day_start = datetime.combine(todo.due_date, time())
        day_end = day_start + timedelta(days=1)
        if day_start >= end or day_end <= start:
            continue
        items.append(
            CalendarItem(
                id=f"todo-{todo.id}",
                kind="todo",
                source_id=todo.id,
                title=todo.title,
                start=day_start,
                end=day_end,
                all_day=True,
                color=TODO_COLOR,
                done=todo.status == "done",
            )
        )
    return items


def _expense_items(session: SessionDep, start: datetime, end: datetime) -> list[CalendarItem]:
    """One all-day badge per day with spending, carrying that day's total."""
    totals = session.exec(
        select(Expense.spent_on, func.sum(Expense.amount_cents))
        .where(Expense.spent_on >= start.date(), Expense.spent_on < end.date() + timedelta(days=1))
        .group_by(Expense.spent_on)
    ).all()
    items = []
    for day, total in totals:
        day_start = datetime.combine(day, time())
        if day_start >= end or day_start + timedelta(days=1) <= start:
            continue
        items.append(
            CalendarItem(
                id=f"expense-{day:%Y%m%d}",
                kind="expense",
                source_id=0,
                title="Spent",
                start=day_start,
                end=day_start + timedelta(days=1),
                all_day=True,
                color=EXPENSE_COLOR,
                amount_cents=total,
            )
        )
    return items


def _workout_items(session: SessionDep, start: datetime, end: datetime) -> list[CalendarItem]:
    workouts = session.exec(
        select(Workout).where(
            Workout.performed_on >= start.date(),
            Workout.performed_on < end.date() + timedelta(days=1),
        )
    )
    items = []
    for workout in workouts:
        day_start = datetime.combine(workout.performed_on, time())
        if day_start >= end or day_start + timedelta(days=1) <= start:
            continue
        items.append(
            CalendarItem(
                id=f"workout-{workout.id}",
                kind="workout",
                source_id=workout.id,
                title=workout.title or f"{workout.kind.capitalize()} workout",
                start=day_start,
                end=day_start + timedelta(days=1),
                all_day=True,
                color=WORKOUT_COLOR,
            )
        )
    return items
