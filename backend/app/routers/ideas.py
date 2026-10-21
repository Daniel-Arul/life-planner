from collections import Counter
from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, text
from sqlmodel import col, select

from ..crud import get_or_404, save, update_changes
from ..deps import SessionDep
from ..models import Idea, IdeaCreate, IdeaRead, IdeaUpdate

router = APIRouter(prefix="/ideas", tags=["ideas"])

StatusFilter = Literal["active", "new", "exploring", "done", "archived", "all"]
ACTIVE = ("new", "exploring")


class TagCount(BaseModel):
    tag: str
    count: int


@router.get("", response_model=list[IdeaRead])
def list_ideas(
    session: SessionDep,
    status_filter: Annotated[StatusFilter, Query(alias="status")] = "active",
    tag: str | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[Idea]:
    """Most recently updated first. "active" means new or exploring."""
    query = select(Idea).order_by(col(Idea.updated_at).desc(), col(Idea.id).desc())
    if status_filter == "active":
        query = query.where(col(Idea.status).in_(ACTIVE))
    elif status_filter != "all":
        query = query.where(Idea.status == status_filter)
    if tag:
        query = query.where(
            text("EXISTS (SELECT 1 FROM json_each(idea.tags) WHERE json_each.value = :tag)").bindparams(
                tag=tag.strip().lstrip("#").lower()
            )
        )
    if q and q.strip():
        pattern = f"%{q.strip().lower()}%"
        query = query.where(or_(func.lower(Idea.title).like(pattern), func.lower(Idea.body).like(pattern)))
    return list(session.exec(query.limit(limit)))


@router.get("/tags", response_model=list[TagCount])
def list_tags(session: SessionDep) -> list[TagCount]:
    """Tags on non-archived ideas, most used first."""
    counts = Counter(
        tag
        for tags in session.exec(select(Idea.tags).where(Idea.status != "archived"))
        for tag in tags
    )
    return [TagCount(tag=t, count=c) for t, c in sorted(counts.items(), key=lambda tc: (-tc[1], tc[0]))]


@router.post("", response_model=IdeaRead, status_code=status.HTTP_201_CREATED)
def create_idea(body: IdeaCreate, session: SessionDep) -> Idea:
    return save(session, Idea.model_validate(body, update={"title": body.title.strip()}))


@router.get("/{idea_id}", response_model=IdeaRead)
def get_idea(idea_id: int, session: SessionDep) -> Idea:
    return get_or_404(session, Idea, idea_id)


@router.patch("/{idea_id}", response_model=IdeaRead)
def update_idea(idea_id: int, body: IdeaUpdate, session: SessionDep) -> Idea:
    idea = get_or_404(session, Idea, idea_id)
    changes = update_changes(body, required=("title", "body", "tags", "status"))
    if "title" in changes:
        changes["title"] = changes["title"].strip()
    idea.sqlmodel_update(changes)
    return save(session, idea)


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idea(idea_id: int, session: SessionDep) -> None:
    session.delete(get_or_404(session, Idea, idea_id))
    session.commit()
