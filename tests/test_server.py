from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server

PROFILE = {
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


@pytest.fixture
def client(monkeypatch):
    """API client with login and the LangGraph agent stubbed out (no model calls)."""
    server._graphs.clear()
    calls = {"create_graph": 0}

    def fake_login(member_id):
        cleaned = member_id.strip().upper()
        if cleaned == "PT-0001":
            return {
                "success": True,
                "member_id": "PT-0001",
                "first_name": "Test",
                "profile": PROFILE,
                "message": "Welcome back Test!",
            }
        return {"success": False, "message": "Member ID not found"}

    def fake_register(**kwargs):
        return {
            "success": True,
            "member_id": "PT-0001",
            "message": "Welcome!",
        }

    def fake_create_graph(profile, checkpointer):
        calls["create_graph"] += 1
        return object()

    def fake_run_graph(user_message, profile, compiled_graph, thread_id):
        return f"echo: {user_message}"

    monkeypatch.setattr(server, "login_user", fake_login)
    monkeypatch.setattr(server, "register_user", fake_register)
    monkeypatch.setattr(server, "create_graph", fake_create_graph)
    monkeypatch.setattr(server, "run_graph", fake_run_graph)

    test_client = TestClient(server.app)
    test_client.calls = calls
    return test_client


def test_chat_returns_agent_reply(client):
    response = client.post("/chat", json={"member_id": "PT-0001", "message": "hello"})
    assert response.status_code == 200
    assert response.json() == {"reply": "echo: hello"}


def test_api_chat_returns_agent_reply(client):
    response = client.post("/api/chat", json={"member_id": "PT-0001", "message": "hello"})
    assert response.status_code == 200
    assert response.json() == {"reply": "echo: hello"}


def test_chat_builds_one_graph_per_member(client):
    for text in ("first", "second"):
        client.post("/chat", json={"member_id": "PT-0001", "message": text})
    assert client.calls["create_graph"] == 1


def test_chat_unknown_member_returns_404(client):
    response = client.post("/chat", json={"member_id": "PT-9999", "message": "hi"})
    assert response.status_code == 404


def test_chat_rejects_missing_message(client):
    response = client.post("/chat", json={"member_id": "PT-0001"})
    assert response.status_code == 422


def test_get_member_returns_profile(client):
    response = client.get("/members/PT-0001")
    assert response.status_code == 200
    assert response.json()["first_name"] == "Test"


def test_get_member_unknown_returns_404(client):
    assert client.get("/members/PT-9999").status_code == 404


def test_workouts_endpoint_passes_query_params(client, monkeypatch):
    seen = {}

    def fake_history(days, body_part, user_id):
        seen.update(days=days, body_part=body_part, user_id=user_id)
        return {"total_sessions": 0}

    monkeypatch.setattr(server, "get_workout_history", fake_history)
    response = client.get("/members/PT-0001/workouts?days=14&body_part=legs")

    assert response.status_code == 200
    assert seen == {"days": 14, "body_part": "legs", "user_id": "PT-0001"}


def test_api_login_returns_profile(client):
    response = client.post("/api/login", json={"member_id": "PT-0001"})
    assert response.status_code == 200
    assert response.json()["member_id"] == "PT-0001"
    assert response.json()["profile"]["first_name"] == "Test"


def test_api_register_returns_member(client):
    response = client.post(
        "/api/register",
        json={
            "first_name": "Sam",
            "last_name": "Lee",
            "age": 28,
            "weight_kg": 75,
            "height_cm": 180,
            "fitness_level": "beginner",
            "goals": ["strength"],
            "injuries": [],
            "days_per_week": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["member_id"] == "PT-0001"
    assert body["profile"]["first_name"] == "Test"


def test_web_index_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Form" in response.text


def test_web_assets_are_served(client):
    css = client.get("/static/styles.css")
    js = client.get("/static/app.js")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert js.status_code == 200
    assert Path(server.WEB_DIR / "app.js").is_file()
