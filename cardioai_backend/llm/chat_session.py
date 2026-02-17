from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

from cardioai_backend.services.dr7_llm import Dr7LlmClient


class ChatSession:
    """
    Minimal stateful chat wrapper for the backend LLM client.

    This exists primarily to support the `tests/` harness which expects a
    `send_message()` API and internally keeps message history.
    """

    def __init__(
        self,
        *,
        system_prompt: str,
        client: Optional[Dr7LlmClient] = None,
    ) -> None:
        self.client = client or Dr7LlmClient()
        self.messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        self.last_error: Optional[str] = None

    async def send_message_async(self, user_message: str) -> Optional[str]:
        try:
            self.messages.append({"role": "user", "content": user_message})
            reply = await self.client.chat(self.messages)
            self.messages.append({"role": "assistant", "content": reply})
            self.last_error = None
            return reply
        except Exception as e:
            self.last_error = str(e)
            return None

    def send_message(self, user_message: str) -> Optional[str]:
        """
        Synchronous wrapper (used by legacy scripts).
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.send_message_async(user_message))
        raise RuntimeError("ChatSession.send_message() cannot be used inside a running event loop; use send_message_async().")

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self.messages)

