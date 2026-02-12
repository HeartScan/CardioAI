from typing import Any, Dict, List, Optional

from openai import OpenAI  # type: ignore
import os
import time

from utils import get_secret  # type: ignore

import json
from pathlib import Path


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
        # Create SDK client; reads OPENAI_API_KEY from secrets.ini by default.
        client_kwargs: Dict[str, Any] = {}
        secrets_key = get_secret("OPENAI_API_KEY")
        if api_key or secrets_key:
            client_kwargs["api_key"] = api_key or secrets_key
        if base_url or os.environ.get("OPENAI_BASE_URL"):
            # allow override via argument or env if user still uses it for tests
            client_kwargs["base_url"] = base_url or os.environ.get("OPENAI_BASE_URL")
        self.client = OpenAI(**client_kwargs)
        self.messages: List[Dict[str, str]] = []
        self.last_error_type: Optional[str] = None
        self.last_error: Optional[str] = None
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        # #region agent log
        try:
            repo_root = Path(__file__).resolve().parents[2]
            log_path = repo_root / ".cursor" / "debug.log"
            payload = {
                "timestamp": int(time.time() * 1000),
                "location": "tests/providers/openai_adapter.py:__init__",
                "message": "openai_client_initialized",
                "data": {
                    "model": self.model,
                    "has_api_key": bool(api_key or os.environ.get("OPENAI_API_KEY")),
                    "has_base_url": bool(base_url or os.environ.get("OPENAI_BASE_URL")),
                },
                "sessionId": "debug-session",
                "runId": os.environ.get("CARDIOAI_DEBUG_RUN_ID", "openai"),
                "hypothesisId": "C",
            }
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # #endregion

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
                self.last_error_type = None
                self.last_error = None
            return msg
        except Exception as e1:
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
                    self.last_error_type = None
                    self.last_error = None
                return msg
            except Exception as e:
                # #region agent log
                try:
                    repo_root = Path(__file__).resolve().parents[2]
                    log_path = repo_root / ".cursor" / "debug.log"
                    payload = {
                        "timestamp": int(time.time() * 1000),
                        "location": "tests/providers/openai_adapter.py:_complete_once",
                        "message": "openai_call_failed",
                        "data": {
                            "error_type": type(e).__name__,
                            "error": str(e)[:300],
                            "model": self.model,
                        },
                        "sessionId": "debug-session",
                        "runId": os.environ.get("CARDIOAI_DEBUG_RUN_ID", "openai"),
                        "hypothesisId": "C",
                    }
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                except Exception:
                    pass
                # #endregion
                self.last_error_type = type(e).__name__
                self.last_error = str(e)
                return None
        finally:
            # record the first exception if retry wasn't attempted/failed
            if "e1" in locals() and self.last_error_type is None:
                self.last_error_type = type(e1).__name__
                self.last_error = str(e1)

    def complete_with_user_input(self, user_input: str) -> Optional[str]:
        self.messages.append({"role": "user", "content": user_input})
        return self._complete_once()

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self.messages)

    def get_last_error(self) -> Dict[str, Optional[str]]:
        return {"type": self.last_error_type, "message": self.last_error}


