#!/usr/bin/env python3
"""
Verify that directional intelligence is being captured: intel_snapshot_entry/exit,
direction_event.jsonl, and direction_intel_embed in exit_attribution/exit_event.

Usage: python scripts/verify_intelligence_capture.py [--base-dir .] [--last 50]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _iter_jsonl(path: Path, limit: int | None = None):
    if not path.exists():
        return
    n = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
            n += 1
            if limit is not None and n >= limit:
                return
        except json.JSONDecodeError:
            continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default="", help="Repo root")
    ap.add_argument("--last", type=int, default=50, help="Last N records to check")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    logs = base / "logs"
    last_n = max(1, args.last)

    issues = []
    ok = []

    # 1) intel_snapshot_entry.jsonl
    entry_path = logs / "intel_snapshot_entry.jsonl"
    if entry_path.exists():
        recs = list(_iter_jsonl(entry_path, limit=last_n))
        ok.append(f"intel_snapshot_entry: {len(recs)} record(s)")
        for r in recs[:3]:
            if "premarket_intel" not in r and "timestamp" not in r:
                issues.append("intel_snapshot_entry missing premarket_intel or timestamp")
                break
    else:
        issues.append("intel_snapshot_entry.jsonl not found (capture may not have run yet)")

    # 2) intel_snapshot_exit.jsonl
    exit_path = logs / "intel_snapshot_exit.jsonl"
    if exit_path.exists():
        recs = list(_iter_jsonl(exit_path, limit=last_n))
        ok.append(f"intel_snapshot_exit: {len(recs)} record(s)")
    else:
        issues.append("intel_snapshot_exit.jsonl not found")

    # 3) direction_event.jsonl
    dir_path = logs / "direction_event.jsonl"
    if dir_path.exists():
        recs = list(_iter_jsonl(dir_path, limit=last_n))
        ok.append(f"direction_event: {len(recs)} record(s)")
        for r in recs[:3]:
            if "direction_components" not in r:
                issues.append("direction_event missing direction_components")
                break
    else:
        issues.append("direction_event.jsonl not found")

    # 4) exit_attribution has direction_intel_embed
    attr_exit = logs / "exit_attribution.jsonl"
    if attr_exit.exists():
        recs_exit = list(_iter_jsonl(attr_exit, limit=last_n))
        with_embed = sum(1 for r in recs_exit if r.get("direction_intel_embed"))
        ok.append(f"exit_attribution with direction_intel_embed: {with_embed}/{len(recs_exit)}")
        if with_embed == 0 and last_n > 0:
            issues.append("no exit_attribution record has direction_intel_embed")
    else:
        issues.append("exit_attribution.jsonl not found")

    # 5) exit_event has direction_intel_embed
    evt_path = logs / "exit_event.jsonl"
    if evt_path.exists():
        recs_evt = list(_iter_jsonl(evt_path, limit=last_n))
        with_embed = sum(1 for r in recs_evt if r.get("direction_intel_embed"))
        ok.append(f"exit_event with direction_intel_embed: {with_embed}/{len(recs_evt)}")
    else:
        issues.append("exit_event.jsonl not found")

    # Report
    for s in ok:
        print("OK:", s)
    for s in issues:
        print("ISSUE:", s)

    if issues:
        print("\nVerification FAILED (see ISSUEs above).")
        return 1
    print("\nVerification PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
