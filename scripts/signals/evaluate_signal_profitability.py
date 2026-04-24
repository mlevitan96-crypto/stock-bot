#!/usr/bin/env python3
"""
Evaluate signal profitability from weight sweeps.
--require-nonzero-delta: FAIL if no sweep has non-zero entry or exit delta.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate signal profitability from sweeps")
    ap.add_argument("--sweeps", required=True)
    ap.add_argument("--require-nonzero-delta", action="store_true", help="Exit non-zero if no sweep has real deltas")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.sweeps)
    if not path.exists():
        print(f"Sweeps missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    sweeps = data.get("sweeps", []) or []

    has_nonzero = False
    for s in sweeps:
        if not isinstance(s, dict):
            continue
        ed = s.get("entry_delta")
        xd = s.get("exit_delta")
        if (ed is not None and float(ed) != 0) or (xd is not None and float(xd) != 0):
            has_nonzero = True
            break
        # Stub sweeps may have entry_signals/exit_signals with weight_delta
        ed = (s.get("entry_signals") or {}).get("weight_delta")
        xd = (s.get("exit_signals") or {}).get("weight_delta")
        if (ed is not None and float(ed) != 0) or (xd is not None and float(xd) != 0):
            has_nonzero = True
            break

    if args.require_nonzero_delta and not has_nonzero:
        print("SIGNAL_PROFITABILITY: FAIL (no sweep with non-zero delta; use --mode real and deltas)", file=sys.stderr)
        return 3

    # Per-symbol or aggregate profitability (real: use delta info; stub: trade count)
    by_symbol = {}
    for s in sweeps:
        if isinstance(s, dict) and s.get("symbol"):
            key = s["symbol"]
            by_symbol[key] = by_symbol.get(key, 0) + 1
    profitability = [
        {"symbol": sym, "trade_count": n, "profitability_score": None}
        for sym, n in sorted(by_symbol.items(), key=lambda x: -x[1])[:50]
    ]

    out = {
        "date": data.get("date"),
        "profitability": profitability,
        "sweep_count": len(sweeps),
        "has_nonzero_delta": has_nonzero,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
