import json
import re

from trainer import auth


def _register(**overrides):
    details = dict(
        first_name="Sam", last_name="Lee", age=28, weight_kg=75.0, height_cm=180.0,
        fitness_level="beginner", goals=["weight loss"], injuries=[], days_per_week=3,
    )
    details.update(overrides)
    return auth.register_user(**details)


def test_register_user_saves_profile_with_member_id(data_files):
    result = _register()

    assert result["success"] is True
    assert re.fullmatch(r"PT-\d{4}", result["member_id"])

    saved = json.loads(data_files["users"].read_text())
    assert saved[result["member_id"]]["first_name"] == "Sam"
    assert "joined_date" in saved[result["member_id"]]


def test_generate_member_id_skips_ids_already_taken(data_files, monkeypatch):
    # PT-0001 already exists in the fixture, so 0001 must be rejected.
    digits = iter([list("0001"), list("0002")])
    monkeypatch.setattr(auth.random, "choices", lambda *a, **k: next(digits))

    assert auth.generate_member_id() == "PT-0002"


def test_login_accepts_lowercase_and_extra_spaces(data_files):
    result = auth.login_user("  pt-0001 ")
    assert result["success"] is True
    assert result["member_id"] == "PT-0001"
    assert result["profile"]["first_name"] == "Test"


def test_login_rejects_unknown_member(data_files):
    result = auth.login_user("PT-9999")
    assert result["success"] is False
    assert "not found" in result["message"]
