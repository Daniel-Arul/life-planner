from app.auth import COOKIE_NAME

from .conftest import PASSWORD, USERNAME


def login(client, username=USERNAME, password=PASSWORD):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_me_requires_login(client):
    assert client.get("/api/auth/me").status_code == 401


def test_login_sets_session_cookie(client, user):
    response = login(client)
    assert response.status_code == 200
    assert response.json() == {"id": user.id, "username": USERNAME}

    cookie = response.headers["set-cookie"]
    assert COOKIE_NAME in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie

    assert client.get("/api/auth/me").json()["username"] == USERNAME


def test_wrong_password_and_unknown_user_are_rejected(client, user):
    assert login(client, password="nope").status_code == 401
    assert login(client, username="someone-else").status_code == 401
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_session(client, user):
    login(client)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_tampered_cookie_is_rejected(client, user):
    login(client)
    client.cookies.set(COOKIE_NAME, client.cookies[COOKIE_NAME] + "x")
    assert client.get("/api/auth/me").status_code == 401


def test_cookie_is_secure_by_default(client, user, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("PLANNER_COOKIE_SECURE", "true")
    get_settings.cache_clear()
    assert "Secure" in login(client).headers["set-cookie"]


def test_repeated_failures_are_rate_limited(client, user):
    for _ in range(5):
        assert login(client, password="nope").status_code == 401
    # Locked out even with the right password until the window passes.
    assert login(client).status_code == 429
