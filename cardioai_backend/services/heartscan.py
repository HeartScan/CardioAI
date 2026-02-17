from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from cardioai_backend.utils import get_config, get_secret


class HeartscanClient:
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> None:
        self.base_url = base_url or get_config("URL", section="HEARTSCAN", fallback="").strip() or (
            "https://heartscan-api-175148683457.us-central1.run.app/api/v1/cardiolog/realtime_analysis"
        )
        self.api_key = api_key if api_key is not None else get_secret("HEARTSCAN_API_KEY")
        self.timeout_s = float(timeout_s) if timeout_s is not None else float(
            get_config("TIMEOUT_S", section="HEARTSCAN", fallback="30")
        )

    async def analyze(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"X-API-Key": self.api_key or ""}
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            res = await client.post(self.base_url, json=observation, headers=headers)
        res.raise_for_status()
        return res.json()

