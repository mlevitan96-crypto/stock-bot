#!/usr/bin/env python3
"""
One-off SRE repair: append canonical_trade_id_resolved so strict gate aliases
mis-typed displacement preflight keys to broker-truth fill keys.

Safe to re-run only if the edge is missing (idempotent-ish: duplicate edges still expand aliases).

Usage (droplet):
  cd /root/stock-bot && PYTHONPATH=/root/stock-bot python3 scripts/_tmp_nvda_bridge_repair.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/root/stock-bot", help="Repo root (contains logs/run.jsonl)")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    run_path = root / "logs" / "run.jsonl"
    if not run_path.is_file():
        print(f"ERROR: missing {run_path}", flush=True)
        return 2
    ev = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": "canonical_trade_id_resolved",
        "symbol": "NVDA",
        # Strict gate indexes intent -> fill (undirected expansion).
        "canonical_trade_id_intent": "NVDA|SHORT|1776271357",
        "canonical_trade_id_fill": "NVDA|LONG|1776267830",
        "close_truth_chain_reason": "sre_displacement_bridge_repair",
        "resolution_reason": "sre_displacement_bridge_repair",
    }
    line = json.dumps(ev, separators=(",", ":")) + "\n"
    with open(run_path, "a", encoding="utf-8") as f:
        f.write(line)
    print("appended:", line.strip(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
