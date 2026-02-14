"""
Paper-mode intelligence overrides: boost capacity (max_positions, max_new_positions_per_cycle).
Mark: "We are on paper trading so if we need more positions then let's have more positions. No issues."
"""
from __future__ import annotations

import os


def is_paper_mode() -> bool:
    """True if Alpaca base URL indicates paper trading."""
    url = os.environ.get("ALPACA_BASE_URL") or os.environ.get("APCA_API_BASE_URL") or ""
    return "paper" in url.lower()


def apply_paper_overrides() -> None:
    """
    For PAPER mode: increase max_positions and max_new_positions_per_cycle by 2.0x.
    Recalibrated for intelligence overhaul; allows displacement override for high-UW candidates.
    Keeps risk discipline (MIN_NOTIONAL, correlation_concentration_risk_multiplier) unchanged.
    """
    if not is_paper_mode():
        return
    base_max = int(os.environ.get("MAX_CONCURRENT_POSITIONS", 16))
    new_max = int(base_max * 2.0)
    os.environ["MAX_CONCURRENT_POSITIONS"] = str(new_max)
    base_per_cycle = int(os.environ.get("MAX_NEW_POSITIONS_PER_CYCLE", 6))
    new_per_cycle = int(base_per_cycle * 2.0)
    os.environ["MAX_NEW_POSITIONS_PER_CYCLE"] = str(new_per_cycle)


def score_floor_breach_threshold_multiplier() -> float:
    """Paper mode: reduce score_floor_breach sensitivity by 10% (multiplier 0.9)."""
    return 0.9 if is_paper_mode() else 1.0


def write_paper_mode_intel_state() -> None:
    """Write paper-mode state to telemetry/paper_mode_intel_state.json for audit."""
    try:
        from pathlib import Path
        import json
        root = Path(__file__).resolve().parent.parent
        state_path = root / "telemetry" / "paper_mode_intel_state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "paper_mode": is_paper_mode(),
            "max_concurrent_positions": int(os.environ.get("MAX_CONCURRENT_POSITIONS", 16)),
            "max_new_positions_per_cycle": int(os.environ.get("MAX_NEW_POSITIONS_PER_CYCLE", 6)),
        }
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass
