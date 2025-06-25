from utils import get_client


class WriterChatSession:
    """
    Класс для управления интерактивной чат-сессией с моделью Writer.
    """
    def __init__(self, system_prompt=None, model_name="palmyra-med"):
        """
        Инициализирует объект WriterChatSession.

        Args:
            api_key (str): API ключ для доступа к WriterAI.
            system_prompt (str, optional): Системный промпт для установки контекста.
                                           По умолчанию None (без системного промпта).
            model_name (str): Название модели Writer для использования.
        """
        try:
            self.client = get_client()
            self.model_name = model_name
            self.messages = []
            if system_prompt:
                self.messages.append({"role": "system", "content": system_prompt})
            print(f"Сессия WriterChatSession инициализирована с моделью {self.model_name}")
            if system_prompt:
                print("Установлен системный промпт.")
        except Exception as e:
            print(f"Ошибка при инициализации клиента Writer: {e}")
            self.client = None

    def start_session(self):
        """
        Начинает интерактивную чат-сессию.
        """
        if not self.client:
            print("Клиент Writer не был инициализирован. Невозможно начать сессию.")
            return

        #print(f"\nНачат чат с моделью {self.model_name}. Введите 'exit' для завершения.")
        print(f"\nChat started with CardioAI model. Enter 'exit' to finish.")

        while True:
            user_input = input("user: ")#("Вы: ")
            if user_input.lower() == 'exit':
                break

            self.messages.append({"role": "user", "content": user_input})

            try:
                chat_response = self.client.chat.chat(
                    messages=self.messages,
                    model=self.model_name,
                )
                model_response = chat_response.choices[0].message.content
                #print(f"Модель ({self.model_name}): {model_response}")
                print(f"agent: {model_response}")
                self.messages.append({"role": "assistant", "content": model_response}) # Добавляем ответ модели в историю
            except Exception as e:
                #print(f"Произошла ошибка при общении с моделью: {e}")
                print(f"Shit happend: {e}")
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
            print("Клиент Writer не был инициализирован. Невозможно отправить сообщение.")
            return None

        self.messages.append({"role": "user", "content": user_message})

        try:
            chat_response = self.client.chat.chat(
                messages=self.messages,
                model=self.model_name,
            )
            model_response = chat_response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": model_response})
            return model_response
        except Exception as e:
            print(f"Произошла ошибка при отправке сообщения: {e}")
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
