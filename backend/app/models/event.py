from datetime import datetime

from dateutil.rrule import rrulestr
from pydantic import NaiveDatetime, field_validator, model_validator
from sqlmodel import Field, SQLModel

from .base import Accent, TimestampMixin


def validate_rrule(value: str | None) -> str | None:
    """Accept an RRULE body such as 'FREQ=WEEKLY;BYDAY=MO,WE'."""
    if value is None or not value.strip():
        return None
    value = value.strip().removeprefix("RRULE:")
    if any(c in value for c in ":\n\r"):
        raise ValueError("rrule must be a single RRULE body, without DTSTART")
    try:
        rrulestr(value, dtstart=datetime(2000, 1, 1))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid rrule: {exc}") from exc
    return value


class EventBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = ""
    # Local wall-clock times with no timezone, so a weekly 9:00 stays at 9:00
    # across daylight-saving changes. For all-day events, start is midnight of
    # the first day and end is midnight after the last day (exclusive).
    start: NaiveDatetime = Field(index=True)
    end: NaiveDatetime
    all_day: bool = False
    rrule: str | None = Field(default=None, max_length=500)
    color: Accent | None = None


class Event(EventBase, TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    color: str | None = None


class _EventValidators(SQLModel):
    @field_validator("rrule", check_fields=False)
    @classmethod
    def _rrule(cls, value: str | None) -> str | None:
        return validate_rrule(value)


class EventCreate(EventBase, _EventValidators):
    @model_validator(mode="after")
    def _end_after_start(self):
        if self.end < self.start:
            raise ValueError("end must not be before start")
        return self


class EventUpdate(_EventValidators):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None
    start: NaiveDatetime | None = None
    end: NaiveDatetime | None = None
    all_day: bool | None = None
    rrule: str | None = Field(default=None, max_length=500)
    color: Accent | None = None


class EventRead(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime
