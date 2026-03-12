#!/usr/bin/env python3
"""
Analyze stability and drift of promotable configs over the history.
Computes rank_persistence, presence_days, volatility (if metrics available).
Read-only; shadow-only.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze promotion stability over history.")
    parser.add_argument("--history", required=True, help="PROMOTABLE_HISTORY_${END_DATE}.json path.")
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=["rank_persistence", "presence_days", "volatility"],
        help="Metrics to compute.",
    )
    parser.add_argument("--output", required=True, help="Output STABILITY_ANALYSIS_${END_DATE}.json path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    with open(root / args.history, encoding="utf-8") as f:
        history = json.load(f)

    # config_id -> list of (date, rank, metrics)
    by_config: dict[str, list[dict]] = defaultdict(list)
    for day in history.get("days", []):
        for e in day.get("entries", []):
            cid = e.get("config_id")
            if not cid:
                continue
            by_config[cid].append({
                "date": day["date"],
                "rank": e.get("rank"),
                "metrics": e.get("metrics") or {},
            })

    metrics_set = set(args.metrics)
    analysis = []
    for config_id, recs in by_config.items():
        ranks = [r["rank"] for r in recs if r.get("rank") is not None]
        presence_days = len(recs)
        avg_rank = sum(ranks) / len(ranks) if ranks else None
        rank_std = (sum((x - avg_rank) ** 2 for x in ranks) / len(ranks)) ** 0.5 if len(ranks) > 1 else 0.0

        # Volatility: std of stability metric if present, else rank std
        stabilities = [r.get("metrics", {}).get("stability") for r in recs]
        stabilities = [s for s in stabilities if s is not None]
        volatility = (sum((s - sum(stabilities) / len(stabilities)) ** 2 for s in stabilities) / len(stabilities)) ** 0.5 if len(stabilities) > 1 else (rank_std or 0.0)

        entry = {
            "config_id": config_id,
            "presence_days": presence_days,
            "rank_persistence": round(avg_rank, 4) if avg_rank is not None else None,
            "rank_volatility": round(rank_std, 4) if rank_std is not None else None,
            "volatility": round(volatility, 4),
        }
        analysis.append(entry)

    # Sort by rank_persistence (lower rank = better) then presence_days (more = better)
    analysis.sort(key=lambda x: (x.get("rank_persistence") or 999, -x.get("presence_days", 0)))

    out = {
        "history_path": args.history,
        "metrics_requested": args.metrics,
        "configs_analyzed": len(analysis),
        "analysis": analysis,
    }

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
