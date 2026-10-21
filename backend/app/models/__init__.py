# Import every model here so SQLModel.metadata (used by Alembic) sees all tables.
from .user import User

__all__ = ["User"]
