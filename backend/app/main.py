from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.graph import app_graph
from langchain_core.messages import HumanMessage
import uuid
import os
from app.models.schemas import UserMessage
from app.core.error_handler import generate_error_response

load_dotenv()

app = FastAPI(title="Banco Ágil API")

origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
    
@app.post("/chat")
def chat_endpoint(user_msg: UserMessage):
    """
    Invoca o agente LangGraph.
    """

    session_id = user_msg.session_id

    if session_id not in sessions:

        sessions[session_id] = {
            "messages": [],
            "user_data": None,
            "auth_attempts": 0,
            "next_node": "triage",
            "active_agent": "triage",
            "interview_step": 0,
            "interview_answers": [],
            "triage_step": "greeting",
            "temp_cpf": None
        }

    current_state = sessions[session_id]
    current_state["messages"].append(HumanMessage(content=user_msg.message))

    try:
        output = app_graph.invoke(current_state)

        sessions[session_id] = output

        last_message = output["messages"][-1].content

        return {
            "response": last_message
        }

    except Exception as e:

        print(f"Error processing request: {e}")
        error_msg = generate_error_response(str(e))

        return {
            "response": error_msg
        }