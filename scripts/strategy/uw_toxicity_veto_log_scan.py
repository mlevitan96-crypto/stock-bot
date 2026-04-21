#!/usr/bin/env python3
"""
Scan JSONL logs for ``uw_toxicity_veto`` (composite / gate telemetry) to detect over-vetoing.

**Quant impact:** if veto rate is high vs marginal toxicity, EV is lost to false negatives; if low
under stress, tail risk dominates. Tune gates in ``uw_composite_v2`` / ``UW_TOXICITY_VETO_STICKY``.

Default: ``logs/run.jsonl`` (strict runlog). Falls back to empty if missing.

Usage:
  PYTHONPATH=. python scripts/strategy/uw_toxicity_veto_log_scan.py [--root PATH] [--tail N]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _walk(obj: Any, key: str) -> List[Any]:
    out: List[Any] = []
    if isinstance(obj, dict):
        if key in obj:
            out.append(obj[key])
        for v in obj.values():
            out.extend(_walk(v, key))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_walk(v, key))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Scan logs for uw_toxicity_veto signals.")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--log", type=Path, default=None, help="Default: <root>/logs/run.jsonl")
    ap.add_argument("--tail", type=int, default=50000, help="Max lines to read from end (approx)")
    args = ap.parse_args()
    log_p = args.log or (args.root / "logs" / "run.jsonl")
    if not log_p.exists():
        print(f"missing_log={log_p}")
        return
    text = log_p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    chunk = lines[-args.tail :] if len(lines) > args.tail else lines
    total = 0
    veto_true = 0
    for line in chunk:
        line = line.strip()
        if "uw_toxicity_veto" not in line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        hits = _walk(rec, "uw_toxicity_veto")
        if any(bool(x) for x in hits if isinstance(x, (bool, int))):
            veto_true += 1
    print(f"log={log_p} lines_scanned~={len(chunk)} records_with_key_uw_toxicity_veto={total} veto_true_rows={veto_true}")


if __name__ == "__main__":
    main()
