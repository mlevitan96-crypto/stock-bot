#!/usr/bin/env python3
"""
Emit baseline JSON for Alpaca strict gate (+ Kraken inventory stub) for learning-readiness closure.
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

    kraken = {
        "venue": "kraken",
        "kraken_data_telegram_certification_suite_py": None,
        "strict_tail_gate_in_repo": False,
        "milestone_telegram_script_in_repo": False,
        "note": (
            "No kraken_data_telegram_certification_suite.py found in repository; "
            "Kraken path is downloader + shell massive review only (see scripts/run_kraken_on_droplet.py)."
        ),
        "evidence_ts_utc": datetime.now(timezone.utc).isoformat(),
    }

    (REPO / f"reports/ALPACA_BASELINE_{ts}.json").write_text(
        json.dumps({"ts_utc": ts, "root": str(root), "strict": alpaca}, indent=2),
        encoding="utf-8",
    )
    (REPO / f"reports/KRAKEN_BASELINE_{ts}.json").write_text(
        json.dumps(kraken, indent=2),
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

    k_md = REPO / f"reports/audit/KRAKEN_BASELINE_{ts}.md"
    k_md.write_text(
        f"""# Kraken baseline — learning telemetry ({ts})

## Status

**No runnable Kraken strict-tail / Telegram certification suite** is present in this repository under the mission name. Baseline JSON is an explicit **inventory negative**.

## Machine JSON

`reports/KRAKEN_BASELINE_{ts}.json`
""",
        encoding="utf-8",
    )

    print(json.dumps({"ts": ts, "alpaca_json": f"reports/ALPACA_BASELINE_{ts}.json"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
