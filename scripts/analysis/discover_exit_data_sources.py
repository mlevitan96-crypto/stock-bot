#!/usr/bin/env python3
"""
Discover legacy exit-relevant data sources under repo (logs/, state/, reports/).
Output: exit_data_sources.json listing paths and types for harvest.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    repo = Path(args.repo)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sources = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repo": str(repo),
        "streams": [],
    }

    candidates = [
        ("logs/exit_attribution.jsonl", "exit_attribution", "jsonl"),
        ("logs/exit_truth.jsonl", "exit_truth", "jsonl"),
        ("logs/attribution.jsonl", "attribution", "jsonl"),
        ("logs/run.jsonl", "run", "jsonl"),
        ("logs/exits.jsonl", "exits", "jsonl"),
    ]
    for rel, name, fmt in candidates:
        path = repo / rel
        if path.exists():
            try:
                size = path.stat().st_size
                mtime = path.stat().st_mtime
            except Exception:
                size = mtime = None
            sources["streams"].append({
                "path": rel,
                "name": name,
                "format": fmt,
                "size_bytes": size,
                "mtime_epoch": mtime,
            })

    out_path.write_text(json.dumps(sources, indent=2, default=str), encoding="utf-8")
    print(f"Discovered {len(sources['streams'])} sources -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
