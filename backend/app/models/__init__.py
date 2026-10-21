# Import every model here so SQLModel.metadata (used by Alembic) sees all tables.
from .event import Event, EventCreate, EventRead, EventUpdate
from .expense import (
    Expense,
    ExpenseCategory,
    ExpenseCategoryCreate,
    ExpenseCategoryRead,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseRead,
    ExpenseUpdate,
)
from .idea import Idea, IdeaCreate, IdeaRead, IdeaUpdate
from .todo import Todo, TodoCreate, TodoRead, TodoReorder, TodoUpdate
from .user import User
from .workout import (
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

__all__ = [
    "Event",
    "EventCreate",
    "EventRead",
    "EventUpdate",
    "Expense",
    "ExpenseCategory",
    "ExpenseCategoryCreate",
    "ExpenseCategoryRead",
    "ExpenseCategoryUpdate",
    "ExpenseCreate",
    "ExpenseRead",
    "ExpenseUpdate",
    "Idea",
    "IdeaCreate",
    "IdeaRead",
    "IdeaUpdate",
    "Todo",
    "TodoCreate",
    "TodoRead",
    "TodoReorder",
    "TodoUpdate",
    "User",
    "EntryInput",
    "EntryRead",
    "Exercise",
    "ExerciseCreate",
    "ExerciseRead",
    "ExerciseUpdate",
    "Workout",
    "WorkoutEntry",
    "WorkoutInput",
    "WorkoutRead",
]
