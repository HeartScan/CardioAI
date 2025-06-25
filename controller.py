from utils import get_settings, preprocess_obs
from chat_model import WriterChatSession


class Controller:
    """
    Связывает Web-API и LLM.

    После создания:
      • отправляет наблюдение в модель;
      • сохраняет первый ответ (self.init_response),
        чтобы фронт мог тут же показать результат.
    """

    def __init__(self, observation: str) -> None:
        # 1) Системный промпт и клиент
        self.system_prompt = get_settings(section="DEFAULT",
                                          variable="SYSTEM_PROMPT")
        self.client = WriterChatSession(system_prompt=self.system_prompt)

        # 2) Препроцессинг и первый запрос к модели
        self.observation = preprocess_obs(observation)
        self.init_response: str = self.client.send_message(
            f"SCG data:\n{self.observation}"
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

