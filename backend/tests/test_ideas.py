import time


def create(api, title, **fields):
    response = api.post("/api/ideas", json={"title": title, **fields})
    assert response.status_code == 201, response.text
    return response.json()


def titles(api, **params):
    return [i["title"] for i in api.get("/api/ideas", params=params).json()]


def test_create_normalizes_tags(api):
    idea = create(api, "  Garden shed  ", body="# Plan\n- cedar", tags=["#DIY", " diy", "Garden", ""])
    assert idea["title"] == "Garden shed"
    assert idea["tags"] == ["diy", "garden"]
    assert idea["status"] == "new"


def test_validation(api):
    assert api.post("/api/ideas", json={"title": ""}).status_code == 422
    assert api.post("/api/ideas", json={"title": "x", "status": "maybe"}).status_code == 422
    assert api.post("/api/ideas", json={"title": "x", "tags": ["a" * 31]}).status_code == 422
    assert api.post("/api/ideas", json={"title": "x", "tags": [str(i) for i in range(21)]}).status_code == 422
    idea = create(api, "x")
    assert api.patch(f"/api/ideas/{idea['id']}", json={"tags": None}).status_code == 422


def test_update_bumps_order(api):
    a = create(api, "A")
    time.sleep(0.01)
    create(api, "B")
    assert titles(api) == ["B", "A"]
    time.sleep(0.01)
    updated = api.patch(f"/api/ideas/{a['id']}", json={"body": "more", "tags": ["x"]}).json()
    assert updated["tags"] == ["x"]
    assert titles(api) == ["A", "B"]


def test_status_tag_and_search_filters(api):
    create(api, "Podcast", tags=["media"], status="exploring")
    create(api, "Blog redesign", body="Use the RETRO theme", tags=["media", "web"])
    create(api, "Old plan", status="archived", tags=["web"])
    create(api, "Shipped", status="done")

    assert sorted(titles(api)) == ["Blog redesign", "Podcast"]  # active = new + exploring
    assert titles(api, status="archived") == ["Old plan"]
    assert len(titles(api, status="all")) == 4
    assert sorted(titles(api, tag="#Media")) == ["Blog redesign", "Podcast"]
    # Newest first (ties broken by id), so the later-created idea leads.
    assert titles(api, status="all", tag="web") == ["Old plan", "Blog redesign"]
    assert titles(api, q="retro") == ["Blog redesign"]
    assert titles(api, q="POD") == ["Podcast"]

    tags = api.get("/api/ideas/tags").json()
    assert tags == [{"tag": "media", "count": 2}, {"tag": "web", "count": 1}]


def test_delete(api):
    idea = create(api, "Gone")
    assert api.delete(f"/api/ideas/{idea['id']}").status_code == 204
    assert api.get(f"/api/ideas/{idea['id']}").status_code == 404
