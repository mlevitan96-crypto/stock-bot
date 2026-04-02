#!/usr/bin/env python3
"""Smoke: paper caps module import, synthetic intents, JSONL path writable."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.paper.paper_cap_enforcement import (  # noqa: E402
    PaperCapReplayState,
    append_paper_cap_log,
    enforce_paper_caps,
    load_paper_caps_from_env,
    pretrade_key,
)


def main() -> int:
    os.environ["PAPER_CAPS_ENABLED"] = "1"
    os.environ["PAPER_CAP_FAIL_CLOSED"] = "1"
    os.environ["PAPER_CAP_MAX_GROSS_USD"] = "1000"
    os.environ["PAPER_CAP_MAX_NET_USD"] = "800"
    os.environ["PAPER_CAP_MAX_PER_SYMBOL_USD"] = "400"
    os.environ["PAPER_CAP_MAX_ORDERS_PER_MINUTE"] = "100"
    os.environ["PAPER_CAP_MAX_NEW_POSITIONS_PER_CYCLE"] = "10"
    os.environ["PAPER_CAP_HOLD_MINUTES"] = "60"
    os.environ["PAPER_CAP_CYCLE_MINUTES"] = "1"

    caps = load_paper_caps_from_env()
    assert caps["enabled"] is True

    st = PaperCapReplayState()
    t0 = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
    ok1, r1, _ = enforce_paper_caps(
        intent={"symbol": "AAPL", "side": "long", "intended_notional_usd": 300.0, "ts": t0},
        state=st,
        caps=caps,
    )
    assert ok1 and not r1

    # After first leg gross=300; need new_gross > max_gross_usd (1000) => add >700
    ok2, r2, _ = enforce_paper_caps(
        intent={"symbol": "MSFT", "side": "long", "intended_notional_usd": 800.0, "ts": t0},
        state=st,
        caps=caps,
    )
    assert not ok2 and "max_gross_usd" in r2

    log_path = REPO / "logs" / "paper_cap_decisions.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    test_touch = log_path.parent / ".paper_cap_write_test"
    test_touch.write_text("ok", encoding="utf-8")
    test_touch.unlink(missing_ok=True)

    append_paper_cap_log(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "symbol": "TEST",
            "side": "long",
            "intended_notional_usd": 1.0,
            "current_gross_usd": 0.0,
            "current_net_usd": 0.0,
            "per_symbol_usd": {},
            "cap_check_result": "PASS",
            "fail_reason_codes": [],
            "decision_outcome": "allowed",
            "pretrade_key": pretrade_key("TEST", "long", t0.isoformat(), 1.0),
            "smoke": True,
        }
    )
    print("verify_paper_caps_wired: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
