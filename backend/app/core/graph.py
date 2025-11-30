from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
import operator
from app.agents.triage import triage_node
from app.agents.credit import credit_node, interview_offer_node
from app.agents.interview import interview_node
from app.agents.exchange import exchange_node
from app.models.state import AgentState

workflow = StateGraph(AgentState)
workflow.add_node("triage", triage_node)
workflow.add_node("credit_agent", credit_node)
workflow.add_node("interview_offer", interview_offer_node)
workflow.add_node("interview_agent", interview_node)
workflow.add_node("exchange_agent", exchange_node)

def router(state):
    return state["next_node"]

workflow.set_entry_point("triage")

workflow.add_conditional_edges(
    "triage",
    router,
    {
        "triage": "triage",
        "credit_agent": "credit_agent",
        "exchange_agent": "exchange_agent",
        "interview_agent": "interview_agent",
        "interview_offer": "interview_offer",
        "end": END
    }
)

workflow.add_conditional_edges(
    "credit_agent",
    router,
    {
        "triage": "triage",
        "credit_agent": "credit_agent",
        "interview_offer": "interview_offer",
        "end": END
    }
)

workflow.add_conditional_edges(
    "interview_offer",
    router,
    {
        "interview_agent": "interview_agent",
        "triage": "triage",
        "end": END
    }
)

workflow.add_conditional_edges(
    "interview_agent",
    router,
    {
        "interview_agent": "interview_agent",
        "credit_agent": "credit_agent",
        "end": END
    }
)

workflow.add_conditional_edges(
    "exchange_agent",
    router,
    {
        "triage": "triage",
        "end": END
    }
)

app_graph = workflow.compile()
