from typing import Annotated, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    Representa o estado do grafo do agente.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    user_data: Dict[str, Any]
    auth_attempts: int
    next_node: str
    active_agent: str
    interview_step: int
    interview_answers: List[str]
    triage_step: str
    temp_cpf: str
