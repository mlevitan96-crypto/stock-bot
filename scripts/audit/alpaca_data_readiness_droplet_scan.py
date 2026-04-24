#!/usr/bin/env python3
"""
Run on droplet (repo root): PYTHONPATH=. python3 scripts/audit/alpaca_data_readiness_droplet_scan.py
Emits JSON with integrity + sufficiency metrics for ALPACA DATA READINESS gate.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOGS = REPO / "logs"
sys.path.insert(0, str(REPO))

from src.telemetry.alpaca_trade_key import normalize_symbol, normalize_time  # noqa: E402


def _canonical_live_key(symbol: object, entry_ts: object) -> str:
    """Normalize live:SYMBOL:entry_ts to second precision for joins (matches main.py stable_trade_id intent)."""
    sym = normalize_symbol(symbol)
    ts = normalize_time(entry_ts)
    if not sym or not ts:
        return ""
    return f"live:{sym}:{ts}"


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main() -> int:
    exit_path = LOGS / "exit_attribution.jsonl"
    master_path = LOGS / "master_trade_log.jsonl"
    attr_path = LOGS / "attribution.jsonl"

    exit_join_keys: list[str] = []
    exit_by_join: dict[str, dict] = {}
    missing_exit = Counter()
    for rec in _iter_jsonl(exit_path):
        et = rec.get("entry_ts") or rec.get("entry_timestamp")
        jk = _canonical_live_key(rec.get("symbol"), et)
        exit_join_keys.append(jk)
        if jk:
            exit_by_join.setdefault(jk, rec)
        if not (rec.get("trade_id") or "").strip():
            missing_exit["missing_trade_id"] += 1
        if not (rec.get("symbol") or "").strip():
            missing_exit["missing_symbol"] += 1
        pnl = rec.get("pnl")
        pnl2 = rec.get("realized_pnl") or rec.get("pnl_usd")
        if pnl is None and pnl2 is None:
            missing_exit["missing_pnl"] += 1
        et = rec.get("entry_ts") or rec.get("entry_timestamp")
        xt = rec.get("exit_ts") or rec.get("timestamp")
        if not et:
            missing_exit["missing_entry_ts"] += 1
        if not xt:
            missing_exit["missing_exit_ts"] += 1
        die = rec.get("direction_intel_embed")
        if not isinstance(die, dict):
            missing_exit["missing_direction_intel_embed_dict"] += 1
        elif die.get("intel_snapshot_entry") in (None, {}):
            missing_exit["empty_intel_snapshot_entry"] += 1

    master_exit_keys_closed: set[str] = set()
    master_by_exit_key: dict[str, dict] = {}
    for rec in _iter_jsonl(master_path):
        ex = rec.get("exit_ts")
        if not ex:
            continue
        et = rec.get("entry_ts") or rec.get("timestamp")
        jk = _canonical_live_key(rec.get("symbol"), et)
        if not jk:
            tid = str(rec.get("trade_id") or "")
            if tid.startswith("live:") and tid.count(":") >= 2:
                _, sym, raw_ts = tid.split(":", 2)
                jk = _canonical_live_key(sym, raw_ts)
        if jk:
            master_exit_keys_closed.add(jk)
            master_by_exit_key[jk] = rec

    # Closed attribution rows → exit join key via same helper as exit_attribution shape
    attr_closed_keys: set[str] = set()
    for rec in _iter_jsonl(attr_path):
        if rec.get("type") != "attribution":
            continue
        tid = str(rec.get("trade_id") or "")
        if tid.startswith("open_"):
            continue
        if not tid:
            continue
        et = rec.get("entry_ts") or rec.get("ts")
        jk = _canonical_live_key(rec.get("symbol"), et)
        if jk:
            attr_closed_keys.add(jk)

    exit_key_set = {x for x in exit_join_keys if x}
    orphan_exit = sorted(exit_key_set - master_exit_keys_closed)
    orphan_master = sorted(master_exit_keys_closed - exit_key_set)
    exit_no_master = sorted(exit_key_set - set(master_by_exit_key.keys()))

    # Sufficiency
    sym_c = Counter()
    day_c = Counter()
    wins = losses = 0
    exit_reason_c = Counter()
    for rec in exit_by_join.values():
        sym = (rec.get("symbol") or "?").strip().upper()
        sym_c[sym] += 1
        xt = rec.get("exit_ts") or rec.get("timestamp") or ""
        if isinstance(xt, str) and len(xt) >= 10:
            day_c[xt[:10]] += 1
        pnl = rec.get("pnl")
        if pnl is None:
            pnl = rec.get("realized_pnl")
        try:
            pv = float(pnl) if pnl is not None else 0.0
        except (TypeError, ValueError):
            pv = 0.0
        if pv > 0:
            wins += 1
        elif pv < 0:
            losses += 1
        rc = rec.get("exit_reason_code") or rec.get("exit_reason") or "unknown"
        exit_reason_c[str(rc)[:80]] += 1

    n_closed = len(exit_by_join)
    raw_lines_exit = 0
    if exit_path.exists():
        with open(exit_path, "rb") as f:
            raw_lines_exit = sum(1 for _ in f)

    out = {
        "scan_ts_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO),
        "line_counts": {
            "exit_attribution_jsonl": raw_lines_exit,
            "exit_attribution_parsed_records": len(exit_join_keys),
            "exit_unique_join_key": len(exit_key_set),
            "master_trade_log_lines": sum(1 for _ in open(master_path, "rb")) if master_path.exists() else 0,
            "attribution_jsonl_lines": sum(1 for _ in open(attr_path, "rb")) if attr_path.exists() else 0,
        },
        "missing_field_counts_exit_attribution": dict(missing_exit),
        "joins": {
            "orphaned_exits_join_key_not_in_master_closed": orphan_exit[:25],
            "orphaned_exits_count": len(orphan_exit),
            "orphaned_master_closed_not_in_exit_attribution": orphan_master[:25],
            "orphaned_master_count": len(orphan_master),
            "exit_join_key_missing_master_row": exit_no_master[:25],
            "exit_no_master_count": len(exit_no_master),
            "attr_closed_keys_not_in_exit": sorted(attr_closed_keys - exit_key_set)[:25],
            "attr_closed_not_in_exit_count": len(attr_closed_keys - exit_key_set),
        },
        "sufficiency": {
            "closed_trades_exit_attribution_unique_join_key": n_closed,
            "wins": wins,
            "losses": losses,
            "breakeven_or_unknown_pnl": n_closed - wins - losses,
            "trades_per_symbol_top": sym_c.most_common(30),
            "trades_per_day_top": day_c.most_common(40),
            "exit_reason_distribution": exit_reason_c.most_common(40),
        },
    }
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
