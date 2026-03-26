#!/usr/bin/env python3
"""
Replay lab (additive): run Alpaca strict completeness gate against an isolated workspace tree.

Usage:
  PYTHONPATH=. python scripts/audit/alpaca_replay_lab_strict_gate.py --workspace artifacts/alpaca_replay_lab_smoke/logs

The workspace should contain the same relative paths the gate expects under a ``logs/`` directory
(i.e. pass --workspace pointing at the **repo root** that contains ``logs/``, or a copy of that layout).

This does not mutate source logs unless you pass --init-snapshot (copies listed jsonl from --source-root).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--workspace",
        type=Path,
        default=REPO / "artifacts" / "alpaca_replay_lab_default",
        help="Directory treated as bot root (must contain logs/...)",
    )
    ap.add_argument(
        "--source-root",
        type=Path,
        default=REPO,
        help="Repo root to copy logs from when --init-snapshot",
    )
    ap.add_argument("--init-snapshot", action="store_true", help="Copy jsonl logs into workspace")
    ap.add_argument("--open-ts-epoch", type=float, required=True)
    ap.add_argument("--audit", action="store_true")
    ap.add_argument(
        "--ts",
        default=None,
        help="Output report suffix ALPACA_REPLAY_LAB_GATE_<ts>.json (default: now UTC)",
    )
    args = ap.parse_args()

    sys.path.insert(0, str(REPO))
    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    ws: Path = args.workspace.resolve()
    if args.init_snapshot:
        src_logs = args.source_root.resolve() / "logs"
        dst_logs = ws / "logs"
        dst_logs.mkdir(parents=True, exist_ok=True)
        for name in (
            "exit_attribution.jsonl",
            "run.jsonl",
            "alpaca_unified_events.jsonl",
            "orders.jsonl",
            "alpaca_entry_attribution.jsonl",
            "alpaca_exit_attribution.jsonl",
            "alpaca_emit_failures.jsonl",
        ):
            p = src_logs / name
            if p.is_file():
                shutil.copy2(p, dst_logs / name)

    r = evaluate_completeness(ws, open_ts_epoch=args.open_ts_epoch, audit=args.audit)
    ts = args.ts or datetime.now(timezone.utc).strftime("%Y%m%d_%H%MZ")
    out_json = REPO / "reports" / f"ALPACA_REPLAY_LAB_GATE_{ts}.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "workspace": str(ws),
                "open_ts_epoch": args.open_ts_epoch,
                "init_snapshot": args.init_snapshot,
                "gate": r,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"written": str(out_json), "LEARNING_STATUS": r.get("LEARNING_STATUS")}, indent=2))
    return 0 if r.get("trades_incomplete", 1) == 0 and r.get("trades_seen", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
