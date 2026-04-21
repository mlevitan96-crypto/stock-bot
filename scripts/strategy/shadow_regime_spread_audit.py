#!/usr/bin/env python3
"""
Extract ``regime_shadow_execution_intent`` rows from ``logs/unified_events.jsonl`` for CHOP
shadow passive maker analysis.

**Quant impact:** aggregates shadow intents so CPA can join to NBBO or fill prints and
estimate hypothetical half-spread capture vs market-take baseline (EV lift in chop, fee-aware).

Usage:
  PYTHONPATH=. python scripts/strategy/shadow_regime_spread_audit.py [--root PATH] [--out CSV]
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def _iter_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit regime shadow execution intents (CHOP passive).")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="Repo root")
    ap.add_argument(
        "--log",
        type=Path,
        default=None,
        help="Path to unified_events.jsonl (default: <root>/logs/unified_events.jsonl)",
    )
    ap.add_argument("--out", type=Path, default=None, help="Optional CSV output path")
    ap.add_argument(
        "--assume-half-spread-bps",
        type=float,
        default=5.0,
        help="Illustrative half-spread saved vs mid (bps) for notional proxy when price missing",
    )
    args = ap.parse_args()
    root: Path = args.root
    log_p = args.log or (root / "logs" / "unified_events.jsonl")
    events = [r for r in _iter_jsonl(log_p) if r.get("event_type") == "regime_shadow_execution_intent"]
    by_sym: Dict[str, int] = defaultdict(int)
    total_qty = 0
    for r in events:
        sym = str(r.get("symbol") or "").upper()
        by_sym[sym] += 1
        try:
            total_qty += int(r.get("qty") or 0)
        except (TypeError, ValueError):
            pass
    print(f"source={log_p}")
    print(f"shadow_intent_rows={len(events)} unique_symbols={len(by_sym)} sum_qty={total_qty}")
    if by_sym:
        top = sorted(by_sym.items(), key=lambda x: -x[1])[:15]
        print("top_symbols:", ", ".join(f"{s}:{n}" for s, n in top))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "ts_utc",
                    "symbol",
                    "side",
                    "qty",
                    "shadow_entry_style",
                    "shadow_sizing_mult",
                    "entry_score",
                    "correlation_id",
                    "live_market_regime_label",
                    "hypothetical_half_spread_bps",
                ],
                extrasaction="ignore",
            )
            w.writeheader()
            for r in events:
                extra = r.get("extra") if isinstance(r.get("extra"), dict) else {}
                w.writerow(
                    {
                        "ts_utc": r.get("ts_utc"),
                        "symbol": r.get("symbol"),
                        "side": r.get("side"),
                        "qty": r.get("qty"),
                        "shadow_entry_style": r.get("shadow_entry_style"),
                        "shadow_sizing_mult": r.get("shadow_sizing_mult"),
                        "entry_score": r.get("entry_score"),
                        "correlation_id": r.get("correlation_id"),
                        "live_market_regime_label": extra.get("live_market_regime_label"),
                        "hypothetical_half_spread_bps": args.assume_half_spread_bps,
                    }
                )
        print(f"wrote_csv={args.out}")


if __name__ == "__main__":
    main()
