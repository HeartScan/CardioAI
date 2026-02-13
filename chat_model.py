import json
import requests
import time
from utils import get_config, get_secret

class ChatSession:
    """
    Direct Medical AI API (Dr7.ai) client using standard requests.
    """
    def __init__(self, system_prompt=None, model_name=None, timeout_s=None):
        try:
            self.messages = []
            self.last_error = None
            
            # Settings
            self.api_key = get_secret("DR7_API_KEY") or get_secret("HF_TOKEN")
            self.base_url = "https://dr7.ai/api/v1/medical/chat/completions"
            self.model_name = model_name or get_config("MODEL", section="HF", fallback="medgemma-27b-it")
            self.temperature = float(get_config("TEMPERATURE", section="HF", fallback="0.7"))
            self.max_tokens = int(float(get_config("MAX_TOKENS", section="HF", fallback="1000")))
            self.timeout_s = timeout_s or float(get_config("TIMEOUT_S", section="HF", fallback="120"))
            self.retries = int(float(get_config("RETRIES", section="HF", fallback="3")))

            if not self.api_key:
                raise ValueError("API Key (DR7_API_KEY) is not set")

            if system_prompt:
                self.messages.append({"role": "system", "content": system_prompt})
            
            print(f"ChatSession initialized for Dr7.ai. model={self.model_name}")
        except Exception as e:
            print(f"Error initializing ChatSession: {e}")
            self.last_error = str(e)

    def _complete_once(self) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": self.messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout_s
        )

        if response.status_code != 200:
            raise RuntimeError(f"API Error {response.status_code}: {response.text}")

        data = response.json()
        model_response = data["choices"][0]["message"]["content"]
        
        if not model_response:
            raise RuntimeError("Empty response from model")
            
        return self._sanitize_response(model_response)

    @staticmethod
    def _sanitize_response(text: str) -> str:
        t = (text or "").lstrip()
        if t.endswith('"""'):
            t = t[: -3].rstrip()
        return t

    def _complete_with_retry(self) -> str:
        last_exc = None
        attempts = 1 + self.retries
        for i in range(attempts):
            try:
                return self._complete_once()
            except Exception as e:
                last_exc = e
                print(f"Attempt {i+1} failed: {e}")
                if i < attempts - 1:
                    time.sleep(1.0)
        raise last_exc

    def send_message(self, user_message):
        if not self.api_key:
            print("API Key not set. Cannot send message.")
            return None

        self.messages.append({"role": "user", "content": user_message})

        try:
            model_response = self._complete_with_retry()
            self.messages.append({"role": "assistant", "content": model_response})
            self.last_error = None
            return model_response
        except Exception as e:
            print(f"Error in send_message: {e}")
            self.last_error = str(e)
            if self.messages and self.messages[-1]['role'] == 'user':
                self.messages.pop()
            return None

    def get_messages(self):
        return self.messages

    def clear_history(self):
        system_message = None
        if self.messages and self.messages[0]['role'] == 'system':
            system_message = self.messages[0]
        self.messages = []
        if system_message:
            self.messages.append(system_message)
        print("History cleared.")
