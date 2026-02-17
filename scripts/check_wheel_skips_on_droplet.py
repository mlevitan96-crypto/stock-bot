#!/usr/bin/env python3
"""Fetch wheel_csp_skipped events from droplet and summarize by reason."""
from pathlib import Path
import sys
import json
from collections import Counter

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main():
    from droplet_client import DropletClient

    # Fetch raw wheel_csp_skipped lines from droplet (last 300)
    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "cd $REPO && "
        "grep '\"event_type\": \"wheel_csp_skipped\"' logs/system_events.jsonl 2>/dev/null | tail -300"
    )
    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=60)
    text = out or ""
    if err:
        print("STDERR:", err, file=sys.stderr)

    # Parse locally: extract JSON from each line
    reasons = []
    pairs = []  # (symbol, reason)
    raw_objs = []
    for line in text.splitlines():
        line = line.strip()
        if not line or "wheel_csp_skipped" not in line:
            continue
        try:
            i = line.find("{")
            if i >= 0:
                obj = json.loads(line[i:])
                r = obj.get("reason") or "unknown"
                reasons.append(r)
                s = obj.get("symbol", "")
                if s:
                    pairs.append((s, r))
                raw_objs.append(obj)
        except Exception:
            pass

    reason_counts = list(Counter(reasons).most_common())

    print("=== WHEEL_CSP_SKIPPED REVIEW (droplet) ===\n")
    print(f"Total skips in window: {len(reasons)}\n")

    if not reason_counts:
        print("No wheel_csp_skipped events found in last 300 lines.")
        return 0

    print("Count by reason:")
    for r, n in reason_counts:
        print(f"  {r}: {n}")
    print()

    print("Sample (symbol, reason) last 20:")
    for s, r in pairs[-20:]:
        print(f"  {s}: {r}")
    print()

    print("Raw last 5 events:")
    for obj in raw_objs[-5:]:
        print(" ", json.dumps(obj, indent=2))
    print()

    # Interpretation
    known_good = {
        "max_positions_reached",
        "per_position_limit",
        "capital_limit",
        "existing_order",
        "earnings_window",
        "iv_rank",
        "no_contracts_in_range",
        "no_spot",
        "max_per_symbol",
        "insufficient_buying_power",
    }
    top_reason = reason_counts[0][0]
    print("--- INTERPRETATION ---")
    if top_reason in known_good:
        print(f"Top reason '{top_reason}' is a normal governance/limit or data skip (not a bug).")
    else:
        print(f"Top reason '{top_reason}' — verify in wheel_strategy.py; may be a new or unexpected code path.")
    print("Valid skip reasons: max_positions_reached, per_position_limit, capital_limit, existing_order,")
    print("earnings_window, iv_rank, no_contracts_in_range, no_spot, max_per_symbol, insufficient_buying_power.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
