"""
Signal health recording for scoring pipeline.
Appends one JSONL record per scored symbol so we can see which signals have real data.
Tied to trading pipeline: call from main.py where composite_meta is available (expectancy gate path).
See reports/SIGNAL_INTEGRITY_REAL_SCORES_PATH.md.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parent
SIGNAL_HEALTH_JSONL = _REPO_ROOT / "logs" / "signal_health.jsonl"

# Canonical component names used by uw_composite_v2 (must match component_sources keys)
COMPONENT_NAMES = (
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
    "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score",
    "freshness_factor",
)


def append_signal_health(
    symbol: str,
    component_sources: Optional[Dict[str, str]] = None,
    components: Optional[Dict[str, float]] = None,
) -> None:
    """
    Append one record to logs/signal_health.jsonl.
    For each component: has_data = (source != "missing"), contribution = value.
    Safe to call from live path; never raises.
    """
    component_sources = component_sources or {}
    components = components or {}
    try:
        SIGNAL_HEALTH_JSONL.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        health = {}
        for name in COMPONENT_NAMES:
            src = component_sources.get(name, "missing")
            raw = components.get(name)
            try:
                contrib = float(raw) if raw is not None else 0.0
            except (TypeError, ValueError):
                contrib = 0.0
            health[name] = {
                "has_data": src != "missing",
                "source": src,
                "contribution": round(contrib, 4),
            }
        rec = {
            "ts": int(now.timestamp()),
            "ts_iso": now.isoformat(),
            "symbol": symbol,
            "components": health,
        }
        line = json.dumps(rec, default=str) + "\n"
        with SIGNAL_HEALTH_JSONL.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
        # CTR mirror (Phase 1: when TRUTH_ROUTER_ENABLED=1)
        try:
            from src.infra.truth_router import append_jsonl as ctr_append
            ctr_append("health/signal_health.jsonl", rec, expected_max_age_sec=600)
        except Exception:
            pass
    except Exception:
        if os.environ.get("SIGNAL_HEALTH_DEBUG") == "1":
            raise
        pass
