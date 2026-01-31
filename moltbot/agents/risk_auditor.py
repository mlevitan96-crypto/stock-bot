"""risk_auditor — evaluates blocked-trade impact and exit health."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

REPO = Path(__file__).resolve().parents[2]


def run_risk_auditor(date: str, base_dir: Path | None = None) -> Dict[str, Any]:
    """Read EXIT_JOIN_HEALTH, BLOCKED_TRADE_INTEL. Produce verdict."""
    base = base_dir or REPO
    exit_path = base / "reports" / f"EXIT_JOIN_HEALTH_{date}.md"
    blocked_path = base / "reports" / f"BLOCKED_TRADE_INTEL_{date}.md"
    exit_text = exit_path.read_text(encoding="utf-8", errors="replace") if exit_path.exists() else ""
    blocked_text = blocked_path.read_text(encoding="utf-8", errors="replace") if blocked_path.exists() else ""
    verdict = "ABSTAIN"
    reason = "No exit/blocked data"
    if exit_text or blocked_text:
        if "DEGRADED" in exit_text or "FAIL" in exit_text:
            verdict = "OPPOSE"
            reason = "Exit join health degraded"
        elif "Match rate" in exit_text and "0.0%" in exit_text and "Exit snapshots" in exit_text:
            verdict = "ABSTAIN"
            reason = "Zero exit snapshots; cannot assess risk"
        else:
            verdict = "SUPPORT"
            reason = "Exit join and blocked-trade attribution operational"
    return {
        "agent": "risk_auditor",
        "verdict": verdict,
        "reason": reason,
        "artifact_read": f"{exit_path.name}, {blocked_path.name}",
    }
