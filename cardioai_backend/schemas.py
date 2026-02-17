from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: Optional[str] = None
    history: Optional[List[Message]] = []
    observation: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    history: List[Dict[str, str]]

