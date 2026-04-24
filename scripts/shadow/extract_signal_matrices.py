#!/usr/bin/env python3
"""
Shadow: Extract signal matrices from backfilled ledgers (one row per trade, columns = signals).
Read-only; requires signal_vectors / normalized_scores in ledger. Outputs matrix + outcome column.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract signal matrices from backfilled ledgers")
    ap.add_argument("--ledger-dir", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ledger_dir = Path(args.ledger_dir)
    if not ledger_dir.exists():
        print(f"Ledger dir missing: {ledger_dir}", file=sys.stderr)
        return 2

    all_signal_names = set()
    rows = []
    for lp in sorted(ledger_dir.glob("FULL_TRADE_LEDGER_*.json")):
        data = _load_json(lp)
        executed = data.get("executed", []) or []
        for t in executed:
            if not isinstance(t, dict):
                continue
            row = {}
            # signal_vectors: list of {name, value}
            for sv in (t.get("signal_vectors") or []):
                if isinstance(sv, dict) and "name" in sv:
                    name = sv.get("name", "")
                    val = sv.get("value", 0)
                    row[f"sv_{name}"] = float(val)
                    all_signal_names.add(f"sv_{name}")
            # normalized_scores: dict
            for k, v in (t.get("normalized_scores") or {}).items():
                if isinstance(v, (int, float)):
                    row[f"ns_{k}"] = float(v)
                    all_signal_names.add(f"ns_{k}")
            pnl = float(t.get("realized_pnl") or 0)
            row["outcome"] = 1 if pnl > 0 else 0
            row["_trade_id"] = f"{t.get('symbol','')}_{t.get('entry_ts','')}"
            rows.append(row)
            all_signal_names.update(k for k in row if k not in ("outcome", "_trade_id"))

    all_signal_names.discard("outcome")
    all_signal_names.discard("_trade_id")
    signal_names = sorted(all_signal_names)
    matrix = []
    for r in rows:
        vec = [r.get(s, 0.0) for s in signal_names]
        matrix.append(vec)
    outcome = [r.get("outcome", 0) for r in rows]

    out = {
        "signal_names": signal_names,
        "matrix": matrix,
        "outcome": outcome,
        "n_trades": len(rows),
        "ledger_dir": str(ledger_dir.resolve()),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Signal matrices:", len(rows), "trades,", len(signal_names), "signals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
