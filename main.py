from trainer.agent import run_agent

def main():
    print("=" * 50)
    print("Welcome to your Personal Trainer AI Agent")
    print("Type 'quit' to exit")
    print("=" * 50)

    # Start with empty conversation history
    messages = []

    # Ask for user ID once at the start
    user_id = input("\nEnter your user ID (e.g. user_001): ").strip()

    print(f"\nHello! I am your personal trainer. How can I help you today?\n")

    # Main conversation loop
    while True:

        # Get user input
        user_input = input("You: ").strip()

        # Exit condition
        if user_input.lower() == "quit":
            print("\nGoodbye! Keep up the great work! 💪")
            break

        # Skip empty input
        if not user_input:
            continue

        # Add user ID context to every message
        message_with_context = f"[User ID: {user_id}] {user_input}"

        # Run the agent
        response, messages = run_agent(message_with_context, messages)

        # Print Claude's response
        print(f"\nTrainer: {response}\n")


if __name__ == "__main__":
    main()