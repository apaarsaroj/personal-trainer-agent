import pytest
from fastapi.testclient import TestClient

import server

PROFILE = {"member_id": "PT-0001", "first_name": "Test"}


@pytest.fixture
def client(monkeypatch):
    """API client with login and the LangGraph agent stubbed out (no model calls)."""
    server._graphs.clear()
    calls = {"create_graph": 0}

    def fake_login(member_id):
        if member_id == "PT-0001":
            return {"success": True, "profile": PROFILE}
        return {"success": False, "message": "Member ID not found"}

    def fake_create_graph(profile, checkpointer):
        calls["create_graph"] += 1
        return object()

    def fake_run_graph(user_message, profile, compiled_graph, thread_id):
        return f"echo: {user_message}"

    monkeypatch.setattr(server, "login_user", fake_login)
    monkeypatch.setattr(server, "create_graph", fake_create_graph)
    monkeypatch.setattr(server, "run_graph", fake_run_graph)

    test_client = TestClient(server.app)
    test_client.calls = calls
    return test_client


def test_chat_returns_agent_reply(client):
    response = client.post("/chat", json={"member_id": "PT-0001", "message": "hello"})
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
