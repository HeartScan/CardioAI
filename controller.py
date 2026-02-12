import json
from typing import Any

from utils import get_settings, preprocess_obs, normalize_observation
from chat_model import ChatSession


class Controller:
    """
    Связывает Web-API и LLM.

    После создания:
      • отправляет наблюдение в модель;
      • сохраняет первый ответ (self.init_response),
        чтобы фронт мог тут же показать результат.
    """

    def __init__(self, observation: Any) -> None:
        # 1) Системный промпт и клиент
        self.system_prompt = get_settings(section="DEFAULT",
                                          variable="SYSTEM_PROMPT")
        self.client = ChatSession(system_prompt=self.system_prompt)

        # 2) Препроцессинг и первый запрос к модели
        obs_norm, fs = normalize_observation(observation)
        metrics = preprocess_obs(obs_norm, fs=fs)
        self.observation = metrics
        self.init_response: str = self.client.send_message(
            "SCG data:\n" + json.dumps(metrics, ensure_ascii=False)
        )

    # ---------- API, вызываемая из server.py ----------

    def get_init_response(self) -> str:
        """Вернуть ответ, полученный сразу после инициализации."""
        return self.init_response

    def send_user_message(self, message: str) -> str:
        """Отправить пользовательское сообщение в LLM и получить ответ."""
        return self.client.send_message(message)

    def get_history(self):
        """Получить всю историю диалога."""
        return self.client.get_messages()

