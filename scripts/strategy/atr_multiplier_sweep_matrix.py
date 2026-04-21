#!/usr/bin/env python3
"""
Parameter sweep helper for ``DYNAMIC_ATR_MULTIPLIER`` (e.g. 1.5 vs 2.0).

**Quant impact:** tighter multiplier (1.5) trails closer → faster profit lock but more whip stops;
looser (2.0) reduces noise exits at cost of deeper give-back. Use with replay or forward paper
segments to compare expectancy and tail loss.

Does not run backtests; prints env lines and a comparison matrix for operators / droplet overlays.

Usage:
  python scripts/strategy/atr_multiplier_sweep_matrix.py
  python scripts/strategy/atr_multiplier_sweep_matrix.py --mults 1.25,1.5,1.75,2.0,2.5
"""
from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser(description="DYNAMIC_ATR_MULTIPLIER sweep matrix (print-only).")
    ap.add_argument("--mults", type=str, default="1.5,2.0", help="Comma-separated multipliers to compare")
    args = ap.parse_args()
    mults = [float(x.strip()) for x in args.mults.split(",") if x.strip()]
    print("# Set one at a time on paper/replay host, then compare exit_attribution / PnL cohorts")
    print("# Required: DYNAMIC_ATR_EXITS_ENABLED=1")
    print()
    for m in mults:
        print(f"export DYNAMIC_ATR_MULTIPLIER={m}")
    print()
    print("matrix:")
    print("  mult | stop_distance_vs_atr | noise_stop_risk | tail_giveback_risk")
    for m in mults:
        print(
            f"  {m:>4} | {m}xATR from HH/entry     | "
            f"{'higher' if m < 2.0 else 'baseline' if abs(m - 2.0) < 0.01 else 'lower'} | "
            f"{'lower' if m < 2.0 else 'baseline' if abs(m - 2.0) < 0.01 else 'higher'}"
        )


if __name__ == "__main__":
    main()
