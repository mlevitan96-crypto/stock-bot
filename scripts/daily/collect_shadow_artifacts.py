#!/usr/bin/env python3
"""
Collect shadow artifacts for a given date and write an index JSON.
Used by the daily governance review checkpoint (read-only, shadow-only).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect shadow artifacts for daily review.")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD).")
    parser.add_argument(
        "--required",
        nargs="+",
        default=[],
        help="Required artifact paths (relative to cwd).",
    )
    parser.add_argument("--output", required=True, help="Output index JSON path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    index: dict = {
        "date": args.date,
        "artifacts": [],
        "all_present": True,
    }

    for path_str in args.required:
        path = root / path_str
        present = path.exists()
        index["artifacts"].append({
            "path": path_str,
            "resolved": str(path.resolve()) if path.exists() else None,
            "present": present,
        })
        if not present:
            index["all_present"] = False

    if not index["all_present"]:
        missing = [a["path"] for a in index["artifacts"] if not a["present"]]
        raise SystemExit(f"Missing required artifacts: {missing}")

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
