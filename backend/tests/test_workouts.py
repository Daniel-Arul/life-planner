def log(api, day, entries, **fields):
    body = {"performed_on": day, "kind": "strength", "entries": entries, **fields}
    response = api.post("/api/workouts", json=body)
    assert response.status_code == 201, response.text
    return response.json()


BENCH = {"exercise_name": "Bench press", "sets": 3, "reps": 8, "weight": 60}


def test_log_workout_creates_exercises_by_name(api):
    workout = log(
        api,
        "2026-10-20",
        [BENCH, {"exercise_name": "  bench PRESS ", "sets": 1, "reps": 5, "weight": 70}],
        title="Push day",
        duration_min=55,
    )
    assert workout["title"] == "Push day"
    assert [e["exercise_name"] for e in workout["entries"]] == ["Bench press", "Bench press"]
    exercises = api.get("/api/exercises").json()
    assert len(exercises) == 1  # matched case-insensitively, not duplicated
    assert exercises[0]["times_logged"] == 1
    assert exercises[0]["last_done"] == "2026-10-20"


def test_replace_workout_entries(api):
    workout = log(api, "2026-10-20", [BENCH])
    squat = api.post("/api/exercises", json={"name": "Squat"}).json()
    body = {
        "performed_on": "2026-10-21",
        "kind": "strength",
        "entries": [{"exercise_id": squat["id"], "sets": 5, "reps": 5, "weight": 100}],
    }
    updated = api.put(f"/api/workouts/{workout['id']}", json=body).json()
    assert updated["performed_on"] == "2026-10-21"
    assert [(e["exercise_name"], e["sets"]) for e in updated["entries"]] == [("Squat", 5)]


def test_validation(api):
    assert api.post(
        "/api/workouts", json={"performed_on": "2026-10-20", "entries": [{"sets": 3}]}
    ).status_code == 422
    assert api.post(
        "/api/workouts",
        json={"performed_on": "2026-10-20", "entries": [{"exercise_id": 999}]},
    ).status_code == 422
    assert api.post(
        "/api/workouts", json={"performed_on": "2026-10-20", "kind": "yoga"}
    ).status_code == 422
    bad_reps = {**BENCH, "reps": -1}
    assert api.post(
        "/api/workouts", json={"performed_on": "2026-10-20", "entries": [bad_reps]}
    ).status_code == 422


def test_cardio_entry(api):
    run = log(
        api,
        "2026-10-19",
        [{"exercise_name": "Run", "distance": 5.2, "duration_s": 1680}],
        kind="cardio",
    )
    entry = run["entries"][0]
    assert (entry["distance"], entry["duration_s"], entry["weight"]) == (5.2, 1680, None)
    assert api.get("/api/exercises").json()[0]["kind"] == "cardio"


def test_delete_workout_cascades_and_exercise_guard(api):
    workout = log(api, "2026-10-20", [BENCH])
    bench_id = workout["entries"][0]["exercise_id"]
    assert api.delete(f"/api/exercises/{bench_id}").status_code == 409
    assert api.delete(f"/api/workouts/{workout['id']}").status_code == 204
    assert api.get("/api/exercises").json()[0]["times_logged"] == 0
    assert api.delete(f"/api/exercises/{bench_id}").status_code == 204


def test_exercise_rename_conflict(api):
    a = api.post("/api/exercises", json={"name": "Deadlift"}).json()
    api.post("/api/exercises", json={"name": "Row"})
    assert api.post("/api/exercises", json={"name": "deadlift"}).status_code == 409
    assert api.patch(f"/api/exercises/{a['id']}", json={"name": "ROW"}).status_code == 409
    assert api.patch(f"/api/exercises/{a['id']}", json={"name": "Deadlift "}).json()["name"] == "Deadlift"


def test_list_filters(api):
    log(api, "2026-09-30", [BENCH], title="Sept")
    log(api, "2026-10-02", [BENCH], title="Oct A")
    log(api, "2026-10-09", [BENCH], title="Oct B")
    titles = lambda **p: [w["title"] for w in api.get("/api/workouts", params=p).json()]
    assert titles(month="2026-10") == ["Oct B", "Oct A"]
    assert titles(start="2026-10-01", end="2026-10-05") == ["Oct A"]
    assert titles(limit=1) == ["Oct B"]


def test_weekly_stats_and_streak(api):
    # Today is Wednesday 2026-10-21; weeks start on Monday.
    log(api, "2026-10-19", [BENCH], duration_min=40)  # this week
    log(api, "2026-10-21", [], duration_min=20)  # this week
    log(api, "2026-10-13", [BENCH])  # last week
    log(api, "2026-09-29", [BENCH])  # three weeks ago: gap at 10-05, so not in streak
    stats = api.get("/api/stats/workouts", params={"weeks": 4, "today": "2026-10-21"}).json()
    assert [w["week_start"] for w in stats["weeks"]] == [
        "2026-09-28",
        "2026-10-05",
        "2026-10-12",
        "2026-10-19",
    ]
    assert [w["workouts"] for w in stats["weeks"]] == [1, 0, 1, 2]
    assert stats["weeks"][-1]["volume"] == 3 * 8 * 60
    assert stats["this_week_workouts"] == 2
    assert stats["this_week_minutes"] == 60
    assert stats["streak_weeks"] == 2


def test_streak_counts_from_last_week_when_this_week_is_empty(api):
    log(api, "2026-10-14", [BENCH])
    stats = api.get("/api/stats/workouts", params={"today": "2026-10-21"}).json()
    assert stats["streak_weeks"] == 1
    assert stats["this_week_workouts"] == 0


def test_exercise_progress(api):
    log(api, "2026-10-01", [BENCH])
    log(api, "2026-10-08", [BENCH, {**BENCH, "sets": 1, "reps": 3, "weight": 72.5}])
    bench_id = api.get("/api/exercises").json()[0]["id"]
    points = api.get(f"/api/stats/exercises/{bench_id}").json()
    assert [(p["date"], p["best_weight"]) for p in points] == [
        ("2026-10-01", 60.0),
        ("2026-10-08", 72.5),
    ]
    assert points[1]["volume"] == 3 * 8 * 60 + 3 * 72.5
    assert points[1]["max_reps"] == 8
    assert api.get("/api/stats/exercises/999").status_code == 404


def test_calendar_shows_workouts(api):
    log(api, "2026-10-03", [BENCH], title="Push day")
    log(api, "2026-10-04", [], kind="cardio")
    items = api.get(
        "/api/calendar", params={"start": "2026-10-01T00:00:00", "end": "2026-10-08T00:00:00"}
    ).json()
    assert [(i["kind"], i["title"]) for i in items if i["kind"] == "workout"] == [
        ("workout", "Push day"),
        ("workout", "Cardio workout"),
    ]
