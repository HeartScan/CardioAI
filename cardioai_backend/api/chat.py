from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException

from cardioai_backend.schemas import ChatRequest, ChatResponse, Message
from cardioai_backend.services.dr7_llm import Dr7LlmClient
from cardioai_backend.services.heartscan import HeartscanClient
from cardioai_backend.utils import get_system_prompt

router = APIRouter(prefix="/api")


def _model_to_dict(m: Message) -> Dict[str, str]:
    # Pydantic v1 uses .dict(); v2 uses .model_dump()
    if hasattr(m, "model_dump"):
        return m.model_dump()  # type: ignore[no-any-return]
    return m.dict()  # type: ignore[no-any-return]


def parse_math_data(data: Dict[str, Any]) -> str:
    avg_bpm = round(data.get("avg_bpm", 0))
    min_bpm = round(data.get("min_bpm", 0))
    max_bpm = round(data.get("max_bpm", 0))
    episodes_count = data.get("episodes_count", 0)
    episodes_per_hour = data.get("episodes_per_hour", 0)

    # episodes_timestamps can be list of lists [start, end]
    raw_timestamps = data.get("episodes_timestamps", [])
    formatted_ts: List[str] = []
    for ts in raw_timestamps:
        if isinstance(ts, list):
            formatted_ts.append("-".join(str(i) for i in ts))
        else:
            formatted_ts.append(str(ts))

    timestamps_str = ", ".join(formatted_ts) if formatted_ts else "None"

    return (
        """
--- CLINICAL MEASUREMENT REPORT ---
[Metric: Average Heart Rate]
Value: {avg_bpm} BPM
Description: The mean heart rate calculated during the measurement period.

[Metric: Heart Rate Range]
Value: Min {min_bpm} BPM - Max {max_bpm} BPM
Description: The minimum and maximum instantaneous heart rate values detected.

[Metric: Abnormal Episodes]
Value: {episodes_count} detected
Description: Total number of rhythmic anomalies or significant deviations from the baseline heart rate.

[Metric: Frequency of Anomalies]
Value: {episodes_per_hour:.1f} episodes per hour
Description: The extrapolated density of abnormal heart rhythm events.

[Metric: Event Timestamps]
Value: {timestamps_str}
Description: Precise time markers within the recording when anomalies were identified.
-----------------------------------
""".strip()
    ).format(
        avg_bpm=avg_bpm,
        min_bpm=min_bpm,
        max_bpm=max_bpm,
        episodes_count=episodes_count,
        episodes_per_hour=float(episodes_per_hour or 0),
        timestamps_str=timestamps_str,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Canonical production endpoint.
    Accepts either:
      - message + history
      - observation (raw SCG accelerometer payload) + optional message/history
    """
    try:
        system_prompt = get_system_prompt()
        if not system_prompt:
            raise RuntimeError(
                "Missing SYSTEM_PROMPT in cardioai_backend/config.ini (section [DEFAULT])."
            )

        clean_history: List[Dict[str, str]] = [
            _model_to_dict(m) for m in (request.history or []) if m.role != "system"
        ]
        full_messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if request.observation:
            math_client = HeartscanClient()
            try:
                math_data = await math_client.analyze(request.observation)
            except httpx.HTTPStatusError as e:  # type: ignore[name-defined]
                raise HTTPException(status_code=e.response.status_code, detail=f"Math API Error: {e.response.text}")
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Math API Error: {str(e)}")

            if not math_data.get("avg_bpm") or math_data.get("avg_bpm") == 0:
                error_msg = (
                    "Data could not be processed. Please perform the measurement again. "
                    "Lie down flat, place the phone in the middle of your chest vertically or under your left breast horizontally, "
                    "and start the measurement for 60 seconds. During the process, the phone will make sounds like a heart monitor."
                )

                new_history = list(clean_history)
                if request.message:
                    new_history.append({"role": "user", "content": request.message})
                new_history.append({"role": "assistant", "content": error_msg})

                return {"response": error_msg, "history": new_history}

            full_messages.append(
                {
                    "role": "system",
                    "content": "User just performed a heart rhythm measurement. Results Summary:\n"
                    + parse_math_data(math_data),
                }
            )

        full_messages.extend(clean_history)

        if request.message:
            full_messages.append({"role": "user", "content": request.message})
        elif request.observation:
            full_messages.append({"role": "user", "content": "Analyze my heart rhythm measurement."})

        llm_client = Dr7LlmClient()
        try:
            ai_response = await llm_client.chat(full_messages)
        except httpx.HTTPStatusError as e:  # type: ignore[name-defined]
            raise HTTPException(status_code=e.response.status_code, detail=f"LLM API Error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM API Error: {str(e)}")

        new_history = list(clean_history)
        if request.message:
            new_history.append({"role": "user", "content": request.message})
        elif request.observation:
            new_history.append({"role": "user", "content": "Analyze my heart rhythm measurement."})
        new_history.append({"role": "assistant", "content": ai_response})

        return {"response": ai_response, "history": new_history}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

