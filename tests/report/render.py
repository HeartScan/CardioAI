import json
from pathlib import Path
from typing import Dict, Any


def _score_line(name: str, val: Any) -> str:
    try:
        ival = int(val)
    except Exception:
        ival = val
    return f"- **{name}**: {ival}"


def render_to_markdown(run_dir: Path) -> str:
    conv_path = run_dir / "conversation.json"
    eval_path = run_dir / "evaluation.json"
    meta_path = run_dir / "metadata.json"

    conv = json.loads(conv_path.read_text(encoding="utf-8")) if conv_path.exists() else []
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    eva = json.loads(eval_path.read_text(encoding="utf-8")) if eval_path.exists() else {}

    lines = []
    lines.append("# CardioAI Product Test Report")
    lines.append("")
    if "scenario" in meta:
        scen = meta["scenario"]
        lines.append(f"**Scenario**: {scen.get('id','')} — {scen.get('title','')}")
    lines.append("")
    lines.append("## Models")
    mm = meta.get("models", {})
    lines.append(f"- **Writer (cardio)**: {mm.get('writer_model','unknown')}")
    lines.append(f"- **OpenAI (patient)**: {mm.get("openai_patient_model","unknown")}")
    lines.append("")

    lines.append("## Scores")
    scores = eva.get("scores", {})
    if isinstance(scores, dict) and scores:
        for k, v in scores.items():
            lines.append(_score_line(k, v))
    else:
        lines.append("_No structured scores found._")
    lines.append("")

    if eva.get("verdict"):
        lines.append(f"**Verdict**: {eva['verdict']}")
        lines.append("")

    lines.append("## Findings")
    findings = eva.get("findings", [])
    if isinstance(findings, list) and findings:
        for f in findings[:10]:
            lines.append(f"- {f}")
    else:
        lines.append("_No findings provided._")
    lines.append("")

    lines.append("## Conversation (first 12 messages)")
    for i, m in enumerate(conv[:12], start=1):
        role = m.get("role","")
        content = (m.get("content","") or "").replace("\n", " ")
        content = content[:600]
        lines.append(f"- **{role} {i}**: {content}")
    lines.append("")

    return "\n".join(lines)


