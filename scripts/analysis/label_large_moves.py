#!/usr/bin/env python3
"""
Label large price moves (up/down) from truth dataset using trade/exit PnL %.
Output: labeled_moves.json for replay_entry_signals and policy discovery.
Uses real droplet truth (trades + exits with pnl_pct).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--move_pcts", default="0.5,1.0,1.5,2.0", help="Comma-separated pct thresholds for 'large move'")
    ap.add_argument("--lookahead_minutes", default="5,15,30,60", help="Not used for labeling; for downstream")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    truth_path = Path(args.truth)
    if not truth_path.is_absolute():
        truth_path = REPO / truth_path
    if not truth_path.exists():
        print(f"Truth not found: {truth_path}", file=sys.stderr)
        return 1

    data = json.loads(truth_path.read_text(encoding="utf-8"))
    trades = data.get("trades", [])
    exits = data.get("exits", [])

    thresholds = [float(x.strip()) for x in args.move_pcts.split(",") if x.strip()]

    labeled = []
    for t in trades:
        ts = t.get("timestamp") or t.get("ts")
        symbol = t.get("symbol")
        pnl_pct = t.get("pnl_pct")
        if ts is None or symbol is None:
            continue
        try:
            pct = float(pnl_pct) if pnl_pct is not None else 0.0
        except (TypeError, ValueError):
            pct = 0.0
        direction = "up" if pct >= 0 else "down"
        abs_pct = abs(pct)
        tier = "small"
        for th in sorted(thresholds, reverse=True):
            if abs_pct >= th:
                tier = f"move_{th}pct"
                break
        labeled.append({
            "timestamp": ts,
            "symbol": symbol,
            "pnl_pct": pct,
            "direction": direction,
            "tier": tier,
            "source": "trade",
        })

    for e in exits:
        ts = e.get("timestamp") or e.get("ts")
        symbol = e.get("symbol")
        pnl_pct = e.get("pnl_pct")
        if ts is None or symbol is None:
            continue
        try:
            pct = float(pnl_pct) if pnl_pct is not None else 0.0
        except (TypeError, ValueError):
            pct = 0.0
        direction = "up" if pct >= 0 else "down"
        abs_pct = abs(pct)
        tier = "small"
        for th in sorted(thresholds, reverse=True):
            if abs_pct >= th:
                tier = f"move_{th}pct"
                break
        labeled.append({
            "timestamp": ts,
            "symbol": symbol,
            "pnl_pct": pct,
            "direction": direction,
            "tier": tier,
            "source": "exit",
        })

    out = {
        "window": data.get("window_start") and data.get("window_end"),
        "move_pcts": thresholds,
        "lookahead_minutes": [int(x.strip()) for x in args.lookahead_minutes.split(",") if x.strip()],
        "count": len(labeled),
        "labeled": labeled[:50000],
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Labeled {len(labeled)} moves (wrote {len(out['labeled'])} to {out_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
