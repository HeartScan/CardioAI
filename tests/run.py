import argparse
import datetime
import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allow running from repo root or tests/
REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = Path(__file__).resolve().parent
sys.path.append(str(REPO_ROOT))

# Reuse existing pipeline parts
from utils import preprocess_obs  # type: ignore

# Local adapters
from tests.providers.writer_adapter import WriterCardioAdapter  # type: ignore
from tests.providers.openai_adapter import OpenAIChatSession  # type: ignore


DEBUG_LOG_PATH = REPO_ROOT / ".cursor" / "debug.log"
DEBUG_RUN_ID = f"post-fix-{int(time.time())}"
os.environ["CARDIOAI_DEBUG_RUN_ID"] = DEBUG_RUN_ID


def _dbg(hypothesis_id: str, location: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    # #region agent log
    try:
        payload = {
            "id": f"log_{int(time.time() * 1000)}_{hypothesis_id}",
            "timestamp": int(time.time() * 1000),
            "location": location,
            "message": message,
            "data": data or {},
            "sessionId": "debug-session",
            "runId": DEBUG_RUN_ID,
            "hypothesisId": hypothesis_id,
        }
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    cfg_path = TESTS_ROOT / "config.json"
    if cfg_path.exists():
        return read_json(cfg_path)
    # Defaults if config.json missing
    return {
        "openai": {
            "patient_model": "gpt-4o-mini",
            "critic_model": "gpt-4o-mini",
            "patient_temperature": 0.8,
            "critic_temperature": 0.3
        },
        "dialog": {
            "max_turns": 8
        },
        "io": {
            "runs_dir": str(TESTS_ROOT / "runs")
        }
    }


def list_scenarios() -> List[Path]:
    scenarios_dir = TESTS_ROOT / "scenarios"
    if not scenarios_dir.exists():
        return []
    return sorted(scenarios_dir.glob("*.json"))


def load_scenario(path: Path) -> Dict[str, Any]:
    data = read_json(path)
    data["_scenario_path"] = str(path)
    return data


def safe_load_peaks(pkl_path: Path) -> List[Dict[str, float]]:
    """
    Loads peaks from pickle and normalizes to [{'x': int|float, 'y': float}, ...]
    The test harness tolerates several common shapes:
      - list[dict{'x','y'}]
      - list[int|float] -> becomes [{'x': v, 'y': 1.0}]
      - numpy array of numbers or dicts
    """
    with pkl_path.open("rb") as f:
        obj = pickle.load(f)
    # Defer numpy import until needed to avoid dependency issues
    try:
        import numpy as np  # type: ignore
        is_np_array = isinstance(obj, np.ndarray)
    except Exception:
        is_np_array = False

    if is_np_array:
        try:
            obj = obj.tolist()
        except Exception:
            pass

    # Already correct shape
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "x" in obj[0]:
        return [{"x": float(d["x"]), "y": float(d.get("y", 1.0))} for d in obj]  # type: ignore

    # List of numbers
    if isinstance(obj, list) and (len(obj) == 0 or isinstance(obj[0], (int, float))):
        return [{"x": float(v), "y": 1.0} for v in obj]  # type: ignore

    # Unknown shape → try to adapt best-effort
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        # Try common alternative keys
        adapted = []
        for d in obj:
            if "index" in d:
                adapted.append({"x": float(d["index"]), "y": float(d.get("value", 1.0))})
            elif "t" in d:
                adapted.append({"x": float(d["t"]), "y": float(d.get("amp", 1.0))})
        if adapted:
            return adapted

    raise ValueError(f"Unsupported peaks format in {pkl_path}")


def load_observation_from_pickle(pkl_path: Path, obs_index: int = 0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Loads a single observation dict compatible with utils.preprocess_obs().

    Supported pickle shapes:
      - list[{"peaks": [...]}]  -> dataset of observations; choose obs_index
      - {"peaks": [...]}        -> single observation
      - list[{"x":..,"y":..}]   -> peaks list directly -> wrap into {"peaks": ...}
      - list[int|float]         -> x indices -> wrap into {"peaks":[{"x":..,"y":1.0}]}

    Returns: (observation_dict, info_dict)
    """
    with pkl_path.open("rb") as f:
        obj = pickle.load(f)
    _dbg("A", "tests/run.py:load_observation_from_pickle", "pickle_loaded", {"type": str(type(obj)), "obs_index": obs_index})

    # Defer numpy import until needed
    try:
        import numpy as np  # type: ignore
        if isinstance(obj, np.ndarray):
            obj = obj.tolist()
    except Exception:
        pass

    info: Dict[str, Any] = {"source": str(pkl_path), "obs_index": obs_index}

    # Dataset: list of observations
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "peaks" in obj[0]:
        info["obs_count_total"] = len(obj)
        _dbg("A", "tests/run.py:load_observation_from_pickle", "dataset_detected", {"obs_count_total": len(obj)})
        if obs_index < 0 or obs_index >= len(obj):
            raise IndexError(f"obs_index out of range: {obs_index} (total {len(obj)})")
        obs = obj[obs_index]
        # Normalize peaks to include y if missing
        peaks = obs.get("peaks", [])
        norm_peaks = [{"x": float(p["x"]), "y": float(p.get("y", 1.0))} for p in peaks] if peaks else []
        _dbg("A", "tests/run.py:load_observation_from_pickle", "observation_selected", {"obs_index": obs_index, "peaks_count": len(norm_peaks)})
        return {"peaks": norm_peaks}, info

    # Single observation dict
    if isinstance(obj, dict) and "peaks" in obj:
        peaks = obj.get("peaks", [])
        norm_peaks = [{"x": float(p["x"]), "y": float(p.get("y", 1.0))} for p in peaks] if peaks else []
        info["obs_count_total"] = 1
        _dbg("A", "tests/run.py:load_observation_from_pickle", "single_observation_detected", {"peaks_count": len(norm_peaks)})
        return {"peaks": norm_peaks}, info

    # Peaks list directly (reuse existing normalizer)
    peaks = safe_load_peaks(pkl_path)
    info["obs_count_total"] = 1
    return {"peaks": peaks}, info


def build_patient_system_prompt(profile: Dict[str, Any]) -> str:
    system_tpl_path = TESTS_ROOT / "prompts" / "patient_system.txt"
    with system_tpl_path.open("r", encoding="utf-8") as f:
        base = f.read().strip()
    profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
    return f"{base}\n\nPATIENT_PROFILE_JSON:\n{profile_json}"


def build_critic_system_prompt() -> str:
    critic_tpl_path = TESTS_ROOT / "prompts" / "critic_system.txt"
    with critic_tpl_path.open("r", encoding="utf-8") as f:
        return f.read().strip()


def stops_on_completion(cardio_reply: str) -> bool:
    """
    Heuristic stop: look for disclaimer presence, short closing, or explicit goodbye.
    We still bound by max_turns regardless.
    """
    if not cardio_reply:
        return True
    text = cardio_reply.lower()
    if "not replace a visit" in text or "not a substitute for a doctor" in text:
        return True
    if "take care" in text and "any other questions" not in text:
        return True
    return False


def run_single_scenario(
    scenario: Dict[str, Any],
    config: Dict[str, Any],
    obs_index: int = 0,
    peaks_limit: Optional[int] = None,
) -> Tuple[Path, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Returns: (run_dir, metadata, conversation)
    """
    runs_dir = Path(config.get("io", {}).get("runs_dir", str(TESTS_ROOT / "runs")))
    ensure_dir(runs_dir)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = runs_dir / f"{scenario.get('id','scenario')}_obs{obs_index}_{ts}"
    ensure_dir(run_dir)

    # Prepare observation (SCG metrics) via existing pipeline
    peaks_rel = scenario.get("peaks_pickle", "tests/peaks.pkl")
    peaks_path = Path(peaks_rel)
    if not peaks_path.is_absolute():
        peaks_path = REPO_ROOT / peaks_rel
    obs_raw, obs_info = load_observation_from_pickle(peaks_path, obs_index=obs_index)
    if peaks_limit is not None and peaks_limit > 0:
        obs_raw = {"peaks": obs_raw.get("peaks", [])[: int(peaks_limit)]}
    _dbg("A", "tests/run.py:run_single_scenario", "observation_ready", {"obs_index": obs_index, "peaks_count_used": len(obs_raw.get("peaks", [])), "peaks_limit": peaks_limit})
    fs = scenario.get("fs", 100.0)
    # preprocess_obs signature defaults fs=100.0; wrap if FS provided
    metrics = preprocess_obs(obs_raw, fs=fs) if fs else preprocess_obs(obs_raw)
    _dbg("A", "tests/run.py:run_single_scenario", "metrics_computed", {"keys": list(metrics.keys()), "episodes_count": metrics.get("episodes_count")})

    # Initialize CardioAI (HF OpenAI-compatible endpoint)
    writer_timeout_s = float(config.get("writer", {}).get("timeout_s", 60.0))
    _dbg("B", "tests/run.py:run_single_scenario", "cardio_init_start", {"provider": "hf_openai_compat", "timeout_s": writer_timeout_s})
    writer = WriterCardioAdapter(timeout_s=writer_timeout_s)
    cardio_first = writer.init_with_metrics(metrics)
    cardio_err = writer.get_last_error()
    _dbg("B", "tests/run.py:run_single_scenario", "cardio_init_done", {"cardio_first_len": len(cardio_first or ""), "err": cardio_err})
    if cardio_first is None:
        # Persist a minimal run and stop early (can't continue dialog)
        conversation: List[Dict[str, Any]] = []
        conversation.append({
            "role": "cardio",
            "content": f"[ERROR] CardioAI initialization failed ({cardio_err}). Check HF_TOKEN / [HF] BASE_URL / network / timeout.",
            "ts": datetime.datetime.utcnow().isoformat() + "Z"
        })
        metadata = {
            "scenario": scenario,
            "models": {"writer_model": writer.model_name},
            "parameters": {"writer_timeout_s": writer_timeout_s},
            "metrics": metrics,
            "observation_info": {**obs_info, "fs": fs, "peaks_limit": peaks_limit, "peaks_count_used": len(obs_raw.get("peaks", []))},
            "error": {"stage": "cardio_init", "kind": cardio_err},
        }
        (run_dir / "conversation.json").write_text(json.dumps(conversation, ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return run_dir, metadata, conversation

    # Initialize Patient (OpenAI)
    patient_profile = scenario.get("profile", {})
    patient_system = build_patient_system_prompt(patient_profile)
    patient_model = config.get("openai", {}).get("patient_model", "gpt-4o-mini")
    patient_temperature = float(config.get("openai", {}).get("patient_temperature", 0.8))
    patient = OpenAIChatSession(
        model=patient_model,
        system_prompt=patient_system,
        temperature=patient_temperature,
    )
    _dbg("C", "tests/run.py:run_single_scenario", "patient_session_ready", {"model": patient_model})

    # Conversation loop
    max_turns = int(config.get("dialog", {}).get("max_turns", 8))
    conversation: List[Dict[str, Any]] = []

    # Log helper
    def log(role: str, content: str) -> None:
        conversation.append({
            "role": role,
            "content": content,
            "ts": datetime.datetime.utcnow().isoformat() + "Z"
        })

    # First cardio response already produced during cardio init (CardioAI / HF)
    log("cardio", cardio_first or "")

    # Alternate turns: cardio -> patient -> cardio -> ...
    last_from_cardio = True
    for _ in range(max_turns):
        if last_from_cardio:
            # Patient replies to cardio
            _dbg("C", "tests/run.py:run_single_scenario", "patient_turn_start", {"turn_role": "patient"})
            patient_reply = patient.complete_with_user_input(conversation[-1]["content"])
            if not patient_reply:
                err = getattr(patient, "get_last_error", lambda: {"type": None, "message": None})()
                log("patient", f"[ERROR] Patient model failed: {err}")
                _dbg("C", "tests/run.py:run_single_scenario", "patient_turn_failed", {"err": err})
                break
            log("patient", patient_reply)
            _dbg("C", "tests/run.py:run_single_scenario", "patient_turn_done", {"reply_len": len(patient_reply)})
            last_from_cardio = False
        else:
            # Cardio replies to patient
            _dbg("B", "tests/run.py:run_single_scenario", "cardio_turn_start", {"turn_role": "cardio"})
            cardio_reply = writer.send_user_message(conversation[-1]["content"])
            if not cardio_reply:
                err = writer.get_last_error()
                log("cardio", f"[ERROR] CardioAI reply failed: {err}")
                _dbg("B", "tests/run.py:run_single_scenario", "cardio_turn_failed", {"err": err})
                break
            log("cardio", cardio_reply)
            _dbg("B", "tests/run.py:run_single_scenario", "cardio_turn_done", {"reply_len": len(cardio_reply), "err": writer.get_last_error()})
            last_from_cardio = True
            if stops_on_completion(cardio_reply or ""):
                break

    # Persist conversation and metadata
    metadata = {
        "scenario": scenario,
        "models": {
            "writer_model": writer.model_name,
            "openai_patient_model": patient_model
        },
        "parameters": {
            "max_turns": max_turns,
            "patient_temperature": patient_temperature
        },
        "metrics": metrics,
        "observation_info": {
            **obs_info,
            "fs": fs,
            "peaks_limit": peaks_limit,
            "peaks_count_used": len(obs_raw.get("peaks", [])),
        },
    }
    (run_dir / "conversation.json").write_text(json.dumps(conversation, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    return run_dir, metadata, conversation


def evaluate_run(run_dir: Path, metadata: Dict[str, Any], conversation: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    # If Writer failed, evaluation is meaningless; persist a structured skip
    if isinstance(metadata, dict) and metadata.get("error", {}).get("stage") in ("writer_init", "cardio_init"):
        evaluation_json = {
            "error": "skipped",
            "reason": "cardio_init_failed",
            "cardio_error": metadata.get("error", {}),
        }
        (run_dir / "evaluation.json").write_text(json.dumps(evaluation_json, ensure_ascii=False, indent=2), encoding="utf-8")
        return evaluation_json

    critic_model = config.get("openai", {}).get("critic_model", "gpt-4o-mini")
    critic_temperature = float(config.get("openai", {}).get("critic_temperature", 0.3))
    critic_system = build_critic_system_prompt()

    critic = OpenAIChatSession(
        model=critic_model,
        system_prompt=critic_system,
        temperature=critic_temperature,
    )
    _dbg("C", "tests/run.py:evaluate_run", "critic_session_ready", {"model": critic_model})

    # Build a single user message with all context to limit tokens
    convo_lines = []
    for i, msg in enumerate(conversation, start=1):
        role = msg["role"]
        content = msg["content"]
        convo_lines.append(f"[{i}] {role.upper()}: {content}")
    convo_text = "\n".join(convo_lines)

    eval_user_prompt = (
        "You are the CRITIC. Evaluate the CARIOLOGIST assistant's behavior using the rubric.\n\n"
        "INPUTS:\n"
        f"- SYSTEM_PROMPT (cardiologist): Loaded from repo config.ini (assume as provided to the model).\n"
        f"- PATIENT_PROFILE: {json.dumps(metadata.get('scenario', {}).get('profile', {}), ensure_ascii=False)}\n"
        f"- SCG_METRICS: {json.dumps(metadata.get('metrics', {}), ensure_ascii=False)}\n"
        "- FULL_DIALOG:\n"
        f"{convo_text}\n\n"
        "Respond STRICTLY with a valid JSON according to the schema described in your system prompt. Do not add any extra text."
    )

    evaluation_str = critic.complete_with_user_input(eval_user_prompt)
    _dbg("C", "tests/run.py:evaluate_run", "critic_response_received", {"len": len(evaluation_str or "")})
    if not evaluation_str:
        err = getattr(critic, "get_last_error", lambda: {"type": None, "message": None})()
        evaluation_json = {
            "error": "openai_failed",
            "openai_error": err,
            "hint": "If error is RateLimitError/insufficient_quota, check OpenAI billing/quota.",
        }
        (run_dir / "evaluation.json").write_text(json.dumps(evaluation_json, ensure_ascii=False, indent=2), encoding="utf-8")
        return evaluation_json
    try:
        evaluation_json = json.loads(evaluation_str or "{}")
    except Exception:
        # Fallback: wrap as text if JSON parsing failed
        evaluation_json = {"raw": evaluation_str, "error": "non_json_response"}

    (run_dir / "evaluation.json").write_text(json.dumps(evaluation_json, ensure_ascii=False, indent=2), encoding="utf-8")
    return evaluation_json


def render_report(run_dir: Path) -> None:
    # Lazy import to keep file localized
    try:
        from tests.report.render import render_to_markdown  # type: ignore
    except Exception:
        # Minimal inline renderer
        def render_to_markdown(run_path: Path) -> str:
            conv = json.loads((run_path / "conversation.json").read_text(encoding="utf-8"))
            evalj_path = run_path / "evaluation.json"
            evalj = json.loads(evalj_path.read_text(encoding="utf-8")) if evalj_path.exists() else {}
            lines = ["# CardioAI Test Report", ""]
            lines.append("## Conversation (truncated)")
            for i, m in enumerate(conv[:12], start=1):
                lines.append(f"- **{m['role']} {i}**: {m['content'][:400].replace(chr(10),' ')}")
            lines.append("")
            lines.append("## Evaluation (summary)")
            if isinstance(evalj, dict) and "scores" in evalj:
                for k, v in evalj.get("scores", {}).items():
                    lines.append(f"- **{k}**: {v}")
            else:
                lines.append("Evaluation JSON not structured or missing.")
            return "\n".join(lines)

    md = render_to_markdown(run_dir)
    (run_dir / "report.md").write_text(md, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Product test harness for CardioAI (tests)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--scenario", type=str, help="Path to a scenario JSON file under tests/scenarios/")
    g.add_argument("--all", action="store_true", help="Run all scenarios in tests/scenarios/")
    p.add_argument("--report", type=str, help="Generate report for a given run dir (no execution)")
    p.add_argument("--N", type=int, help="Run first N observations from peaks.pkl (dataset mode)")
    p.add_argument("--peaksN", type=int, help="Optional: cap number of peaks within each observation")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config()

    if args.report:
        run_dir = Path(args.report)
        if not run_dir.exists():
            print(f"Run dir not found: {run_dir}")
            sys.exit(1)
        render_report(run_dir)
        print(f"Report written to: {run_dir / 'report.md'}")
        return

    scenarios: List[Path] = []
    if args.all:
        scenarios = list_scenarios()
        if not scenarios:
            print("No scenarios found under tests/scenarios/")
            sys.exit(1)
    elif args.scenario:
        scenarios = [Path(args.scenario)]
    else:
        # Default to all if nothing provided
        scenarios = list_scenarios()
        if not scenarios:
            print("No scenarios found under tests/scenarios/")
            sys.exit(1)

    for sc_path in scenarios:
        scenario = load_scenario(sc_path)
        print(f"Running scenario: {sc_path.name}")
        # If peaks.pkl is a dataset (list of observations), --N controls how many to run
        n_obs = int(args.N) if (args.N is not None and args.N > 0) else 1
        peaks_limit = int(args.peaksN) if (args.peaksN is not None and args.peaksN > 0) else None
        for obs_index in range(n_obs):
            run_dir, metadata, conversation = run_single_scenario(
                scenario,
                cfg,
                obs_index=obs_index,
                peaks_limit=peaks_limit,
            )
            evaluate_run(run_dir, metadata, conversation, cfg)
            render_report(run_dir)
            print(f"Completed obs #{obs_index}. Outputs: {run_dir}")


if __name__ == "__main__":
    main()


