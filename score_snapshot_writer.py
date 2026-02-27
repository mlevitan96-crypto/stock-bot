"""
Append-only score snapshot for truth audit and diagnostics.
Emit one JSONL record per candidate at the expectancy gate (canonical score truth).
"""
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional  # noqa: F401 Any used for signal_group_scores

# CWD-independent: always write under repo root so tail/wc from repo root see the file.
_REPO_ROOT = Path(__file__).resolve().parent
SCORE_SNAPSHOT_FILE = _REPO_ROOT / "logs" / "score_snapshot.jsonl"


def _sanitize(obj: Any) -> Any:
    """Replace NaN/Inf so JSON is valid."""
    if isinstance(obj, float):
        if math.isfinite(obj):
            return round(obj, 6)
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    return obj


def append_score_snapshot(
    *,
    symbol: str,
    composite_score: float,
    expectancy_floor: float,
    composite_gate_pass: bool,
    expectancy_gate_pass: bool,
    block_reason: Optional[str] = None,
    decision_id: Optional[str] = None,
    trade_id: Optional[str] = None,
    signal_group_scores: Optional[Dict[str, Any]] = None,
    per_signal: Optional[Dict[str, float]] = None,
    weighted_contributions: Optional[Dict[str, float]] = None,
    group_sums: Optional[Dict[str, float]] = None,
    composite_pre_norm: Optional[float] = None,
    composite_post_norm: Optional[float] = None,
    uw_deferred: bool = False,
    defer_reason: Optional[str] = None,
    next_retry_ts: Optional[int] = None,
    candidate_status: Optional[str] = None,
) -> None:
    """Append one JSONL record to logs/score_snapshot.jsonl. Safe to call from live path.
    Multi-model attribution: weighted_contributions, group_sums, composite_pre_norm, composite_post_norm.
    """
    _snap_debug = os.environ.get("SCORE_SNAPSHOT_DEBUG") == "1"
    try:
        SCORE_SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
        path_abs = SCORE_SNAPSHOT_FILE.resolve()
        if _snap_debug:
            print(f"SCORE_SNAPSHOT_DEBUG: append_score_snapshot path={path_abs!s}", flush=True)
        now = datetime.now(timezone.utc)
        rec = {
            "ts": int(now.timestamp()),
            "ts_iso": now.isoformat(),
            "symbol": symbol,
            "decision_id": decision_id,
            "trade_id": trade_id,
            "composite_score": _sanitize(composite_score),
            "expectancy_floor": _sanitize(expectancy_floor),
            "gates": {
                "composite_gate_pass": composite_gate_pass,
                "expectancy_gate_pass": expectancy_gate_pass,
                "block_reason": block_reason,
            },
        }
        if signal_group_scores is not None:
            rec["signal_group_scores"] = _sanitize(signal_group_scores)
        if per_signal is not None:
            rec["per_signal"] = _sanitize(per_signal)
        if weighted_contributions is not None:
            rec["weighted_contributions"] = _sanitize(weighted_contributions)
        if group_sums is not None:
            rec["group_sums"] = _sanitize(group_sums)
        if composite_pre_norm is not None:
            rec["composite_pre_norm"] = _sanitize(composite_pre_norm)
        if composite_post_norm is not None:
            rec["composite_post_norm"] = _sanitize(composite_post_norm)
        if uw_deferred or candidate_status == "DEFERRED":
            rec["uw_deferred"] = True
            rec["candidate_status"] = "DEFERRED"
            if defer_reason is not None:
                rec["defer_reason"] = defer_reason
            if next_retry_ts is not None:
                rec["next_retry_ts"] = int(next_retry_ts)
        elif candidate_status is not None:
            rec["candidate_status"] = candidate_status
        line = json.dumps(rec, allow_nan=False) + "\n"
        if _snap_debug:
            print(f"SCORE_SNAPSHOT_DEBUG: append_score_snapshot write attempt symbol={symbol}", flush=True)
        with SCORE_SNAPSHOT_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
        # CTR mirror (Phase 1: when TRUTH_ROUTER_ENABLED=1)
        try:
            from src.infra.truth_router import append_jsonl as ctr_append
            ctr_append("telemetry/score_snapshot.jsonl", rec, expected_max_age_sec=300)
        except Exception:
            pass
        if _snap_debug:
            print(f"SCORE_SNAPSHOT_DEBUG: append_score_snapshot write done symbol={symbol}", flush=True)
    except Exception as e:
        if _snap_debug:
            print(f"SCORE_SNAPSHOT_DEBUG: append_score_snapshot EXCEPTION symbol={symbol} error={e!r}", flush=True)
            raise  # Do not swallow when debugging
        pass  # Do not break trading when debug off
