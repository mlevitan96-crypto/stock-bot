#!/usr/bin/env python3
"""
Signal system expansion: explode entry/exit signal weights from ledger.
Mode 'local' (stub): minimal sweep schema. Mode 'real': apply weight deltas for perturbations.
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import product
from pathlib import Path


def _parse_deltas(s: str) -> list[float]:
    return [float(x.strip()) for x in (s or "").split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Explode signal weights from ledger")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--mode", default="local", choices=["local", "real"], help="real = weight deltas; local = stub")
    ap.add_argument("--include-entry-signals", action="store_true", default=True)
    ap.add_argument("--include-exit-signals", action="store_true", default=True)
    ap.add_argument("--entry-weight-deltas", default="-0.3,-0.2,-0.1,0.1,0.2,0.3", help="Comma-separated; used when mode=real")
    ap.add_argument("--exit-weight-deltas", default="-0.3,-0.2,-0.1,0.1,0.2,0.3", help="Comma-separated; used when mode=real")
    ap.add_argument("--weight-sweep-mode", default="local")
    ap.add_argument("--emit-interactions", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.ledger)
    if not path.exists():
        print(f"Ledger missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    executed = data.get("executed", []) or []

    if args.mode == "real":
        entry_deltas = _parse_deltas(args.entry_weight_deltas)
        exit_deltas = _parse_deltas(args.exit_weight_deltas)
        if not entry_deltas or not exit_deltas:
            print("Need at least one entry and one exit delta", file=sys.stderr)
            return 2
        # One sweep per (symbol, entry_delta, exit_delta); cap total
        seen_symbols = set()
        sweeps = []
        for e in executed:
            if not isinstance(e, dict):
                continue
            sym = e.get("symbol")
            if not sym or sym in seen_symbols:
                continue
            seen_symbols.add(sym)
            for (ed, xd) in product(entry_deltas, exit_deltas):
                sweeps.append({
                    "symbol": sym,
                    "entry_delta": ed,
                    "exit_delta": xd,
                    "entry_signals": {"weight_delta": ed},
                    "exit_signals": {"weight_delta": xd},
                    "weight_sweep_mode": "real",
                    "interactions": [] if not args.emit_interactions else [{"entry_delta": ed, "exit_delta": xd}],
                })
            if len(sweeps) >= 500:
                break
    else:
        # Stub: one sweep per executed trade (symbol + placeholder weights)
        sweeps = []
        for e in executed[:500] if executed else []:
            if isinstance(e, dict):
                sweeps.append({
                    "symbol": e.get("symbol"),
                    "entry_signals": {},
                    "exit_signals": {},
                    "weight_sweep_mode": args.weight_sweep_mode,
                    "interactions": [],
                })

    out = {
        "date": data.get("date"),
        "weight_sweep_mode": args.mode,
        "sweeps": sweeps,
        "count": len(sweeps),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, "sweeps:", len(sweeps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
