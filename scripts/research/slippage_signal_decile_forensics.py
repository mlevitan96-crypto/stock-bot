#!/usr/bin/env python3
"""
Slippage vs signal deciles — offline join ``entry_snapshots.jsonl`` ↔ ``exit_attribution.jsonl``.

Join key: ``entry_snapshots.order_id`` ↔ ``exit_attribution.entry_order_id`` (when present).

Usage:
  PYTHONPATH=. python3 scripts/research/slippage_signal_decile_forensics.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from bisect import bisect_right
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _iter_jsonl(path: Path):
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _f(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if not math.isfinite(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--entry-log", type=Path, default=None)
    ap.add_argument("--exit-log", type=Path, default=None)
    ap.add_argument("--max-rows", type=int, default=500_000)
    args = ap.parse_args()
    root = args.root.resolve()
    entry_path = (args.entry_log or (root / "logs" / "entry_snapshots.jsonl")).resolve()
    exit_path = (args.exit_log or (root / "logs" / "exit_attribution.jsonl")).resolve()

    by_oid: Dict[str, Dict[str, Any]] = {}
    n_ent = 0
    for r in _iter_jsonl(entry_path):
        if n_ent >= args.max_rows:
            break
        if str(r.get("msg") or "") != "entry_snapshot":
            continue
        oid = str(r.get("order_id") or "").strip()
        if not oid:
            continue
        sc = _f(r.get("composite_score"))
        if sc is None:
            continue
        by_oid[oid] = {"composite_score": sc, "symbol": str(r.get("symbol") or "").upper()}
        n_ent += 1

    slips: List[Tuple[float, float]] = []  # (score, abs_slip_bps)
    for r in _iter_jsonl(exit_path):
        oid = str(r.get("entry_order_id") or "").strip()
        if not oid or oid not in by_oid:
            continue
        slip = _f(r.get("exit_slippage_bps"))
        if slip is None:
            slip = _f(r.get("touch_slippage_bps"))
        if slip is None:
            continue
        sc = by_oid[oid]["composite_score"]
        slips.append((sc, abs(float(slip))))

    if not slips:
        print("# Slippage vs signal deciles\n\nNo joined rows (need entry_snapshots + exit slippage fields).")
        return 0

    scores = sorted(s[0] for s in slips)
    cuts = [scores[int(len(scores) * p / 10)] for p in range(1, 10)]

    buckets: List[List[float]] = [[] for _ in range(10)]
    for sc, sl in slips:
        d = min(9, bisect_right(cuts, sc))
        buckets[d].append(sl)

    print("# Slippage vs signal decile (joined on entry_order_id)\n")
    print("| Decile | N | Median slip bps | Mean slip bps |")
    print("|--------|---|-----------------|---------------|")
    for i, arr in enumerate(buckets):
        if not arr:
            print(f"| {i} | 0 | n/a | n/a |")
            continue
        arr.sort()
        med = arr[len(arr) // 2]
        mean = sum(arr) / len(arr)
        print(f"| {i} | {len(arr)} | {med:.2f} | {mean:.2f} |")

    top = buckets[-1]
    rest = [x for b in buckets[:-1] for x in b]
    if top and rest:
        rest.sort()
        rmed = rest[len(rest) // 2]
        tmed = top[len(top) // 2]
        print("\n**Elite (decile 9) vs rest:** median slip", f"{tmed:.2f}", "bps vs", f"{rmed:.2f}", "bps")
        if tmed > rmed * 1.25:
            print(
                "\n> Suggestion: enable ``ELITE_SCORE_LIMIT_PATIENCE_ENABLED`` with a small ``ELITE_LIMIT_EXTRA_BPS`` "
                "so top-decile entries rest further inside the book."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
