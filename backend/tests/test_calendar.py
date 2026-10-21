from datetime import datetime

from app.recurrence import MAX_OCCURRENCES, occurrences

OCT = {"start": "2026-10-01T00:00:00", "end": "2026-11-01T00:00:00"}


def feed(api, **params):
    response = api.get("/api/calendar", params={**OCT, **params})
    assert response.status_code == 200, response.text
    return response.json()


def test_combines_events_and_todos(api):
    api.post(
        "/api/events",
        json={"title": "Dentist", "start": "2026-10-21T09:00:00", "end": "2026-10-21T10:00:00"},
    )
    todo = api.post("/api/todos", json={"title": "Pay rent", "due_date": "2026-10-21"}).json()
    api.patch(f"/api/todos/{todo['id']}", json={"status": "done"})
    api.post("/api/todos", json={"title": "No date"})
    api.post("/api/todos", json={"title": "November", "due_date": "2026-11-01"})

    items = feed(api)
    assert [(i["kind"], i["title"]) for i in items] == [("todo", "Pay rent"), ("event", "Dentist")]
    todo_item = items[0]
    assert todo_item["all_day"] is True
    assert todo_item["done"] is True
    assert todo_item["color"] == "butter"
    assert todo_item["start"] == "2026-10-21T00:00:00"
    assert items[1]["color"] == "lavender"


def test_expands_recurring_events(api):
    api.post(
        "/api/events",
        json={
            "title": "Gym",
            "start": "2026-09-07T18:00:00",  # a Monday, before the range
            "end": "2026-09-07T19:00:00",
            "rrule": "FREQ=WEEKLY;BYDAY=MO",
        },
    )
    items = feed(api)
    assert [i["start"][:10] for i in items] == [
        "2026-10-05",
        "2026-10-12",
        "2026-10-19",
        "2026-10-26",
    ]
    assert all(i["recurring"] for i in items)
    assert len({i["id"] for i in items}) == 4  # each occurrence has its own id


def test_includes_events_overlapping_range_edges(api):
    api.post(
        "/api/events",
        json={"title": "Trip", "start": "2026-09-28T00:00:00", "end": "2026-10-03T00:00:00", "all_day": True},
    )
    api.post(
        "/api/events",
        json={"title": "Ended", "start": "2026-09-29T00:00:00", "end": "2026-10-01T00:00:00", "all_day": True},
    )
    assert [i["title"] for i in feed(api)] == ["Trip"]


def test_rejects_bad_ranges(api):
    assert api.get("/api/calendar", params={"start": OCT["end"], "end": OCT["start"]}).status_code == 422
    too_long = {"start": "2026-01-01T00:00:00", "end": "2027-06-01T00:00:00"}
    assert api.get("/api/calendar", params=too_long).status_code == 422
    aware = {"start": "2026-10-01T00:00:00Z", "end": "2026-11-01T00:00:00Z"}
    assert api.get("/api/calendar", params=aware).status_code == 422


def test_occurrence_spanning_range_start_is_included():
    # Daily 22:00-02:00 event; the one starting the night before still overlaps the range.
    result = occurrences(
        datetime(2026, 10, 1, 22),
        datetime(2026, 10, 2, 2),
        "FREQ=DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )
    assert result[0] == (datetime(2026, 10, 4, 22), datetime(2026, 10, 5, 2))
    assert len(result) == 2


def test_recurrence_respects_count_and_cap():
    start, end = datetime(2026, 10, 1, 9), datetime(2026, 10, 1, 10)
    assert len(occurrences(start, end, "FREQ=DAILY;COUNT=3", datetime(2026, 9, 1), datetime(2026, 12, 1))) == 3
    minutely = occurrences(start, end, "FREQ=MINUTELY", datetime(2026, 10, 1), datetime(2026, 11, 1))
    assert len(minutely) == MAX_OCCURRENCES
