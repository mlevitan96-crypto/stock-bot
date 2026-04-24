"""
Paper-only second-chance displacement scheduling.

- Enabled only when PAPER_SECOND_CHANCE_DISPLACEMENT=1.
- Appends audit rows to logs/second_chance_displacement.jsonl and state/paper_second_chance_queue.jsonl.
- Does not submit orders, modify positions, or change live gate outcomes.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, default=str) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def record_displacement_block_scheduled(
    *,
    symbol: str,
    direction: Optional[str],
    score: float,
    components: Optional[Dict[str, Any]],
    displaced_symbol: str,
    policy_reason: str,
    decision_price: Optional[float],
    effective_min_score_at_block: float,
    market_regime: Optional[str],
    challenger_uw_proxy: Optional[float],
    variant_id: Optional[str],
) -> None:
    """
    Called from main.py when displacement_blocked is logged (paper-only env).
    """
    if os.environ.get("PAPER_SECOND_CHANCE_DISPLACEMENT") != "1":
        return
    try:
        delay = int(os.environ.get("PAPER_SECOND_CHANCE_DELAY_SECONDS", "60"))
    except ValueError:
        delay = 60
    root = _repo_root()
    now = time.time()
    original_ts_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    reeval_epoch = int(now) + max(1, delay)
    reeval_ts_iso = datetime.fromtimestamp(reeval_epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    pending_id = hashlib.sha256(
        f"{symbol}|{original_ts_iso}|{displaced_symbol}|{score}".encode()
    ).hexdigest()[:20]

    queue_row = {
        "pending_id": pending_id,
        "due_epoch": reeval_epoch,
        "original_ts_iso": original_ts_iso,
        "reeval_ts_iso": reeval_ts_iso,
        "symbol": str(symbol or "").upper().strip(),
        "direction": direction,
        "original_score": float(score),
        "original_components": dict(components or {}),
        "effective_min_score_at_block": float(effective_min_score_at_block),
        "displaced_symbol": str(displaced_symbol or "").upper().strip(),
        "policy_reason_at_block": str(policy_reason or ""),
        "challenger_uw_flow_proxy": challenger_uw_proxy,
        "block_reason": "displacement_blocked",
        "decision_price": decision_price,
        "market_regime_at_block": market_regime,
        "variant_id_at_block": variant_id,
    }
    qpath = root / "state" / "paper_second_chance_queue.jsonl"
    _append_jsonl(qpath, queue_row)

    log_row = {
        "paper_only": True,
        "event": "scheduled",
        "pending_id": pending_id,
        "original_ts": original_ts_iso,
        "reeval_ts": reeval_ts_iso,
        "symbol": queue_row["symbol"],
        "direction": direction,
        "original_scores": {
            "final_score": float(score),
            "components": dict(components or {}),
            "effective_min_score_at_block": float(effective_min_score_at_block),
        },
        "block_reason": "displacement_blocked",
        "reeval_outcome": None,
        "reeval_block_reason": None,
        "displaced_symbol": queue_row["displaced_symbol"],
        "policy_reason_at_block": queue_row["policy_reason_at_block"],
        "delay_seconds": delay,
    }
    lpath = root / "logs" / "second_chance_displacement.jsonl"
    _append_jsonl(lpath, log_row)
