from datetime import datetime
from typing import Literal

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from .base import TimestampMixin

IdeaStatus = Literal["new", "exploring", "done", "archived"]


def normalize_tags(tags: list[str] | None) -> list[str] | None:
    """Lowercase, strip '#' and spaces, drop blanks and duplicates (keeping order)."""
    if tags is None:
        return None
    seen: list[str] = []
    for tag in tags:
        clean = tag.strip().lstrip("#").strip().lower()
        if len(clean) > 30:
            raise ValueError(f"tag '{clean[:30]}…' is longer than 30 characters")
        if clean and clean not in seen:
            seen.append(clean)
    if len(seen) > 20:
        raise ValueError("an idea can have at most 20 tags")
    return seen


class Idea(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=120)
    # Markdown, rendered (and sanitized) in the browser.
    body: str = ""
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    status: str = Field(default="new", index=True)


class IdeaCreate(SQLModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(default="", max_length=20000)
    tags: list[str] = Field(default_factory=list)
    status: IdeaStatus = "new"

    _tags = field_validator("tags")(normalize_tags)


class IdeaUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    body: str | None = Field(default=None, max_length=20000)
    tags: list[str] | None = None
    status: IdeaStatus | None = None

    _tags = field_validator("tags")(normalize_tags)


class IdeaRead(SQLModel):
    id: int
    title: str
    body: str
    tags: list[str]
    status: IdeaStatus
    created_at: datetime
    updated_at: datetime
