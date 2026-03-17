"""
Canonical Alpaca attribution schema — entry and exit.
Deterministic, versioned; used for lever-level edge discovery and promotion.
NO live behavior changes; additive telemetry only.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

SCHEMA_VERSION = "1.2.0"


# --- Entry attribution (per trade open) ---

def entry_attribution_shape() -> Dict[str, Any]:
    """Canonical shape for entry_attribution. Truth contributions; dominant lever; margin to threshold; trade_key for join."""
    return {
        "schema_version": SCHEMA_VERSION,
        "event_type": "alpaca_entry_attribution",
        "trade_id": "",
        "trade_key": "",  # canonical join: symbol|side|entry_time_iso (UTC, second)
        "symbol": "",
        "timestamp": "",
        "side": "",  # LONG | SHORT
        "raw_signals": {},  # {<signal_name>: value (float or str)}
        "weights": {},  # {<signal_name>: weight}
        "contributions": {},  # {<signal_name>: weight*value}
        "composite_score": None,
        "entry_dominant_component": None,  # name of component with max abs(contribution)
        "entry_dominant_component_value": None,  # that contribution value
        "entry_margin_to_threshold": None,  # composite_score - threshold if threshold exists
        "gates": {
            "lead_gate": {"pass": None, "reason": ""},
            "exhaustion_gate": {"pass": None, "reason": ""},
            "funding_veto": {"pass": None, "reason": ""},
            "whitelist": {"pass": None, "reason": ""},
            "regime_gate": {"pass": None, "reason": ""},
            "score_threshold": {"pass": None, "reason": ""},
            "cooldown": {"pass": None, "reason": ""},
            "position_exists": {"pass": None, "reason": ""},
        },
        "decision": "",  # OPEN_LONG | OPEN_SHORT | HOLD
        "decision_reason": "",
    }


def validate_entry_attribution(rec: Dict[str, Any]) -> list[str]:
    """Return list of validation issues (empty if valid)."""
    issues = []
    if rec.get("event_type") != "alpaca_entry_attribution":
        issues.append("event_type must be 'alpaca_entry_attribution'")
    if not rec.get("schema_version"):
        issues.append("schema_version required")
    return issues


# --- Exit attribution (per evaluation tick + final exit) ---

def exit_attribution_shape() -> Dict[str, Any]:
    """Canonical shape for exit_attribution. Dominant component; pressure margins; explicit snapshot; trade_key for join."""
    return {
        "schema_version": SCHEMA_VERSION,
        "event_type": "alpaca_exit_attribution",
        "trade_id": "",
        "trade_key": "",  # canonical join: symbol|side|entry_time_iso (UTC, second)
        "symbol": "",
        "timestamp": "",
        "exit_components_raw": {
            "timing_pressure": None,
            "mfe_giveback_pressure": None,
            "time_decay_pressure": None,
            "signal_deterioration": None,
            "flow_reversal": None,
            "regime_risk": None,
            "position_risk": None,
            "profit_protection": None,
        },
        "exit_weights": {},
        "exit_contributions": {},
        "exit_pressure_total": None,
        "exit_dominant_component": None,
        "exit_dominant_component_value": None,
        "exit_pressure_margin_exit_now": None,  # pressure - threshold_normal
        "exit_pressure_margin_exit_soon": None,  # pressure - threshold_urgent (e.g. exit_soon)
        "thresholds_used": {"normal": None, "urgent": None},
        "eligible_mechanisms": {
            "tp": False,
            "sl": False,
            "trailing": False,
            "time_exit": False,
            "score_exit": False,
            "signal_decay": False,
            "stale_alpha_cutoff": False,
            "flow_reversal": False,
        },
        "winner": "",  # exit_reason
        "winner_explanation": "",
        "snapshot": {
            "pnl": None,
            "pnl_pct": None,
            "pnl_unrealized": None,  # pct or usd when applicable
            "mfe": None,
            "mae": None,
            "mfe_pct_so_far": None,
            "mae_pct_so_far": None,
            "hold_minutes": None,
        },
    }


def validate_exit_attribution(rec: Dict[str, Any]) -> list[str]:
    """Return list of validation issues (empty if valid)."""
    issues = []
    if rec.get("event_type") != "alpaca_exit_attribution":
        issues.append("event_type must be 'alpaca_exit_attribution'")
    if not rec.get("schema_version"):
        issues.append("schema_version required")
    return issues
