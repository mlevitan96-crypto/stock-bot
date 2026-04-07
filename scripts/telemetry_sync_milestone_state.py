#!/usr/bin/env python3
"""
Write data/.milestone_state.json for telemetry_milestone_watcher.py after a Harvester sync.

Default: mark 10-trade SPI checkpoint as sent at current canonical trade count; clear OOS 100/250
sent flags; set meta cutoff to STRICT_EPOCH_START.

Does not touch trading logic.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE_PATH = REPO / "data" / ".milestone_state.json"


def main() -> int:
    sys.path.insert(0, str(REPO))
    from src.governance.canonical_trade_count import compute_canonical_trade_count
    from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START

    n = int(
        compute_canonical_trade_count(REPO, floor_epoch=float(STRICT_EPOCH_START)).get(
            "total_trades_post_era", 0
        )
    )
    floor_iso = datetime.fromtimestamp(float(STRICT_EPOCH_START), tz=timezone.utc).isoformat()
    now = datetime.now(timezone.utc).isoformat()

    data = {
        "milestones_sent": {
            "10_trade_checkpoint_passed": {
                "sent_at": now,
                "trade_count": n,
            },
        },
        "meta": {
            "harvester_count_floor_utc": floor_iso,
            "cutoff_utc": floor_iso,
            "last_run_utc": now,
            "last_trade_count_since_cutoff": n,
            "patched_by": "telemetry_sync_milestone_state.py",
        },
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(STATE_PATH)
    print(f"Wrote {STATE_PATH} trade_count={n} floor={floor_iso}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
