#!/usr/bin/env python3
"""
Write backtests/config/30d_backtest_config.json for the full 30-day backtest (droplet).
Run from repo root. Creates config with start_date, end_date (last 30 days), and feature flags.
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "backtests" / "config"
CONFIG_PATH = CONFIG_DIR / "30d_backtest_config.json"


def main() -> int:
    end = date.today()
    start = end - timedelta(days=30)
    cfg = {
        "start_date": str(start),
        "end_date": str(end),
        "mode": "paper",
        "use_exit_regimes": True,
        "use_uw": True,
        "use_survivorship": True,
        "use_constraints": True,
        "use_correlation_sizing": True,
        "use_wheel_strategy": True,
        "log_all_candidates": True,
        "log_all_exits": True,
        "log_all_blocks": True,
    }
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("BACKTEST CONFIG WRITTEN:", json.dumps(cfg, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
