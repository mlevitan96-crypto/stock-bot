#!/usr/bin/env python3
"""One-off runner for SSH / cron; strict completeness at STRICT_EPOCH_START."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)

r = evaluate_completeness(ROOT, open_ts_epoch=STRICT_EPOCH_START, audit=False)
keys = (
    "LEARNING_STATUS",
    "learning_fail_closed_reason",
    "trades_seen",
    "trades_complete",
    "trades_incomplete",
    "reason_histogram",
)
print(json.dumps({k: r[k] for k in keys if k in r}, indent=2))
