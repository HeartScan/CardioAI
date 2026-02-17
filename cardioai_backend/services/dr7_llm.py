from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from cardioai_backend.utils import get_config, get_secret


class Dr7LlmClient:
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout_s: Optional[float] = None,
    ) -> None:
        self.base_url = base_url or get_config(
            "BASE_URL", section="DR7", fallback="https://dr7.ai/api/v1/medical/chat/completions"
        )
        self.api_key = api_key if api_key is not None else get_secret("DR7_API_KEY")
        self.model = model or get_config("MODEL", section="DR7", fallback="medgemma-27b-it")
        self.temperature = float(temperature) if temperature is not None else float(
            get_config("TEMPERATURE", section="DR7", fallback="0.7")
        )
        self.max_tokens = int(max_tokens) if max_tokens is not None else int(
            float(get_config("MAX_TOKENS", section="DR7", fallback="1000"))
        )
        self.timeout_s = float(timeout_s) if timeout_s is not None else float(
            get_config("TIMEOUT_S", section="DR7", fallback="60")
        )

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key or ''}"}
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            res = await client.post(self.base_url, json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]

