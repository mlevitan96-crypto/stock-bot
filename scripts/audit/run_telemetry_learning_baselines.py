#!/usr/bin/env python3
"""
Emit baseline JSON for Alpaca strict gate for learning-readiness closure.
Telemetry-only; no strategy changes.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--ts",
        default=datetime.now(timezone.utc).strftime("%Y%m%d_%H%MZ"),
        help="Artifact timestamp suffix (default: current UTC)",
    )
    args = ap.parse_args()
    ts = args.ts
    root = REPO
    alpaca = evaluate_completeness(root, open_ts_epoch=STRICT_EPOCH_START, audit=True)

    (REPO / f"reports/ALPACA_BASELINE_{ts}.json").write_text(
        json.dumps({"ts_utc": ts, "root": str(root), "strict": alpaca}, indent=2),
        encoding="utf-8",
    )

    # Short markdown summaries
    a_md = REPO / f"reports/audit/ALPACA_BASELINE_{ts}.md"
    a_md.parent.mkdir(parents=True, exist_ok=True)
    a_md.write_text(
        f"""# Alpaca baseline — learning telemetry ({ts})

## Command (local workspace)

`PYTHONPATH=. python telemetry/alpaca_strict_completeness_gate.py --root . --audit --open-ts-epoch {STRICT_EPOCH_START}`

## Headline metrics

| Field | Value |
|------|-------|
| LEARNING_STATUS | {alpaca.get("LEARNING_STATUS")} |
| trades_seen | {alpaca.get("trades_seen")} |
| trades_incomplete | {alpaca.get("trades_incomplete")} |
| precheck | {alpaca.get("precheck")} |

## Machine JSON

`reports/ALPACA_BASELINE_{ts}.json`
""",
        encoding="utf-8",
    )

    print(json.dumps({"ts": ts, "alpaca_json": f"reports/ALPACA_BASELINE_{ts}.json"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
