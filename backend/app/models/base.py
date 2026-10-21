from datetime import UTC, datetime
from typing import Literal

from sqlmodel import Field, SQLModel

# Pastel accent names shared with the frontend theme (app.css).
Accent = Literal["lavender", "mint", "peach", "butter", "sky", "rose"]


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=utcnow, nullable=False, sa_column_kwargs={"onupdate": utcnow}
    )
