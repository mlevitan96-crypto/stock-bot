#!/usr/bin/env python3
"""
Write ``config/strict_completeness_quarantine.json`` from current incomplete_trade_ids_all.

Usage (droplet):
  PYTHONPATH=. python3 scripts/audit/materialize_strict_quarantine.py --root /root/stock-bot --enable

  ``--open-ts-epoch`` defaults to ``STRICT_EPOCH_START`` from ``telemetry.alpaca_strict_completeness_gate``.

When not --dry-run, merges with existing file (preserves manual ids unless --replace).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--open-ts-epoch",
        type=float,
        default=None,
        help=f"UTC epoch for evaluate_completeness window (default: STRICT_EPOCH_START = {STRICT_EPOCH_START})",
    )
    ap.add_argument("--enable", action="store_true", help="Set enabled true in output JSON")
    ap.add_argument("--dry-run", action="store_true", help="Print JSON only; do not write")
    ap.add_argument("--replace", action="store_true", help="Replace trade_ids entirely (no merge)")
    args = ap.parse_args()
    root = args.root.resolve()
    open_ts = float(args.open_ts_epoch) if args.open_ts_epoch is not None else float(STRICT_EPOCH_START)
    r = evaluate_completeness(root, open_ts_epoch=open_ts, audit=True)
    ids = list(r.get("incomplete_trade_ids_all") or [])
    out_path = root / "config" / "strict_completeness_quarantine.json"
    prev: dict = {}
    if out_path.is_file():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    merged_ids: list = []
    if args.replace or not isinstance(prev.get("trade_ids"), list):
        merged_ids = ids
    else:
        seen = set(str(x) for x in prev.get("trade_ids") or [])
        merged_ids = list(prev.get("trade_ids") or [])
        for x in ids:
            s = str(x).strip()
            if s and s not in seen:
                seen.add(s)
                merged_ids.append(s)
    payload = {
        "version": int(prev.get("version") or 1),
        "enabled": bool(args.enable),
        "reason": prev.get("reason")
        or "Materialized from evaluate_completeness incomplete_trade_ids_all; SRE sign-off required to enable.",
        "trade_ids": merged_ids,
        "materialized_from_open_ts_epoch": open_ts,
        "source_snapshot": {
            "LEARNING_STATUS": r.get("LEARNING_STATUS"),
            "trades_seen": r.get("trades_seen"),
            "trades_incomplete": r.get("trades_incomplete"),
        },
    }
    txt = json.dumps(payload, indent=2) + "\n"
    print(txt)
    if args.dry_run:
        return 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(txt, encoding="utf-8")
    print("Wrote", out_path, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
