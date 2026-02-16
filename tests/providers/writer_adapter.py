import json
from typing import Any, Dict, List, Optional

from chat_model import ChatSession  # type: ignore
from utils import get_settings  # type: ignore


class WriterCardioAdapter:
    """
    Thin wrapper around the existing WriterChatSession to mimic
    the production pipeline used by Controller:
      - loads SYSTEM_PROMPT from config.ini
      - sends first message as 'SCG data:\\n{metrics_json}'
    """

    def __init__(self, system_prompt: Optional[str] = None, model_name: Optional[str] = None, timeout_s: Optional[float] = None) -> None:
        self.system_prompt = system_prompt or get_settings(section="DEFAULT", variable="SYSTEM_PROMPT")
        # WriterChatSession now defaults to HF model from config.ini ([HF] MODEL).
        if model_name:
            self.session = ChatSession(system_prompt=self.system_prompt, model_name=model_name, timeout_s=timeout_s)
            self.model_name = model_name
        else:
            self.session = ChatSession(system_prompt=self.system_prompt, timeout_s=timeout_s)
            self.model_name = "med-gemma"

    def init_with_metrics(self, metrics: Dict[str, Any]) -> Optional[str]:
        payload = f"SCG data:\n{json.dumps(metrics, ensure_ascii=False)}"
        return self.session.send_message(payload)

    def send_user_message(self, message: str) -> Optional[str]:
        return self.session.send_message(message)

    def get_history(self) -> List[Dict[str, str]]:
        return self.session.get_messages()

    def get_last_error(self) -> Optional[str]:
        return getattr(self.session, "last_error", None)


