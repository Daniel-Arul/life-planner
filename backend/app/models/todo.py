from datetime import date, datetime
from typing import Literal

from sqlmodel import Field, SQLModel

from .base import TimestampMixin

TodoStatus = Literal["open", "done"]


class TodoBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = ""
    due_date: date | None = Field(default=None, index=True)
    # 0 = none, 1 = low, 2 = medium, 3 = high
    priority: int = Field(default=0, ge=0, le=3)
    tag: str | None = Field(default=None, max_length=50)


class Todo(TodoBase, TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(default="open", index=True)
    completed_at: datetime | None = None
    # Manual sort order within the list; lower comes first.
    position: int = 0


class TodoCreate(TodoBase):
    pass


class TodoUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None
    due_date: date | None = None
    priority: int | None = Field(default=None, ge=0, le=3)
    tag: str | None = Field(default=None, max_length=50)
    status: TodoStatus | None = None


class TodoRead(TodoBase):
    id: int
    status: TodoStatus
    completed_at: datetime | None
    position: int
    created_at: datetime
    updated_at: datetime


class TodoReorder(SQLModel):
    ids: list[int]
