import csv
import io
import json
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import Response
from sqlmodel import Session, select

from ..deps import SessionDep
from ..models import Event, Expense, ExpenseCategory, Exercise, Idea, Todo, Workout, WorkoutEntry
from .workouts import _read_many

router = APIRouter(tags=["export"])

EXPORT_VERSION = 1
Dataset = Literal["todos", "events", "expenses", "workouts", "ideas"]


def _rows(session: Session, model, order) -> list[dict]:
    return [row.model_dump(mode="json") for row in session.exec(select(model).order_by(order))]


def _attachment(content: str, filename: str, media_type: str) -> Response:
    return Response(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export.json")
def export_json(session: SessionDep) -> Response:
    """Everything, as one JSON document, for backups or moving elsewhere."""
    workouts = list(session.exec(select(Workout).order_by(Workout.performed_on, Workout.id)))
    data = {
        "app": "life-planner",
        "version": EXPORT_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "todos": _rows(session, Todo, Todo.id),
        "events": _rows(session, Event, Event.start),
        "expense_categories": _rows(session, ExpenseCategory, ExpenseCategory.position),
        "expenses": _rows(session, Expense, Expense.spent_on),
        "exercises": _rows(session, Exercise, Exercise.name),
        "workouts": [w.model_dump(mode="json") for w in _read_many(session, workouts)],
        "ideas": _rows(session, Idea, Idea.id),
    }
    return _attachment(
        json.dumps(data, indent=2, ensure_ascii=False),
        f"life-planner-{date.today():%Y-%m-%d}.json",
        "application/json",
    )


def _csv(header: list[str], rows) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def _cents(cents: int) -> str:
    return f"{cents / 100:.2f}"


def _blank(value):
    """None as an empty cell; keep real zeros."""
    return "" if value is None else value


def _entry_cells(entry: WorkoutEntry | None) -> list:
    if entry is None:  # a workout logged without exercises
        return [""] * 5
    return [entry.sets, *(_blank(v) for v in (entry.reps, entry.weight, entry.distance, entry.duration_s))]


@router.get("/export/{dataset}.csv")
def export_csv(dataset: Dataset, session: SessionDep) -> Response:
    """One dataset as a spreadsheet-friendly CSV."""
    if dataset == "todos":
        content = _csv(
            ["title", "status", "due_date", "priority", "tag", "notes", "completed_at"],
            (
                [t.title, t.status, t.due_date or "", t.priority, t.tag or "", t.notes, t.completed_at or ""]
                for t in session.exec(select(Todo).order_by(Todo.id))
            ),
        )
    elif dataset == "events":
        content = _csv(
            ["title", "start", "end", "all_day", "repeats", "color", "notes"],
            (
                [e.title, e.start.isoformat(), e.end.isoformat(), e.all_day, e.rrule or "", e.color or "", e.notes]
                for e in session.exec(select(Event).order_by(Event.start))
            ),
        )
    elif dataset == "expenses":
        names = {c.id: c.name for c in session.exec(select(ExpenseCategory))}
        content = _csv(
            ["date", "amount", "category", "description", "paid_with"],
            (
                [x.spent_on, _cents(x.amount_cents), names.get(x.category_id, ""), x.description, x.payment_method or ""]
                for x in session.exec(select(Expense).order_by(Expense.spent_on, Expense.id))
            ),
        )
    elif dataset == "workouts":
        # One row per exercise entry, repeating the workout's details.
        rows = session.exec(
            select(Workout, WorkoutEntry, Exercise.name)
            .join(WorkoutEntry, WorkoutEntry.workout_id == Workout.id, isouter=True)
            .join(Exercise, Exercise.id == WorkoutEntry.exercise_id, isouter=True)
            .order_by(Workout.performed_on, Workout.id, WorkoutEntry.position)
        )
        content = _csv(
            ["date", "workout", "type", "minutes", "exercise", "sets", "reps", "weight", "distance", "duration_s"],
            (
                [w.performed_on, w.title, w.kind, _blank(w.duration_min), name or "", *_entry_cells(e)]
                for w, e, name in rows
            ),
        )
    else:
        content = _csv(
            ["title", "status", "tags", "body", "created_at", "updated_at"],
            (
                [i.title, i.status, ", ".join(i.tags), i.body, i.created_at.isoformat(), i.updated_at.isoformat()]
                for i in session.exec(select(Idea).order_by(Idea.id))
            ),
        )
    # BOM so Excel reads UTF-8 (accents, emoji) correctly.
    return _attachment("﻿" + content, f"life-planner-{dataset}-{date.today():%Y-%m-%d}.csv", "text/csv")
