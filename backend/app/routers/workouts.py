from collections import defaultdict
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from ..crud import get_or_404, save, update_changes
from ..deps import SessionDep
from ..models import (
    EntryInput,
    EntryRead,
    Exercise,
    ExerciseCreate,
    ExerciseRead,
    ExerciseUpdate,
    Workout,
    WorkoutEntry,
    WorkoutInput,
    WorkoutRead,
)
from ..months import OptionalMonthParam, month_bounds

exercises_router = APIRouter(prefix="/exercises", tags=["workouts"])
router = APIRouter(prefix="/workouts", tags=["workouts"])


# --- Exercises ----------------------------------------------------------------


def _find_exercise(session: Session, name: str) -> Exercise | None:
    query = select(Exercise).where(func.lower(Exercise.name) == name.strip().lower())
    return session.exec(query).first()


@exercises_router.get("", response_model=list[ExerciseRead])
def list_exercises(session: SessionDep) -> list[ExerciseRead]:
    """All exercises with how often and how recently they were logged."""
    usage = {
        exercise_id: (count, last)
        for exercise_id, count, last in session.exec(
            select(
                WorkoutEntry.exercise_id,
                func.count(func.distinct(WorkoutEntry.workout_id)),
                func.max(Workout.performed_on),
            )
            .join(Workout, col(Workout.id) == WorkoutEntry.workout_id)
            .group_by(WorkoutEntry.exercise_id)
        )
    }
    return [
        ExerciseRead(
            id=e.id,
            name=e.name,
            kind=e.kind,
            times_logged=usage.get(e.id, (0, None))[0],
            last_done=usage.get(e.id, (0, None))[1],
        )
        for e in session.exec(select(Exercise).order_by(func.lower(Exercise.name)))
    ]


@exercises_router.post("", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
def create_exercise(body: ExerciseCreate, session: SessionDep) -> ExerciseRead:
    if _find_exercise(session, body.name):
        raise HTTPException(status.HTTP_409_CONFLICT, f"'{body.name.strip()}' already exists")
    exercise = save(session, Exercise(name=body.name.strip(), kind=body.kind))
    return ExerciseRead(id=exercise.id, name=exercise.name, kind=exercise.kind)


@exercises_router.patch("/{exercise_id}", response_model=ExerciseRead)
def update_exercise(exercise_id: int, body: ExerciseUpdate, session: SessionDep) -> ExerciseRead:
    exercise = get_or_404(session, Exercise, exercise_id)
    changes = update_changes(body, required=("name", "kind"))
    if "name" in changes:
        changes["name"] = changes["name"].strip()
        clash = _find_exercise(session, changes["name"])
        if clash and clash.id != exercise.id:
            raise HTTPException(status.HTTP_409_CONFLICT, f"'{changes['name']}' already exists")
    exercise.sqlmodel_update(changes)
    exercise = save(session, exercise)
    return ExerciseRead(id=exercise.id, name=exercise.name, kind=exercise.kind)


@exercises_router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: int, session: SessionDep) -> None:
    exercise = get_or_404(session, Exercise, exercise_id)
    uses = session.exec(
        select(func.count()).select_from(WorkoutEntry).where(WorkoutEntry.exercise_id == exercise_id)
    ).one()
    if uses:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"'{exercise.name}' is in {uses} logged entr{'y' if uses == 1 else 'ies'}; "
            "remove those first or rename it instead",
        )
    session.delete(exercise)
    session.commit()


# --- Workouts -----------------------------------------------------------------


def _read_many(session: Session, workouts: list[Workout]) -> list[WorkoutRead]:
    """Attach entries (with exercise names) to workouts in one query."""
    ids = [w.id for w in workouts]
    entries: dict[int, list[EntryRead]] = defaultdict(list)
    if ids:
        rows = session.exec(
            select(WorkoutEntry, Exercise.name)
            .join(Exercise, col(Exercise.id) == WorkoutEntry.exercise_id)
            .where(col(WorkoutEntry.workout_id).in_(ids))
            .order_by(WorkoutEntry.workout_id, WorkoutEntry.position)
        )
        for entry, name in rows:
            entries[entry.workout_id].append(
                EntryRead(**entry.model_dump(exclude={"workout_id", "position"}), exercise_name=name)
            )
    return [
        WorkoutRead(**w.model_dump(exclude={"updated_at"}), entries=entries[w.id]) for w in workouts
    ]


def _resolve_exercise(session: Session, entry: EntryInput, kind: str) -> int:
    if entry.exercise_id is not None:
        if session.get(Exercise, entry.exercise_id) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown exercise")
        return entry.exercise_id
    name = entry.exercise_name.strip()
    exercise = _find_exercise(session, name)
    if exercise is None:
        exercise = Exercise(name=name, kind=kind)
        session.add(exercise)
        session.flush()
    return exercise.id


def _write(session: Session, workout: Workout, body: WorkoutInput) -> WorkoutRead:
    workout.sqlmodel_update(body.model_dump(exclude={"entries"}))
    workout.title = workout.title.strip()
    session.add(workout)
    session.flush()
    session.exec(delete(WorkoutEntry).where(col(WorkoutEntry.workout_id) == workout.id))
    for position, entry in enumerate(body.entries):
        session.add(
            WorkoutEntry(
                workout_id=workout.id,
                exercise_id=_resolve_exercise(session, entry, body.kind),
                position=position,
                **entry.model_dump(include={"sets", "reps", "weight", "distance", "duration_s"}),
            )
        )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Could not save workout")
    session.refresh(workout)
    return _read_many(session, [workout])[0]


@router.get("", response_model=list[WorkoutRead])
def list_workouts(
    session: SessionDep,
    month: OptionalMonthParam = None,
    start: date | None = None,
    end: date | None = None,
    limit: int = 200,
) -> list[WorkoutRead]:
    """Newest first. Filter by month (YYYY-MM) or an inclusive start/end date range."""
    query = select(Workout).order_by(col(Workout.performed_on).desc(), col(Workout.id).desc())
    if month:
        first, after = month_bounds(month)
        query = query.where(Workout.performed_on >= first, Workout.performed_on < after)
    if start:
        query = query.where(Workout.performed_on >= start)
    if end:
        query = query.where(Workout.performed_on <= end)
    return _read_many(session, list(session.exec(query.limit(min(max(limit, 1), 1000)))))


@router.post("", response_model=WorkoutRead, status_code=status.HTTP_201_CREATED)
def create_workout(body: WorkoutInput, session: SessionDep) -> WorkoutRead:
    return _write(session, Workout(performed_on=body.performed_on), body)


@router.get("/{workout_id}", response_model=WorkoutRead)
def get_workout(workout_id: int, session: SessionDep) -> WorkoutRead:
    return _read_many(session, [get_or_404(session, Workout, workout_id)])[0]


@router.put("/{workout_id}", response_model=WorkoutRead)
def replace_workout(workout_id: int, body: WorkoutInput, session: SessionDep) -> WorkoutRead:
    """Replace the workout and all its entries (the form always sends the whole thing)."""
    return _write(session, get_or_404(session, Workout, workout_id), body)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, session: SessionDep) -> None:
    session.delete(get_or_404(session, Workout, workout_id))
    session.commit()
