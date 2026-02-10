#!/usr/bin/env python3
"""
Run wheel root-cause report and key diagnostics on the droplet via SSH.
Output is printed to stdout (and can be saved). Uses DropletClient from repo root.
"""
from __future__ import annotations

import json
import re
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
        "echo '' && echo '=== LAST 5 wheel_position_limit_check / wheel_position_limit_blocked ===' && "
        "(grep -E '\"event_type\": \"wheel_position_limit_check\"|\"event_type\": \"wheel_position_limit_blocked\"' logs/system_events.jsonl 2>/dev/null | tail -5 || echo 'None') && "
        "echo '' && echo '=== LAST 5 wheel_csp_skipped ===' && "
        "(grep '\"event_type\": \"wheel_csp_skipped\"' logs/system_events.jsonl 2>/dev/null | tail -5 || echo 'None') && "
        "echo '' && echo '=== LAST 5 wheel_order_idempotency_hit ===' && "
        "(grep '\"event_type\": \"wheel_order_idempotency_hit\"' logs/system_events.jsonl 2>/dev/null | tail -5 || echo 'None (expected 0; >0 proves restart protection)') && "
        "echo '' && echo '=== WORKER DEBUG LOG (last 25 lines) ===' && "
        "(tail -25 logs/worker_debug.log 2>/dev/null || echo 'No worker_debug.log') && "
        "echo '' && echo '=== STOCK-BOT SERVICE ===' && "
        "(systemctl is-active stock-bot 2>/dev/null; systemctl show stock-bot -p ActiveEnterTimestamp --value 2>/dev/null) && "
        "echo '' && echo '=== ROOT CAUSE REPORT ===' && "
        f"(cat reports/{report_name} 2>/dev/null || echo 'Report not found') && "
        "echo '' && echo '=== SPOT RESOLUTION VERIFICATION REPORT ===' && "
        f"(cat reports/{verification_report} 2>/dev/null || echo 'Report not found') && "
        "echo '' && echo '=== SIGNAL PROPAGATION CHECK ===' && "
        "python3 scripts/audit_signal_propagation.py --minutes 15; S=$?; "
        "echo '' && echo '=== SIGNAL ANALYTICS ===' && "
        "python3 scripts/compute_signal_correlation_snapshot.py --minutes 60 --topk 20 --no-emit 2>/dev/null || true; "
        "python3 -c \"
import json
from pathlib import Path
p=Path('state/signal_strength_cache.json')
c=json.load(p.open()) if p.exists() else {}
total=len([s for s,ent in c.items() if isinstance(ent,dict) and ent.get('signal_strength') is not None])
with_delta=[(s,ent.get('signal_delta')) for s,ent in c.items() if isinstance(ent,dict) and ent.get('signal_delta') is not None]
pct=100*len(with_delta)/total if total else 0
print('Trend coverage:', round(pct,1), '%')
with_delta.sort(key=lambda x:x[1])
for s,d in with_delta[:3]: print('Weakening', s, d)
for s,d in with_delta[-3:][::-1]: print('Strengthening', s, d)
p2=Path('state/signal_correlation_cache.json')
cor=json.load(p2.open()) if p2.exists() else {}
for p in (cor.get('pairs') or [])[:3]: print('Pair', p.get('a'), p.get('b'), p.get('corr'))
\" 2>/dev/null || echo 'Signal analytics N/A'; "
        "echo '' && echo '=== WHEEL DAILY REVIEW (completeness gate) ===' && "
        "python3 scripts/generate_wheel_daily_review.py --days 1; R=$?; "
        "echo '' && echo 'WHEEL GOVERNANCE BADGE' && echo '---------------------' && "
        "python3 -c \"import json; from pathlib import Path; from datetime import datetime, timezone; d=datetime.now(timezone.utc).strftime('%Y-%m-%d'); p=Path('reports')/('wheel_governance_badge_'+d+'.json'); b=json.load(p.open()) if p.exists() else {}; print('Status:', b.get('overall_status','?')); print('Event chain coverage:', str(b.get('event_chain_coverage_pct',''))+'%'); print('Idempotency hits:', b.get('idempotency_hits',0)); print('Board action closure:', b.get('board_action_closure','?')); print('Dominant blocker:', b.get('dominant_blocker','?'))\" 2>/dev/null || echo 'Badge not found'; "
        "echo '' && echo '=== BOARD WATCHLISTS ===' && "
        "python3 -c \""
        "import json,sys\nfrom pathlib import Path\nfrom datetime import datetime,timezone\n"
        "d=datetime.now(timezone.utc).strftime('%Y-%m-%d')\np=Path('reports')/('wheel_watchlists_'+d+'.json')\n"
        "if not p.exists(): print('wheel_watchlists_'+d+'.json MISSING'); sys.exit(1)\n"
        "data=json.load(p.open())\nw=data.get('weakening_signals') or []\nc=data.get('correlation_concentration') or []\n"
        "print('weakening_watchlist_count:', len(w))\nprint('correlation_watchlist_count:', len(c))\n"
        "missing=[e.get('symbol') for e in w if not (e.get('board_rationale') and str(e.get('board_rationale')).strip())]\n"
        "missing+=[e.get('symbol') for e in c if not (e.get('board_rationale') and str(e.get('board_rationale')).strip())]\n"
        "if missing: print('FAIL: missing rationales for', missing); sys.exit(1)\n"
        "\" ; W=$?; "
        "exit $((R|S|W))"
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

    # Per-position limits (wheel budget fraction): wheel_position_limit_check must appear
    if '"event_type": "wheel_run_started"' in out_str and '"event_type": "wheel_position_limit_check"' not in out_str:
        print("\n*** WARN: wheel_run_started present but no wheel_position_limit_check events. Deploy wheel per-position logic. ***", file=sys.stderr)
    if '"event_type": "wheel_position_limit_check"' in out_str:
        print("\n[OK] wheel_position_limit_check events present (per-position limit = fraction of wheel budget).", file=sys.stderr)
    if '"event_type": "wheel_position_limit_blocked"' in out_str:
        print("\n[INFO] wheel_position_limit_blocked occurred; see LAST 5 wheel_position_limit_check/blocked above.", file=sys.stderr)

    # Summary: wheel budget, per_position_limit, first symbol allowed, order submission status
    wheel_budget = None
    per_position_limit = None
    for line in (out_str or "").splitlines():
        if '"event_type": "wheel_position_limit_check"' in line and '"wheel_budget"' in line:
            # Parse first occurrence for summary
            try:
                # Find JSON object in line (event may be embedded in log line)
                start = line.find("{")
                if start >= 0:
                    obj = json.loads(line[start:].split("\n")[0].strip())
                    wheel_budget = obj.get("wheel_budget")
                    per_position_limit = obj.get("per_position_limit")
                    if wheel_budget is not None and per_position_limit is not None:
                        break
            except Exception:
                pass
    order_submitted_count = out_str.count('"event_type": "wheel_order_submitted"')
    first_symbol_allowed = None
    for line in (out_str or "").splitlines():
        if '"event_type": "wheel_order_submitted"' in line and '"symbol"' in line:
            try:
                start = line.find("{")
                if start >= 0:
                    obj = json.loads(line[start:].split("\n")[0].strip())
                    first_symbol_allowed = obj.get("symbol")
                    break
            except Exception:
                pass
    print("\n--- WHEEL PER-POSITION SUMMARY ---", file=sys.stderr)
    print(f"  wheel_budget: {wheel_budget}", file=sys.stderr)
    print(f"  per_position_limit: {per_position_limit}", file=sys.stderr)
    if per_position_limit is not None and wheel_budget is not None and wheel_budget and abs(per_position_limit - 0.5 * wheel_budget) < 0.02 * wheel_budget:
        print("  [OK] per_position_limit ≈ 50% of wheel_budget.", file=sys.stderr)
    elif per_position_limit is not None and wheel_budget is not None:
        print("  [INFO] per_position_limit vs 50% of wheel_budget: check config per_position_fraction_of_wheel_budget.", file=sys.stderr)
    print(f"  first symbol allowed (order submitted): {first_symbol_allowed or 'none'}", file=sys.stderr)
    print(f"  wheel_order_submitted count: {order_submitted_count}", file=sys.stderr)
    if order_submitted_count > 0:
        print("  [OK] At least one CSP order submitted (paper).", file=sys.stderr)
    else:
        print("  [INFO] No wheel_order_submitted yet; ensure candidates pass capital + per-position checks.", file=sys.stderr)
    idempotency_hits = out_str.count('"event_type": "wheel_order_idempotency_hit"')
    if idempotency_hits > 0:
        print(f"  [INFO] wheel_order_idempotency_hit count: {idempotency_hits} (restart protection worked).", file=sys.stderr)
    print("  [INFO] After EOD board run, verify reports/wheel_actions_<date>.json exists and prior actions have closure.", file=sys.stderr)

    # Governance badge: fail and point to review if badge status is FAIL
    if "WHEEL GOVERNANCE BADGE" in out_str and "Status: FAIL" in out_str:
        print(f"\n*** FAIL: Wheel governance badge is FAIL. See reports/wheel_daily_review_{today}.md ***", file=sys.stderr)
        return 1

    # Signal propagation: fail if audit reported MISSING
    if "SIGNAL PROPAGATION CHECK" in out_str and "FAIL:" in out_str and "signal_strength_evaluated" in out_str:
        print("\n*** FAIL: At least one open position missing signal_strength_evaluated. Run engine so open_position_refresh runs. ***", file=sys.stderr)
        return 1

    # Board watchlists: fail if artifact missing or rationales missing
    if "BOARD WATCHLISTS" in out_str:
        if "MISSING" in out_str and "wheel_watchlists_" in out_str:
            print("\n*** FAIL: reports/wheel_watchlists_<date>.json missing. Run Board EOD to generate. ***", file=sys.stderr)
            return 1
        if "FAIL: missing rationales" in out_str:
            print("\n*** FAIL: Board watchlist entries missing board rationales. Re-run Board EOD and address all watchlist symbols. ***", file=sys.stderr)
            return 1
        # Print summary from remote output
        for line in out_str.splitlines():
            if "weakening_watchlist_count:" in line or "correlation_watchlist_count:" in line:
                print(f"  {line.strip()}", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
