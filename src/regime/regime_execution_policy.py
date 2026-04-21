"""
Regime → execution style matrix (shadow-first).

Live order routing is unchanged unless explicitly enabled elsewhere; ``REGIME_POLICY_SHADOW=1``
logs counterfactual intents for CPA / spread-capture analysis.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RegimeExecutionPolicy:
    entry_style: str
    sizing_mult: float


REGIME_EXECUTION_POLICIES: Dict[str, RegimeExecutionPolicy] = {
    "TREND": RegimeExecutionPolicy(entry_style="market_take", sizing_mult=1.0),
    "CHOP": RegimeExecutionPolicy(entry_style="passive_bid_vwap", sizing_mult=0.5),
    "MACRO_DOWNTREND": RegimeExecutionPolicy(entry_style="short_or_deep_discount", sizing_mult=0.5),
}


def resolve_regime_execution_policy(regime_state: Optional[str]) -> RegimeExecutionPolicy:
    key = str(regime_state or "TREND").strip().upper()
    return REGIME_EXECUTION_POLICIES.get(key, REGIME_EXECUTION_POLICIES["TREND"])


def _repo_logs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "logs"


def _shadow_flag_on() -> bool:
    return os.environ.get("REGIME_POLICY_SHADOW", "0").strip().lower() in ("1", "true", "yes", "on")


def log_shadow_regime_execution_intent(
    *,
    regime_state: str,
    symbol: str,
    side: str,
    qty: int,
    correlation_id: str = "",
    entry_score: float = 0.0,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Append one JSON line to ``logs/unified_events.jsonl`` (CPA shadow lane).

    **Guardrail:** only emits for ``CHOP`` + ``REGIME_POLICY_SHADOW=1`` (counterfactual passive).
    """
    if not _shadow_flag_on():
        return
    rs = str(regime_state or "").strip().upper()
    if rs != "CHOP":
        return
    pol = resolve_regime_execution_policy(rs)
    rec: Dict[str, Any] = {
        "event_type": "regime_shadow_execution_intent",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "regime_state": rs,
        "shadow_entry_style": pol.entry_style,
        "shadow_sizing_mult": pol.sizing_mult,
        "symbol": str(symbol).upper(),
        "side": str(side).lower(),
        "qty": int(qty),
        "entry_score": float(entry_score),
        "correlation_id": str(correlation_id or ""),
        "note": "shadow_only_no_live_routing_change",
    }
    if extra:
        rec["extra"] = extra
    path = _repo_logs_dir() / "unified_events.jsonl"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str, separators=(",", ":")) + "\n")
    except Exception:
        return
