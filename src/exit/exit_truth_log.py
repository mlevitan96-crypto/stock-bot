"""
Exit truth logging — exhaustive emission for every exit evaluation and every executed close.

File: logs/exit_truth.jsonl
Schema: ts, symbol, position_id, exit_pressure, thresholds, decision, components, close_reason,
        exit_reason_code, regime_snapshot, entry_snapshot, pnl_snapshot, mfe, mae, giveback, etc.

Contract: MUST NOT raise in execution path; append-only.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

OUT = Path(os.environ.get("EXIT_TRUTH_LOG_PATH", "logs/exit_truth.jsonl"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_exit_truth(
    *,
    symbol: str,
    position_id: Optional[str] = None,
    exit_pressure: float,
    threshold_normal: float,
    threshold_urgent: float,
    decision: str,
    components: List[Dict[str, Any]],
    close_reason: str,
    exit_reason_code: str,
    regime_snapshot: Optional[Dict[str, Any]] = None,
    entry_snapshot: Optional[Dict[str, Any]] = None,
    pnl_snapshot: Optional[Dict[str, Any]] = None,
    mfe: Optional[float] = None,
    mae: Optional[float] = None,
    giveback: Optional[float] = None,
    tick_type: str = "evaluation",
    **extra: Any,
) -> None:
    """Append one record to logs/exit_truth.jsonl. Never raises."""
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": _now_iso(),
            "symbol": symbol,
            "position_id": position_id,
            "exit_pressure": round(float(exit_pressure), 4),
            "thresholds": {"normal": threshold_normal, "urgent": threshold_urgent},
            "decision": decision,
            "components": components,
            "close_reason": close_reason,
            "exit_reason_code": exit_reason_code,
            "regime_snapshot": regime_snapshot or {},
            "entry_snapshot": entry_snapshot or {},
            "pnl_snapshot": pnl_snapshot or {},
            "mfe": mfe,
            "mae": mae,
            "giveback": giveback,
            "tick_type": tick_type,
            **{k: v for k, v in extra.items() if v is not None},
        }
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        # CTR mirror (Phase 1: when TRUTH_ROUTER_ENABLED=1)
        try:
            from src.infra.truth_router import append_jsonl as ctr_append
            ctr_append("exits/exit_truth.jsonl", rec, expected_max_age_sec=600)
        except Exception:
            pass
    except Exception:
        pass
