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
    For PAPER mode: increase max_positions and max_new_positions_per_cycle by 1.5x.
    Keeps risk discipline (MIN_NOTIONAL, correlation_concentration_risk_multiplier) unchanged.
    """
    if not is_paper_mode():
        return
    base_max = int(os.environ.get("MAX_CONCURRENT_POSITIONS", 16))
    new_max = int(base_max * 1.5)
    os.environ["MAX_CONCURRENT_POSITIONS"] = str(new_max)
    # policy_variants.get_live_safety_caps uses max_new_positions_per_cycle; paper uses caps only when is_live()
    # For paper, main.py uses MAX_NEW_POSITIONS_PER_CYCLE from get_live_safety_caps when is_live() else default 6.
    # Since paper => is_live() is False, we need to set an env that main.py or policy_variants reads for paper.
    base_per_cycle = int(os.environ.get("MAX_NEW_POSITIONS_PER_CYCLE", 6))
    new_per_cycle = int(base_per_cycle * 1.5)
    os.environ["MAX_NEW_POSITIONS_PER_CYCLE"] = str(new_per_cycle)


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
