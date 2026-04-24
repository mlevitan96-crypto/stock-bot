#!/usr/bin/env python3
"""
Surgical quarantine for a single broken trade_id: copy matching JSONL rows to
logs/quarantined_events.jsonl, then remove those lines from canonical sources.

Used when strict completeness fails (e.g. missing_unified_entry_attribution) so
evaluate_completeness no longer sees that terminal close.

Default files mirror telemetry/alpaca_strict_completeness_gate.py inputs.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


DEFAULT_RELATIVE_LOGS = [
    "exit_attribution.jsonl",
    "alpaca_unified_events.jsonl",
    "strict_backfill_alpaca_unified_events.jsonl",
    "run.jsonl",
    "orders.jsonl",
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_exit_row(logs: Path, trade_id: str) -> Optional[Dict[str, Any]]:
    path = logs / "exit_attribution.jsonl"
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(rec.get("trade_id") or "") == trade_id:
                return rec
    return None


def _alias_keys_for_trade(exit_row: Optional[Dict[str, Any]], trade_id: str) -> Set[str]:
    keys: Set[str] = {trade_id}
    if not exit_row:
        return keys
    for k in ("canonical_trade_id", "trade_key"):
        v = exit_row.get(k)
        if v:
            s = str(v)
            keys.add(s)
            parts = s.split("|")
            if len(parts) == 3:
                sym, _side, epoch = parts[0], parts[1], parts[2]
                keys.add(f"{sym}|LONG|{epoch}")
                keys.add(f"{sym}|SHORT|{epoch}")
    return {k for k in keys if k}


def _line_matches(
    obj: Dict[str, Any],
    trade_id: str,
    alias_keys: Set[str],
) -> bool:
    if str(obj.get("trade_id") or "") == trade_id:
        return True
    for k in ("canonical_trade_id", "trade_key"):
        v = obj.get(k)
        if v and str(v) in alias_keys:
            return True
    return False


def _rewrite_file(
    path: Path,
    quarantine_path: Path,
    trade_id: str,
    alias_keys: Set[str],
    dry_run: bool,
) -> Tuple[int, int]:
    """Returns (lines_quarantined, lines_kept)."""
    if not path.is_file():
        return 0, 0
    tmp = path.with_suffix(path.suffix + ".quarantine_tmp")
    qn = 0
    kept = 0
    out_lines: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as inf:
        for raw in inf:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                kept += 1
                out_lines.append(line)
                continue
            if _line_matches(obj, trade_id, alias_keys):
                qn += 1
                envelope = {
                    "quarantined_at_utc": _iso_now(),
                    "source_file": str(path),
                    "quarantine_reason": "incomplete_trade_chain_surgical_quarantine",
                    "trade_id": trade_id,
                    "record": obj,
                }
                if not dry_run:
                    with quarantine_path.open("a", encoding="utf-8") as qf:
                        qf.write(json.dumps(envelope, ensure_ascii=False) + "\n")
            else:
                kept += 1
                out_lines.append(line)
    if dry_run:
        return qn, kept
    tmp.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
    os.replace(tmp, path)
    return qn, kept


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--trade-id", required=True, help="e.g. open_MRNA_2026-04-16T15:16:26.774838+00:00")
    ap.add_argument(
        "--extra-alias",
        action="append",
        default=[],
        help="Additional canonical_trade_id / trade_key substring to match on orders/run lines",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root: Path = args.root.resolve()
    logs = root / "logs"
    trade_id: str = str(args.trade_id)
    exit_row = _load_exit_row(logs, trade_id)
    alias_keys = _alias_keys_for_trade(exit_row, trade_id)
    for x in args.extra_alias or []:
        if x:
            alias_keys.add(str(x))

    quarantine_path = logs / "quarantined_events.jsonl"
    if not args.dry_run:
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)

    total_q = 0
    for rel in DEFAULT_RELATIVE_LOGS:
        p = logs / rel
        qn, kept = _rewrite_file(p, quarantine_path, trade_id, alias_keys, args.dry_run)
        if qn:
            print(f"{rel}: quarantined={qn} kept={kept}")
        total_q += qn

    print(f"TOTAL_QUARANTINED_LINES: {total_q}")
    print(f"QUARANTINE_FILE: {quarantine_path}")
    if args.dry_run:
        print("DRY_RUN: no files modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
