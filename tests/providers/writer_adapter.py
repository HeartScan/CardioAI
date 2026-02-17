import json
from typing import Any, Dict, List, Optional

from cardioai_backend.llm.chat_session import ChatSession  # type: ignore
from cardioai_backend.utils import get_system_prompt  # type: ignore


class WriterCardioAdapter:
    """
    Thin wrapper around the existing WriterChatSession to mimic
    the production pipeline used by Controller:
      - loads SYSTEM_PROMPT from config.ini
      - sends first message as 'SCG data:\\n{metrics_json}'
    """

    def __init__(self, system_prompt: Optional[str] = None, model_name: Optional[str] = None, timeout_s: Optional[float] = None) -> None:
        # model_name/timeout_s kept for backward compatibility of the harness CLI;
        # backend LLM settings are read from cardioai_backend/config.ini.
        self.system_prompt = system_prompt or get_system_prompt()
        self.session = ChatSession(system_prompt=self.system_prompt)
        self.model_name = model_name or "dr7"

    def init_with_metrics(self, metrics: Dict[str, Any]) -> Optional[str]:
        payload = f"SCG data:\n{json.dumps(metrics, ensure_ascii=False)}"
        return self.session.send_message(payload)

    def send_user_message(self, message: str) -> Optional[str]:
        return self.session.send_message(message)

    def get_history(self) -> List[Dict[str, str]]:
        return self.session.get_messages()

    def get_last_error(self) -> Optional[str]:
        return getattr(self.session, "last_error", None)


