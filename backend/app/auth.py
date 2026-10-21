import time
from collections import defaultdict, deque
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, Response, status
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .config import Settings
from .deps import SessionDep, SettingsDep
from .models import User

COOKIE_NAME = "lp_session"

_hasher = PasswordHasher()
# Verified against when the username doesn't exist, so a wrong username takes
# as long as a wrong password and doesn't leak which usernames are valid.
_DUMMY_HASH = _hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        matches = _hasher.verify(password_hash or _DUMMY_HASH, password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    return matches and password_hash is not None


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt="session")


def set_session_cookie(response: Response, user_id: int, settings: Settings) -> None:
    response.set_cookie(
        COOKIE_NAME,
        _serializer(settings).dumps({"uid": user_id}),
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        COOKIE_NAME, httponly=True, secure=settings.cookie_secure, samesite="lax"
    )


def get_current_user(request: Request, session: SessionDep, settings: SettingsDep) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise unauthorized
    try:
        data = _serializer(settings).loads(token, max_age=settings.session_days * 86400)
    except BadSignature:  # also covers expired tokens
        raise unauthorized
    user = session.get(User, data.get("uid"))
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class LoginRateLimiter:
    """In-memory limit on failed logins per client, enough for a single-user app."""

    def __init__(self, max_failures: int = 5, window_seconds: float = 300) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str) -> deque[float]:
        failures = self._failures[key]
        cutoff = time.monotonic() - self.window_seconds
        while failures and failures[0] < cutoff:
            failures.popleft()
        return failures

    def check(self, key: str) -> None:
        if len(self._prune(key)) >= self.max_failures:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS, "Too many failed logins, try again later"
            )

    def record_failure(self, key: str) -> None:
        self._prune(key).append(time.monotonic())

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def clear(self) -> None:
        self._failures.clear()
