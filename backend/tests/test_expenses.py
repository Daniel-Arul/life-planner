def category(api, name, budget=None):
    response = api.post(
        "/api/expense-categories", json={"name": name, "monthly_budget_cents": budget}
    )
    assert response.status_code == 201, response.text
    return response.json()


def expense(api, amount, day, category_id=None, description=""):
    response = api.post(
        "/api/expenses",
        json={
            "amount_cents": amount,
            "spent_on": day,
            "category_id": category_id,
            "description": description,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_category_crud_and_unique_names(api):
    food = category(api, "Food", 40000)
    assert api.post("/api/expense-categories", json={"name": "Food"}).status_code == 409
    renamed = api.patch(f"/api/expense-categories/{food['id']}", json={"name": " Groceries "})
    assert renamed.json()["name"] == "Groceries"
    cleared = api.patch(
        f"/api/expense-categories/{food['id']}", json={"monthly_budget_cents": None}
    )
    assert cleared.json()["monthly_budget_cents"] is None
    assert [c["name"] for c in api.get("/api/expense-categories").json()] == ["Groceries"]


def test_expense_validation(api):
    bad = {"amount_cents": 0, "spent_on": "2026-10-20"}
    assert api.post("/api/expenses", json=bad).status_code == 422
    unknown = {"amount_cents": 100, "spent_on": "2026-10-20", "category_id": 999}
    assert api.post("/api/expenses", json=unknown).status_code == 422
    created = expense(api, 1250, "2026-10-20")
    assert api.patch(f"/api/expenses/{created['id']}", json={"amount_cents": -5}).status_code == 422
    assert api.patch(f"/api/expenses/{created['id']}", json={"amount_cents": None}).status_code == 422


def test_list_filters_and_order(api):
    food = category(api, "Food")
    expense(api, 100, "2026-09-30", food["id"], "september")
    expense(api, 200, "2026-10-01", food["id"], "first")
    expense(api, 300, "2026-10-31", None, "last")

    october = api.get("/api/expenses", params={"month": "2026-10"}).json()
    assert [e["description"] for e in october] == ["last", "first"]
    by_cat = api.get("/api/expenses", params={"category_id": food["id"]}).json()
    assert len(by_cat) == 2
    ranged = api.get("/api/expenses", params={"start": "2026-09-30", "end": "2026-10-01"}).json()
    assert len(ranged) == 2
    assert api.get("/api/expenses", params={"month": "2026-13"}).status_code == 422
    assert api.get("/api/expenses", params={"month": "Oct"}).status_code == 422


def test_deleting_category_uncategorizes_expenses(api):
    food = category(api, "Food")
    spent = expense(api, 500, "2026-10-05", food["id"])
    assert api.delete(f"/api/expense-categories/{food['id']}").status_code == 204
    assert api.get(f"/api/expenses/{spent['id']}").json()["category_id"] is None


def test_monthly_stats(api):
    food = category(api, "Food", 30000)
    fun = category(api, "Fun", 5000)
    category(api, "Idle")  # no spending, no budget: left out
    travel = category(api, "Travel")  # no budget
    expense(api, 1000, "2026-09-15", food["id"])
    expense(api, 2500, "2026-10-01", food["id"])
    expense(api, 1500, "2026-10-01", travel["id"])
    expense(api, 6000, "2026-10-20", fun["id"])
    expense(api, 700, "2026-10-31")

    stats = api.get("/api/stats/expenses", params={"month": "2026-10"}).json()
    assert stats["total_cents"] == 10700
    assert stats["previous_total_cents"] == 1000
    assert stats["budget_cents"] == 35000
    assert [(c["name"], c["total_cents"], c["budget_cents"]) for c in stats["categories"]] == [
        ("Fun", 6000, 5000),
        ("Food", 2500, 30000),
        ("Travel", 1500, None),
        ("Uncategorized", 700, None),
    ]
    assert len(stats["daily"]) == 31
    assert stats["daily"][0] == {"date": "2026-10-01", "total_cents": 4000}
    assert stats["daily"][1]["total_cents"] == 0


def test_stats_previous_month_wraps_year(api):
    expense(api, 900, "2025-12-31")
    stats = api.get("/api/stats/expenses", params={"month": "2026-01"}).json()
    assert stats["previous_total_cents"] == 900
    assert stats["budget_cents"] is None
    assert stats["total_cents"] == 0


def test_calendar_has_daily_expense_totals(api):
    expense(api, 1200, "2026-10-03")
    expense(api, 800, "2026-10-03")
    items = api.get(
        "/api/calendar", params={"start": "2026-10-01T00:00:00", "end": "2026-10-08T00:00:00"}
    ).json()
    spent = [i for i in items if i["kind"] == "expense"]
    assert len(spent) == 1
    assert spent[0]["amount_cents"] == 2000
    assert spent[0]["start"] == "2026-10-03T00:00:00"


def test_config_reports_currency(api, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("PLANNER_CURRENCY", "gbp")
    get_settings.cache_clear()
    assert api.get("/api/config").json() == {"currency": "GBP"}
