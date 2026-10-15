"""Shared fixtures. Tests never touch the real data files or the Anthropic API."""
import json
import sys
from pathlib import Path

import pytest

# Make the project root importable no matter where pytest is launched from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def data_files(tmp_path, monkeypatch):
    """Point the tools and auth modules at throwaway JSON files."""
    users_file = tmp_path / "users.json"
    workouts_file = tmp_path / "workouts.json"

    users_file.write_text(json.dumps({
        "PT-0001": {
            "member_id": "PT-0001",
            "first_name": "Test",
            "last_name": "User",
            "age": 30,
            "weight_kg": 70.0,
            "height_cm": 175.0,
            "fitness_level": "intermediate",
            "goals": ["strength"],
            "injuries": [],
            "days_per_week": 4,
            "joined_date": "2026-01-01",
        }
    }))
    workouts_file.write_text(json.dumps({}))

    import trainer.auth as auth
    import trainer.tools as tools

    monkeypatch.setattr(tools, "USERS_FILE", str(users_file))
    monkeypatch.setattr(tools, "WORKOUTS_FILE", str(workouts_file))
    monkeypatch.setattr(auth, "USERS_FILE", str(users_file))

    return {"users": users_file, "workouts": workouts_file}
