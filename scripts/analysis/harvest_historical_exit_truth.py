#!/usr/bin/env python3
"""
Harvest historical exit truth from legacy sources (discovered by discover_exit_data_sources).
Reads exit_attribution, exit_truth, attribution, etc.; filters by date window; outputs single JSON.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def _parse_ts(s) -> datetime | None:
    try:
        if s is None:
            return None
        s = str(s).strip()
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        if s.isdigit():
            return datetime.fromtimestamp(int(s) if len(s) < 11 else int(s) / 1000, tz=timezone.utc)
        return None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--start", default="2025-10-01")
    ap.add_argument("--end", default="2026-02-23")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sources_path = Path(args.sources)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    start_ts = datetime.fromisoformat(args.start.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
    end_ts = datetime.fromisoformat(args.end.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)

    if not sources_path.exists():
        out_path.write_text(json.dumps({
            "window_start": args.start,
            "window_end": args.end,
            "count": 0,
            "exits": [],
            "message": "No sources file",
        }, indent=2, default=str), encoding="utf-8")
        print(f"Wrote 0 exits (no sources) -> {out_path}")
        return 0

    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    repo = Path(sources.get("repo", "."))
    streams = sources.get("streams", [])
    records = []

    for stream in streams:
        path = repo / stream["path"]
        if not path.exists():
            continue
        name = stream.get("name", path.stem)
        for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            ts_val = rec.get("ts") or rec.get("ts_iso") or rec.get("exit_timestamp") or rec.get("timestamp")
            if ts_val is None:
                continue
            dt = _parse_ts(ts_val)
            if dt and start_ts <= dt <= end_ts:
                rec["_source"] = name
                rec["_path"] = stream["path"]
                records.append(rec)

    records.sort(key=lambda r: (r.get("ts") or r.get("ts_iso") or r.get("exit_timestamp") or ""))
    out = {
        "window_start": args.start,
        "window_end": args.end,
        "count": len(records),
        "exits": records,
    }
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Harvested {len(records)} exits -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
