class ChatSession:
    """
    Backwards-compatible chat session wrapper used by Controller,
    but the underlying provider is now a HuggingFace Inference Endpoint
    with an OpenAI-compatible API.
    """
    def __init__(self, system_prompt=None, model_name=None, timeout_s=None):
        """
        Инициализирует объект чата.
        Настройки:
          - HF токен: secrets.ini -> HF_TOKEN
          - HF endpoint base_url: config.ini -> [HF] BASE_URL
          - HF model: config.ini -> [HF] MODEL
        """
        try:
            from openai import OpenAI  # local import to keep startup lighter
            from utils import get_config, get_secret
            import time

            self.messages = []
            self.timeout_s = timeout_s
            self.last_error = None
            self._sleep = time.sleep

            hf_token = get_secret("DR7_API_KEY") or get_secret("HF_TOKEN")
            base_url = get_config("BASE_URL", section="HF")
            hf_model = get_config("MODEL", section="HF", fallback="med-gemma")
            hf_temperature = get_config("TEMPERATURE", section="HF", fallback="0.2")
            hf_max_tokens = get_config("MAX_TOKENS", section="HF", fallback="512")
            hf_timeout_s = get_config("TIMEOUT_S", section="HF", fallback="60")
            hf_retries = get_config("RETRIES", section="HF", fallback="1")

            # Normalize base_url: OpenAI-compatible endpoints typically expose /v1/*
            base_url = (base_url or "").strip()
            if base_url.endswith("/"):
                base_url = base_url[:-1]
            if base_url and not base_url.endswith("/v1"):
                base_url = base_url + "/v1"

            if not base_url:
                raise ValueError("HF BASE_URL is not set in config.ini ([HF] BASE_URL)")
            if not hf_token:
                raise ValueError("HF_TOKEN is not set (check Environment Variables or secrets.ini)")

            # If caller passed an explicit model_name, prefer it; otherwise use config.
            self.model_name = model_name or hf_model

            self.client = OpenAI(api_key=hf_token, base_url=base_url)
            # Call settings
            try:
                self.temperature = float(hf_temperature)
            except Exception:
                self.temperature = 0.2
            try:
                self.max_tokens = int(float(hf_max_tokens))
            except Exception:
                self.max_tokens = 512
            if self.timeout_s is None:
                try:
                    self.timeout_s = float(hf_timeout_s)
                except Exception:
                    self.timeout_s = 60.0
            try:
                self.retries = max(0, int(float(hf_retries)))
            except Exception:
                self.retries = 1

            if system_prompt:
                self.messages.append({"role": "system", "content": system_prompt})
            print(f"Сессия инициализирована (HF OpenAI-compatible). model={self.model_name}")
            if system_prompt:
                print("Установлен системный промпт.")
        except Exception as e:
            print(f"Ошибка при инициализации клиента HF: {e}")
            self.client = None
            self.last_error = str(e)

    def _complete_once(self) -> str:
        chat_response = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,  # type: ignore
            timeout=self.timeout_s,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        model_response = chat_response.choices[0].message.content if chat_response.choices else None
        if not model_response:
            raise RuntimeError("Empty response from model")
        return self._sanitize_response(model_response)

    @staticmethod
    def _sanitize_response(text: str) -> str:
        """
        Best-effort cleanup for models that sometimes emit chain-of-thought-like prefixes
        (e.g., starting with 'thought'/'analysis') or prompt artifacts.
        """
        t = (text or "").lstrip()

        # Drop accidental trailing triple quotes (seen in earlier prompt leakage cases)
        if t.endswith('"""'):
            t = t[: -3].rstrip()

        lower = t.lower()
        if lower.startswith("thought") or lower.startswith("analysis"):
            # If the model includes the required user-facing prefix later, keep from there.
            marker = "i am cardioai"
            idx = lower.find(marker)
            if idx >= 0:
                return t[idx:].lstrip()

            # Otherwise, remove the first "thought/analysis" block up to the first blank line.
            parts = t.split("\n\n", 1)
            if len(parts) == 2 and parts[1].strip():
                return parts[1].lstrip()

        return t

    def _complete_with_retry(self) -> str:
        last_exc = None
        attempts = 1 + int(getattr(self, "retries", 0) or 0)
        for i in range(attempts):
            try:
                return self._complete_once()
            except Exception as e:
                last_exc = e
                if i < attempts - 1:
                    try:
                        self._sleep(1.0)
                    except Exception:
                        pass
        raise last_exc

    def start_session(self):
        """
        Начинает интерактивную чат-сессию.
        """
        if not self.client:
            print("Клиент HF не был инициализирован. Невозможно начать сессию.")
            return

        #print(f"\nНачат чат с моделью {self.model_name}. Введите 'exit' для завершения.")
        print(f"\nChat started with CardioAI model. Enter 'exit' to finish.")

        while True:
            user_input = input("user: ")#("Вы: ")
            if user_input.lower() == 'exit':
                break

            self.messages.append({"role": "user", "content": user_input})

            try:
                model_response = self._complete_with_retry()
                #print(f"Модель ({self.model_name}): {model_response}")
                print(f"agent: {model_response}")
                self.messages.append({"role": "assistant", "content": model_response}) # Добавляем ответ модели в историю
            except Exception as e:
                #print(f"Произошла ошибка при общении с моделью: {e}")
                print(f"Shit happend: {e}")
                self.last_error = str(e)
                if self.messages and self.messages[-1]['role'] == 'user':
                    self.messages.pop() # Удаляем последний ввод пользователя, если произошла ошибка

    def send_message(self, user_message):
        """
        Отправляет сообщение модели и возвращает ответ.

        Args:
            user_message (str): Сообщение пользователя.

        Returns:
            str: Ответ модели или None в случае ошибки.
        """
        if not self.client:
            print("Клиент HF не был инициализирован. Невозможно отправить сообщение.")
            return None

        self.messages.append({"role": "user", "content": user_message})

        try:
            model_response = self._complete_with_retry()
            self.messages.append({"role": "assistant", "content": model_response})
            self.last_error = None
            return model_response
        except Exception as e:
            print(f"Произошла ошибка при отправке сообщения: {e}")
            self.last_error = str(e)
            if self.messages and self.messages[-1]['role'] == 'user':
                 self.messages.pop() # Удаляем последний ввод пользователя, если произошла ошибка
            return None

    def get_messages(self):
        """
        Возвращает историю сообщений в сессии.

        Returns:
            list: Список словарей с сообщениями.
        """
        return self.messages

    def clear_history(self):
        """
        Очищает историю сообщений, сохраняя системный промпт, если он был установлен.
        """
        system_message = None
        if self.messages and self.messages[0]['role'] == 'system':
            system_message = self.messages[0]
        self.messages = []
        if system_message:
            self.messages.append(system_message)
        print("История сообщений очищена.")
