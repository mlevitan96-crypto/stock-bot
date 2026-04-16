#!/usr/bin/env python3
"""
Append-only signal context for enter / exit / blocked decisions.
Writes logs/signal_context.jsonl. Never raises.

Env:
  ALPACA_SIGNAL_CONTEXT_EMIT — if 0/false/no, no-op (default: 1).
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_EMIT = os.getenv("ALPACA_SIGNAL_CONTEXT_EMIT", "1").strip().lower() not in ("0", "false", "no", "off")

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _log_path() -> Path:
    """CWD-independent: always under repo root (matches score_snapshot_writer)."""
    try:
        from config.registry import LogFiles

        p = LogFiles.SIGNAL_CONTEXT
        if p.is_absolute():
            return p
        return (_REPO_ROOT / p).resolve()
    except Exception:
        return (_REPO_ROOT / "logs" / "signal_context.jsonl").resolve()


def default_threshold() -> float:
    try:
        from config.registry import Thresholds

        return float(getattr(Thresholds, "MIN_EXEC_SCORE", 2.5))
    except Exception:
        return 2.5


def confidence_bucket_from_score(score: Any) -> str:
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "unknown"
    if s < 2.0:
        return "low"
    if s < 3.0:
        return "medium"
    return "high"


def size_bucket_from_position(position_size_usd: Any, base_usd: Any) -> str:
    try:
        p = float(position_size_usd)
        b = float(base_usd) if base_usd else 500.0
    except (TypeError, ValueError):
        return "unknown"
    if p <= 0:
        return "unknown"
    r = p / max(b, 1.0)
    if r < 0.5:
        return "small"
    if r < 1.5:
        return "base"
    if r < 3.0:
        return "large"
    return "xlarge"


def get_or_set_first_signal_ts_utc(symbol: str) -> str:
    """First-call timestamp for this symbol in the running process (caller caches via setdefault)."""
    return datetime.now(timezone.utc).isoformat()


def _infer_mid(signals: Dict[str, Any]) -> Optional[float]:
    if not isinstance(signals, dict):
        return None
    for k in ("mid", "last"):
        v = signals.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    q = signals.get("quote")
    if isinstance(q, dict):
        try:
            b, a = float(q.get("bid") or 0), float(q.get("ask") or 0)
            if b > 0 and a > 0:
                return (b + a) / 2.0
        except (TypeError, ValueError):
            pass
    return None


def log_signal_context(
    symbol: str,
    mode: str,
    decision: str,
    decision_reason: str = "",
    *,
    pnl_usd: Any = None,
    signals: Optional[Dict[str, Any]] = None,
    final_score: Any = None,
    threshold: Any = None,
    confidence_bucket: Optional[str] = None,
    counterfactual: Optional[Dict[str, Any]] = None,
    signal_contributions: Optional[Dict[str, Any]] = None,
    first_signal_ts_utc: Optional[str] = None,
    entry_delay_seconds: Any = None,
    position_size: Any = None,
    size_bucket: Optional[str] = None,
    **_: Any,
) -> None:
    if not _EMIT:
        return
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        sig = dict(signals or {})
        mid = _infer_mid(sig)
        rec: Dict[str, Any] = {
            "ts": int(time.time()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": str(symbol).upper(),
            "mode": str(mode),
            "decision": str(decision),
            "decision_reason": str(decision_reason or ""),
            "pnl_usd": pnl_usd,
            "signals": sig,
            "mid": mid,
            "last": sig.get("last"),
            "final_score": final_score,
            "threshold": threshold if threshold is not None else default_threshold(),
            "confidence_bucket": confidence_bucket,
            "counterfactual": counterfactual,
            "signal_contributions": signal_contributions,
            "first_signal_ts_utc": first_signal_ts_utc,
            "entry_delay_seconds": entry_delay_seconds,
            "position_size": position_size,
            "size_bucket": size_bucket,
        }
        try:
            from telemetry.attribution_emit_keys import get_symbol_attribution_keys

            _ak = get_symbol_attribution_keys(symbol)
            for _k in ("canonical_trade_id", "decision_event_id", "symbol_normalized", "time_bucket_id"):
                if _ak.get(_k) is not None:
                    rec[_k] = _ak[_k]
        except Exception:
            pass
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        pass
