from trainer.auth import register_user, login_user
from trainer.graph import create_graph, run_graph
import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

def registration_flow() -> dict:
    """Handle new member registration."""

    print("\n--- New Member Registration ---\n")

    first_name = input("First name: ").strip().capitalize()
    last_name = input("Last name: ").strip().capitalize()
    age = int(input("Age: ").strip())
    weight_kg = float(input("Weight (kg): ").strip())
    height_cm = float(input("Height (cm): ").strip())
    while True:
        fitness_level = input("Fitness level (beginner/intermediate/advanced): ").strip().lower()
        if fitness_level in ["beginner", "intermediate", "advanced"]:
            break
        print("Invalid input. Please enter beginner, intermediate, or advanced.")
    goals = input("Goals (comma separated e.g. build muscle, lose weight): ").strip().split(",")
    injuries = input("Injuries (comma separated or press Enter for none): ").strip()
    days_per_week = int(input("How many days per week can you train? (1-7): ").strip())

    goals = [g.strip() for g in goals]
    injuries = [i.strip() for i in injuries.split(",")] if injuries else []

    # Validate days per week
    if days_per_week < 1:
        days_per_week = 1
    if days_per_week > 7:
        days_per_week = 7

    result = register_user(
        first_name=first_name,
        last_name=last_name,
        age=age,
        weight_kg=weight_kg,
        height_cm=height_cm,
        fitness_level=fitness_level,
        goals=goals,
        injuries=injuries,
        days_per_week=days_per_week
    )

    print(f"\n{result['message']}")
    print("Please save your member ID before continuing.\n")

    return result


def login_flow() -> dict:
    """Handle member login."""

    print("\n--- Member Login ---\n")

    while True:
        code = input("Enter your 4-digit member code (PT-____): ").strip()
        member_id = f"PT-{code}"
        result = login_user(member_id)

        if result["success"]:
            print(f"\n{result['message']}")
            return result
        else:
            print(f"\n{result['message']}")
            print("Please try again.\n")


def chat_loop(profile: dict):
    """Run the main chat loop."""

    print(f"\nHello {profile['first_name']}! I am your personal trainer.")
    print("Type 'quit' to exit.\n")
    print("-" * 50)

    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/memory.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    compiled_graph = create_graph(profile, memory)

    while True:

        user_input = input("\nYou: ").strip()

        if user_input.lower() == "quit":
            print(f"\nGoodbye {profile['first_name']}! Keep up the great work!")
            break

        if not user_input:
            continue

        response = run_graph(user_input, profile, compiled_graph, profile["member_id"])
        print(f"\nTrainer: {response}")


def main():
    print("=" * 50)
    print("  Welcome to Personal Trainer AI")
    print("=" * 50)

    choice = input("\nAre you a member? (yes/no): ").strip().lower()

    if choice == "no":
        reg_result = registration_flow()
        login_result = login_user(reg_result["member_id"])
        profile = login_result["profile"]
    else:
        login_result = login_flow()
        profile = login_result["profile"]

    chat_loop(profile)


if __name__ == "__main__":
    main()