import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from app.auth import hash_password
from app.config import get_settings
from app.db import get_engine
from app.main import create_app
from app.models import User
from app.routers.auth import limiter

USERNAME = "daniel"
PASSWORD = "correct horse battery"


def _clear_caches() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setenv("PLANNER_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PLANNER_SECRET_KEY", "test-secret")
    # TestClient talks plain HTTP, which won't send Secure cookies back.
    monkeypatch.setenv("PLANNER_COOKIE_SECURE", "false")
    _clear_caches()
    yield get_settings()
    get_engine().dispose()
    _clear_caches()


@pytest.fixture
def client(settings):
    SQLModel.metadata.create_all(get_engine())
    limiter.clear()
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def user(client) -> User:
    with Session(get_engine()) as session:
        user = User(username=USERNAME, password_hash=hash_password(PASSWORD))
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def api(client, user):
    """A logged-in client."""
    response = client.post("/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 200
    return client
