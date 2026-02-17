import json
import math
import re
import unittest
from pathlib import Path
from typing import Any, Dict, List


class TestBackendResponsePreprocessing(unittest.TestCase):
    def test_preprocess_single_backend_record_before_llm(self) -> None:
        """
        Validates that a single backend measurement response (as stored in
        resp_example/heart_rate_first10_responses.json) is correctly normalized and
        preprocessed into SCG metrics BEFORE any LLM call.
        """
        repo_root = Path(__file__).resolve().parents[1]
        sample_path = repo_root / "resp_example" / "heart_rate_first10_responses.json"
        self.assertTrue(sample_path.exists(), f"Missing sample file: {sample_path}")

        records = json.loads(sample_path.read_text(encoding="utf-8"))
        self.assertIsInstance(records, list)
        self.assertGreater(len(records), 0)

        record0: Dict[str, Any] = records[0]
        self.assertIn("sampling_rate", record0)
        self.assertIn("response", record0)
        self.assertIn("base_peaks", record0["response"])

        # Import here so this test is independent from server/controller/LLM
        from cardioai_backend.scg.processing import normalize_observation, preprocess_obs  # type: ignore

        obs_norm, fs = normalize_observation(record0)
        self.assertAlmostEqual(fs, float(record0["sampling_rate"]), places=6)

        # Normalized structure for preprocess_obs()
        self.assertIn("peaks", obs_norm)
        peaks: List[Dict[str, Any]] = obs_norm["peaks"]
        self.assertIsInstance(peaks, list)
        self.assertGreater(len(peaks), 2)
        self.assertIsInstance(peaks[0], dict)
        self.assertIn("x", peaks[0])
        self.assertIsInstance(peaks[0]["x"], int)

        # Should preserve some useful upstream metadata if present
        self.assertEqual(obs_norm.get("bpm"), record0["response"].get("bpm"))
        self.assertEqual(obs_norm.get("confidence"), record0["response"].get("confidence"))

        metrics = preprocess_obs(obs_norm, fs=fs)
        self.assertIsInstance(metrics, dict)

        # Required keys produced by preprocess_obs()
        for k in (
            "instantaneous_bpm",
            "bpm_deviation",
            "avg_bpm",
            "min_bpm",
            "max_bpm",
            "episodes_count",
            "episodes_per_hour",
            "episodes_timestamps",
        ):
            self.assertIn(k, metrics)

        self.assertIsInstance(metrics["instantaneous_bpm"], list)
        self.assertIsInstance(metrics["bpm_deviation"], list)
        self.assertGreater(len(metrics["instantaneous_bpm"]), 0)
        self.assertEqual(len(metrics["instantaneous_bpm"]), len(metrics["bpm_deviation"]))

        # Numeric invariants
        inst = metrics["instantaneous_bpm"]
        avg = float(metrics["avg_bpm"])
        mn = float(metrics["min_bpm"])
        mx = float(metrics["max_bpm"])
        self.assertLessEqual(mn, avg)
        self.assertLessEqual(avg, mx)
        self.assertAlmostEqual(avg, sum(inst) / len(inst), places=6)
        self.assertAlmostEqual(mn, min(inst), places=6)
        self.assertAlmostEqual(mx, max(inst), places=6)

        # Confirm sampling_rate (fs) is actually used in the computation:
        # expected first bpm = 60 / ((dx)/fs) = 60 * fs / dx
        base_peaks = record0.get("response", {}).get("base_peaks", [])
        self.assertIsInstance(base_peaks, list)
        self.assertGreaterEqual(len(base_peaks), 2)
        dx = int(base_peaks[1]) - int(base_peaks[0])
        self.assertGreater(dx, 0)
        expected_first_bpm = 60.0 * float(fs) / float(dx)
        actual_first_bpm = float(inst[0])
        self.assertTrue(math.isfinite(actual_first_bpm))
        # allow small numerical differences and filtering effects
        self.assertLess(abs(actual_first_bpm - expected_first_bpm), 10.0)

        # Episodes structure invariants
        self.assertIsInstance(metrics["episodes_count"], int)
        self.assertGreaterEqual(metrics["episodes_count"], 0)
        self.assertIsInstance(metrics["episodes_per_hour"], (int, float))
        self.assertIsInstance(metrics["episodes_timestamps"], list)

        # Timestamp format check (HH:MM:SS) if any episodes are present
        ts_re = re.compile(r"^\d{2}:\d{2}:\d{2}$")
        for pair in metrics["episodes_timestamps"]:
            self.assertIsInstance(pair, list)
            self.assertEqual(len(pair), 2)
            self.assertRegex(pair[0], ts_re)
            self.assertRegex(pair[1], ts_re)


if __name__ == "__main__":
    unittest.main()
