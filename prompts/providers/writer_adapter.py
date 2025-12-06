import json
from typing import Any, Dict, List, Optional

from chat_model import WriterChatSession  # type: ignore
from utils import get_settings  # type: ignore


class WriterCardioAdapter:
    """
    Thin wrapper around the existing WriterChatSession to mimic
    the production pipeline used by Controller:
      - loads SYSTEM_PROMPT from config.ini
      - sends first message as 'SCG data:\\n{metrics_json}'
    """

    def __init__(self, system_prompt: Optional[str] = None, model_name: Optional[str] = None) -> None:
        self.system_prompt = system_prompt or get_settings(section="DEFAULT", variable="SYSTEM_PROMPT")
        # WriterChatSession already has a default model 'palmyra-med'
        if model_name:
            self.session = WriterChatSession(system_prompt=self.system_prompt, model_name=model_name)
            self.model_name = model_name
        else:
            self.session = WriterChatSession(system_prompt=self.system_prompt)
            self.model_name = "palmyra-med"

    def init_with_metrics(self, metrics: Dict[str, Any]) -> Optional[str]:
        payload = f"SCG data:\n{json.dumps(metrics, ensure_ascii=False)}"
        return self.session.send_message(payload)

    def send_user_message(self, message: str) -> Optional[str]:
        return self.session.send_message(message)

    def get_history(self) -> List[Dict[str, str]]:
        return self.session.get_messages()


