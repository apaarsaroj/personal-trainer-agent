"""Member registration and login against the local JSON user store."""

import json
import random
import string
from datetime import datetime

USERS_FILE = "data/users.json"


def generate_member_id() -> str:
    """Generate a unique member ID in format PT-XXXX."""
    with open(USERS_FILE) as f:
        users = json.load(f)

    while True:
        digits = "".join(random.choices(string.digits, k=4))
        member_id = f"PT-{digits}"
        if member_id not in users:
            return member_id


def register_user(
    first_name: str,
    last_name: str,
    age: int,
    weight_kg: float,
    height_cm: float,
    fitness_level: str,
    goals: list,
    injuries: list,
    days_per_week: int,
) -> dict:
    """Register a new user and return their member ID."""
    with open(USERS_FILE) as f:
        users = json.load(f)

    member_id = generate_member_id()

    new_user = {
        "member_id": member_id,
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "fitness_level": fitness_level,
        "goals": goals,
        "injuries": injuries,
        "days_per_week": days_per_week,
        "joined_date": datetime.now().strftime("%Y-%m-%d"),
    }

    users[member_id] = new_user

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    return {
        "success": True,
        "member_id": member_id,
        "message": (
            f"Welcome {first_name}! Your member ID is {member_id}. "
            "Please save this — you will need it to login."
        ),
    }


def login_user(member_id: str) -> dict:
    """Verify a member ID and return their full profile."""
    member_id = member_id.strip().upper()

    with open(USERS_FILE) as f:
        users = json.load(f)

    if member_id not in users:
        return {
            "success": False,
            "message": (
                f"Member ID {member_id} not found. "
                "Please check your ID or register as a new member."
            ),
        }

    user = users[member_id]

    return {
        "success": True,
        "member_id": member_id,
        "first_name": user["first_name"],
        "profile": user,
        "message": f"Welcome back {user['first_name']}!",
    }
