import numpy as np
from scipy.special import softmax
from typing import Any, Dict, List, Tuple

def sec2hms(sec: float) -> str:
    """Converts seconds to HH:MM:SS format."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def mistake_holder(obs, th=5):
    """Filters out low-count episodes as potential noise."""
    if obs['episodes_count'] < th:
        obs['episodes_count'] = 0
        obs['episodes_per_hour'] = 0
        obs['episodes_timestamps'] = []
    return obs

def filter_peaks(peaks_x: list, N: int=0) -> list:
    """Filters out peaks that are too close to each other (relaxation zone)."""
    peaks = [i['x'] for i in peaks_x]
    if not peaks:
        return []
        
    if N == 0:
        N = np.diff(peaks).mean() / 2

    filtered = [peaks[0]]
    for i in range(1, len(peaks)):
        if peaks[i] - filtered[-1] > N:
            filtered.append(peaks[i])
    return [{'x': i} for i in filtered]

def preprocess_obs(observation: Dict[str, Any], fs: float = 100.0) -> Dict[str, Any]:
    """
    Calculates detailed heart rate variability statistics from peak data.
    
    Parameters
    ----------
    observation : dict
        Expected format: {'peaks': [{'x': int}, ...]}
        Where 'x' is the index/sample number.
    fs : float
        Sampling frequency in Hz.
    """
    peaks = observation.get("peaks", [])
    if not peaks:
        return {
            "avg_bpm": 0, "min_bpm": 0, "max_bpm": 0, 
            "episodes_count": 0, "episodes_per_hour": 0, "episodes_timestamps": []
        }

    # 1. Filter peaks falling into the relaxation zone
    peaks = filter_peaks(peaks)

    if len(peaks) < 2:
        return {
            "avg_bpm": 0, "min_bpm": 0, "max_bpm": 0, 
            "episodes_count": 0, "episodes_per_hour": 0, "episodes_timestamps": []
        }

    # 2. Calculate RR-intervals in seconds
    rr_intervals = [
        (peaks[i + 1]["x"] - peaks[i]["x"]) / fs
        for i in range(len(peaks) - 1)
    ]
    instantaneous_bpm = 60.0 / np.array(rr_intervals)

    # 3. Calculate basic statistics
    mean_bpm = np.mean(instantaneous_bpm)
    bpm_deviation = np.array(instantaneous_bpm) - mean_bpm 
       
    min_bpm = np.min(instantaneous_bpm)
    max_bpm = np.max(instantaneous_bpm)

    # 4. Detect anomalous episodes
    # Complexity threshold using standard deviation and softmax for weighting
    sigma = np.std(bpm_deviation) + np.std(bpm_deviation) * softmax(instantaneous_bpm).std()

    # Indices where absolute deviation exceeds the threshold
    idx = np.where(np.abs(np.array(bpm_deviation)) > sigma)[0]

    if idx.size:        
        # Group contiguous indices into episodes
        breaks = np.where(np.diff(idx) > 1)[0] + 1
        groups = np.split(idx, breaks)

        episodes_timestamps = [
            [
                sec2hms(peaks[g[0]]["x"] / fs),        # Start
                sec2hms(peaks[g[-1] + 1]["x"] / fs)    # End
            ]
            for g in groups
        ]
    else:
        episodes_timestamps = []

    episodes_count = len(episodes_timestamps)
    
    # Calculate episode frequency per hour
    duration_min = (peaks[-1]["x"] - peaks[0]["x"]) / fs / 60.0
    episodes_per_hour = (60.0 / duration_min) * episodes_count if duration_min > 0 else 0.0

    # 5. Final assembly and noise filtering
    return mistake_holder({
        "instantaneous_bpm": instantaneous_bpm.tolist(),
        "bpm_deviation": bpm_deviation.tolist(),
        "avg_bpm": mean_bpm.item(),
        "min_bpm": min_bpm.item(),
        "max_bpm": max_bpm.item(),
        "episodes_count": episodes_count,
        "episodes_per_hour": episodes_per_hour,
        "episodes_timestamps": episodes_timestamps,
    }, th=4)
