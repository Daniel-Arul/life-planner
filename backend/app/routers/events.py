from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import NaiveDatetime
from sqlmodel import col, or_, select

from ..crud import get_or_404, save, update_changes
from ..deps import SessionDep
from ..models import Event, EventCreate, EventRead, EventUpdate

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
def list_events(
    session: SessionDep,
    start: Annotated[NaiveDatetime | None, Query(description="only events ending after this")] = None,
    end: Annotated[NaiveDatetime | None, Query(description="only events starting before this")] = None,
) -> list[Event]:
    """Stored events (series are not expanded; use /calendar for occurrences)."""
    query = select(Event).order_by(Event.start)
    if start is not None:
        query = query.where(or_(col(Event.rrule).is_not(None), Event.end >= start))
    if end is not None:
        query = query.where(Event.start < end)
    return list(session.exec(query))


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(body: EventCreate, session: SessionDep) -> Event:
    return save(session, Event.model_validate(body))


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: int, session: SessionDep) -> Event:
    return get_or_404(session, Event, event_id)


@router.patch("/{event_id}", response_model=EventRead)
def update_event(event_id: int, body: EventUpdate, session: SessionDep) -> Event:
    event = get_or_404(session, Event, event_id)
    changes = update_changes(body, required=("title", "notes", "start", "end", "all_day"))
    event.sqlmodel_update(changes)
    if event.end < event.start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "end must not be before start")
    return save(session, event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, session: SessionDep) -> None:
    session.delete(get_or_404(session, Event, event_id))
    session.commit()
