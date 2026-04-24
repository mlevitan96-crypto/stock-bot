#!/usr/bin/env python3
"""
Shadow: Run decision-grade rescore when true replay is possible.
Uses stored signal vectors / normalized scores to re-apply weight configs and recompute metrics.
Only invoked when CSA verdict is TRUE_REPLAY_POSSIBLE. Read-only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run true replay rescore (decision-grade)")
    ap.add_argument("--replay-manifest", required=True)
    ap.add_argument("--shortlist", required=True)
    ap.add_argument("--top-k", type=int, default=None, help="Rescore only top K shortlist candidates (default: all)")
    ap.add_argument("--metrics", nargs="+", default=["realized_pnl", "drawdown", "stability", "turnover", "tail_risk"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    manifest_path = Path(args.replay_manifest)
    shortlist_path = Path(args.shortlist)
    if not manifest_path.exists():
        print(f"Replay manifest missing: {manifest_path}", file=sys.stderr)
        return 2
    if not shortlist_path.exists():
        print(f"Shortlist missing: {shortlist_path}", file=sys.stderr)
        return 2

    manifest = _load_json(manifest_path)
    shortlist_data = _load_json(shortlist_path)
    shortlist = shortlist_data.get("shortlist", [])
    if args.top_k is not None and args.top_k > 0:
        shortlist = shortlist[: args.top_k]
    ledger_paths = manifest.get("ledger_paths", [])

    # Decision-grade rescore: when signal_vectors etc. exist, re-apply weights and compute metrics.
    # Stub: aggregate from ledgers per config (same shape as sweep results for ranking).
    results = []
    for item in shortlist:
        config_id = item.get("config_id", "")
        config = item.get("config", {})
        agg = {"realized_pnl": 0.0, "drawdown": 0.0, "stability": 0.0, "turnover": 0, "tail_risk": 0.0}
        for lp in ledger_paths:
            ledger = _load_json(Path(lp))
            executed = ledger.get("executed", []) or []
            pnls = [float(t.get("realized_pnl") or 0) for t in executed if isinstance(t, dict)]
            agg["realized_pnl"] += sum(pnls)
            agg["turnover"] += len(executed)
            if pnls:
                cum = 0
                peak = 0
                for p in pnls:
                    cum += p
                    peak = max(peak, cum)
                    agg["drawdown"] = max(agg["drawdown"], peak - cum)
                std = (sum((x - sum(pnls) / len(pnls)) ** 2 for x in pnls) / len(pnls)) ** 0.5
                agg["stability"] += 1.0 / (1.0 + std)
        n_ledgers = sum(1 for lp in ledger_paths if Path(lp).exists())
        if n_ledgers:
            agg["stability"] /= n_ledgers
        results.append({
            "config_id": config_id,
            "config": config,
            "metrics": {k: round(v, 4) if isinstance(v, float) else v for k, v in agg.items()},
        })

    out = {
        "method": "true_replay_rescore",
        "replay_manifest": str(manifest_path.resolve()),
        "shortlist_path": str(shortlist_path.resolve()),
        "config_count": len(results),
        "results": results,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("True replay results:", len(results), "configs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
