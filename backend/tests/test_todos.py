def create(api, **fields):
    response = api.post("/api/todos", json={"title": "Buy milk", **fields})
    assert response.status_code == 201, response.text
    return response.json()


def titles(api, **params):
    return [t["title"] for t in api.get("/api/todos", params=params).json()]


def test_create_and_get(api):
    todo = create(api, due_date="2026-10-21", priority=2, tag="home")
    assert todo["status"] == "open"
    assert todo["completed_at"] is None
    assert api.get(f"/api/todos/{todo['id']}").json()["tag"] == "home"


def test_validation(api):
    assert api.post("/api/todos", json={"title": ""}).status_code == 422
    assert api.post("/api/todos", json={"title": "x", "priority": 5}).status_code == 422
    todo = create(api)
    assert api.patch(f"/api/todos/{todo['id']}", json={"title": None}).status_code == 422
    assert api.patch(f"/api/todos/{todo['id']}", json={"status": "maybe"}).status_code == 422


def test_complete_and_reopen_sets_completed_at(api):
    todo = create(api)
    done = api.patch(f"/api/todos/{todo['id']}", json={"status": "done"}).json()
    assert done["completed_at"] is not None
    reopened = api.patch(f"/api/todos/{todo['id']}", json={"status": "open"}).json()
    assert reopened["completed_at"] is None


def test_clear_due_date(api):
    todo = create(api, due_date="2026-10-21")
    updated = api.patch(f"/api/todos/{todo['id']}", json={"due_date": None}).json()
    assert updated["due_date"] is None


def test_filters(api):
    create(api, title="a", tag="work")
    b = create(api, title="b", tag="home")
    create(api, title="c")
    api.patch(f"/api/todos/{b['id']}", json={"status": "done"})

    assert titles(api) == ["a", "c"]
    assert titles(api, status="done") == ["b"]
    assert titles(api, status="all") == ["a", "c", "b"]
    assert titles(api, status="all", tag="home") == ["b"]
    assert api.get("/api/todos/tags").json() == ["home", "work"]


def test_reorder_keeps_unlisted_items_in_place(api):
    a, b, c, d = (create(api, title=t) for t in "abcd")
    # Swap b and d only; a and c keep their slots.
    assert api.put("/api/todos/reorder", json={"ids": [d["id"], b["id"]]}).status_code == 204
    assert titles(api) == ["a", "d", "c", "b"]
    assert api.put("/api/todos/reorder", json={"ids": [999]}).status_code == 404


def test_delete(api):
    todo = create(api)
    assert api.delete(f"/api/todos/{todo['id']}").status_code == 204
    assert api.get(f"/api/todos/{todo['id']}").status_code == 404
