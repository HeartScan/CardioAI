from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def sec2hms(sec: float) -> str:
    """Convert seconds to HH:MM:SS."""
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _mean(xs: List[float]) -> float:
    return sum(xs) / float(len(xs)) if xs else 0.0


def _std_pop(xs: List[float]) -> float:
    """
    Population std dev (ddof=0) to match numpy default.
    """
    if not xs:
        return 0.0
    mu = _mean(xs)
    var = _mean([(x - mu) ** 2 for x in xs])
    return math.sqrt(var)


def _softmax(xs: List[float]) -> List[float]:
    if not xs:
        return []
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps)
    if s <= 0:
        # fallback uniform
        return [1.0 / len(xs) for _ in xs]
    return [e / s for e in exps]


def mistake_holder(obs: Dict[str, Any], th: int = 5) -> Dict[str, Any]:
    """Filter out low-count episodes as potential noise."""
    if int(obs.get("episodes_count", 0) or 0) < th:
        obs["episodes_count"] = 0
        obs["episodes_per_hour"] = 0
        obs["episodes_timestamps"] = []
    return obs


def filter_peaks(peaks_x: List[Dict[str, Any]], N: float = 0.0) -> List[Dict[str, int]]:
    """
    Filter out peaks that are too close to each other (relaxation zone).
    Input: [{'x': int|float, ...}, ...]
    Output: [{'x': int}, ...]
    """
    peaks: List[int] = []
    for p in peaks_x or []:
        try:
            peaks.append(int(p.get("x")))  # type: ignore[arg-type]
        except Exception:
            continue
    if not peaks:
        return []

    if N <= 0:
        diffs = [peaks[i] - peaks[i - 1] for i in range(1, len(peaks))]
        avg_diff = _mean([float(d) for d in diffs]) if diffs else 0.0
        N = avg_diff / 2.0 if avg_diff > 0 else 0.0

    filtered = [peaks[0]]
    for i in range(1, len(peaks)):
        if float(peaks[i] - filtered[-1]) > float(N):
            filtered.append(peaks[i])
    return [{"x": int(i)} for i in filtered]


def preprocess_obs(observation: Dict[str, Any], fs: float = 100.0) -> Dict[str, Any]:
    """
    Calculate heart rhythm metrics from peaks.

    Expected observation format:
      {'peaks': [{'x': int}, ...]}
    """
    peaks_in = observation.get("peaks", []) if isinstance(observation, dict) else []
    if not peaks_in:
        return {
            "avg_bpm": 0,
            "min_bpm": 0,
            "max_bpm": 0,
            "episodes_count": 0,
            "episodes_per_hour": 0,
            "episodes_timestamps": [],
            "instantaneous_bpm": [],
            "bpm_deviation": [],
        }

    peaks = filter_peaks(peaks_in)
    if len(peaks) < 2 or fs <= 0:
        return {
            "avg_bpm": 0,
            "min_bpm": 0,
            "max_bpm": 0,
            "episodes_count": 0,
            "episodes_per_hour": 0,
            "episodes_timestamps": [],
            "instantaneous_bpm": [],
            "bpm_deviation": [],
        }

    rr_intervals: List[float] = []
    for i in range(len(peaks) - 1):
        dx = float(peaks[i + 1]["x"] - peaks[i]["x"])
        if dx <= 0:
            continue
        rr_intervals.append(dx / float(fs))

    if not rr_intervals:
        return {
            "avg_bpm": 0,
            "min_bpm": 0,
            "max_bpm": 0,
            "episodes_count": 0,
            "episodes_per_hour": 0,
            "episodes_timestamps": [],
            "instantaneous_bpm": [],
            "bpm_deviation": [],
        }

    instantaneous_bpm = [60.0 / rr for rr in rr_intervals if rr > 0]
    if not instantaneous_bpm:
        return {
            "avg_bpm": 0,
            "min_bpm": 0,
            "max_bpm": 0,
            "episodes_count": 0,
            "episodes_per_hour": 0,
            "episodes_timestamps": [],
            "instantaneous_bpm": [],
            "bpm_deviation": [],
        }

    mean_bpm = _mean(instantaneous_bpm)
    bpm_deviation = [bpm - mean_bpm for bpm in instantaneous_bpm]
    min_bpm = min(instantaneous_bpm)
    max_bpm = max(instantaneous_bpm)

    sigma0 = _std_pop(bpm_deviation)
    weights = _softmax(instantaneous_bpm)
    sigma = sigma0 + sigma0 * _std_pop(weights)

    idx = [i for i, d in enumerate(bpm_deviation) if abs(d) > sigma]
    episodes_timestamps: List[List[str]] = []
    if idx:
        groups: List[List[int]] = [[idx[0]]]
        for j in idx[1:]:
            if j == groups[-1][-1] + 1:
                groups[-1].append(j)
            else:
                groups.append([j])

        for g in groups:
            start_i = g[0]
            end_i = g[-1]
            # episodes are indexed over RR intervals; map them to peak indices
            start_peak = peaks[start_i]["x"]
            end_peak = peaks[min(end_i + 1, len(peaks) - 1)]["x"]
            episodes_timestamps.append([sec2hms(float(start_peak) / fs), sec2hms(float(end_peak) / fs)])

    episodes_count = len(episodes_timestamps)
    duration_min = float(peaks[-1]["x"] - peaks[0]["x"]) / float(fs) / 60.0
    episodes_per_hour = (60.0 / duration_min) * episodes_count if duration_min > 0 else 0.0

    return mistake_holder(
        {
            "instantaneous_bpm": instantaneous_bpm,
            "bpm_deviation": bpm_deviation,
            "avg_bpm": float(mean_bpm),
            "min_bpm": float(min_bpm),
            "max_bpm": float(max_bpm),
            "episodes_count": int(episodes_count),
            "episodes_per_hour": float(episodes_per_hour),
            "episodes_timestamps": episodes_timestamps,
        },
        th=4,
    )


def normalize_observation(record: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
    """
    Normalize a record from `resp_example/heart_rate_first10_responses.json` into
    the shape expected by `preprocess_obs()` plus return sampling rate.

    Output observation includes:
      - peaks: [{'x': int, 'y': 1.0}, ...]
      - bpm / confidence (if present upstream)
    """
    if not isinstance(record, dict):
        return {"peaks": []}, 0.0

    fs_raw = record.get("sampling_rate", 0) or 0
    try:
        fs = float(fs_raw)
    except Exception:
        fs = 0.0

    resp = record.get("response", {}) if isinstance(record.get("response", {}), dict) else {}
    base_peaks = resp.get("base_peaks", []) if isinstance(resp.get("base_peaks", []), list) else []

    peaks: List[Dict[str, Any]] = []
    for v in base_peaks:
        try:
            peaks.append({"x": int(v), "y": 1.0})
        except Exception:
            continue

    obs_norm: Dict[str, Any] = {"peaks": peaks}
    if "bpm" in resp:
        obs_norm["bpm"] = resp.get("bpm")
    if "confidence" in resp:
        obs_norm["confidence"] = resp.get("confidence")

    return obs_norm, fs

