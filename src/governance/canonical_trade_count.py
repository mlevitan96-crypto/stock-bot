"""
Canonical closed-trade counts for dashboard, Telegram milestones, and PnL audit alignment.

Trade unit: one row in logs/exit_attribution.jsonl that yields a stable Alpaca trade_key
(build_trade_key(symbol, side, entry_ts)) and is not excluded by the era cut (pre-era entries
skipped per utils/era_cut.learning_excluded_for_exit_record).

Optional time floor: Telegram integrity milestones also require exit_ts >= floor_epoch
(see telemetry.alpaca_telegram_integrity.milestone.build_milestone_snapshot).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set

from src.telemetry.alpaca_trade_key import build_trade_key
from utils.era_cut import learning_excluded_for_exit_record


def _iter_exit_attribution(path: Path) -> Iterator[dict]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                yield o


def _parse_exit_epoch(rec: dict) -> Optional[float]:
    for k in ("exit_ts", "timestamp", "ts", "exit_timestamp"):
        v = rec.get(k)
        if not v:
            continue
        try:
            s = str(v).strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except (TypeError, ValueError):
            continue
    return None


@dataclass
class CanonicalTradeCountResult:
    total_trades_post_era: int
    realized_pnl_sum_usd: float
    unique_trade_keys: List[str]
    last_exit_timestamp_utc: Optional[str]
    next_milestone: Optional[int]
    remaining_to_next_milestone: int
    trades_to_100: int
    trades_to_250: int
    era_cut_excluded_rows: int
    floor_excluded_rows: int
    skipped_no_trade_key: int


def compute_canonical_trade_count(
    root: Path,
    *,
    floor_epoch: Optional[float] = None,
    max_samples: int = 8,
) -> Dict[str, Any]:
    """
    Count unique closed trades (trade_key) from exit_attribution.jsonl.

    - Excludes pre-era entries via learning_excluded_for_exit_record (config/era_cut.json).
    - If floor_epoch is set, excludes exits with parsed exit time strictly before floor.
    """
    exit_path = root / "logs" / "exit_attribution.jsonl"
    keys: Set[str] = set()
    samples: List[str] = []
    era_ex = floor_ex = skip_tk = 0
    last_ex: Optional[float] = None
    pnl_sum = 0.0
    first_row_pnl_by_key: Dict[str, float] = {}

    for rec in _iter_exit_attribution(exit_path):
        if learning_excluded_for_exit_record(rec):
            era_ex += 1
            continue
        ex = _parse_exit_epoch(rec)
        if floor_epoch is not None:
            if ex is None or ex < floor_epoch:
                floor_ex += 1
                continue
        elif ex is None:
            continue

        sym = rec.get("symbol")
        side = rec.get("side") or rec.get("position_side")
        et = rec.get("entry_ts") or rec.get("entry_timestamp")
        try:
            tk = build_trade_key(sym, side, et)
        except Exception:
            skip_tk += 1
            continue
        if tk in keys:
            if ex is not None and (last_ex is None or ex > last_ex):
                last_ex = ex
            continue
        keys.add(tk)
        if len(samples) < max_samples:
            samples.append(tk)
        if ex is not None and (last_ex is None or ex > last_ex):
            last_ex = ex
        pv = rec.get("pnl")
        if pv is not None:
            try:
                first_row_pnl_by_key[tk] = float(pv)
            except (TypeError, ValueError):
                pass

    n = len(keys)
    pnl_sum = round(sum(first_row_pnl_by_key.values()), 2)
    last_iso = (
        datetime.fromtimestamp(last_ex, tz=timezone.utc).isoformat() if last_ex is not None else None
    )

    if n < 100:
        next_m = 100
        rem = max(0, 100 - n)
    elif n < 250:
        next_m = 250
        rem = max(0, 250 - n)
    else:
        next_m = None
        rem = 0

    t100 = max(0, 100 - n) if n < 100 else 0
    t250 = max(0, 250 - n) if n < 250 else 0

    res = CanonicalTradeCountResult(
        total_trades_post_era=n,
        realized_pnl_sum_usd=pnl_sum,
        unique_trade_keys=samples,
        last_exit_timestamp_utc=last_iso,
        next_milestone=next_m,
        remaining_to_next_milestone=rem,
        trades_to_100=t100,
        trades_to_250=t250,
        era_cut_excluded_rows=era_ex,
        floor_excluded_rows=floor_ex,
        skipped_no_trade_key=skip_tk,
    )
    return {
        "total_trades_post_era": res.total_trades_post_era,
        "realized_pnl_sum_usd": res.realized_pnl_sum_usd,
        "last_exit_timestamp_utc": res.last_exit_timestamp_utc,
        "next_milestone": res.next_milestone,
        "remaining_to_next_milestone": res.remaining_to_next_milestone,
        "trades_to_100": res.trades_to_100,
        "trades_to_250": res.trades_to_250,
        "sample_trade_keys": res.unique_trade_keys,
        "era_cut_excluded_rows": res.era_cut_excluded_rows,
        "floor_excluded_rows": res.floor_excluded_rows,
        "skipped_no_trade_key": res.skipped_no_trade_key,
        "floor_epoch_utc": (
            datetime.fromtimestamp(floor_epoch, tz=timezone.utc).isoformat()
            if floor_epoch is not None
            else None
        ),
    }
