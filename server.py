from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver

from trainer.auth import register_user, login_user
from trainer.graph import create_graph, run_graph
from trainer.tools import get_workout_history, log_workout

app = FastAPI(title="Personal Trainer Agent")

checkpointer = MemorySaver()
_graphs = {}


class ChatRequest(BaseModel):
    member_id: str
    message: str


@app.post("/chat")
def chat(req: ChatRequest):
    auth = login_user(req.member_id)
    if not auth["success"]:
        raise HTTPException(status_code=404, detail=auth["message"])

    profile = auth["profile"]

    if req.member_id not in _graphs:
        _graphs[req.member_id] = create_graph(profile, checkpointer)

    reply = run_graph(
        user_message=req.message,
        profile=profile,
        compiled_graph=_graphs[req.member_id],
        thread_id=req.member_id,
    )
    return {"reply": reply}


@app.get("/members/{member_id}")
def get_member(member_id: str):
    auth = login_user(member_id)
    if not auth["success"]:
        raise HTTPException(status_code=404, detail=auth["message"])
    return auth["profile"]


@app.get("/members/{member_id}/workouts")
def list_workouts(member_id: str, days: int = 7, body_part: str = None):
    return get_workout_history(days=days, body_part=body_part, user_id=member_id)
