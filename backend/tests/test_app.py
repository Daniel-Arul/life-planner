from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlmodel import SQLModel

from app.config import get_settings
from app.db import get_engine
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_migrations_match_models(settings):
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
    tables = set(inspect(get_engine()).get_table_names())
    assert {
        "user",
        "event",
        "todo",
        "expense",
        "expense_category",
        "exercise",
        "workout",
        "workout_entry",
    } <= tables

    with get_engine().connect() as connection:
        context = MigrationContext.configure(connection)
        diff = compare_metadata(context, SQLModel.metadata)
    assert diff == [], "models changed without a migration"


def test_data_endpoints_require_login(client):
    for path in (
        "/api/todos",
        "/api/events",
        "/api/expenses",
        "/api/expense-categories",
        "/api/config",
        "/api/stats/expenses?month=2026-10",
        "/api/workouts",
        "/api/exercises",
        "/api/stats/workouts",
        "/api/calendar?start=2026-10-01T00:00&end=2026-11-01T00:00",
    ):
        assert client.get(path).status_code == 401, path


def test_serves_spa_with_fallback(settings, tmp_path, monkeypatch):
    static = tmp_path / "static"
    (static / "_app" / "immutable").mkdir(parents=True)
    (static / "index.html").write_text("<html>spa</html>")
    (static / "_app" / "immutable" / "app.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("outside static dir")
    monkeypatch.setenv("PLANNER_STATIC_DIR", str(static))
    get_settings.cache_clear()

    client = TestClient(create_app())
    assert client.get("/").text == "<html>spa</html>"
    assert client.head("/").status_code == 200
    assert client.get("/calendar").text == "<html>spa</html>"  # client-side route

    asset = client.get("/_app/immutable/app.js")
    assert asset.text == "console.log(1)"
    assert "immutable" in asset.headers["cache-control"]

    assert client.get("/api/does-not-exist").status_code == 404
    assert "outside" not in client.get("/../secret.txt").text
