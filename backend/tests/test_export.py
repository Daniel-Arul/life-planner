import csv
import io


def seed(api):
    api.post("/api/todos", json={"title": "Call mum", "due_date": "2026-10-21"})
    api.post("/api/events", json={"title": "Dentist", "start": "2026-10-21T09:00:00", "end": "2026-10-21T10:00:00"})
    cat = api.post("/api/expense-categories", json={"name": "Café"}).json()
    api.post("/api/expenses", json={"spent_on": "2026-10-20", "amount_cents": 475, "category_id": cat["id"], "description": "Latte, oat"})
    api.post(
        "/api/workouts",
        json={"performed_on": "2026-10-20", "title": "Push", "entries": [{"exercise_name": "Bench", "sets": 3, "reps": 8, "weight": 60}]},
    )
    api.post("/api/workouts", json={"performed_on": "2026-10-19", "kind": "cardio"})  # no entries
    api.post("/api/ideas", json={"title": "Shed", "body": "# Plan", "tags": ["home", "diy"]})


def read_csv(response):
    assert response.headers["content-type"].startswith("text/csv")
    text = response.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def test_json_export_has_everything(api):
    seed(api)
    response = api.get("/api/export.json")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    data = response.json()
    assert data["app"] == "life-planner" and data["version"] == 1
    assert [t["title"] for t in data["todos"]] == ["Call mum"]
    assert data["events"][0]["start"] == "2026-10-21T09:00:00"
    assert data["expenses"][0]["amount_cents"] == 475
    assert data["workouts"][1]["entries"][0]["exercise_name"] == "Bench"
    assert data["ideas"][0]["tags"] == ["home", "diy"]
    assert "password_hash" not in response.text


def test_csv_exports(api):
    seed(api)
    expenses = read_csv(api.get("/api/export/expenses.csv"))
    assert expenses == [
        {"date": "2026-10-20", "amount": "4.75", "category": "Café", "description": "Latte, oat", "paid_with": ""}
    ]
    workouts = read_csv(api.get("/api/export/workouts.csv"))
    assert [(w["date"], w["exercise"], w["weight"]) for w in workouts] == [
        ("2026-10-19", "", ""),
        ("2026-10-20", "Bench", "60.0"),
    ]
    assert read_csv(api.get("/api/export/ideas.csv"))[0]["tags"] == "home, diy"
    assert read_csv(api.get("/api/export/todos.csv"))[0]["due_date"] == "2026-10-21"
    assert read_csv(api.get("/api/export/events.csv"))[0]["all_day"] == "False"
    assert api.get("/api/export/users.csv").status_code == 422


def test_export_requires_login(client):
    assert client.get("/api/export.json").status_code == 401
    assert client.get("/api/export/todos.csv").status_code == 401


def test_manifest_mime_type():
    import mimetypes

    import app.main  # noqa: F401  (registers the type)

    assert mimetypes.guess_type("manifest.webmanifest")[0] == "application/manifest+json"
