from typing import Any, Dict, List, Optional

from openai import OpenAI  # type: ignore
import os
import time


class OpenAIChatSession:
    """
    OpenAI Chat Completions API client using official SDK.
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
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        # Create SDK client; env OPENAI_API_KEY/OPENAI_BASE_URL are supported
        client_kwargs: Dict[str, Any] = {}
        if api_key or os.environ.get("OPENAI_API_KEY"):
            client_kwargs["api_key"] = api_key or os.environ.get("OPENAI_API_KEY")
        if base_url or os.environ.get("OPENAI_BASE_URL"):
            client_kwargs["base_url"] = base_url or os.environ.get("OPENAI_BASE_URL")
        self.client = OpenAI(**client_kwargs)
        self.messages: List[Dict[str, str]] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def _complete_once(self) -> Optional[str]:
        try:
            res = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,  # type: ignore
                temperature=self.temperature,
                max_tokens=int(self.max_tokens) if self.max_tokens is not None else None,
                timeout=self.timeout_s,
            )
            msg = res.choices[0].message.content if res.choices else None  # type: ignore
            if msg:
                self.messages.append({"role": "assistant", "content": msg})
            return msg
        except Exception:
            # Simple one retry for transient issues
            try:
                time.sleep(1.0)
                res = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,  # type: ignore
                    temperature=self.temperature,
                    max_tokens=int(self.max_tokens) if self.max_tokens is not None else None,
                    timeout=self.timeout_s,
                )
                msg = res.choices[0].message.content if res.choices else None  # type: ignore
                if msg:
                    self.messages.append({"role": "assistant", "content": msg})
                return msg
            except Exception:
                return None

    def complete_with_user_input(self, user_input: str) -> Optional[str]:
        self.messages.append({"role": "user", "content": user_input})
        return self._complete_once()

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self.messages)


