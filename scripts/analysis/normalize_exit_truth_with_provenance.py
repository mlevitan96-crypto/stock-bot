#!/usr/bin/env python3
"""
Normalize harvested exit truth: canonical field names, provenance annotation.
Output: normalized_exit_truth.json (same shape as rebuild: window_*, count, exits) for replay.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="input_path", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    in_path = Path(args.input_path)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        out_path.write_text(json.dumps({
            "window_start": None,
            "window_end": None,
            "count": 0,
            "exits": [],
            "provenance": "normalize_exit_truth_with_provenance",
        }, indent=2, default=str), encoding="utf-8")
        print(f"Wrote 0 exits (no input) -> {out_path}")
        return 0

    data = json.loads(in_path.read_text(encoding="utf-8"))
    exits = data.get("exits", [])
    normalized = []
    for rec in exits:
        n = dict(rec)
        n["_provenance"] = {
            "source": rec.get("_source"),
            "path": rec.get("_path"),
            "normalized_utc": datetime.now(timezone.utc).isoformat(),
        }
        # Canonical field aliases for downstream
        if "exit_timestamp" not in n and n.get("ts"):
            n["exit_timestamp"] = n["ts"]
        if "close_reason" not in n and n.get("exit_reason"):
            n["close_reason"] = n["exit_reason"]
        normalized.append(n)

    out = {
        "window_start": data.get("window_start"),
        "window_end": data.get("window_end"),
        "count": len(normalized),
        "exits": normalized,
        "provenance": "normalize_exit_truth_with_provenance",
    }
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Normalized {len(normalized)} exits -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
