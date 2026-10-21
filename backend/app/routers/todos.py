from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import case, func
from sqlmodel import col, select

from ..crud import get_or_404, save, update_changes
from ..deps import SessionDep
from ..models import Todo, TodoCreate, TodoRead, TodoReorder, TodoUpdate
from ..models.base import utcnow

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=list[TodoRead])
def list_todos(
    session: SessionDep,
    status_filter: Annotated[Literal["open", "done", "all"], Query(alias="status")] = "open",
    tag: str | None = None,
) -> list[Todo]:
    query = select(Todo)
    if status_filter != "all":
        query = query.where(Todo.status == status_filter)
    if tag:
        query = query.where(Todo.tag == tag)
    if status_filter == "done":
        query = query.order_by(col(Todo.completed_at).desc())
    else:
        # Open items first, then manual order.
        query = query.order_by(case((Todo.status == "open", 0), else_=1), Todo.position, Todo.id)
    return list(session.exec(query))


@router.get("/tags", response_model=list[str])
def list_tags(session: SessionDep) -> list[str]:
    query = select(Todo.tag).where(col(Todo.tag).is_not(None)).distinct().order_by(Todo.tag)
    return [tag for tag in session.exec(query) if tag]


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(body: TodoCreate, session: SessionDep) -> Todo:
    last = session.exec(select(func.max(Todo.position))).one()
    todo = Todo.model_validate(body, update={"position": (last or 0) + 1})
    return save(session, todo)


# Registered before /{todo_id} so "reorder" isn't parsed as an id.
@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
def reorder_todos(body: TodoReorder, session: SessionDep) -> None:
    """Set manual order: the given ids take positions in the order listed."""
    todos = {t.id: t for t in session.exec(select(Todo).where(col(Todo.id).in_(body.ids)))}
    missing = set(body.ids) - todos.keys()
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown todo ids: {sorted(missing)}")
    # Reuse the slots these items already occupied so unlisted items keep their place.
    slots = sorted(t.position for t in todos.values())
    for slot, todo_id in zip(slots, body.ids, strict=True):
        todos[todo_id].position = slot
        session.add(todos[todo_id])
    session.commit()


@router.get("/{todo_id}", response_model=TodoRead)
def get_todo(todo_id: int, session: SessionDep) -> Todo:
    return get_or_404(session, Todo, todo_id)


@router.patch("/{todo_id}", response_model=TodoRead)
def update_todo(todo_id: int, body: TodoUpdate, session: SessionDep) -> Todo:
    todo = get_or_404(session, Todo, todo_id)
    changes = update_changes(body, required=("title", "notes", "priority", "status"))
    new_status = changes.get("status")
    if new_status and new_status != todo.status:
        todo.completed_at = utcnow() if new_status == "done" else None
    todo.sqlmodel_update(changes)
    return save(session, todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, session: SessionDep) -> None:
    session.delete(get_or_404(session, Todo, todo_id))
    session.commit()
