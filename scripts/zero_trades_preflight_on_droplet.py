#!/usr/bin/env python3
"""
Zero-trades preflight (Phase 0). Run on droplet. No strategy tuning.
Determines which "zero" we have: A) zero candidates, B) candidates exist but all blocked/deferred, C) orders attempted but rejected/never filled.
Writes reports/signal_review/zero_trades_preflight.md and prints required terminal summary.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

LEDGER_JSONL = REPO / "reports" / "decision_ledger" / "decision_ledger.jsonl"
SNAPSHOT_JSONL = REPO / "logs" / "score_snapshot.jsonl"
BLOCKED_JSONL = REPO / "state" / "blocked_trades.jsonl"
RUN_JSONL = REPO / "logs" / "run.jsonl"
ORDERS_JSONL = REPO / "logs" / "orders.jsonl"
SUBMIT_ENTRY_JSONL = REPO / "logs" / "submit_entry.jsonl"
GATE_JSONL = REPO / "logs" / "gate.jsonl"
DEFER_RETRY_JSONL = REPO / "reports" / "uw_health" / "uw_defer_retry_events.jsonl"
DEFERRED_CANDIDATES_JSONL = REPO / "reports" / "uw_health" / "uw_deferred_candidates.jsonl"
OUT_DIR = REPO / "reports" / "signal_review"
OUT_MD = OUT_DIR / "zero_trades_preflight.md"

SEC_24H = 24 * 3600
SEC_2H = 2 * 3600


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


def _read_jsonl(path: Path, ts_key: str = "ts", cutoff_after: int | None = None, cutoff_before: int | None = None) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(r.get(ts_key) or r.get("ts_iso") or r.get("timestamp"))
        if ts is not None and cutoff_after is not None and ts < cutoff_after:
            continue
        if ts is not None and cutoff_before is not None and ts > cutoff_before:
            continue
        out.append(r)
    return out


def first_blocking_gate(gates: list) -> tuple[str, str] | None:
    for g in gates or []:
        if g.get("pass") is False:
            return (g.get("gate_name", "unknown"), g.get("reason", "unknown"))
    return None


def main() -> int:
    now_ts = _now_ts()
    cutoff_24h = now_ts - SEC_24H
    cutoff_2h = now_ts - SEC_2H

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1) Main loop running: newest timestamps ---
    ledger_newest_ts = None
    snapshot_newest_ts = None
    blocked_newest_ts = None
    run_newest_ts = None

    if LEDGER_JSONL.exists():
        for line in LEDGER_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts"))
                if t and (ledger_newest_ts is None or t > ledger_newest_ts):
                    ledger_newest_ts = t
            except Exception:
                continue
    if SNAPSHOT_JSONL.exists():
        for line in SNAPSHOT_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t and (snapshot_newest_ts is None or t > snapshot_newest_ts):
                    snapshot_newest_ts = t
            except Exception:
                continue
    if BLOCKED_JSONL.exists():
        for line in BLOCKED_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("timestamp"))
                if t and (blocked_newest_ts is None or t > blocked_newest_ts):
                    blocked_newest_ts = t
            except Exception:
                continue
    if RUN_JSONL.exists():
        for line in RUN_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t and (run_newest_ts is None or t > run_newest_ts):
                    run_newest_ts = t
            except Exception:
                continue

    # --- 2) Candidate existence: ledger events last 24h and 2h ---
    ledger_24h: list[dict] = []
    ledger_2h: list[dict] = []
    if LEDGER_JSONL.exists():
        for line in LEDGER_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts"))
                if t is None:
                    continue
                if t >= cutoff_24h:
                    ledger_24h.append(r)
                if t >= cutoff_2h:
                    ledger_2h.append(r)
            except Exception:
                continue

    # If no ledger, use snapshot + blocked as proxy for "candidates"
    snapshot_24h_count = 0
    blocked_24h_count = 0
    if not ledger_24h and SNAPSHOT_JSONL.exists():
        for line in SNAPSHOT_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t and t >= cutoff_24h:
                    snapshot_24h_count += 1
            except Exception:
                continue
    if BLOCKED_JSONL.exists():
        for line in BLOCKED_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("timestamp"))
                if t and t >= cutoff_24h:
                    blocked_24h_count += 1
            except Exception:
                continue

    # --- 3) First-fail gate distribution (last 24h) ---
    gate_reason_24h: Counter = Counter()
    status_24h: Counter = Counter()
    for e in ledger_24h:
        status_24h[e.get("candidate_status") or "unknown"] += 1
        fb = first_blocking_gate(e.get("gates", []))
        if fb:
            gate_reason_24h[f"{fb[0]}:{fb[1]}"] += 1

    # --- 4) UW defer lifecycle ---
    defer_24h = 0
    defer_resolved = 0
    defer_expired = 0
    if DEFER_RETRY_JSONL.exists():
        for line in DEFER_RETRY_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                ts = float(r.get("retry_ts") or r.get("first_defer_ts") or 0)
                if ts < cutoff_24h:
                    continue
                defer_24h += 1
                out = (r.get("final_outcome") or "").strip()
                if out == "resolved":
                    defer_resolved += 1
                elif out == "expired_then_penalized":
                    defer_expired += 1
            except Exception:
                continue
    deferred_candidates_count = 0
    if DEFERRED_CANDIDATES_JSONL.exists():
        for line in DEFERRED_CANDIDATES_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if line.strip():
                deferred_candidates_count += 1

    # --- 5) Capacity/risk evidence ---
    capacity_block_24h = sum(c for gr, c in gate_reason_24h.items() if "capacity" in gr.lower() or "max_positions" in gr.lower() or "theme_exposure" in gr.lower() or "max_new_positions" in gr.lower())
    capacity_gate_reasons = [gr for gr in gate_reason_24h if "capacity" in gr.lower() or "max_positions" in gr.lower() or "theme_exposure" in gr.lower() or "max_new_positions" in gr.lower()]

    # --- 6) Order layer ---
    order_lines_24h = 0
    order_fills_24h = 0
    order_rejects_24h = 0
    order_actions: Counter = Counter()
    if ORDERS_JSONL.exists():
        for line in ORDERS_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t and t < cutoff_24h:
                    continue
                order_lines_24h += 1
                action = r.get("action") or r.get("type") or ""
                order_actions[action] += 1
                if "filled" in str(action).lower() or r.get("status") == "filled":
                    order_fills_24h += 1
                if "error" in str(action).lower() or "reject" in str(action).lower() or r.get("error"):
                    order_rejects_24h += 1
            except Exception:
                continue
    submit_entry_attempts_24h = 0
    submit_entry_rejects_24h = 0
    submit_entry_msgs: Counter = Counter()
    if SUBMIT_ENTRY_JSONL.exists():
        for line in SUBMIT_ENTRY_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t and t < cutoff_24h:
                    continue
                msg = (r.get("msg") or "").lower()
                submit_entry_msgs[r.get("msg") or ""] += 1
                submit_entry_attempts_24h += 1
                if "blocked" in msg or "fail" in msg or "error" in msg or "reject" in msg:
                    submit_entry_rejects_24h += 1
            except Exception:
                continue

    order_attempts_24h = order_lines_24h  # any order-log line in 24h = order-layer activity

    # --- Classify ZERO TYPE ---
    candidates_24h = len(ledger_24h) if ledger_24h else (snapshot_24h_count + blocked_24h_count)
    zero_type = "A"
    dominant_blocker = ""
    dominant_count = 0
    dominant_pct = 0.0

    if candidates_24h == 0:
        zero_type = "A"
    elif (order_attempts_24h > 0 or submit_entry_attempts_24h > 0) and order_fills_24h == 0:
        zero_type = "C"  # orders attempted but rejected/never filled
    else:
        zero_type = "B"  # candidates exist but all blocked/deferred
        if gate_reason_24h and ledger_24h:
            top = gate_reason_24h.most_common(1)[0]
            dominant_blocker = top[0]
            dominant_count = top[1]
            dominant_pct = 100.0 * dominant_count / len(ledger_24h)

    # --- Build report ---
    lines = [
        "# Zero-trades preflight (Phase 0)",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**ZERO TYPE: {zero_type}**",
        "",
        "## 1) Main loop running",
        "",
        f"- **reports/decision_ledger/decision_ledger.jsonl** — newest event ts: {ledger_newest_ts} ({datetime.fromtimestamp(ledger_newest_ts, tz=timezone.utc).isoformat() if ledger_newest_ts else 'N/A'})",
        f"- **logs/score_snapshot.jsonl** — newest ts: {snapshot_newest_ts} ({datetime.fromtimestamp(snapshot_newest_ts, tz=timezone.utc).isoformat() if snapshot_newest_ts else 'N/A'})",
        f"- **state/blocked_trades.jsonl** — newest ts: {blocked_newest_ts} ({datetime.fromtimestamp(blocked_newest_ts, tz=timezone.utc).isoformat() if blocked_newest_ts else 'N/A'})",
        f"- **logs/run.jsonl** — newest ts: {run_newest_ts} ({datetime.fromtimestamp(run_newest_ts, tz=timezone.utc).isoformat() if run_newest_ts else 'N/A'})",
        "",
        "## 2) Candidate existence",
        "",
        f"- Ledger events last 24h: **{len(ledger_24h)}** (path: reports/decision_ledger/decision_ledger.jsonl)",
        f"- Ledger events last 2h: **{len(ledger_2h)}**",
        "",
    ]
    if not ledger_24h:
        lines.append(f"- Proxy (no ledger): score_snapshot last 24h lines: {snapshot_24h_count}, blocked_trades last 24h: {blocked_24h_count}")
        lines.append("")
    lines.extend([
        "## 3) First-fail gate distribution (last 24h)",
        "",
        "| Gate:Reason | Count |",
        "|-------------|-------|",
    ])
    for gr, c in gate_reason_24h.most_common(15):
        lines.append(f"| {gr} | {c} |")
    if not gate_reason_24h:
        lines.append("| (none) | 0 |")
    lines.append("")
    lines.extend([
        "## 4) UW defer lifecycle",
        "",
        f"- **reports/uw_health/uw_defer_retry_events.jsonl** — events last 24h: {defer_24h}, resolved: {defer_resolved}, expired_then_penalized: {defer_expired}",
        f"- **reports/uw_health/uw_deferred_candidates.jsonl** — current deferred candidates (line count): {deferred_candidates_count}",
        "",
        "## 5) Capacity/risk",
        "",
        f"- First-fail gate counts (capacity/max_positions/theme_exposure) last 24h: **{capacity_block_24h}**",
        f"- Gate:reason keys: {capacity_gate_reasons or '(none)'}",
        "",
        "## 6) Order layer",
        "",
        f"- **logs/orders.jsonl** — order-related lines last 24h: {order_attempts_24h} (attempts), {order_fills_24h} (fills), {order_rejects_24h} (rejects); action counts: {dict(order_actions.most_common(10))}",
        f"- **logs/submit_entry.jsonl** — submit_entry lines last 24h: {submit_entry_attempts_24h}, reject/block/error: {submit_entry_rejects_24h}; top msg: {submit_entry_msgs.most_common(5)}",
        "",
    ])

    # Board verdict
    lines.append("---")
    lines.append("")
    lines.append("## Board verdict (fix-ready)")
    lines.append("")
    if zero_type == "A":
        lines.append("- **Classification: A — Zero candidates.** No (or negligible) candidate flow in the last 24h.")
        lines.append("- **Fix:** Ensure main loop is running and producing score_snapshot + blocked_trades. Run `python3 scripts/run_decision_ledger_capture.py` to build ledger from telemetry. Check data feeds (bars, UW root cause), EOD job, and that the bot process is active.")
        lines.append("- **Next:** Verify data feed contract (scripts/data_feed_health_contract.py) and daily_uw_health_review; fix missing/stale feeds.")
    elif zero_type == "C":
        lines.append("- **Classification: C — Orders attempted but rejected/never filled.**")
        lines.append(f"- **Evidence:** Order/submit_entry attempts last 24h: {order_attempts_24h + submit_entry_attempts_24h}; fills: {order_fills_24h}; rejects: {order_rejects_24h + submit_entry_rejects_24h}.")
        lines.append("- **Fix:** Inspect logs/orders.jsonl and logs/submit_entry.jsonl for rejection reasons (Alpaca 422, buying power, trade guard, spread, etc.). No strategy tuning; fix broker/guard/validation layer.")
        lines.append("- **Next:** Address specific rejection codes; re-run preflight to confirm ZERO TYPE moves to B or trades fill.")
    else:
        lines.append("- **Classification: B — Candidates exist but all blocked/deferred.**")
        if dominant_blocker:
            lines.append(f"- **Dominant blocker:** {dominant_blocker} (count={dominant_count}, %={dominant_pct:.1f}).")
        lines.append("- **Next:** Proceed to Phase 1 (full signal review): run `python3 scripts/full_signal_review_on_droplet.py` to produce signal_funnel.md/.json, top_50_end_to_end_traces.md, multi_model_adversarial_review.md.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")

    # Required terminal output
    print("")
    print("--- TERMINAL OUTPUT (Phase 0) ---")
    print(f"ZERO TYPE: {zero_type}")
    if zero_type == "B" and dominant_blocker:
        print(f"Dominant blocker (if B): {dominant_blocker} count={dominant_count}, %={dominant_pct:.1f}%")
    print(f"Orders attempted? {'YES' if (order_attempts_24h + submit_entry_attempts_24h) > 0 else 'NO'} (attempts={order_attempts_24h + submit_entry_attempts_24h}), rejected? (count={order_rejects_24h + submit_entry_rejects_24h}), fills={order_fills_24h}")
    if zero_type in ("A", "C"):
        print("(STOP: fix-ready verdict in reports/signal_review/zero_trades_preflight.md board section)")
    else:
        print("(Proceed to Phase 1: full_signal_review_on_droplet.py)")
    print("---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
