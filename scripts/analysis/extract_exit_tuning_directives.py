#!/usr/bin/env python3
"""
Extract tuning directives from a prior exit review run (BOARD_DECISION, edge metrics, board review).
Output: tuning_directives.json for apply_exit_signal_tuning.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev_run", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    prev = Path(args.prev_run)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    directives = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "prev_run": str(prev),
        "decision": None,
        "edge_summary": {},
        "directives": [],
    }

    board_path = prev / "BOARD_DECISION.json"
    if board_path.exists():
        try:
            board = json.loads(board_path.read_text(encoding="utf-8"))
            directives["decision"] = board.get("decision")
            directives["rationale"] = board.get("rationale")
        except Exception:
            pass

    edge_path = prev / "exit_edge_metrics.json"
    if edge_path.exists():
        try:
            edge = json.loads(edge_path.read_text(encoding="utf-8"))
            directives["edge_summary"] = {
                "n_exits": edge.get("n_exits"),
                "baseline_total_pnl": edge.get("baseline", {}).get("total_pnl"),
                "candidates": edge.get("candidates", {}),
            }
        except Exception:
            pass

    if directives["decision"] == "TUNE":
        directives["directives"].append("Consider tightening trailing_stop or profit_target thresholds if giveback is high.")
        directives["directives"].append("Consider relaxing stale_exit threshold if exits are too early.")
    elif directives["decision"] == "HOLD":
        directives["directives"].append("No config change recommended; retain current candidate signal config.")

    out_path.write_text(json.dumps(directives, indent=2, default=str), encoding="utf-8")
    print(f"Wrote tuning directives -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
