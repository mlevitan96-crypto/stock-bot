#!/usr/bin/env python3
"""
Export strict-scope cohort metadata for MASSIVE QUANT EDGE REVIEW (Workstream A).

Reconciles to telemetry.alpaca_strict_completeness_gate.evaluate_completeness:
  len(strict_cohort_trade_ids) must equal trades_seen (same root + open_ts_epoch + flags).

Does not fabricate trade_facts rows — emits cohort IDs + gate summary for downstream joins.

Usage:
  PYTHONPATH=. python3 scripts/audit/export_strict_quant_edge_review_cohort.py --root /root/stock-bot \\
    --open-ts-epoch 1774458080 --out-json reports/ALPACA_STRICT_QUANT_EDGE_COHORT.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export strict cohort trade IDs for quant edge review")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--open-ts-epoch",
        type=float,
        default=None,
        help="UTC epoch floor for exit_attribution cohort (default: STRICT_EPOCH_START)",
    )
    ap.add_argument("--out-json", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    open_ts = float(args.open_ts_epoch) if args.open_ts_epoch is not None else float(STRICT_EPOCH_START)

    r = evaluate_completeness(
        root,
        open_ts_epoch=open_ts,
        audit=False,
        collect_strict_cohort_trade_ids=True,
        collect_complete_trade_ids=True,
    )
    ids = r.get("strict_cohort_trade_ids") or []
    complete = r.get("complete_trade_ids") or []
    seen = int(r.get("trades_seen") or 0)
    cmp_n = int(r.get("trades_complete") or 0)

    recon_ok = len(ids) == seen
    complete_ok = len(complete) == cmp_n

    out = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "open_ts_epoch": open_ts,
        "LEARNING_STATUS": r.get("LEARNING_STATUS"),
        "trades_seen": seen,
        "trades_complete": cmp_n,
        "trades_incomplete": r.get("trades_incomplete"),
        "strict_cohort_trade_id_count": len(ids),
        "complete_trade_id_count": len(complete),
        "reconciliation": {
            "strict_cohort_len_equals_trades_seen": recon_ok,
            "complete_len_equals_trades_complete": complete_ok,
        },
        "authoritative_join_key_rule": r.get("AUTHORITATIVE_JOIN_KEY_RULE"),
        "strict_cohort_trade_ids": ids,
        "complete_trade_ids": complete,
    }

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("strict_cohort_trade_ids", "complete_trade_ids")}, indent=2))
    print(f"strict_cohort_trade_ids: {len(ids)} rows (full list in --out-json if set)")
    print(f"complete_trade_ids: {len(complete)} rows")
    return 0 if recon_ok and complete_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
