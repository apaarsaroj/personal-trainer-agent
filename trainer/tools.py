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




def log_workout(user_id: str, exercise: str, sets: int, reps: int, weight_kg: float) -> dict:
    """Log a workout for a user."""

    # Read existing workouts
    with open(WORKOUTS_FILE, "r") as f:
        workouts = json.load(f)

    # Create a new workout entry
    workout_entry = {
        "exercise": exercise,
        "sets": sets,
        "reps": reps,
        "weight_kg": weight_kg,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # If user has no workouts yet, create empty list
    if user_id not in workouts:
        workouts[user_id] = []

    # Add the new workout to the list
    workouts[user_id].append(workout_entry)

    # Save back to file
    with open(WORKOUTS_FILE, "w") as f:
        json.dump(workouts, f, indent=4)

    return {"success": f"Workout logged for {user_id}"}

def get_workout_history(user_id: str, days: int = 7) -> list:
    """Get workout history for a user for the last N days."""

    # Read workouts file
    with open(WORKOUTS_FILE, "r") as f:
        workouts = json.load(f)

    # Check if user has any workouts
    if user_id not in workouts:
        return []

    # Filter workouts by days
    cutoff_date = datetime.now() - timedelta(days=days)
    user_workouts = workouts[user_id]

    recent_workouts = []
    for workout in user_workouts:
        workout_date = datetime.strptime(workout["date"], "%Y-%m-%d %H:%M:%S")
        if workout_date >= cutoff_date:
            recent_workouts.append(workout)

    return recent_workouts

def generate_workout_plan(goal: str, fitness_level: str, days_per_week: int) -> dict:
    """Generate a basic workout plan based on goal and fitness level."""

    plan = {
        "goal": goal,
        "fitness_level": fitness_level,
        "days_per_week": days_per_week,
        "plan": []
    }

    if goal == "build muscle" and fitness_level == "intermediate":
        plan["plan"] = [
            "Day 1: Chest and Triceps — bench press, incline press, tricep dips",
            "Day 2: Back and Biceps — deadlift, pull ups, barbell curl",
            "Day 3: Rest",
            "Day 4: Shoulders and Abs — overhead press, lateral raises, planks",
            "Day 5: Legs — squat, leg press, lunges",
            "Day 6: Rest",
            "Day 7: Rest"
        ]
    elif goal == "lose weight" and fitness_level == "beginner":
        plan["plan"] = [
            "Day 1: 30 min brisk walking + bodyweight squats",
            "Day 2: Rest",
            "Day 3: 20 min cycling + push ups",
            "Day 4: Rest",
            "Day 5: 30 min walking + planks",
            "Day 6: Light stretching",
            "Day 7: Rest"
        ]
    else:
        plan["plan"] = [
            "Day 1: Full body workout — squats, push ups, rows",
            "Day 2: Rest",
            "Day 3: Cardio — 30 min walking or cycling",
            "Day 4: Rest",
            "Day 5: Full body workout — deadlift, overhead press, planks",
            "Day 6: Rest",
            "Day 7: Rest"
        ]

    return plan