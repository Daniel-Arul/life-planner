EVENT = {"title": "Dentist", "start": "2026-10-21T09:00:00", "end": "2026-10-21T10:00:00"}


def create(api, **fields):
    response = api.post("/api/events", json={**EVENT, **fields})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_get_update_delete(api):
    event = create(api, color="mint", notes="bring card")
    assert event["all_day"] is False
    assert api.get(f"/api/events/{event['id']}").json()["notes"] == "bring card"

    moved = api.patch(
        f"/api/events/{event['id']}",
        json={"start": "2026-10-22T09:00:00", "end": "2026-10-22T11:00:00"},
    ).json()
    assert moved["start"] == "2026-10-22T09:00:00"

    assert api.delete(f"/api/events/{event['id']}").status_code == 204
    assert api.get(f"/api/events/{event['id']}").status_code == 404


def test_rejects_end_before_start(api):
    response = api.post("/api/events", json={**EVENT, "end": "2026-10-21T08:00:00"})
    assert response.status_code == 422
    event = create(api)
    response = api.patch(f"/api/events/{event['id']}", json={"end": "2026-10-20T08:00:00"})
    assert response.status_code == 422
    # The failed patch must not have been saved.
    assert api.get(f"/api/events/{event['id']}").json()["end"] == EVENT["end"]


def test_rejects_timezone_aware_times(api):
    response = api.post("/api/events", json={**EVENT, "start": "2026-10-21T09:00:00Z"})
    assert response.status_code == 422


def test_rrule_validation(api):
    assert create(api, rrule="RRULE:FREQ=WEEKLY;BYDAY=MO")["rrule"] == "FREQ=WEEKLY;BYDAY=MO"
    assert create(api, rrule="")["rrule"] is None
    for bad in ("FREQ=SOMETIMES", "DTSTART:20260101T000000\nRRULE:FREQ=DAILY"):
        assert api.post("/api/events", json={**EVENT, "rrule": bad}).status_code == 422, bad


def test_rejects_unknown_color(api):
    assert api.post("/api/events", json={**EVENT, "color": "neon"}).status_code == 422
