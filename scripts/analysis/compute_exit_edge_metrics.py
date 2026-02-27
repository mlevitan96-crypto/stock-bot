#!/usr/bin/env python3
"""
Compute edge metrics (baseline vs candidates) from replay results.
Output: exit_edge_metrics.json and exit_edge_metrics.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", required=True)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--out_md", required=True)
    args = ap.parse_args()
    replay_path = Path(args.replay)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    if not replay_path.exists():
        metrics = {"baseline": {}, "candidates": {}, "giveback_reduction": {}, "saved_loss_rate": {}, "message": "No replay data"}
    else:
        data = json.loads(replay_path.read_text(encoding="utf-8"))
        candidates = data.get("replay_candidates", data.get("exits", []))
        n = len(candidates)
        pnls = [float(c.get("pnl") or c.get("pnl_usd") or 0) for c in candidates]
        metrics = {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "n_exits": n,
            "baseline": {"count": n, "total_pnl": sum(pnls), "avg_pnl": sum(pnls) / n if n else 0},
            "candidates": {"stale_exit": 0, "trailing_stop": 0, "profit_target": 0},
            "giveback_reduction": {},
            "saved_loss_rate": {},
        }
        for c in candidates:
            if c.get("candidate_stale_exit"):
                metrics["candidates"]["stale_exit"] += 1
            if c.get("candidate_trailing_stop"):
                metrics["candidates"]["trailing_stop"] += 1
            if c.get("candidate_profit_target"):
                metrics["candidates"]["profit_target"] += 1

    out_json.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    md_lines = [
        "# Exit edge metrics",
        "",
        f"- **Exits in window:** {metrics.get('n_exits', 0)}",
        f"- **Baseline total PnL:** {metrics.get('baseline', {}).get('total_pnl', 'N/A')}",
        "",
        "## Candidates (replay)",
        f"- Stale exit: {metrics.get('candidates', {}).get('stale_exit', 0)}",
        f"- Trailing stop: {metrics.get('candidates', {}).get('trailing_stop', 0)}",
        f"- Profit target: {metrics.get('candidates', {}).get('profit_target', 0)}",
    ]
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_json} and {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
