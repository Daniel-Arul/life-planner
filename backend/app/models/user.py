from sqlmodel import Field

from .base import TimestampMixin


class User(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=64)
    password_hash: str
