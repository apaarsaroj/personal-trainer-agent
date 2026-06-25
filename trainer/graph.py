from typing import TypedDict, Annotated
import operator
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from trainer.agent import load_system_prompt, build_tools
from trainer.tools import (
    get_user_profile,
    log_workout,
    get_workout_history,
    generate_workout_plan
)

MODEL = "claude-sonnet-4-6"

class TrainerState(TypedDict) :
    messages: Annotated[list, operator.add]
    user_id: str
    current_plan: str
    session_count: int

def create_chatbot_node(profile: dict) :

    tools = build_tools(profile["member_id"])
    system_prompt = load_system_prompt(profile)

    llm = ChatAnthropic(model=MODEL)
    llm_with_tools = llm.bind_tools(tools)

    def chatbot_node(state: TrainerState) :
        messages =  [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    return chatbot_node

def create_graph(profile: dict, checkpointer) :

    tools = build_tools(profile["member_id"])
    tool_node = ToolNode(tools)
    chatbot_node = create_chatbot_node(profile)

    def should_continue(state: TrainerState) -> str :
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END
    
    graph = StateGraph(TrainerState)
    graph.add_node("chatbot", chatbot_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("chatbot")
    graph.add_conditional_edges("chatbot", should_continue)
    graph.add_edge("tools", "chatbot")

    return graph.compile(checkpointer=checkpointer)

def run_graph(user_message: str, profile: dict, compiled_graph, thread_id: str) :
    config = {"configurable": {"thread_id": thread_id}}

    result = compiled_graph.invoke(
        {
            "messages": [HumanMessage(content=user_message)],
            "user_id": profile["member_id"],
            "current_plan": "",
            "current_session": 0
        },
        config=config
    )

    return result["messages"][-1].content