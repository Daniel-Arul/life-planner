from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlmodel import select

from ..auth import (
    CurrentUser,
    LoginRateLimiter,
    clear_session_cookie,
    set_session_cookie,
    verify_password,
)
from ..deps import SessionDep, SettingsDep
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = LoginRateLimiter()


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str


@router.post("/login", response_model=UserRead)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    key = request.client.host if request.client else "unknown"
    limiter.check(key)
    user = session.exec(select(User).where(User.username == body.username)).first()
    if not verify_password(user.password_hash if user else None, body.password):
        limiter.record_failure(key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password")
    limiter.reset(key)
    set_session_cookie(response, user.id, settings)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, settings: SettingsDep) -> None:
    clear_session_cookie(response, settings)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> User:
    return user
