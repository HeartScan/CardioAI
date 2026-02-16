from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import uuid
from typing import Any, Dict, List, Optional

from agent import CardioAgent

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (can be easily replaced with Redis/DB)
sessions: Dict[str, CardioAgent] = {}

class InitPayload(BaseModel):
    observation: Any

class ChatPayload(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

@app.post("/api/init")
async def init_chat(payload: InitPayload, response: Response):
    session_id = str(uuid.uuid4())
    agent = CardioAgent(payload.observation)
    
    # Store agent instance in memory
    sessions[session_id] = agent
    
    # Set session cookie
    response.set_cookie(
        key="session_id", 
        value=session_id, 
        httponly=True, 
        samesite="none", 
        secure=True # Required for cross-site cookies
    )
    
    initial_msg = agent.get_initial_response()
    
    return {
        "status": "initialized",
        "session_id": session_id,
        "response": initial_msg
    }

@app.post("/api/chat")
async def chat(payload: ChatPayload, session_id: Optional[str] = None):
    # Try to get session from cookie or header (for flexible testing)
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    
    agent = sessions.get(session_id)
    if not agent:
        # If session expired/lost in memory, we could potentially rebuild it 
        # but for now we throw error. In DB-version we would fetch from DB.
        raise HTTPException(status_code=400, detail="Session expired or invalid")
        
    response = agent.handle_message(payload.message, payload.history)
    
    return {
        "response": response
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port
    )
