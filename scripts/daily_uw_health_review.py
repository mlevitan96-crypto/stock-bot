#!/usr/bin/env python3
"""
Daily AI review job: scan reports/uw_health/uw_failure_events.jsonl,
run uw_classification_contradictions and data_feed_health_contract,
write reports/uw_health/daily_uw_health_review.md with verdicts and actionable fixes.
Run on droplet (e.g. cron daily). No strategy tuning.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
UW_FAILURE_EVENTS = REPO / "reports" / "uw_health" / "uw_failure_events.jsonl"
OUT_MD = REPO / "reports" / "uw_health" / "daily_uw_health_review.md"
CONTRADICTIONS_MD = REPO / "reports" / "uw_health" / "uw_classification_contradictions.md"
DATA_FEED_JSON = REPO / "reports" / "data_integrity" / "DATA_FEED_HEALTH_CONTRACT.json"
DEFER_RETRY_EVENTS = REPO / "reports" / "uw_health" / "uw_defer_retry_events.jsonl"
DEFERRED_CANDIDATES = REPO / "reports" / "uw_health" / "uw_deferred_candidates.jsonl"
REPAIR_ATTEMPTS = REPO / "reports" / "data_integrity" / "data_feed_repair_attempts.jsonl"
UW_API_ERRORS = REPO / "reports" / "uw_health" / "uw_api_errors.jsonl"
UW_DEFER_MAX_MIN = int(__import__("os").environ.get("UW_DEFER_MAX_MINUTES", "120"))


def _is_market_hours_utc() -> bool:
    t = datetime.now(timezone.utc)
    if t.weekday() >= 5:
        return False
    h = t.hour + t.minute / 60.0 + t.second / 3600.0
    return 13.5 <= h < 20.0


def load_events(limit: int = 50000, window_days: int = 1) -> list[dict]:
    if not UW_FAILURE_EVENTS.exists():
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).timestamp()
    out = []
    for line in UW_FAILURE_EVENTS.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            ts = float(r.get("ts") or r.get("event_ts") or 0)
            if ts >= cutoff:
                out.append(r)
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def main() -> int:
    # Run governance jobs
    contradictions_rc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "uw_classification_contradictions.py")],
        cwd=str(REPO), capture_output=True, timeout=60,
    )
    contract_rc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "data_feed_health_contract.py")],
        cwd=str(REPO), capture_output=True, timeout=60,
    )
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "uw_defer_retry_engine.py")],
        cwd=str(REPO), capture_output=True, timeout=120,
    )
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "uw_api_integrity_summary.py")],
        cwd=str(REPO), capture_output=True, timeout=30,
    )
    contradictions_verdict = "FAIL" if contradictions_rc.returncode != 0 else "PASS"
    contradictions_count = 0
    if CONTRADICTIONS_MD.exists():
        try:
            t = CONTRADICTIONS_MD.read_text(encoding="utf-8")
            for line in t.splitlines():
                if "Contradiction count:" in line:
                    try:
                        contradictions_count = int(line.split(":")[-1].strip().strip("**"))
                    except Exception:
                        pass
                    break
        except Exception:
            pass
    data_feed_verdict = "PASS"
    data_feed_reasons: list[str] = []
    no_bars_rate_24h = 0.0
    websocket_connected = True
    last_tick_age_seconds = 0.0
    data_feed_checks: dict = {}
    if DATA_FEED_JSON.exists():
        try:
            payload = json.loads(DATA_FEED_JSON.read_text(encoding="utf-8"))
            data_feed_checks = payload.get("checks") or {}
            data_feed_verdict = payload.get("verdict", "PASS")
            data_feed_reasons = payload.get("reasons_fail") or []
            no_bars_rate_24h = float(payload.get("no_bars_rate_24h") or 0)
            websocket_connected = payload.get("websocket_connected", True)
            last_tick_age_seconds = float(payload.get("last_tick_age_seconds") or 0)
            ws_check = data_feed_checks.get("websocket") or {}
            if "pass" in ws_check:
                websocket_connected = ws_check.get("pass", True)
            if "last_tick_age_seconds" in ws_check:
                last_tick_age_seconds = float(ws_check.get("last_tick_age_seconds") or 0)
        except Exception:
            pass

    # UW API errors (last 24h) counts by type
    uw_api_errors_by_type: dict[str, int] = {}
    if UW_API_ERRORS.exists():
        cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).timestamp()
        for line in UW_API_ERRORS.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                if float(r.get("ts") or 0) < cutoff_24h:
                    continue
                t = r.get("uw_api_error_type") or "unknown"
                uw_api_errors_by_type[t] = uw_api_errors_by_type.get(t, 0) + 1
            except Exception:
                continue

    # Deferred outcomes (last 24h from retry events)
    cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).timestamp()
    defer_total = 0
    defer_resolved = 0
    defer_expired = 0
    if DEFER_RETRY_EVENTS.exists():
        for line in DEFER_RETRY_EVENTS.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                ts = float(r.get("retry_ts") or r.get("first_defer_ts") or 0)
                if ts < cutoff_24h:
                    continue
                defer_total += 1
                out = (r.get("final_outcome") or "").strip()
                if out == "resolved":
                    defer_resolved += 1
                elif out == "expired_then_penalized":
                    defer_expired += 1
            except Exception:
                continue
    defer_resolved_pct = (100.0 * defer_resolved / defer_total) if defer_total else 0.0
    defer_expired_pct = (100.0 * defer_expired / defer_total) if defer_total else 0.0

    # Repair attempts (data feed)
    repair_count = 0
    repair_success_count = 0
    if REPAIR_ATTEMPTS.exists():
        for line in REPAIR_ATTEMPTS.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                repair_count += 1
                if r.get("repair_success"):
                    repair_success_count += 1
            except Exception:
                continue
    repair_success_rate = (100.0 * repair_success_count / repair_count) if repair_count else 0.0

    # ALL REQUIRED DATA FEEDS FIRING: YES if contract PASS and (websocket OK or not market hours)
    all_feeds_firing = data_feed_verdict == "PASS" and (websocket_connected or not _is_market_hours_utc())

    # Deferred persist beyond max (fail condition)
    deferred_persist_fail = False
    if DEFERRED_CANDIDATES.exists():
        now_ts = datetime.now(timezone.utc).timestamp()
        max_ts = now_ts - UW_DEFER_MAX_MIN * 60
        expired_syms = set()
        if (REPO / "state" / "uw_defer_expired_symbols.json").exists():
            try:
                d = json.loads((REPO / "state" / "uw_defer_expired_symbols.json").read_text(encoding="utf-8"))
                expired_syms = set(d.get("symbols", []) if isinstance(d, dict) else d)
            except Exception:
                pass
        for line in DEFERRED_CANDIDATES.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                first = int(r.get("first_defer_ts") or 0)
                sym = r.get("symbol", "")
                if first < max_ts and sym and sym not in expired_syms:
                    deferred_persist_fail = True
                    break
            except Exception:
                continue

    events = load_events(window_days=1)
    by_class = Counter(r.get("failure_class") or "UNKNOWN" for r in events)
    by_decision = Counter(r.get("decision_taken") or "unknown" for r in events)
    by_symbol = defaultdict(int)
    for r in events:
        by_symbol[r.get("symbol") or "?"] += 1
    top_symbols = sorted(by_symbol.items(), key=lambda x: -x[1])[:20]

    lines = [
        "# Daily UW health review",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Events in last 24h: **{len(events)}**",
        "",
        "## Contradictions verdict",
        "",
        f"- **{contradictions_verdict}** (count: {contradictions_count})",
        "",
        "## Data feed contract verdict",
        "",
        f"- **{data_feed_verdict}**",
        "",
        "## ALL REQUIRED DATA FEEDS FIRING",
        "",
        f"- **{'YES' if all_feeds_firing else 'NO'}**",
        "",
        "## UW API errors (last 24h)",
        "",
    ]
    for etype, count in sorted(uw_api_errors_by_type.items(), key=lambda x: -x[1]):
        lines.append(f"- **{etype}**: {count}")
    if not uw_api_errors_by_type:
        lines.append("- None recorded.")
    lines.extend([
        "",
        "## Websocket health",
        "",
        f"- Connected: **{'YES' if websocket_connected else 'NO'}**, last_tick_age_seconds: **{last_tick_age_seconds:.0f}**",
        "",
        "## Bar coverage (from contract)",
        "",
        f"- alpaca_bars: **{'PASS' if data_feed_checks.get('alpaca_bars', {}).get('pass') else 'FAIL/unknown'}**",
        "",
        "## NO_BARS rate (last 24h)",
        "",
        f"- **{no_bars_rate_24h:.2%}**",
        "",
        "## Deferred outcomes (last 24h)",
        "",
        f"- Total retry events: **{defer_total}**",
        f"- Resolved: **{defer_resolved}** ({defer_resolved_pct:.1f}%)",
        f"- Expired then penalized: **{defer_expired}** ({defer_expired_pct:.1f}%)",
        "",
        "## Repair attempts (data feed)",
        "",
        f"- Count: **{repair_count}**, success rate: **{repair_success_rate:.1f}%**",
        "",
        "## Dominant failure classes",
        "",
    ]
    for cls, count in by_class.most_common(10):
        pct = 100.0 * count / len(events) if events else 0
        lines.append(f"- **{cls}**: {count} ({pct:.1f}%)")
    lines.extend([
        "",
        "## Decision distribution",
        "",
    ])
    for dec, count in by_decision.most_common(5):
        lines.append(f"- {dec}: {count}")
    lines.extend([
        "",
        "## Top affected symbols",
        "",
    ])
    for sym, count in top_symbols:
        lines.append(f"- {sym}: {count}")
    lines.extend([
        "",
        "## Proposed actions",
        "",
    ])
    if not events:
        lines.append("- No failure events in window. No action required.")
    else:
        if by_class.get("UW_MISSING_DATA", 0) > 0:
            lines.append("- **UW_MISSING_DATA**: Ensure EOD runs and writes `board/eod/out/<date>/uw_root_cause.json`. Consider bar backfill for missing symbols; refresh UW cache (attribution/blocked logs) so root cause has candidates.")
        if by_class.get("UW_STALE_DATA", 0) > 0:
            lines.append("- **UW_STALE_DATA**: Run EOD more frequently or ensure latest date is used; consider cache TTL and invalidation for uw_root_cause.")
        if by_class.get("UW_CONTRADICTORY_DATA", 0) > 0:
            lines.append("- **UW_CONTRADICTORY_DATA**: Align global vs per-symbol quality in root cause build; audit consistency checks.")
        if by_class.get("UW_LOW_QUALITY_SIGNAL", 0) > 0:
            lines.append("- **UW_LOW_QUALITY_SIGNAL**: Genuine weak signal; no data fix. Optional: review threshold or signal pipeline if volume is unexpectedly high.")
        if by_class.get("UW_INTERNAL_ERROR", 0) > 0:
            lines.append("- **UW_INTERNAL_ERROR**: Inspect logs for exceptions in load/diagnose; fix parsing or file access.")
        lines.append("")
        lines.append("## Data pipeline / cache / backfill suggestions")
        lines.append("")
        lines.append("- **Data pipeline**: Ensure `board/eod/run_stock_quant_officer_eod.py` (or equivalent) runs and produces `uw_root_cause.json` for current date.")
        lines.append("- **Cache policies**: UW root cause is read from latest date dir; consider daily refresh before market open.")
        lines.append("- **Backfill schedules**: If bars are missing, run bars pipeline for affected symbols/dates; then re-run EOD for that date.")
    if data_feed_reasons:
        lines.extend(["", "## Data feed contract fail reasons (top)", ""] + [f"- {r}" for r in data_feed_reasons[:5]] + [""])
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    # Terminal output (concise)
    print("")
    print(f"Contradictions: {contradictions_verdict} ({contradictions_count})")
    print(f"Deferred outcomes last 24h: count={defer_total}, resolved={defer_resolved_pct:.0f}%, expired_then_penalized={defer_expired_pct:.0f}%")
    print(f"Data feed contract: {data_feed_verdict}" + (f" — top reasons: {'; '.join(data_feed_reasons[:3])}" if data_feed_reasons else ""))
    print(f"Repair attempts: count={repair_count}, success rate={repair_success_rate:.1f}%")
    print(f"NO_BARS rate last 24h: {no_bars_rate_24h:.2%}")
    print(f"ALL REQUIRED DATA FEEDS FIRING: {'YES' if all_feeds_firing else 'NO'}")
    print(f"UW API errors last 24h: {dict(uw_api_errors_by_type) or 'none'}")
    print(f"Websocket health: {'PASS' if websocket_connected else 'FAIL'} (last_tick_age_seconds={last_tick_age_seconds:.0f})")
    websocket_fail_market_hours = _is_market_hours_utc() and not websocket_connected
    return 1 if (contradictions_verdict == "FAIL" or data_feed_verdict == "FAIL" or deferred_persist_fail or websocket_fail_market_hours) else 0


if __name__ == "__main__":
    sys.exit(main())
