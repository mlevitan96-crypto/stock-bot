#!/usr/bin/env python3
"""
Operator epoch reset: archive ``logs/*.jsonl``, truncate them, write ``state/epoch_state.json``,
reset Telegram / checkpoint guard JSON under ``state/``.

Linux droplet: ``sudo systemctl restart stock-bot.service`` after this (not run from here).

Usage (repo root):
  python scripts/sre/alpaca_epoch_reset_bundle.py --root . --dry-run
  python scripts/sre/alpaca_epoch_reset_bundle.py --root . --execute
"""
from __future__ import annotations

import argparse
import json
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]


def _reset_milestone_files(root: Path, stamp: str, execute: bool) -> List[str]:
    """Clear Telegram milestone / checkpoint guard state (paths used by runner_core)."""
    paths = [
        root / "state" / "alpaca_milestone_250_state.json",
        root / "state" / "alpaca_10trade_harvester_sent.json",
        root / "state" / "alpaca_100trade_sent.json",
    ]
    arm = root / "state" / "alpaca_milestone_integrity_arm.json"
    log: List[str] = []
    for p in paths:
        if execute and p.is_file():
            bak = p.with_suffix(p.suffix + f".bak_{stamp}")
            bak.write_bytes(p.read_bytes())
            p.write_text("{}\n", encoding="utf-8")
            log.append(f"reset {p}")
        elif execute:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{}\n", encoding="utf-8")
            log.append(f"created_empty {p}")
        else:
            log.append(f"would_reset {p}")
    if execute and arm.is_file():
        bak = arm.with_suffix(arm.suffix + f".bak_{stamp}")
        bak.write_bytes(arm.read_bytes())
        arm.unlink()
        log.append(f"removed {arm}")
    elif not execute and arm.is_file():
        log.append(f"would_remove {arm}")
    return log


def _write_epoch_state(root: Path, stamp: str, execute: bool) -> str:
    path = root / "state" / "epoch_state.json"
    now = datetime.now(timezone.utc)
    body: Dict[str, Any] = {
        "epoch_id": f"v2_live_{stamp}",
        "started_at_utc": now.isoformat(),
        "fired_milestones": [],
        "notes": "alpaca_epoch_reset_bundle.py — Telegram milestone guards cleared separately",
    }
    if execute:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
    return str(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    logs_dir = root / "logs"
    arch_dir = root / "reports" / "archive"
    jsonl_files = sorted(logs_dir.glob("*.jsonl")) if logs_dir.is_dir() else []

    plan = {
        "stamp": stamp,
        "execute": bool(args.execute),
        "archive": str(arch_dir / f"logs_pre_v2_live_{stamp}.tar.gz"),
        "jsonl_count": len(jsonl_files),
        "epoch_state": str(root / "state" / "epoch_state.json"),
    }
    print(json.dumps(plan, indent=2))

    if not args.execute:
        print("Dry-run. Pass --execute to archive, truncate logs, reset milestone state, write epoch_state.json.", flush=True)
        for line in _reset_milestone_files(root, stamp, execute=False):
            print(line, flush=True)
        print(f"would_write {root / 'state' / 'epoch_state.json'}", flush=True)
        return 0

    arch_dir.mkdir(parents=True, exist_ok=True)
    arc_path = arch_dir / f"logs_pre_v2_live_{stamp}.tar.gz"
    if jsonl_files:
        with tarfile.open(arc_path, "w:gz") as tf:
            for p in jsonl_files:
                tf.add(p, arcname=f"logs/{p.name}")
        print(f"Archived -> {arc_path}", flush=True)
    for p in jsonl_files:
        p.write_bytes(b"")
        print(f"Truncated {p}", flush=True)

    for line in _reset_milestone_files(root, stamp, execute=True):
        print(line, flush=True)

    ep = _write_epoch_state(root, stamp, execute=True)
    print(f"Wrote {ep}", flush=True)
    print("Done. On droplet: sudo systemctl restart stock-bot.service", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
