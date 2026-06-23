import json
from anthropic import Anthropic
from dotenv import load_dotenv
from trainer.tools import (
    get_user_profile,
    log_workout,
    get_workout_history,
    generate_workout_plan
)

load_dotenv()

MODEL = "claude-sonnet-4-6"


def load_system_prompt(profile: dict) -> str:
    """Load system prompt and inject member profile."""

    with open("prompts/system_prompt.txt", "r") as f:
        template = f.read()

    # Build profile text to inject
    profile_text = f"""Name: {profile['first_name']} {profile['last_name']}
Member ID: {profile['member_id']}
Age: {profile['age']}
Weight: {profile['weight_kg']} kg
Height: {profile['height_cm']} cm
Fitness level: {profile['fitness_level']}
Goals: {', '.join(profile['goals'])}
Injuries: {', '.join(profile['injuries']) if profile['injuries'] else 'None'}
Default training days per week: {profile['days_per_week']}
Joined: {profile['joined_date']}"""

    # Replace placeholder with actual profile
    return template.replace("{member_profile}", profile_text)


def load_tools() -> list:
    """Load tool schemas from file."""
    with open("prompts/tools.json", "r") as f:
        return json.load(f)
    
def dispatch_tool(tool_name: str, tool_input: dict, member_id: str) -> str:
    """Run the correct tool based on what Claude requested."""

    try:
        if tool_name == "get_user_profile":
            result = get_user_profile(**tool_input)

        elif tool_name == "log_workout":
            result = log_workout(user_id=member_id, **tool_input)

        elif tool_name == "get_workout_history":
            result = get_workout_history(user_id=member_id, **tool_input)

        elif tool_name == "generate_workout_plan":
            result = generate_workout_plan(**tool_input)

        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": str(e)})
    
def run_agent(user_message: str, messages: list, profile: dict) -> tuple[str, list]:
    """
    Run one turn of the agent loop.
    
    Args:
        user_message: what the user typed
        messages: full conversation history
    
    Returns:
        final_response: Claude's final text answer
        messages: updated conversation history
    """

    # Add user message to history
    messages.append({
        "role": "user",
        "content": user_message
    })

    system_prompt = load_system_prompt(profile)
    tools = load_tools()
    client = Anthropic()

    # Agent loop — runs until Claude says end_turn
    while True:

        # Send messages to Claude
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        # Add Claude's response to history
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # If Claude is done — return the final answer
        if response.stop_reason == "end_turn":
            final_response = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_response = block.text
            return final_response, messages

        # If Claude wants to use a tool
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"[Agent] Calling tool: {block.name} with {block.input}")

                    tool_output = dispatch_tool(block.name, block.input, profile["member_id"])

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_output
                    })

            # Send tool results back to Claude
            messages.append({
                "role": "user",
                "content": tool_results
            })