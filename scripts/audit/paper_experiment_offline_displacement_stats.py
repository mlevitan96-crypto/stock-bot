#!/usr/bin/env python3
"""Offline paper metric: displacement_blocked subset stats from BLOCKED_COUNTERFACTUAL_PNL_FULL.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO
    p = root / "reports" / "daily" / "2026-04-01" / "evidence" / "BLOCKED_COUNTERFACTUAL_PNL_FULL.json"
    if not p.is_file():
        print("missing", p, file=sys.stderr)
        return 1
    d = json.loads(p.read_text(encoding="utf-8"))
    rows = [
        x
        for x in d["per_row"]
        if x.get("coverage") and x.get("block_reason") == "displacement_blocked"
    ]
    pos = sum(1 for x in rows if x.get("pnl_variant_a_usd", {}).get("pnl_60m", 0) > 0)
    out = {
        "lever": "offline_counterfactual_only_displacement_blocked",
        "n_covered": len(rows),
        "n_positive_pnl_60m_variant_a": pos,
        "share_positive": round(pos / len(rows), 6) if rows else 0.0,
        "mean_score": round(
            sum(float(x["score"]) for x in rows if x.get("score") is not None)
            / max(1, sum(1 for x in rows if x.get("score") is not None)),
            6,
        )
        if rows
        else None,
    }
    print(json.dumps(out, indent=2))
    dest = root / "reports" / "daily" / "2026-04-01" / "evidence" / "PAPER_EXPERIMENT_RESULTS.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
