import requests
import time
from utils import get_config, get_secret

class LLMService:
    """
    Service to encapsulate all communication with LLM providers (currently Dr7.ai).
    """
    def __init__(self):
        self.api_key = get_secret("DR7_API_KEY") or get_secret("HF_TOKEN")
        self.base_url = "https://dr7.ai/api/v1/medical/chat/completions"
        self.model_name = get_config("MODEL", section="HF", fallback="medgemma-27b-it")
        self.temperature = float(get_config("TEMPERATURE", section="HF", fallback="0.7"))
        self.max_tokens = int(float(get_config("MAX_TOKENS", section="HF", fallback="1000")))
        self.timeout_s = float(get_config("TIMEOUT_S", section="HF", fallback="120"))
        self.retries = int(float(get_config("RETRIES", section="HF", fallback="5")))

    def get_response(self, messages: list) -> str:
        """
        Sends a list of messages to the LLM and returns the text response.
        """
        if not self.api_key:
            raise ValueError("LLM API Key not set.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        last_error = None
        for i in range(1 + self.retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_s
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return self._sanitize(content)
                
                error_msg = f"API Error {response.status_code}: {response.text}"
                print(f"Attempt {i+1} failed: {error_msg}")
                last_error = RuntimeError(error_msg)
                
            except Exception as e:
                print(f"Attempt {i+1} failed: {e}")
                last_error = e
            
            if i < self.retries:
                time.sleep(1.0)
        
        raise last_error

    def _sanitize(self, text: str) -> str:
        t = (text or "").lstrip()
        if t.endswith('"""'):
            t = t[: -3].rstrip()
        return t
