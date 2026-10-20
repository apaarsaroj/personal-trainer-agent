"""LangGraph trainer agent: guardrails → chatbot ↔ tools → output guard."""

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from trainer.agent import build_tools, load_system_prompt
from trainer.config import MODEL
from trainer.guardrails import check_input, check_output, text_of

load_dotenv()


class TrainerState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    current_plan: str
    session_count: int
    guardrail: str


def create_chatbot_node(profile: dict):
    tools = build_tools(profile["member_id"])
    system_prompt = load_system_prompt(profile)

    llm = ChatAnthropic(model=MODEL)
    llm_with_tools = llm.bind_tools(tools)

    def chatbot_node(state: TrainerState):
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    return chatbot_node


def create_graph(profile: dict, checkpointer):
    tools = build_tools(profile["member_id"])
    tool_node = ToolNode(tools)
    chatbot_node = create_chatbot_node(profile)

    def input_guard_node(state: TrainerState):
        """Block unsafe messages before the model sees them."""
        result = check_input(text_of(state["messages"][-1].content))
        if result.allowed:
            return {"guardrail": ""}
        return {
            "guardrail": result.category,
            "messages": [AIMessage(content=result.reply)],
        }

    def after_input_guard(state: TrainerState) -> str:
        return END if state.get("guardrail") else "chatbot"

    def output_guard_node(state: TrainerState):
        """Check the final reply. Replaces it (same message id) if it needs changing."""
        last_message = state["messages"][-1]
        result = check_output(text_of(last_message.content))
        if result.allowed:
            return {}
        return {
            "guardrail": result.category,
            "messages": [AIMessage(content=result.reply, id=last_message.id)],
        }

    def should_continue(state: TrainerState) -> str:
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return "output_guard"

    graph = StateGraph(TrainerState)
    graph.add_node("input_guard", input_guard_node)
    graph.add_node("chatbot", chatbot_node)
    graph.add_node("tools", tool_node)
    graph.add_node("output_guard", output_guard_node)
    graph.set_entry_point("input_guard")
    graph.add_conditional_edges("input_guard", after_input_guard)
    graph.add_conditional_edges("chatbot", should_continue)
    graph.add_edge("tools", "chatbot")
    graph.add_edge("output_guard", END)

    return graph.compile(checkpointer=checkpointer)


def run_graph(user_message: str, profile: dict, compiled_graph, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    result = compiled_graph.invoke(
        {
            "messages": [HumanMessage(content=user_message)],
            "user_id": profile["member_id"],
            "current_plan": "",
            "current_session": 0,
            "guardrail": "",
        },
        config=config,
    )

    return result["messages"][-1].content
