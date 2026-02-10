#!/usr/bin/env python3
"""
Run wheel root-cause report and key diagnostics on the droplet via SSH.
Output is printed to stdout (and can be saved). Uses DropletClient from repo root.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    today = datetime.now(timezone.utc).date().isoformat()
    report_name = f"WHEEL_ROOT_CAUSE_REPORT_{today}.md"
    verification_report = f"wheel_spot_resolution_verification_{today}.md"

    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "cd $REPO && "
        "echo '=== WHEEL ROOT CAUSE REPORT ===' && "
        "python3 scripts/wheel_root_cause_report.py --days 7 && "
        "echo '' && echo '=== WHEEL SPOT RESOLUTION VERIFICATION ===' && "
        "python3 scripts/wheel_spot_resolution_verification.py --days 7 && "
        "echo '' && echo '=== WHEEL EVENT COUNTS (system_events.jsonl) ===' && "
        "(grep '\"subsystem\": \"wheel\"' logs/system_events.jsonl 2>/dev/null | grep -o '\"event_type\": \"[^\"]*\"' | sort | uniq -c || echo 'No wheel events or file missing') && "
        "echo '' && echo '=== LAST wheel_run_started ===' && "
        "(grep '\"event_type\": \"wheel_run_started\"' logs/system_events.jsonl 2>/dev/null | tail -1 || echo 'None') && "
        "echo '' && echo '=== LAST 5 wheel_spot_resolved / wheel_spot_unavailable ===' && "
        "(grep -E '\"event_type\": \"wheel_spot_resolved\"|\"event_type\": \"wheel_spot_unavailable\"' logs/system_events.jsonl 2>/dev/null | tail -5 || echo 'None') && "
        "echo '' && echo '=== LAST 5 wheel_capital_check / wheel_capital_blocked ===' && "
        "(grep -E '\"event_type\": \"wheel_capital_check\"|\"event_type\": \"wheel_capital_blocked\"' logs/system_events.jsonl 2>/dev/null | tail -5 || echo 'None') && "
        "echo '' && echo '=== LAST 5 wheel_csp_skipped ===' && "
        "(grep '\"event_type\": \"wheel_csp_skipped\"' logs/system_events.jsonl 2>/dev/null | tail -5 || echo 'None') && "
        "echo '' && echo '=== WORKER DEBUG LOG (last 25 lines) ===' && "
        "(tail -25 logs/worker_debug.log 2>/dev/null || echo 'No worker_debug.log') && "
        "echo '' && echo '=== STOCK-BOT SERVICE ===' && "
        "(systemctl is-active stock-bot 2>/dev/null; systemctl show stock-bot -p ActiveEnterTimestamp --value 2>/dev/null) && "
        "echo '' && echo '=== ROOT CAUSE REPORT ===' && "
        f"(cat reports/{report_name} 2>/dev/null || echo 'Report not found') && "
        "echo '' && echo '=== SPOT RESOLUTION VERIFICATION REPORT ===' && "
        f"(cat reports/{verification_report} 2>/dev/null || echo 'Report not found')"
    )

    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=120)
    # Save full output to report (UTF-8) so Windows console encoding doesn't drop content
    report_path = REPO / "reports" / f"droplet_wheel_check_{today}.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write(out or "")
        if err:
            f.write("\n--- STDERR ---\n")
            f.write(err)
    print(f"Full output saved to: {report_path}")
    # Print with replacement for console (avoid Windows cp1252 UnicodeError)
    safe = (out or "").encode("ascii", errors="replace").decode("ascii")
    print(safe)
    if err:
        print(err.encode("ascii", errors="replace").decode("ascii"), file=sys.stderr)

    # Hard assertion: spot resolution must succeed during market hours (verification report)
    out_str = out or ""
    import re
    resolved_match = re.search(r"\*\*wheel_spot_resolved\*\*:\s*(\d+)", out_str)
    unavail_match = re.search(r"\*\*wheel_spot_unavailable\*\*:\s*(\d+)", out_str)
    resolved_count = int(resolved_match.group(1)) if resolved_match else -1
    unavail_count = int(unavail_match.group(1)) if unavail_match else -1
    if unavail_count >= 0 and resolved_count >= 0 and unavail_count > 0 and resolved_count == 0:
        print("\n*** FAIL: All wheel cycles emitted wheel_spot_unavailable; no spot resolved. ***", file=sys.stderr)
        print("Wheel cannot reach option chain or submit orders. Fix spot resolution (Alpaca quote/bar contract).", file=sys.stderr)
        return 1
    if "No spot resolved" in out_str and "FAIL" in out_str:
        print("\n*** FAIL: Spot resolution verification report indicates no spot resolved. ***", file=sys.stderr)
        return 1

    # Capital partitioning: wheel_capital_check must appear when wheel runs (fixed 25% allocation in effect)
    if '"event_type": "wheel_run_started"' in out_str and '"event_type": "wheel_capital_check"' not in out_str:
        print("\n*** WARN: wheel_run_started present but no wheel_capital_check events. Ensure capital allocator is deployed. ***", file=sys.stderr)
    if '"event_type": "wheel_capital_check"' in out_str:
        print("\n[OK] wheel_capital_check events present (fixed 25% wheel allocation in effect).", file=sys.stderr)
    if '"event_type": "wheel_capital_blocked"' in out_str:
        print("\n[INFO] wheel_capital_blocked occurred; see LAST 5 wheel_capital_check/wheel_capital_blocked above for budget math.", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
