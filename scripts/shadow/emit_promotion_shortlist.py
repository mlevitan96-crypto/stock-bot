#!/usr/bin/env python3
"""
Shadow: Emit promotion shortlist from ranking (no auto-promotion).
Candidates feed into the daily promotion loop; human/CSA selects one at a time.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit promotion shortlist from ranking")
    ap.add_argument("--ranking", required=True)
    ap.add_argument("--method", default=None, help="e.g. true_replay_rescore")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.ranking)
    if not path.exists():
        print(f"Ranking missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    ranking = data.get("ranking", [])

    shortlist = []
    for r in ranking:
        shortlist.append({
            "rank": r.get("rank"),
            "config_id": r.get("config_id"),
            "config": r.get("config"),
            "metrics": r.get("metrics"),
        })

    out = {
        "ranking_path": str(path.resolve()),
        "shortlist": shortlist,
        "note": "For daily promotion loop; no auto-promotion. One candidate at a time.",
    }
    if args.method:
        out["method"] = args.method
        out["promotable"] = args.method == "true_replay_rescore"

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Shortlist:", len(shortlist), "candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
