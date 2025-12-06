import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class OpenAIChatSession:
    """
    Minimal OpenAI Chat Completions API client using stdlib only.
    Keeps message history and returns assistant replies.
    """

    def __init__(
        self,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_s: float = 60.0,
        max_tokens: Optional[int] = None,
    ) -> None:
        self.model = model
        self.temperature = float(temperature)
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or ""
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, str]] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def _http_post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)

    def _complete_once(self) -> Optional[str]:
        # Endpoint for Chat Completions
        path = "/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": self.messages,
            "temperature": self.temperature,
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = int(self.max_tokens)
        try:
            res = self._http_post(path, payload)
            choice = (res.get("choices") or [{}])[0]
            msg = (choice.get("message") or {}).get("content")
            if msg:
                self.messages.append({"role": "assistant", "content": msg})
            return msg
        except urllib.error.HTTPError as e:
            # Simple backoff retry once on 429/500s
            if e.code in (429, 500, 502, 503):
                time.sleep(1.5)
                try:
                    res = self._http_post(path, payload)
                    choice = (res.get("choices") or [{}])[0]
                    msg = (choice.get("message") or {}).get("content")
                    if msg:
                        self.messages.append({"role": "assistant", "content": msg})
                    return msg
                except Exception:
                    return None
            return None
        except Exception:
            return None

    def complete_with_user_input(self, user_input: str) -> Optional[str]:
        self.messages.append({"role": "user", "content": user_input})
        return self._complete_once()

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self.messages)


