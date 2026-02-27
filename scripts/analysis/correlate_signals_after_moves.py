#!/usr/bin/env python3
"""
Correlate outcomes AFTER labeled price moves (exhaustion vs continuation).
Exit intelligence: after a +X% move, do we see reversal (exit losses) or continuation (more gains)?
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
            return t if t > 1e10 else t
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
    ap = argparse.ArgumentParser(description="Outcomes AFTER moves (exit intelligence)")
    ap.add_argument("--truth", required=True)
    ap.add_argument("--labeled_moves", required=True)
    ap.add_argument("--lookahead_minutes", default="5,15,30,60,120")
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
    lookahead_minutes = [int(x.strip()) for x in args.lookahead_minutes.split(",") if x.strip()]

    exits = truth.get("exits", [])
    trades = truth.get("trades", [])
    exit_events = []
    for e in exits:
        ts = _ts_seconds(e.get("timestamp") or e.get("ts"))
        if ts is None:
            continue
        symbol = e.get("symbol")
        if not symbol:
            continue
        try:
            pct = float(e.get("pnl_pct")) if e.get("pnl_pct") is not None else 0.0
        except (TypeError, ValueError):
            pct = 0.0
        exit_events.append({"ts": ts, "symbol": symbol, "pnl_pct": pct})
    for t in trades:
        ts = _ts_seconds(t.get("timestamp") or t.get("ts"))
        if ts is None:
            continue
        symbol = t.get("symbol")
        if not symbol:
            continue
        try:
            pct = float(t.get("pnl_pct")) if t.get("pnl_pct") is not None else 0.0
        except (TypeError, ValueError):
            pct = 0.0
        exit_events.append({"ts": ts, "symbol": symbol, "pnl_pct": pct})

    by_tier_dir_lookahead = defaultdict(lambda: {"pnl_pcts": [], "continuation_count": 0, "exhaustion_count": 0})

    for m in labeled:
        move_ts = _ts_seconds(m.get("timestamp") or m.get("ts"))
        symbol = m.get("symbol")
        direction = m.get("direction", "up")
        tier = m.get("tier", "small")
        if move_ts is None or not symbol:
            continue

        for la_min in lookahead_minutes:
            window_end = move_ts + la_min * 60.0
            pcts_after = [
                e["pnl_pct"] for e in exit_events
                if e["symbol"] == symbol and move_ts < e["ts"] <= window_end
            ]
            key = (tier, direction, la_min)
            for pct in pcts_after:
                by_tier_dir_lookahead[key]["pnl_pcts"].append(pct)
                if pct > 0:
                    by_tier_dir_lookahead[key]["continuation_count"] += 1
                else:
                    by_tier_dir_lookahead[key]["exhaustion_count"] += 1

    out = {
        "no_suppression": args.no_suppression,
        "move_pcts": labeled_data.get("move_pcts", []),
        "lookahead_minutes": lookahead_minutes,
        "post_move_intelligence": [],
    }
    for (tier, direction, la_min), v in sorted(by_tier_dir_lookahead.items()):
        n = len(v["pnl_pcts"])
        if n == 0:
            continue
        total = sum(v["pnl_pcts"])
        out["post_move_intelligence"].append({
            "tier": tier,
            "direction": direction,
            "lookahead_minutes": la_min,
            "outcome_count": n,
            "avg_pnl_pct_after": round(total / n, 4),
            "continuation_pct": round(100 * v["continuation_count"] / n, 2),
            "exhaustion_pct": round(100 * v["exhaustion_count"] / n, 2),
        })

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Post-move intelligence -> {out_path} ({len(out['post_move_intelligence'])} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
