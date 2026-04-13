"""
Telegram alerts for Live Whale shadow ML (engine failure) — governance helper, never raises.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[1]


def _truncate(s: str, max_len: int = 480) -> str:
    t = (s or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


def notify_ml_engine_critical_failure(error_detail: Optional[str]) -> bool:
    """
    Send operator alert when shadow ML inference enters CRITICAL_FAILURE.

    Uses ``send_governance_telegram`` (same transport / quiet hours as governance).
    """
    try:
        from scripts.alpaca_telegram import send_governance_telegram
    except Exception:
        return False

    body = _truncate(str(error_detail or "unknown"))
    text = (
        "🚨 ALPACA ML ENGINE FAILURE\n"
        "\n"
        f"Issue: {body}\n"
        "\n"
        "Status: Shadow Mode Suspended. Operator Action Required.\n"
        "\n"
        "(Live trading gates unchanged; ML shadow scores suppressed until model reloads.)"
    )
    return bool(send_governance_telegram(text, script_name="alpaca_ml_engine_failure"))
