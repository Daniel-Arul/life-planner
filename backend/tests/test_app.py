from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.config import get_settings
from app.db import get_engine
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_migrations_create_user_table(settings):
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
    inspector = inspect(get_engine())
    assert "user" in inspector.get_table_names()
    assert {c["name"] for c in inspector.get_columns("user")} >= {"username", "password_hash"}


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
