#!/usr/bin/env python3
"""
Verify that captured intelligence is sufficient for replay: canonical components
present, deltas at exit, and schema consistency.

Usage: python scripts/verify_intelligence_replay_readiness.py [--base-dir .]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

CANONICAL = [
    "premarket_direction", "postmarket_direction", "overnight_direction",
    "futures_direction", "volatility_direction", "breadth_direction",
    "sector_direction", "etf_flow_direction", "macro_direction", "uw_direction",
]


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
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    logs = base / "logs"

    issues = []
    ok = []

    # 1) direction_event has all canonical components in direction_components
    dir_path = logs / "direction_event.jsonl"
    if not dir_path.exists():
        issues.append("direction_event.jsonl missing")
    else:
        for r in _iter_jsonl(dir_path, limit=20):
            comps = r.get("direction_components") or {}
            missing = [c for c in CANONICAL if c not in comps]
            if missing:
                issues.append(f"direction_event missing components: {missing[:5]}")
                break
        else:
            ok.append("direction_event has canonical direction_components")

    # 2) exit direction_event metadata has intel_deltas
    if dir_path.exists():
        exit_events = [r for r in _iter_jsonl(dir_path, limit=30) if r.get("event_type") == "exit"]
        if exit_events:
            meta = exit_events[0].get("metadata") or {}
            if "intel_deltas" in meta:
                ok.append("exit direction_event has metadata.intel_deltas")
            else:
                issues.append("exit direction_event metadata missing intel_deltas")
        else:
            ok.append("no exit direction_events yet (skip intel_deltas check)")

    # 3) direction_intel_embed in exit_attribution has intel_deltas and canonical_direction_components
    attr_exit = logs / "exit_attribution.jsonl"
    if attr_exit.exists():
        for r in _iter_jsonl(attr_exit, limit=20):
            embed = r.get("direction_intel_embed") or {}
            if not embed:
                continue
            if "canonical_direction_components" in embed:
                ok.append("direction_intel_embed has canonical_direction_components")
            else:
                issues.append("direction_intel_embed missing canonical_direction_components")
            if "intel_deltas" in embed:
                ok.append("direction_intel_embed has intel_deltas")
            break
        else:
            issues.append("no exit_attribution record with direction_intel_embed")
    else:
        issues.append("exit_attribution.jsonl not found")

    for s in ok:
        print("OK:", s)
    for s in issues:
        print("ISSUE:", s)

    if issues:
        print("\nReplay readiness check FAILED.")
        return 1
    print("\nReplay readiness check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
