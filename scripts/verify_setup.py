"""Manual smoke script: register, login, and run a few legacy agent turns.

Requires ANTHROPIC_API_KEY. Prefer pytest for automated checks.
"""

from trainer.agent import run_agent
from trainer.auth import login_user, register_user

print("=" * 50)
print("Step 1: Registering test user")
print("=" * 50)

result = register_user(
    first_name="Apaar",
    last_name="Saroj",
    age=25,
    weight_kg=88,
    height_cm=175,
    fitness_level="intermediate",
    goals=["build muscle", "improve endurance"],
    injuries=["lower back pain"],
    days_per_week=4,
)

print(result["message"])
member_id = result["member_id"]

print("\n" + "=" * 50)
print("Step 2: Logging in")
print("=" * 50)

login_result = login_user(member_id)
profile = login_result["profile"]
print(login_result["message"])

print("\n" + "=" * 50)
print("Step 3: Chat with agent")
print("=" * 50)

messages = []

response, messages = run_agent(
    "Can you give me a workout plan for this week?",
    messages,
    profile,
)
print("\nTrainer:", response)

print("\n" + "=" * 50)
print("Step 4: Log a workout")
print("=" * 50)

response, messages = run_agent(
    "I just did 4 sets of bench press, 8 reps, 70kg",
    messages,
    profile,
)
print("\nTrainer:", response)

print("\n" + "=" * 50)
print("Step 5: Check workout history")
print("=" * 50)

response, messages = run_agent(
    "What have I trained this week?",
    messages,
    profile,
)
print("\nTrainer:", response)
