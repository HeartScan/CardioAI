from __future__ import annotations

from cardioai_backend.config import get_config


def get_system_prompt() -> str:
    """
    Load the system prompt from `cardioai_backend/config.ini`.
    """
    return get_config("SYSTEM_PROMPT", section="DEFAULT", fallback="").strip()

