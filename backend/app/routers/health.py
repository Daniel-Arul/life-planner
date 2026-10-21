from fastapi import APIRouter
from sqlalchemy import text

from ..deps import SessionDep

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: SessionDep) -> dict[str, str]:
    session.exec(text("SELECT 1"))
    return {"status": "ok"}
