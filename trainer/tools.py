import json
import os
from datetime import datetime, timedelta

# Path to data files
USERS_FILE = "data/users.json"
WORKOUTS_FILE = "data/workouts.json"


def get_user_profile(user_id: str) -> dict:
    """Get a user's profile by their user ID."""
    
    # Open and read the users.json file
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    
    # Check if user exists
    if user_id not in users:
        return {"error": f"User {user_id} not found"}
    
    return users[user_id]




def log_workout(exercise: str, sets: int, reps: int, weight_kg: float, body_part: str, user_id: str = None) -> dict:
    """Log a completed workout for a user."""

    with open(WORKOUTS_FILE, "r") as f:
        workouts = json.load(f)

    workout_entry = {
        "exercise": exercise,
        "body_part": body_part,
        "sets": sets,
        "reps": reps,
        "weight_kg": weight_kg,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if user_id not in workouts:
        workouts[user_id] = []

    workouts[user_id].append(workout_entry)

    with open(WORKOUTS_FILE, "w") as f:
        json.dump(workouts, f, indent=4)

    return {"success": f"Workout logged for {user_id} — {exercise} ({body_part})"}



def get_workout_history(days: int = 7, body_part: str = None, user_id: str = None) -> dict:
    """Get workout history for a user for the last N days with optional body part filter."""

    with open(WORKOUTS_FILE, "r") as f:
        workouts = json.load(f)

    if user_id not in workouts:
        return {
            "total_sessions": 0,
            "body_parts_trained": [],
            "last_trained": None,
            "workouts": []
        }

    cutoff_date = datetime.now() - timedelta(days=days)
    user_workouts = workouts[user_id]

    # Filter by days
    recent_workouts = []
    for workout in user_workouts:
        workout_date = datetime.strptime(workout["date"], "%Y-%m-%d %H:%M:%S")
        if workout_date >= cutoff_date:
            recent_workouts.append(workout)

    # Filter by body part if specified
    if body_part:
        recent_workouts = [
            w for w in recent_workouts
            if w.get("body_part", "").lower() == body_part.lower()
        ]

    # Build summary
    body_parts_trained = list(set(w.get("body_part", "unknown") for w in recent_workouts))
    last_trained = recent_workouts[-1]["date"] if recent_workouts else None

    return {
        "total_sessions": len(recent_workouts),
        "body_parts_trained": body_parts_trained,
        "last_trained": last_trained,
        "workouts": recent_workouts
    }


def generate_workout_plan(days_per_week: int, focus: str = None) -> dict:
    """
    Prepare inputs for workout plan generation.
    Claude generates the actual plan using the member profile
    already available in the system prompt.

    Args:
        days_per_week: how many days per week the member can train
        focus: optional specific focus e.g. chest, legs, cardio
    """

    if days_per_week < 1:
        days_per_week = 1
    if days_per_week > 7:
        days_per_week = 7

    return {
        "days_per_week": days_per_week,
        "focus": focus if focus else "full body"
    }

def search_knowledge_base(query: str) -> dict:
    """Search the fitness knowledge base for relevant information."""
    from trainer.knowledge_base import retrieve
    
    results = retrieve(query, n_results=3)
    
    return {
        "query": query,
        "results": results
    }