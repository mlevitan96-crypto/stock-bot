#!/usr/bin/env python3
"""
Ablation suite: for each signal in attribution_components, compute impact of zero/invert perturbation
by counterfactual score (would trade have been taken?). Writes ablation_summary.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True, help="Path to backtest_trades.jsonl")
    ap.add_argument("--perturbations", default="zero,invert", help="Comma-separated: zero,invert,delay")
    ap.add_argument("--min-score", type=float, default=1.8, help="Min score threshold for entry")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    trades_path = Path(args.trades)
    if not trades_path.is_absolute():
        trades_path = REPO / trades_path
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    perts = [p.strip() for p in args.perturbations.split(",") if p.strip()]

    trades = []
    for line in trades_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            trades.append(json.loads(line))
        except Exception:
            continue

    # Build component set and per-trade score contribution by signal
    signals_seen = set()
    for t in trades:
        for c in (t.get("context") or {}).get("attribution_components") or []:
            sid = c.get("signal_id")
            if sid:
                signals_seen.add(sid)

    min_score = args.min_score
    ablation = {"perturbations": perts, "min_score": min_score, "signals": {}}

    for sid in sorted(signals_seen):
        zero_dropped = []
        zero_pnl_dropped = 0.0
        invert_dropped = []
        invert_pnl_dropped = 0.0
        for t in trades:
            score = float(t.get("entry_score") or 0)
            comps = (t.get("context") or {}).get("attribution_components") or []
            contrib = next((float(c.get("contribution_to_score") or 0) for c in comps if c.get("signal_id") == sid), 0.0)
            pnl = float(t.get("pnl_usd") or 0)
            score_zero = score - contrib
            score_invert = score - 2 * contrib
            if score_zero < min_score:
                zero_dropped.append(t.get("trade_id"))
                zero_pnl_dropped += pnl
            if score_invert < min_score:
                invert_dropped.append(t.get("trade_id"))
                invert_pnl_dropped += pnl
        ablation["signals"][sid] = {
            "zero": {"trades_dropped": len(zero_dropped), "pnl_dropped_usd": round(zero_pnl_dropped, 2)},
            "invert": {"trades_dropped": len(invert_dropped), "pnl_dropped_usd": round(invert_pnl_dropped, 2)},
        }

    (out_dir / "ablation_summary.json").write_text(json.dumps(ablation, indent=2), encoding="utf-8")
    print(f"Ablation suite -> {out_dir / 'ablation_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
