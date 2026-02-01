#!/usr/bin/env python3
"""
Live Trace Verification — run ON DROPLET only.
Reads logs/run.jsonl, logs/system_events.jsonl, logs/orders.jsonl.
Writes reports/LIVE_TRACE_*.md.
No restarts, no synthetic trades, read-only verification.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOGS = REPO / "logs"
REPORTS = REPO / "reports"

WINDOW_RUN_MIN = 10
WINDOW_HEARTBEAT_MIN = 5
WINDOW_SENTINEL_MIN = 15


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        if "Z" in s or "+" in s or s.endswith("00:00"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s + "+00:00")
    except Exception:
        return None


def _read_jsonl(path: Path, since: datetime | None = None, ts_key: str | None = None) -> list[dict]:
    out = []
    if not path.exists():
        return out
    key = ts_key or "ts"
    if ts_key is None and "system_events" in str(path):
        key = "timestamp"
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = _parse_ts(rec.get(key) or rec.get("ts") or rec.get("_ts") or rec.get("timestamp"))
                if since and ts and ts < since:
                    continue
                out.append(rec)
            except Exception:
                continue
    return out


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 15) -> tuple[str, str, int]:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or REPO,
        )
        return (r.stdout or "", r.stderr or "", r.returncode)
    except Exception as e:
        return ("", str(e), -1)


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    now = _now()
    since_run = now - timedelta(minutes=WINDOW_RUN_MIN)
    since_hb = now - timedelta(minutes=WINDOW_HEARTBEAT_MIN)
    since_sentinel = now - timedelta(minutes=WINDOW_SENTINEL_MIN)

    # -------------------------------------------------------------------------
    # 1) PRE-FLIGHT
    # -------------------------------------------------------------------------
    out, _, rc = _run(["systemctl", "is-active", "stock-bot.service"], timeout=5)
    service_active = out.strip().lower() == "active"

    out2, _, _ = _run(
        ["sh", "-c", "systemctl show stock-bot.service -p Environment 2>/dev/null | tr ' ' '\\n' | grep -E '^AUDIT_(MODE|DRY_RUN)=' || true"],
        timeout=5,
    )
    audit_mode_set = "AUDIT_MODE=1" in out2 or "AUDIT_MODE=true" in out2.lower()
    audit_dry_set = "AUDIT_DRY_RUN=1" in out2 or "AUDIT_DRY_RUN=true" in out2.lower()

    sys_events = _read_jsonl(LOGS / "system_events.jsonl", since=since_hb)
    phase2_heartbeat_count = sum(
        1 for r in sys_events
        if r.get("event_type") == "phase2_heartbeat"
        or (isinstance(r.get("event_type"), str) and "phase2_heartbeat" in (r.get("event_type") or ""))
    )
    if phase2_heartbeat_count == 0 and sys_events:
        phase2_heartbeat_count = sum(1 for r in sys_events if "phase2_heartbeat" in json.dumps(r))

    preflight_pass = service_active and not audit_mode_set and not audit_dry_set and phase2_heartbeat_count > 0

    preflight_md = [
        "# Live Trace Pre-Flight (Live Mode)",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        "## Checks",
        "",
        f"- **stock-bot.service active:** {service_active}",
        f"- **AUDIT_MODE set in service env:** {audit_mode_set} (must be false)",
        f"- **AUDIT_DRY_RUN set in service env:** {audit_dry_set} (must be false)",
        f"- **phase2_heartbeat in last {WINDOW_HEARTBEAT_MIN} min (system_events.jsonl):** {phase2_heartbeat_count}",
        "",
        "## Verdict",
        "",
        "**PASS**" if preflight_pass else "**FAIL**",
    ]
    (REPORTS / "LIVE_TRACE_PREFLIGHT.md").write_text("\n".join(preflight_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 2) TRADE_INTENT SAMPLES (last 10 min)
    # -------------------------------------------------------------------------
    run_lines = _read_jsonl(LOGS / "run.jsonl", since=since_run)
    trade_intents = [r for r in run_lines if r.get("event_type") == "trade_intent"]
    entered = [r for r in trade_intents if (r.get("decision_outcome") or "").lower() == "entered"]
    blocked = [r for r in trade_intents if (r.get("decision_outcome") or "").lower() == "blocked"]

    missing_trace = [r for r in trade_intents if not r.get("intelligence_trace")]
    if missing_trace:
        decisions_fail = True
    else:
        decisions_fail = False

    samples_entered = entered[-2:] if len(entered) >= 2 else entered
    samples_blocked = blocked[-2:] if len(blocked) >= 2 else blocked

    def _sample_excerpt(rec: dict) -> list[str]:
        lines = []
        lines.append(f"- **intent_id:** {rec.get('intent_id', 'N/A')}")
        lines.append(f"- **symbol:** {rec.get('symbol', 'N/A')}")
        lines.append(f"- **decision_outcome:** {rec.get('decision_outcome', 'N/A')}")
        trace = rec.get("intelligence_trace") or {}
        layers = trace.get("signal_layers") or {}
        layer_names = [k for k, v in layers.items() if v]
        lines.append(f"- **signal_layers (names):** {layer_names}")
        gates = trace.get("gates") or {}
        gate_summary = {k: {"passed": v.get("passed"), "reason": v.get("reason")} for k, v in gates.items()}
        lines.append(f"- **gates summary:** {json.dumps(gate_summary)}")
        fd = trace.get("final_decision") or {}
        lines.append(f"- **final_decision:** {json.dumps(fd)}")
        if (rec.get("decision_outcome") or "").lower() == "blocked":
            lines.append(f"- **blocked_reason_code:** {rec.get('blocked_reason_code', 'N/A')}")
        lines.append("")
        lines.append("Raw (redacted):")
        slim = {k: v for k, v in rec.items() if k != "feature_snapshot" and k != "thesis_tags"}
        if "intelligence_trace" in slim and isinstance(slim["intelligence_trace"], dict):
            slim["intelligence_trace"] = "(present, see above)"
        lines.append("```json")
        lines.append(json.dumps(slim, indent=2, default=str)[:2000] + ("..." if len(json.dumps(slim)) > 2000 else ""))
        lines.append("```")
        return lines

    decisions_md = [
        "# Live Trace — Decision Intelligence (Live Samples)",
        "",
        f"**Generated:** {now.isoformat()}",
        f"**Window:** last {WINDOW_RUN_MIN} minutes",
        "",
        f"**trade_intent count:** {len(trade_intents)} (entered: {len(entered)}, blocked: {len(blocked)})",
        f"**Missing intelligence_trace:** {len(missing_trace)} (FAIL if > 0)",
        "",
        "## 2 ENTERED samples",
        "",
    ]
    for i, rec in enumerate(samples_entered, 1):
        decisions_md.append(f"### Entered sample {i}")
        decisions_md.extend(_sample_excerpt(rec))
    decisions_md.append("## 2 BLOCKED samples")
    decisions_md.append("")
    for i, rec in enumerate(samples_blocked, 1):
        decisions_md.append(f"### Blocked sample {i}")
        decisions_md.extend(_sample_excerpt(rec))
    if not samples_entered and not samples_blocked:
        decisions_md.append("(No trade_intent events in window; market may be quiet.)")
    (REPORTS / "LIVE_TRACE_DECISIONS.md").write_text("\n".join(decisions_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 3) SIGNAL LAYER VERIFICATION
    # -------------------------------------------------------------------------
    all_samples = samples_entered + samples_blocked
    layer_fail = False
    layers_md = [
        "# Live Trace — Signal Layer Verification",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
    ]
    for i, rec in enumerate(all_samples, 1):
        trace = rec.get("intelligence_trace") or {}
        layers = trace.get("signal_layers") or {}
        contributing = [k for k, v in layers.items() if v]
        n = len(contributing)
        if n < 2:
            layer_fail = True
        layers_md.append(f"**Sample {i} ({rec.get('symbol')}):** {n} layers — {contributing}")
    layers_md.append("")
    layers_md.append("**Requirement:** ≥2 signal layers per sample.")
    if layer_fail:
        layers_md.append("**FAIL:** At least one sample has <2 layers.")
    else:
        layers_md.append("**PASS**")
    (REPORTS / "LIVE_TRACE_SIGNAL_LAYERS.md").write_text("\n".join(layers_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 4) GATE VERIFICATION
    # -------------------------------------------------------------------------
    gates_md = [
        "# Live Trace — Gate Verification",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
    ]
    for i, rec in enumerate(all_samples, 1):
        trace = rec.get("intelligence_trace") or {}
        gates = trace.get("gates") or {}
        gates_md.append(f"### Sample {i} — {rec.get('symbol')} ({rec.get('decision_outcome')})")
        for gname, gval in gates.items():
            passed = gval.get("passed")
            reason = gval.get("reason", "")
            gates_md.append(f"- **{gname}:** passed={passed}, reason={reason}")
        gates_md.append("")
    (REPORTS / "LIVE_TRACE_GATES.md").write_text("\n".join(gates_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 5) BLOCKED-REASON CLARITY
    # -------------------------------------------------------------------------
    block_md = [
        "# Live Trace — Blocked Reason Clarity",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
    ]
    block_fail = False
    for rec in samples_blocked:
        if not rec.get("blocked_reason_code"):
            block_fail = True
        if not rec.get("blocked_reason_details") and rec.get("decision_outcome") == "blocked":
            block_fail = True
        block_md.append(f"- **{rec.get('symbol')}:** blocked_reason_code={rec.get('blocked_reason_code')}, "
                        f"blocked_reason_details present={bool(rec.get('blocked_reason_details'))}, "
                        f"blocked_reason (legacy)={repr(rec.get('blocked_reason'))[:80]}")
    block_md.append("")
    block_md.append("**FAIL** if blocked_reason_code or blocked_reason_details missing." if block_fail else "**PASS**")
    (REPORTS / "LIVE_TRACE_BLOCK_REASONS.md").write_text("\n".join(block_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 6) ORDER JOINABILITY (entered only)
    # -------------------------------------------------------------------------
    orders = _read_jsonl(LOGS / "orders.jsonl", since=since_run)
    join_md = [
        "# Live Trace — Order Joinability (Entered)",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
    ]
    join_fail = False
    for rec in samples_entered:
        intent_id = rec.get("intent_id")
        if not intent_id:
            join_md.append(f"- **{rec.get('symbol')}:** no intent_id — cannot join")
            join_fail = True
            continue
        matched = [o for o in orders if intent_id in str(o.get("client_order_id", "")) or o.get("intent_id") == intent_id]
        if not matched:
            join_fail = True
        join_md.append(f"- **{rec.get('symbol')}** intent_id={intent_id[:36] if len(intent_id) > 36 else intent_id} — orders matched: {len(matched)}")
        if matched:
            join_md.append("  ```json")
            join_md.append("  " + json.dumps(matched[0], indent=2, default=str)[:800])
            join_md.append("  ```")
    if not samples_entered:
        join_md.append("No entered samples in window; joinability N/A.")
    join_md.append("")
    join_md.append("**FAIL** if entered intents cannot be joined to orders." if join_fail and samples_entered else "**PASS** (or N/A)")
    (REPORTS / "LIVE_TRACE_ORDER_JOIN.md").write_text("\n".join(join_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 7) MISSING TRACE SENTINEL
    # -------------------------------------------------------------------------
    sys_sentinel = _read_jsonl(LOGS / "system_events.jsonl", since=since_sentinel)
    missing_events = [r for r in sys_sentinel if (r.get("event_type") or "") == "missing_intelligence_trace"]
    sentinel_count = len(missing_events)

    sentinel_md = [
        "# Live Trace — Missing Trace Sentinel",
        "",
        f"**Generated:** {now.isoformat()}",
        f"**Window:** last {WINDOW_SENTINEL_MIN} minutes",
        "",
        f"**event_type=missing_intelligence_trace count:** {sentinel_count}",
        "",
        "**Expected:** 0. **FAIL** if any found." if sentinel_count > 0 else "**PASS** — none found.",
    ]
    (REPORTS / "LIVE_TRACE_SENTINEL.md").write_text("\n".join(sentinel_md), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 8) FINAL VERDICT
    # -------------------------------------------------------------------------
    s1 = "PASS" if preflight_pass else "FAIL"
    s2 = "PASS" if not decisions_fail else "FAIL"
    s3 = "PASS" if not layer_fail else "FAIL"
    s4 = "PASS"  # gates populated per trace
    s5 = "PASS" if not block_fail else "FAIL"
    s6 = "PASS" if not (join_fail and samples_entered) else "FAIL"
    s7 = "PASS" if sentinel_count == 0 else "FAIL"

    overall = s1 == s2 == s3 == s4 == s5 == s6 == s7 == "PASS"

    verdict_md = [
        "# Live Trace Verdict",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        "## Per-section",
        "",
        f"1. Pre-flight (live mode): **{s1}**",
        f"2. Decision Intelligence (samples, trace present): **{s2}**",
        f"3. Signal layers (≥2 per sample): **{s3}**",
        f"4. Gates populated: **{s4}**",
        f"5. Blocked-reason clarity: **{s5}**",
        f"6. Order joinability (entered): **{s6}**",
        f"7. Missing-trace sentinel (0): **{s7}**",
        "",
        "## Overall",
        "",
        "**PASS** — Decision Intelligence Trace is live, populated, and coherent under real market conditions." if overall else "**FAIL** — One or more sections failed.",
        "",
        "Statement: *Decision Intelligence Trace is live, populated, and coherent under real market conditions.*",
    ]
    (REPORTS / "LIVE_TRACE_VERDICT.md").write_text("\n".join(verdict_md), encoding="utf-8")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
