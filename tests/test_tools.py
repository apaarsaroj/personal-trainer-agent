import json
import sys
import types
from datetime import datetime, timedelta

from trainer import tools


def _write_workouts(path, user_id, entries):
    path.write_text(json.dumps({user_id: entries}))


def _entry(days_ago, body_part, exercise="Squat"):
    date = datetime.now() - timedelta(days=days_ago)
    return {
        "exercise": exercise,
        "body_part": body_part,
        "sets": 3,
        "reps": 10,
        "weight_kg": 60.0,
        "date": date.strftime("%Y-%m-%d %H:%M:%S"),
    }


def test_get_user_profile_returns_existing_member(data_files):
    profile = tools.get_user_profile("PT-0001")
    assert profile["first_name"] == "Test"


def test_get_user_profile_unknown_member_returns_error(data_files):
    result = tools.get_user_profile("PT-9999")
    assert "error" in result


def test_log_workout_creates_history_for_new_user(data_files):
    result = tools.log_workout("Bench Press", 3, 8, 50.0, "chest", user_id="PT-0001")
    assert "success" in result

    saved = json.loads(data_files["workouts"].read_text())
    assert len(saved["PT-0001"]) == 1
    assert saved["PT-0001"][0]["exercise"] == "Bench Press"


def test_log_workout_appends_to_existing_history(data_files):
    tools.log_workout("Squat", 3, 5, 80.0, "legs", user_id="PT-0001")
    tools.log_workout("Deadlift", 3, 5, 100.0, "back", user_id="PT-0001")

    saved = json.loads(data_files["workouts"].read_text())
    assert [w["exercise"] for w in saved["PT-0001"]] == ["Squat", "Deadlift"]


def test_history_for_unknown_user_is_empty(data_files):
    history = tools.get_workout_history(user_id="PT-0001")
    assert history["total_sessions"] == 0
    assert history["workouts"] == []
    assert history["last_trained"] is None


def test_history_excludes_workouts_older_than_window(data_files):
    _write_workouts(data_files["workouts"], "PT-0001",
                    [_entry(1, "legs"), _entry(30, "chest")])

    history = tools.get_workout_history(days=7, user_id="PT-0001")
    assert history["total_sessions"] == 1
    assert history["body_parts_trained"] == ["legs"]


def test_history_body_part_filter_ignores_case(data_files):
    _write_workouts(data_files["workouts"], "PT-0001",
                    [_entry(1, "Legs"), _entry(2, "chest")])

    history = tools.get_workout_history(days=7, body_part="legs", user_id="PT-0001")
    assert history["total_sessions"] == 1
    assert history["workouts"][0]["body_part"] == "Legs"


def test_workout_plan_clamps_days_per_week():
    assert tools.generate_workout_plan(0)["days_per_week"] == 1
    assert tools.generate_workout_plan(12)["days_per_week"] == 7
    assert tools.generate_workout_plan(4)["days_per_week"] == 4


def test_workout_plan_defaults_to_full_body():
    assert tools.generate_workout_plan(3)["focus"] == "full body"
    assert tools.generate_workout_plan(3, focus="legs")["focus"] == "legs"


def test_search_knowledge_base_wraps_retrieved_chunks(monkeypatch):
    """The real knowledge base loads an embedding model, so swap in a stub."""
    stub = types.ModuleType("trainer.knowledge_base")
    stub.retrieve = lambda query, n_results=5: [f"chunk about {query}"] * n_results
    monkeypatch.setitem(sys.modules, "trainer.knowledge_base", stub)

    result = tools.search_knowledge_base("hip hinge")
    assert result["query"] == "hip hinge"
    assert len(result["results"]) == 3
    assert result["results"][0] == "chunk about hip hinge"
