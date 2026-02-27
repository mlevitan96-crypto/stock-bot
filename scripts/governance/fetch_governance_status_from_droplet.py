#!/usr/bin/env python3
"""Fetch governance loop state and last run decision from droplet; print summary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    with DropletClient() as c:
        out1, _, _ = c._execute("cat /root/stock-bot/state/equity_governance_loop_state.json", timeout=10)
        state_raw = (out1 or "").strip()
        out2, _, _ = c._execute(
            "ls -td /root/stock-bot/reports/equity_governance/equity_governance_* 2>/dev/null | head -1",
            timeout=10,
        )
        last_dir = (out2 or "").strip()
        decision_raw = ""
        if last_dir:
            out3, _, _ = c._execute(f"cat {last_dir}/lock_or_revert_decision.json", timeout=10)
            decision_raw = (out3 or "").strip()

    print("=== State (equity_governance_loop_state.json) ===")
    if state_raw:
        try:
            s = json.loads(state_raw)
            print(json.dumps(s, indent=2))
        except Exception as e:
            print(state_raw[:500], "\n(parse error:", e, ")")
    else:
        print("(empty or missing)")

    print("\n=== Last run decision ===")
    if decision_raw:
        try:
            d = json.loads(decision_raw)
            cand = d.get("candidate", {})
            base = d.get("baseline", {})
            print("Decision:", d.get("decision"))
            print("Stopping condition met:", d.get("stopping_condition_met"))
            print("Candidate expectancy_per_trade:", cand.get("expectancy_per_trade"))
            print("Candidate win_rate:", cand.get("win_rate"))
            print("Baseline expectancy_per_trade:", base.get("expectancy_per_trade"))
            print("Stopping checks:", json.dumps(d.get("stopping_checks", {}), indent=2))
        except Exception as e:
            print(decision_raw[:500], "\n(parse error:", e, ")")
    else:
        print("(no decision file yet)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
