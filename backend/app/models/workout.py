from datetime import date, datetime
from typing import Literal

from pydantic import model_validator
from sqlmodel import Field, SQLModel

from .base import TimestampMixin

WorkoutKind = Literal["strength", "cardio", "mobility", "other"]

# Weights and distances are stored in whatever units the app is configured for
# (PLANNER_UNITS: metric = kg/km, imperial = lb/mi); the API never converts.


class Exercise(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=60)
    kind: str = "strength"


class ExerciseCreate(SQLModel):
    name: str = Field(min_length=1, max_length=60)
    kind: WorkoutKind = "strength"


class ExerciseUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    kind: WorkoutKind | None = None


class ExerciseRead(SQLModel):
    id: int
    name: str
    kind: WorkoutKind
    times_logged: int = 0
    last_done: date | None = None


class Workout(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    performed_on: date = Field(index=True)
    kind: str = "strength"
    title: str = Field(default="", max_length=80)
    duration_min: int | None = None
    notes: str = ""


class WorkoutEntry(SQLModel, table=True):
    """One line of a workout, e.g. "Bench press 3 x 8 @ 60": sets x reps at a weight."""

    __tablename__ = "workout_entry"

    id: int | None = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workout.id", ondelete="CASCADE", index=True)
    exercise_id: int = Field(foreign_key="exercise.id", ondelete="RESTRICT", index=True)
    position: int = 0
    sets: int = 1
    reps: int | None = None
    weight: float | None = None
    distance: float | None = None
    duration_s: int | None = None


class EntryInput(SQLModel):
    # Either an existing exercise id, or a name (matched case-insensitively,
    # created if new) so typing a new exercise in the form just works.
    exercise_id: int | None = None
    exercise_name: str | None = Field(default=None, max_length=60)
    sets: int = Field(default=1, ge=1, le=100)
    reps: int | None = Field(default=None, ge=0, le=10000)
    weight: float | None = Field(default=None, ge=0, le=10000)
    distance: float | None = Field(default=None, ge=0, le=100000)
    duration_s: int | None = Field(default=None, ge=0, le=86400 * 7)

    @model_validator(mode="after")
    def _needs_exercise(self):
        if self.exercise_id is None and not (self.exercise_name or "").strip():
            raise ValueError("each entry needs exercise_id or exercise_name")
        return self


class WorkoutInput(SQLModel):
    performed_on: date
    kind: WorkoutKind = "strength"
    title: str = Field(default="", max_length=80)
    duration_min: int | None = Field(default=None, ge=0, le=1440)
    notes: str = ""
    entries: list[EntryInput] = Field(default_factory=list, max_length=100)


class EntryRead(SQLModel):
    id: int
    exercise_id: int
    exercise_name: str
    sets: int
    reps: int | None
    weight: float | None
    distance: float | None
    duration_s: int | None


class WorkoutRead(SQLModel):
    id: int
    performed_on: date
    kind: WorkoutKind
    title: str
    duration_min: int | None
    notes: str
    entries: list[EntryRead]
    created_at: datetime
