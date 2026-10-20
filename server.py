"""FastAPI HTTP surface: trainer API + full-screen web chat UI."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from trainer.auth import login_user, register_user
from trainer.graph import create_graph, run_graph
from trainer.tools import get_workout_history

load_dotenv()

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title="Personal Trainer Agent")

checkpointer = MemorySaver()
_graphs: dict = {}


class ChatRequest(BaseModel):
    member_id: str
    message: str


class LoginRequest(BaseModel):
    member_id: str


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    age: int = Field(ge=13, le=100)
    weight_kg: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    fitness_level: str
    goals: list[str]
    injuries: list[str] = []
    days_per_week: int = Field(ge=1, le=7)


@app.post("/api/login")
def api_login(req: LoginRequest):
    auth = login_user(req.member_id)
    if not auth["success"]:
        raise HTTPException(status_code=404, detail=auth["message"])
    return {
        "member_id": auth["member_id"],
        "first_name": auth["first_name"],
        "profile": auth["profile"],
        "message": auth["message"],
    }


@app.post("/api/register")
def api_register(req: RegisterRequest):
    level = req.fitness_level.strip().lower()
    if level not in {"beginner", "intermediate", "advanced"}:
        raise HTTPException(
            status_code=422,
            detail="fitness_level must be beginner, intermediate, or advanced",
        )
    goals = [g.strip() for g in req.goals if g and g.strip()]
    if not goals:
        raise HTTPException(status_code=422, detail="At least one goal is required")

    result = register_user(
        first_name=req.first_name.strip().capitalize(),
        last_name=req.last_name.strip().capitalize(),
        age=req.age,
        weight_kg=req.weight_kg,
        height_cm=req.height_cm,
        fitness_level=level,
        goals=goals,
        injuries=[i.strip() for i in req.injuries if i and i.strip()],
        days_per_week=req.days_per_week,
    )
    auth = login_user(result["member_id"])
    return {
        "member_id": result["member_id"],
        "message": result["message"],
        "profile": auth["profile"],
    }


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    auth = login_user(req.member_id)
    if not auth["success"]:
        raise HTTPException(status_code=404, detail=auth["message"])

    profile = auth["profile"]

    if req.member_id not in _graphs:
        _graphs[req.member_id] = create_graph(profile, checkpointer)

    try:
        reply = run_graph(
            user_message=req.message,
            profile=profile,
            compiled_graph=_graphs[req.member_id],
            thread_id=req.member_id,
        )
    except Exception as exc:  # noqa: BLE001 — surface model/runtime failures to the UI
        raise HTTPException(
            status_code=502,
            detail=(
                "Trainer could not complete that turn. "
                "Check ANTHROPIC_API_KEY and server logs."
            ),
        ) from exc
    return {"reply": reply}


@app.get("/api/members/{member_id}")
def get_member(member_id: str):
    auth = login_user(member_id)
    if not auth["success"]:
        raise HTTPException(status_code=404, detail=auth["message"])
    return auth["profile"]


@app.get("/api/members/{member_id}/workouts")
def list_workouts(member_id: str, days: int = 7, body_part: str | None = None):
    return get_workout_history(days=days, body_part=body_part, user_id=member_id)


# Backward-compatible aliases used by earlier clients/tests.
@app.post("/chat")
def chat(req: ChatRequest):
    return api_chat(req)


@app.get("/members/{member_id}")
def get_member_legacy(member_id: str):
    return get_member(member_id)


@app.get("/members/{member_id}/workouts")
def list_workouts_legacy(member_id: str, days: int = 7, body_part: str | None = None):
    return list_workouts(member_id, days=days, body_part=body_part)


@app.get("/")
def web_index():
    index = WEB_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Web UI not found")
    return FileResponse(index)


if WEB_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
