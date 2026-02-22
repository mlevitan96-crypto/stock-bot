#!/usr/bin/env python3
"""
Blocked-trade opportunity-cost analysis: compare blocked_trades.jsonl to executed trades,
estimate missed opportunity / valid blocks. Writes summary JSON and optional markdown.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blocked", default="state/blocked_trades.jsonl")
    ap.add_argument("--executed", required=True, help="Path to backtest_trades.jsonl or executed trades")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    blocked_path = REPO / args.blocked if not Path(args.blocked).is_absolute() else Path(args.blocked)
    executed_path = Path(args.executed)
    if not executed_path.is_absolute():
        executed_path = REPO / executed_path
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    blocked = _load_jsonl(blocked_path)
    executed = _load_jsonl(executed_path)

    # Build executed by symbol for similarity
    by_symbol = {}
    for t in executed:
        sym = (t.get("symbol") or "").upper()
        if sym not in by_symbol:
            by_symbol[sym] = []
        by_symbol[sym].append(t)

    high_score_blocked = [b for b in blocked if float(b.get("score") or 0) >= 4.0]
    by_reason = {}
    for b in blocked:
        r = b.get("reason") or b.get("block_reason") or "unknown"
        by_reason[r] = by_reason.get(r, 0) + 1

    # Simple opportunity-cost view: high-score blocked count vs executed PnL
    exec_pnl = sum(float(t.get("pnl_usd") or 0) for t in executed)
    exec_wins = sum(1 for t in executed if (t.get("pnl_usd") or 0) > 0)
    exec_n = len(executed)
    win_rate = (exec_wins / exec_n * 100.0) if exec_n else 0.0

    summary = {
        "blocked_count": len(blocked),
        "high_score_blocked_count": len(high_score_blocked),
        "blocked_by_reason": by_reason,
        "executed_count": len(executed),
        "executed_net_pnl_usd": round(exec_pnl, 2),
        "executed_win_rate_pct": round(win_rate, 2),
        "opportunity_cost_note": "Theoretical PnL for blocked trades requires price simulation; see counter_intelligence_analysis.estimate_blocked_outcome for similar-trade estimation.",
        "status": "ok",
    }
    (out_dir / "blocked_opportunity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Blocked-trade analysis -> {out_dir / 'blocked_opportunity_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
