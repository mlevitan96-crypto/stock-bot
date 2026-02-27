#!/usr/bin/env python3
"""
Order Submission Truth Contract — run on droplet.
Produces: submit_call_proof.md, ledger_vs_order_reconciliation.md, board_verdict.md.
Reads: logs/submit_order_called.jsonl, logs/submit_entry.jsonl, logs/orders.jsonl,
       reports/decision_ledger/decision_ledger.jsonl.
Prints required terminal output. No strategy tuning.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REPORT_DIR = REPO / "reports" / "order_review"
LOG_DIR = REPO / "logs"
LEDGER_JSONL = REPO / "reports" / "decision_ledger" / "decision_ledger.jsonl"
SUBMIT_CALLED_JSONL = LOG_DIR / "submit_order_called.jsonl"
SUBMIT_ENTRY_JSONL = LOG_DIR / "submit_entry.jsonl"
ORDERS_JSONL = LOG_DIR / "orders.jsonl"

# Window: last 24h for counts (configurable)
SEC_24H = 24 * 3600


def _parse_ts(v) -> int | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return int(float(v))
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s[:26])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def count_jsonl(path: Path, ts_key: str = "ts", since_ts: int | None = None) -> int:
    n = 0
    if not path.exists():
        return 0
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            if since_ts is not None:
                t = _parse_ts(r.get(ts_key) or r.get("ts_iso"))
                if t is None or t < since_ts:
                    continue
            n += 1
        except Exception:
            continue
    return n


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = _now_ts() - SEC_24H

    # --- SUBMIT_ORDER_CALLED count ---
    submit_called_count = count_jsonl(SUBMIT_CALLED_JSONL, since_ts=cutoff)
    submit_entry_count = count_jsonl(SUBMIT_ENTRY_JSONL, since_ts=cutoff)

    # --- orders.jsonl: success vs fail ---
    order_success = 0
    order_fail = 0
    order_actions: Counter = Counter()
    if ORDERS_JSONL.exists():
        for line in ORDERS_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t is not None and t < cutoff:
                    continue
                action = str(r.get("action") or r.get("type") or "")
                order_actions[action] += 1
                if "filled" in action.lower() or r.get("status") == "filled":
                    order_success += 1
                elif r.get("error") or "error" in action.lower() or "reject" in action.lower():
                    order_fail += 1
            except Exception:
                continue

    # --- Ledger: blocked at expectancy, total in window ---
    ledger_total_24h = 0
    ledger_blocked_expectancy = 0
    if LEDGER_JSONL.exists():
        for line in LEDGER_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts"))
                if t is None or t < cutoff:
                    continue
                ledger_total_24h += 1
                gates = r.get("gates") or []
                for g in gates:
                    if g.get("gate_name") == "expectancy_gate" and g.get("pass") is False:
                        ledger_blocked_expectancy += 1
                        break
            except Exception:
                continue

    # --- Write submit_call_proof.md ---
    proof_lines = [
        "# Submit call proof (Order Truth Contract)",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Window: last 24h (since ts {cutoff})",
        "",
        "## Counts",
        "",
        f"- **SUBMIT_ORDER_CALLED** (lines in `logs/submit_order_called.jsonl` in window): **{submit_called_count}**",
        f"- **submit_entry.jsonl** lines in window: **{submit_entry_count}**",
        f"- **Broker responses** (from `logs/orders.jsonl`): success (filled)=**{order_success}**, fail/error/reject=**{order_fail}**",
        "",
        "## Interpretation",
        "",
        "- If SUBMIT_ORDER_CALLED = 0 and orders.jsonl has lines: those lines are from other sources (e.g. audit_dry_run, log_order from elsewhere), not from the broker submit path.",
        "- If SUBMIT_ORDER_CALLED > 0 and order_success = 0: submit is called but broker never fills (or telemetry for fills is missing).",
        "- If SUBMIT_ORDER_CALLED = 0: submit is never reached; see submit_call_map.md for guards that block before submit.",
        "",
    ]
    (REPORT_DIR / "submit_call_proof.md").write_text("\n".join(proof_lines), encoding="utf-8")

    # --- Write ledger_vs_order_reconciliation.md ---
    recon_lines = [
        "# Ledger vs order layer reconciliation",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Window: last 24h",
        "",
        "## Counts (same window)",
        "",
        f"- Ledger entries (last 24h): **{ledger_total_24h}** (path: `reports/decision_ledger/decision_ledger.jsonl`)",
        f"- Ledger entries blocked at expectancy_gate (first fail): **{ledger_blocked_expectancy}**",
        f"- Candidates reaching order layer (SUBMIT_ORDER_CALLED): **{submit_called_count}**",
        f"- Submit calls (same): **{submit_called_count}**",
        "",
        "## Mismatch explanation",
        "",
    ]
    if ledger_total_24h > 0 and submit_called_count == 0:
        recon_lines.append("- **Mismatch:** Ledger has candidates but SUBMIT_ORDER_CALLED = 0. So no candidate in this window reached the broker submit. They are blocked earlier (e.g. expectancy_gate in ledger, or submit_entry guards before _submit_order_guarded). The 396 order-related lines seen in a prior run were likely from a different log (e.g. log_order from audit_dry_run or other action), not from the real submit path.")
    elif ledger_total_24h > 0 and submit_called_count > 0:
        recon_lines.append(f"- **Reconciliation:** Some candidates reached the submit call ({submit_called_count}). Ledger may include older snapshots; order layer reflects actual submit attempts in window.")
    else:
        recon_lines.append("- No ledger events or no submit calls in window; run with live traffic to reconcile.")
    recon_lines.append("")
    (REPORT_DIR / "ledger_vs_order_reconciliation.md").write_text("\n".join(recon_lines), encoding="utf-8")

    # --- Board verdict: one of four ---
    if submit_called_count == 0:
        if submit_entry_count == 0 and ledger_blocked_expectancy == ledger_total_24h and ledger_total_24h > 0:
            verdict = "Submit never called — all candidates blocked at expectancy_gate (score floor) before reaching submit_entry or before _submit_order_guarded. Exact blocker: expectancy_gate (composite score below MIN_EXEC_SCORE)."
            fix = "No order-layer fix; address score/signal so candidates pass expectancy gate, or run with AUDIT_DRY_RUN=1 to confirm submit path without broker call."
        else:
            verdict = "Submit never called — candidates are blocked before the broker submit. Check submit_call_map.md guards; likely expectancy_gate or submit_entry early returns (trade_guard, spread, notional, audit_dry_run)."
            fix = "Inspect logs/submit_entry.jsonl for block reasons; ensure AUDIT_DRY_RUN is not set if live submit is intended; fix the guard that blocks (no strategy tuning)."
        if not SUBMIT_CALLED_JSONL.exists():
            fix += " If instrumentation (main.py SUBMIT_ORDER_CALLED log) was just deployed, restart the bot and run for a few minutes then re-run this script."
    elif order_success == 0 and order_fail == 0:
        verdict = "Submit called but no broker responses in orders.jsonl — possible telemetry broken (order response not logged) or broker not responding."
        fix = "Confirm logs/orders.jsonl is written after submit (log_order in submit_entry path); check broker/network for response."
    elif order_success == 0 and order_fail > 0:
        verdict = "Submit called and broker rejects — orders.jsonl shows failures. Extract reject reasons from logs/orders.jsonl (action/error fields)."
        fix = "Inspect logs/orders.jsonl and logs/critical_api_failure.log for Alpaca error messages; fix broker-side (price, size, account) or validation layer."
    else:
        verdict = "Submit called and some orders succeed — broker and telemetry are functioning."
        fix = "N/A."

    board_lines = [
        "# Board verdict — Order Submission Truth Contract",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## FINAL VERDICT",
        "",
        verdict,
        "",
        "## Single fix (restore truthful order submission telemetry)",
        "",
        fix,
        "",
        "## Evidence summary",
        "",
        f"- SUBMIT_ORDER_CALLED (24h): {submit_called_count}",
        f"- submit_entry.jsonl lines (24h): {submit_entry_count}",
        f"- Broker success (filled): {order_success}, fail: {order_fail}",
        "",
    ]
    (REPORT_DIR / "board_verdict.md").write_text("\n".join(board_lines), encoding="utf-8")

    # --- Terminal output (required) ---
    print("SUBMIT_ORDER_CALLED: " + ("YES" if submit_called_count > 0 else "NO") + f" ({submit_called_count})")
    print(f"submit_entry.jsonl lines: {submit_entry_count}")
    print(f"Broker responses: success={order_success}, fail={order_fail}")
    print("FINAL VERDICT: " + verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
