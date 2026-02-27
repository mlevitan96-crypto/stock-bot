#!/usr/bin/env python3
"""
Replay historical exits against candidate exit signals (stub: passes through with candidate columns).
Output: exit_replay_results.json for compute_exit_edge_metrics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical", required=True)
    ap.add_argument("--ctr_root", default=None, help="Optional; for CTR-based runs. Omit for legacy/historical harvest.")
    ap.add_argument("--config", default=None, help="Optional; exit_candidate_signals.tuned.json for config-only tuning rerun.")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    hist_path = Path(args.historical)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    config_used = None
    if args.config and Path(args.config).exists():
        try:
            config_used = json.loads(Path(args.config).read_text(encoding="utf-8"))
        except Exception:
            pass

    if not hist_path.exists():
        data = {"exits": [], "replay_candidates": [], "message": "No historical exits"}
    else:
        data = json.loads(hist_path.read_text(encoding="utf-8"))
        exits = data.get("exits", [])
        replay_candidates = []
        for rec in exits:
            replay_candidates.append({
                **rec,
                "candidate_stale_exit": rec.get("decision") == "CLOSE" and rec.get("close_reason", "").startswith("stale"),
                "candidate_trailing_stop": "trailing" in (rec.get("close_reason") or "").lower(),
                "candidate_profit_target": "profit" in (rec.get("close_reason") or "").lower() or "tp" in (rec.get("close_reason") or "").lower(),
            })
        data = {"exits": exits, "replay_candidates": replay_candidates, "count": len(exits)}

    if config_used is not None:
        data["exit_signal_config_used"] = config_used.get("candidate_signals") or config_used

    out_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"Wrote replay results to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
