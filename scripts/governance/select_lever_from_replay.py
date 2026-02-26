#!/usr/bin/env python3
"""
B4 — Feed replay candidates to ONLINE autopilot.
Read campaign_results.json (ranked_candidates), select top implementable lever (one at a time),
output overlay_config.json or recommendation compatible with apply_paper_overlay.
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
    ap.add_argument("--campaign-dir", type=Path, help="equity_replay_campaign_<ts> dir (has campaign_results.json)")
    ap.add_argument("--out", type=Path, help="Write overlay_config.json here")
    ap.add_argument("--run-tag", type=str, default="equity_governance_replay")
    args = ap.parse_args()

    if not args.campaign_dir or not (args.campaign_dir / "campaign_results.json").exists():
        print("No campaign dir or campaign_results.json", file=sys.stderr)
        return 1

    data = json.loads((args.campaign_dir / "campaign_results.json").read_text(encoding="utf-8"))
    ranked = data.get("ranked_candidates") or []

    # Pick top candidate that is implementable (entry or exit with known params)
    chosen = None
    for r in ranked:
        lever_type = r.get("lever_type")
        params = r.get("lever_params") or {}
        if lever_type == "entry" and "min_exec_score" in params:
            chosen = {"lever": "entry", "change": {"type": "entry_bump", "delta": round(params["min_exec_score"] - 2.5, 2)}}
            break
        if lever_type == "exit" and "flow_deterioration" in params:
            chosen = {"lever": "exit", "change": {"type": "single_exit_tweak", "strength": round(params["flow_deterioration"] - 0.22, 2)}}
            break

    if not chosen:
        print("No implementable replay candidate", file=sys.stderr)
        return 2

    overlay = {
        "run_tag": args.run_tag,
        "lever": chosen["lever"],
        "paper_only": True,
        "change": chosen["change"],
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(overlay, indent=2), encoding="utf-8")
        print("Wrote", args.out)
    else:
        print(json.dumps(overlay, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
