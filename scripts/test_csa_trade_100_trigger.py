#!/usr/bin/env python3
"""
Test harness for CSA every-100-trades trigger.
Resets TRADE_CSA_STATE and trade_events.jsonl, simulates 105 trade events via record_trade_event,
then asserts: total_trade_events==105, CSA ran exactly once at 100, artifacts exist, last_csa_trade_count==100.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# Use a test state dir so we don't overwrite production state
os.environ["TRADE_CSA_STATE_DIR"] = str(REPO / "reports" / "state" / "test_csa_100")
STATE_DIR = Path(os.environ["TRADE_CSA_STATE_DIR"])
STATE_FILE = STATE_DIR / "TRADE_CSA_STATE.json"
EVENT_LOG = STATE_DIR / "trade_events.jsonl"
AUDIT_DIR = REPO / "reports" / "audit"
BOARD_DIR = REPO / "reports" / "board"


def reset_test_state() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "total_trade_events": 0,
        "last_csa_trade_count": 0,
        "last_csa_mission_id": "",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    if EVENT_LOG.exists():
        EVENT_LOG.unlink()


def main() -> int:
    from src.infra.csa_trade_state import (
        load_state,
        record_trade_event,
        get_trade_event_count_from_log,
    )
    reset_test_state()
    # Simulate 105 events; CSA runs synchronously at 100 so artifacts are created
    for _ in range(105):
        record_trade_event("executed", _run_csa_in_background=False)

    state = load_state()
    errors = []
    if state["total_trade_events"] != 105:
        errors.append(f"total_trade_events expected 105, got {state['total_trade_events']}")
    if state["last_csa_trade_count"] != 100:
        errors.append(f"last_csa_trade_count expected 100, got {state['last_csa_trade_count']}")
    if not state.get("last_csa_mission_id", "").startswith("CSA_TRADE_100_"):
        errors.append(f"last_csa_mission_id missing or wrong: {state.get('last_csa_mission_id')}")
    log_count = get_trade_event_count_from_log()
    if log_count != 105:
        errors.append(f"event log line count expected 105, got {log_count}")

    # Check artifacts (they may be under reports/audit and reports/board; mission_id in state)
    mission_id = state.get("last_csa_mission_id", "")
    verdict_path = AUDIT_DIR / f"CSA_VERDICT_{mission_id}.json"
    findings_path = AUDIT_DIR / f"CSA_FINDINGS_{mission_id}.md"
    board_reports = list(BOARD_DIR.glob("CSA_TRADE_100_*.md")) if BOARD_DIR.exists() else []
    if not verdict_path.exists():
        errors.append(f"CSA_VERDICT_{mission_id}.json not found at {verdict_path}")
    if not findings_path.exists():
        errors.append(f"CSA_FINDINGS_{mission_id}.md not found at {findings_path}")
    if not board_reports:
        errors.append("No reports/board/CSA_TRADE_100_*.md board report found")

    if errors:
        print("FAIL:", "; ".join(errors), file=sys.stderr)
        return 1
    print("OK: total_trade_events=105, CSA ran at 100, artifacts present, last_csa_trade_count=100")
    return 0


if __name__ == "__main__":
    sys.exit(main())
