#!/usr/bin/env python3
"""
Merge cluster risk / recommendations over the history date range.
Read-only; shadow-only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge cluster risk over time.")
    parser.add_argument("--history", required=True, help="PROMOTABLE_HISTORY_${END_DATE}.json path.")
    parser.add_argument("--cluster-dir", default="reports/shadow/clusters", help="Directory with CLUSTER_RECOMMENDATIONS_${date}.json.")
    parser.add_argument("--output", required=True, help="Output CLUSTER_RISK_OVER_TIME_${END_DATE}.json path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    with open(root / args.history, encoding="utf-8") as f:
        history = json.load(f)
    cluster_dir = root / args.cluster_dir

    by_date = []
    for day in history.get("days", []):
        date_str = day.get("date", "")
        path = cluster_dir / f"CLUSTER_RECOMMENDATIONS_{date_str}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            by_date.append({
                "date": date_str,
                "recommendations": data.get("recommendations", []),
                "scope": data.get("scope", "shadow_only"),
            })

    out = {
        "history_path": args.history,
        "cluster_dir": str(cluster_dir.relative_to(root)),
        "days_with_clusters": len(by_date),
        "by_date": by_date,
    }

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
