"""signal_advocate — evaluates signal contribution and marginal value."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

REPO = Path(__file__).resolve().parents[2]


def run_signal_advocate(date: str, base_dir: Path | None = None) -> Dict[str, Any]:
    """Read SNAPSHOT_OUTCOME_ATTRIBUTION, produce verdict."""
    base = base_dir or REPO
    path = base / "reports" / f"SNAPSHOT_OUTCOME_ATTRIBUTION_{date}.md"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    verdict = "ABSTAIN"
    reason = "No attribution data"
    if text:
        if "informative" in text.lower():
            verdict = "SUPPORT"
            reason = "Some signals show informative marginal value"
        elif "insufficient_data" in text:
            verdict = "ABSTAIN"
            reason = "Insufficient data for marginal value; more days needed"
        else:
            verdict = "ABSTAIN"
            reason = "Attribution present; no clear signal recommendation"
    return {"agent": "signal_advocate", "verdict": verdict, "reason": reason, "artifact_read": path.name}
