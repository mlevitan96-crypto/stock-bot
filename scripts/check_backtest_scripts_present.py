#!/usr/bin/env python3
"""
Check that all required backtest orchestration scripts and configs exist.
Exit 0 if all present; exit 1 and write ERROR_MISSING_SCRIPTS.md to out_dir if any missing.
Usage: python scripts/check_backtest_scripts_present.py [--out-dir reports/backtests/<RUN_ID>]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

REQUIRED = [
    "scripts/run_alpaca_backtest_orchestration_on_droplet.sh",
    "scripts/prep_alpaca_bars_snapshot.py",
    "scripts/run_simulation_backtest_on_droplet.py",
    "scripts/run_event_studies_on_droplet.py",
    "scripts/run_backtest_on_droplet.py",
    "scripts/param_sweep_orchestrator.py",
    "scripts/run_adversarial_tests_on_droplet.py",
    "scripts/multi_model_runner.py",
    "scripts/run_exit_optimization_on_droplet.py",
    "scripts/generate_backtest_summary.py",
    "scripts/run_governance_full.py",
    "scripts/backtest_governance_check.py",
    "configs/backtest_config.json",
    # configs/param_grid.json optional; orchestration step 6 creates it if missing
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=None, help="Write ERROR_MISSING_SCRIPTS.md here if any missing")
    args = ap.parse_args()
    missing = [p for p in REQUIRED if not (REPO / p).exists()]
    if not missing:
        print("All required scripts and configs present.")
        return 0
    lines = [
        "# ERROR: Missing scripts or configs",
        "",
        "The following required files are missing:",
        "",
    ]
    for p in missing:
        lines.append(f"- `{p}`")
    lines.extend(["", "Create or restore these files before running the backtest orchestration.", ""])
    if args.out_dir:
        out = Path(args.out_dir)
        if not out.is_absolute():
            out = REPO / out
        out.mkdir(parents=True, exist_ok=True)
        (out / "ERROR_MISSING_SCRIPTS.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {out / 'ERROR_MISSING_SCRIPTS.md'}")
    else:
        print("\n".join(lines))
    return 1


if __name__ == "__main__":
    sys.exit(main())
