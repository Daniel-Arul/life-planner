from typing import TypeVar

from fastapi import HTTPException, status
from sqlmodel import Session, SQLModel

ModelT = TypeVar("ModelT", bound=SQLModel)


def get_or_404(session: Session, model: type[ModelT], item_id: int) -> ModelT:
    item = session.get(model, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} not found")
    return item


def update_changes(body: SQLModel, required: tuple[str, ...]) -> dict:
    """Fields the client sent in a PATCH, refusing null for required columns."""
    changes = body.model_dump(exclude_unset=True)
    nulled = [name for name in required if name in changes and changes[name] is None]
    if nulled:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"{', '.join(nulled)} cannot be null"
        )
    return changes


def save(session: Session, item: ModelT) -> ModelT:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
