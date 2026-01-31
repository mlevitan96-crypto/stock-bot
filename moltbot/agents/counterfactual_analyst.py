"""counterfactual_analyst — evaluates shadow profile deltas."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

REPO = Path(__file__).resolve().parents[2]


def run_counterfactual_analyst(date: str, base_dir: Path | None = None) -> Dict[str, Any]:
    """Read SNAPSHOT_OUTCOME_ATTRIBUTION (shadow comparisons), BLOCKED_TRADE_INTEL. Produce verdict."""
    base = base_dir or REPO
    path = base / "reports" / f"SNAPSHOT_OUTCOME_ATTRIBUTION_{date}.md"
    blocked_path = base / "reports" / f"BLOCKED_TRADE_INTEL_{date}.md"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    blocked_text = blocked_path.read_text(encoding="utf-8", errors="replace") if blocked_path.exists() else ""
    verdict = "ABSTAIN"
    reason = "No shadow comparison data"
    if "Shadow comparisons" in text or "Shadow Profile" in blocked_text:
        verdict = "SUPPORT"
        reason = "Shadow profiles present; NO-APPLY; ready for multi-day analysis"
    return {
        "agent": "counterfactual_analyst",
        "verdict": verdict,
        "reason": reason,
        "artifact_read": f"{path.name}, {blocked_path.name}",
    }
