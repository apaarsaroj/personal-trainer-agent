import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langchain.tools import tool
from trainer.tools import (
    get_user_profile,
    log_workout,
    get_workout_history,
    generate_workout_plan,
    search_knowledge_base
)

load_dotenv()

MODEL = "claude-sonnet-4-6"


def load_system_prompt(profile: dict) -> str:
    """Load system prompt and inject member profile."""

    with open("prompts/system_prompt.txt", "r") as f:
        template = f.read()

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

    return template.replace("{member_profile}", profile_text)


def build_tools(member_id: str) -> list:
    """Build LangChain tools with member_id already injected."""

    @tool
    def get_member_profile(user_id: str) -> str:
        """Get any member's profile by their member ID. Only use this for fetching OTHER members profiles or if the current member updates their information."""
        result = get_user_profile(user_id)
        return json.dumps(result)

    @tool
    def log_member_workout(exercise: str, sets: int, reps: int, weight_kg: float, body_part: str) -> str:
        """Log a completed workout for the current member. Automatically determine the body_part from the exercise name."""
        result = log_workout(
            exercise=exercise,
            sets=sets,
            reps=reps,
            weight_kg=weight_kg,
            body_part=body_part,
            user_id=member_id
        )
        return json.dumps(result)

    @tool
    def get_member_workout_history(days: int = 7, body_part: str = None) -> str:
        """Get workout history for the current member. Always call this before creating a new workout plan."""
        result = get_workout_history(
            days=days,
            body_part=body_part,
            user_id=member_id
        )
        return json.dumps(result)

    @tool
    def create_workout_plan(days_per_week: int, focus: str = None) -> str:
        """Generate a personalized workout plan for the current member."""
        result = generate_workout_plan(
            days_per_week=days_per_week,
            focus=focus
        )
        return json.dumps(result)
    
    @tool
    def search_fitness_knowledge(query: str) -> str:
        """Search the fitness knowledge base for evidence-based information about exercises, nutrition, recovery, and training principles. Use this before giving any fitness advice."""
        print(f"🔍 SEARCHING KNOWLEDGE BASE: {query}")
        result = search_knowledge_base(query)
        return json.dumps(result)

    return [
        get_member_profile,
        log_member_workout,
        get_member_workout_history,
        create_workout_plan,
        search_fitness_knowledge
    ]


def run_agent(user_message: str, messages: list, profile: dict) -> tuple[str, list]:
    """
    Run one turn of the agent loop using LangChain.

    Args:
        user_message: what the user typed
        messages: full conversation history
        profile: member profile dict

    Returns:
        final_response: Claude's final text answer
        messages: updated conversation history
    """

    system_prompt = load_system_prompt(profile)
    tools = build_tools(profile["member_id"])

    # Create LangChain agent with Claude
    agent = create_agent(
        model=f"anthropic:{MODEL}",
        tools=tools,
        system_prompt=system_prompt
    )

    # Add user message to history
    messages.append({
        "role": "user",
        "content": user_message
    })

    # Run the agent
    result = agent.invoke({"messages": messages})

    # Get final response
    final_response = result["messages"][-1].content

    # Add assistant response to history
    messages.append({
        "role": "assistant",
        "content": final_response
    })

    return final_response, messages