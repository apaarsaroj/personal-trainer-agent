from trainer.agent import run_agent

# Start with empty conversation history
messages = []

# Test 1 — Ask for a workout plan
print("=" * 50)
print("TEST: Ask for a workout plan")
print("=" * 50)

response, messages = run_agent(
    "I am user_001. Can you create a workout plan for me?",
    messages
)

print("\nClaude:", response)

# Test 2 — Log a workout in the same conversation
print("\n" + "=" * 50)
print("TEST: Log a workout")
print("=" * 50)

response, messages = run_agent(
    "I just did 4 sets of deadlifts, 6 reps at 100kg. Please log that for me.",
    messages
)

print("\nClaude:", response)