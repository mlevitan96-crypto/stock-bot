#!/usr/bin/env python3
"""
Correlate signals (entry_score, trade activity) BEFORE labeled price moves.
Entry intelligence: which signals precede +X% / -X% moves.
Profitability: we can enter after a small move when signal hits if more move is likely (e.g. +0.5% then +2%).
Uses real 30d truth; no suppression.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _ts_seconds(ts) -> float | None:
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            t = float(ts)
            return t if t > 1e10 else t  # assume seconds if small
        s = str(ts).strip()
        if not s:
            return None
        if s.replace(".", "").replace("-", "").isdigit():
            t = float(s)
            return t / 1000.0 if t > 1e12 else t
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Signals BEFORE moves (entry intelligence)")
    ap.add_argument("--truth", required=True)
    ap.add_argument("--labeled_moves", required=True)
    ap.add_argument("--lookback_minutes", default="5,15,30,60,120")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    truth_path = Path(args.truth)
    if not truth_path.is_absolute():
        truth_path = REPO / truth_path
    labeled_path = Path(args.labeled_moves)
    if not labeled_path.is_absolute():
        labeled_path = REPO / labeled_path
    if not truth_path.exists():
        print(f"Truth not found: {truth_path}", file=sys.stderr)
        return 1
    if not labeled_path.exists():
        print(f"Labeled moves not found: {labeled_path}", file=sys.stderr)
        return 1

    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    labeled_data = json.loads(labeled_path.read_text(encoding="utf-8"))
    labeled = labeled_data.get("labeled", [])
    lookback_minutes = [int(x.strip()) for x in args.lookback_minutes.split(",") if x.strip()]

    trades = truth.get("trades", [])
    # Build: (symbol, ts_sec) -> trade with entry_score
    trade_events = []
    for t in trades:
        ts = _ts_seconds(t.get("timestamp") or t.get("ts"))
        if ts is None:
            continue
        symbol = t.get("symbol")
        if not symbol:
            continue
        try:
            score = float(t.get("entry_score")) if t.get("entry_score") is not None else None
        except (TypeError, ValueError):
            score = None
        trade_events.append({"ts": ts, "symbol": symbol, "entry_score": score})

    # For each labeled move, find trades in each lookback window before the move
    # Key: (tier, direction, lookback_min) -> list of (avg_entry_score, count) for moves that had that lookback
    by_tier_dir_lookback = defaultdict(lambda: {"entry_scores": [], "counts": [], "move_pnl_pcts": []})

    for m in labeled:
        move_ts = _ts_seconds(m.get("timestamp") or m.get("ts"))
        symbol = m.get("symbol")
        pnl_pct = m.get("pnl_pct")
        direction = m.get("direction", "up")
        tier = m.get("tier", "small")
        if move_ts is None or not symbol:
            continue
        try:
            pct = float(pnl_pct) if pnl_pct is not None else 0.0
        except (TypeError, ValueError):
            pct = 0.0

        for lb_min in lookback_minutes:
            window_start = move_ts - lb_min * 60.0
            scores_in_window = [
                e["entry_score"] for e in trade_events
                if e["symbol"] == symbol and window_start <= e["ts"] <= move_ts and e["entry_score"] is not None
            ]
            key = (tier, direction, lb_min)
            if scores_in_window:
                avg = sum(scores_in_window) / len(scores_in_window)
                by_tier_dir_lookback[key]["entry_scores"].append(avg)
                by_tier_dir_lookback[key]["counts"].append(len(scores_in_window))
                by_tier_dir_lookback[key]["move_pnl_pcts"].append(pct)

    # Aggregate
    out = {
        "no_suppression": args.no_suppression,
        "move_pcts": labeled_data.get("move_pcts", []),
        "lookback_minutes": lookback_minutes,
        "pre_move_intelligence": [],
    }
    for (tier, direction, lb_min), v in sorted(by_tier_dir_lookback.items()):
        n = len(v["entry_scores"])
        if n == 0:
            continue
        out["pre_move_intelligence"].append({
            "tier": tier,
            "direction": direction,
            "lookback_minutes": lb_min,
            "move_count": n,
            "avg_entry_score_before": round(sum(v["entry_scores"]) / n, 4),
            "avg_trades_in_window": round(sum(v["counts"]) / n, 2),
            "avg_move_pnl_pct": round(sum(v["move_pnl_pcts"]) / n, 4),
        })

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Pre-move intelligence -> {out_path} ({len(out['pre_move_intelligence'])} tier/direction/lookback cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
