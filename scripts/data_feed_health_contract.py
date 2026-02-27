#!/usr/bin/env python3
"""
Data feed health contract (droplet). All required data feeds must be present and fresh.
Writes reports/data_integrity/DATA_FEED_HEALTH_CONTRACT.md and .json.
PASS only if all required feeds present+fresh AND NO_BARS rate below threshold.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "data_integrity"
OUT_MD = OUT_DIR / "DATA_FEED_HEALTH_CONTRACT.md"
OUT_JSON = OUT_DIR / "DATA_FEED_HEALTH_CONTRACT.json"
UW_FAILURE_EVENTS = REPO / "reports" / "uw_health" / "uw_failure_events.jsonl"
BARS_DIR = REPO / "data" / "bars"
UW_OUT_DIR = REPO / "board" / "eod" / "out"
ALPACA_WS_HEALTH_JSONL = REPO / "reports" / "data_integrity" / "alpaca_ws_health.jsonl"
NO_BARS_RATE_THRESHOLD = float(__import__("os").environ.get("DATA_FEED_NO_BARS_RATE_THRESHOLD", "0.05"))  # FAIL if NO_BARS rate > 5%
MAX_AGE_DAYS_UW = 2  # UW root cause file must be within this many days
BARS_MTIME_MAX_AGE_HOURS = 8  # bars dir/file mtime must be within this (session freshness)
WS_LAST_MSG_MAX_AGE_SECONDS = 300  # during market hours, FAIL if no ws message in 5 min
WS_TICK_AGE_WORST_SECONDS = 600  # aggregate worst-case tick age for reporting


def _uw_root_cause_status() -> tuple[bool, str, str]:
    if not UW_OUT_DIR.exists():
        return False, "board/eod/out missing", "Create board/eod/out and run EOD (run_stock_quant_officer_eod.py) to produce uw_root_cause.json"
    best_date = ""
    best_path = None
    for d in UW_OUT_DIR.iterdir():
        if d.is_dir() and len(d.name) == 10 and d.name[4] == "-":
            p = d / "uw_root_cause.json"
            if p.exists() and d.name > best_date:
                best_date = d.name
                best_path = p
    if not best_date:
        return False, "no uw_root_cause.json found in board/eod/out", "Run EOD job: python board/eod/run_stock_quant_officer_eod.py (or equivalent) to build uw_root_cause.json"
    try:
        file_dt = datetime.strptime(best_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_days = (now - file_dt).total_seconds() / 86400
        if age_days > MAX_AGE_DAYS_UW:
            return False, f"uw_root_cause stale (date={best_date}, age_days={age_days:.1f})", "Re-run EOD for current date to refresh board/eod/out/<date>/uw_root_cause.json"
        return True, f"uw_root_cause present date={best_date}", ""
    except Exception as e:
        return False, str(e), "Fix EOD output path and re-run EOD"


def _bars_status() -> tuple[bool, str, str]:
    if not BARS_DIR.exists():
        return False, "data/bars missing", "Create data/bars and run bars fetch (e.g. scripts/run_bars_pipeline.py or Alpaca bars job)"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc)
    for date_str in (today, yesterday):
        d = BARS_DIR / date_str
        if d.exists() and d.is_dir():
            files = list(d.glob("*_1Min.json")) or list(d.glob("*_5Min.json")) or list(d.glob("*_15Min.json"))
            if files:
                # Check mtime of first file: must be within BARS_MTIME_MAX_AGE_HOURS
                try:
                    mtime = files[0].stat().st_mtime
                    age_h = (now.timestamp() - mtime) / 3600
                    if age_h > BARS_MTIME_MAX_AGE_HOURS:
                        return False, f"bars for {date_str} stale (mtime age_h={age_h:.1f})", "Re-run bars fetch for intraday session; ensure Alpaca bars pipeline is running"
                except Exception:
                    pass
                return True, f"bars present for {date_str} ({len(files)} files)", ""
    return False, "no bars for today or yesterday (1m/5m/15m)", "Run bars pipeline for most recent session: scripts/run_bars_pipeline.py or enable Alpaca bars job"


def _is_market_hours_utc(now: datetime | None = None) -> bool:
    """US equity 13:30-20:00 UTC (EDT), weekdays."""
    t = now or datetime.now(timezone.utc)
    if t.weekday() >= 5:
        return False
    h = t.hour + t.minute / 60.0 + t.second / 3600.0
    return 13.5 <= h < 20.0


def _websocket_status() -> tuple[bool, str, str, float]:
    """Returns (ok, message, recommended_repair, last_tick_age_seconds)."""
    if not ALPACA_WS_HEALTH_JSONL.exists():
        return False, "alpaca_ws_health.jsonl missing (collector not running)", "Start Alpaca WS collector: python scripts/alpaca_ws_collector.py (or run as service)", float("inf")
    lines = ALPACA_WS_HEALTH_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if not lines:
        return False, "alpaca_ws_health empty", "Start Alpaca WS collector: python scripts/alpaca_ws_collector.py", float("inf")
    try:
        rec = json.loads(lines[-1])
    except Exception:
        return False, "alpaca_ws_health last line unparseable", "Restart Alpaca WS collector", float("inf")
    connected = rec.get("connected") is True
    last_msg = float(rec.get("last_msg_ts") or 0)
    last_bar = float(rec.get("last_bar_ts") or 0)
    now_ts = datetime.now(timezone.utc).timestamp()
    last_tick_age = min(
        (now_ts - last_msg) if last_msg else float("inf"),
        (now_ts - last_bar) if last_bar else float("inf"),
    )
    if last_tick_age == float("inf"):
        last_tick_age = 999999.0
    if not connected:
        return False, "websocket disconnected", "Restart Alpaca WS collector: python scripts/alpaca_ws_collector.py", last_tick_age
    if _is_market_hours_utc() and last_tick_age > WS_LAST_MSG_MAX_AGE_SECONDS:
        return False, f"websocket stale during market hours (last_tick_age_seconds={last_tick_age:.0f})", "Restart Alpaca WS collector or check Alpaca data API key", last_tick_age
    return True, f"websocket connected, last_tick_age_seconds={last_tick_age:.0f}", "", last_tick_age


def _no_bars_rate_24h() -> tuple[float, int, int]:
    if not UW_FAILURE_EVENTS.exists():
        return 0.0, 0, 0
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).timestamp()
    total = 0
    no_bars = 0
    for line in UW_FAILURE_EVENTS.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            ts = float(r.get("ts") or r.get("event_ts") or 0)
            if ts < cutoff:
                continue
            total += 1
            ind = r.get("missing_data_indicators") or {}
            if ind.get("no_bars") or ind.get("bars_empty"):
                no_bars += 1
        except Exception:
            continue
    rate = (no_bars / total) if total else 0.0
    return rate, no_bars, total


def _recommended_repair(reasons: list[str]) -> list[str]:
    out = []
    for r in (reasons or []):
        if "websocket" in r.lower():
            out.append("Restart Alpaca WS collector: python scripts/alpaca_ws_collector.py (or systemd service)")
        elif "uw_root_cause" in r.lower() or ("stale" in r.lower() and "uw" in r.lower()):
            out.append("Re-run EOD: python board/eod/run_stock_quant_officer_eod.py (or equivalent)")
        elif "bars" in r.lower() and "missing" in r.lower():
            out.append("Run bars pipeline: scripts/run_bars_pipeline.py or enable Alpaca bars job")
        elif "no_bars" in r.lower() or "NO_BARS rate" in r:
            out.append("Fix bars pipeline and backfill missing dates; then re-run EOD")
        elif "stale" in r.lower() and "bars" in r.lower():
            out.append("Re-run bars fetch for current session")
        else:
            out.append("Check data pipeline and re-run required jobs")
    return list(dict.fromkeys(out))  # dedupe


def main() -> int:
    import os as _os
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reasons: list[str] = []
    recommended: list[str] = []
    checks = {}

    uw_ok, uw_msg, uw_repair = _uw_root_cause_status()
    checks["uw_root_cause"] = {"pass": uw_ok, "message": uw_msg, "recommended_repair": uw_repair or None}
    if not uw_ok:
        reasons.append(uw_msg)
        if uw_repair:
            recommended.append(uw_repair)

    bars_ok, bars_msg, bars_repair = _bars_status()
    checks["alpaca_bars"] = {"pass": bars_ok, "message": bars_msg, "recommended_repair": bars_repair or None}
    if not bars_ok:
        reasons.append(bars_msg)
        if bars_repair:
            recommended.append(bars_repair)

    no_bars_rate, no_bars_count, events_24h = _no_bars_rate_24h()
    no_bars_ok = no_bars_rate <= NO_BARS_RATE_THRESHOLD or events_24h == 0
    checks["no_bars_rate_24h"] = {"pass": no_bars_ok, "rate": no_bars_rate, "no_bars_count": no_bars_count, "total_events": events_24h}
    if not no_bars_ok:
        reasons.append(f"NO_BARS rate {no_bars_rate:.2%} > threshold {NO_BARS_RATE_THRESHOLD:.0%}")
        recommended.append("Fix bars pipeline and backfill; re-run EOD for affected date")

    ws_ok, ws_msg, ws_repair, last_tick_age_sec = _websocket_status()
    checks["websocket"] = {"pass": ws_ok, "message": ws_msg, "recommended_repair": ws_repair or None, "last_tick_age_seconds": last_tick_age_sec}
    if _is_market_hours_utc() and not ws_ok:
        reasons.append(ws_msg)
        if ws_repair:
            recommended.append(ws_repair)

    recommended = recommended or _recommended_repair(reasons)
    verdict = "PASS" if not reasons else "FAIL"
    payload = {
        "verdict": verdict,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "reasons_fail": reasons,
        "recommended_repair": recommended[:5],
        "no_bars_rate_24h": no_bars_rate,
        "no_bars_count_24h": no_bars_count,
        "events_24h": events_24h,
        "websocket_connected": ws_ok,
        "last_tick_age_seconds": last_tick_age_sec,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Data feed health contract",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"## Verdict: **{verdict}**",
        "",
        "## Checks",
        "",
        f"- uw_root_cause: **{'PASS' if uw_ok else 'FAIL'}** — {uw_msg}",
        f"- alpaca_bars: **{'PASS' if bars_ok else 'FAIL'}** — {bars_msg}",
        f"- no_bars_rate_24h: **{'PASS' if no_bars_ok else 'FAIL'}** — rate={no_bars_rate:.2%} (no_bars={no_bars_count}, total={events_24h}), threshold={NO_BARS_RATE_THRESHOLD:.0%}",
        f"- websocket: **{'PASS' if ws_ok else 'FAIL'}** — {ws_msg}",
        "",
    ]
    if reasons:
        lines.extend(["## Reasons (FAIL)", ""] + [f"- {r}" for r in reasons[:10]] + ["", "## Recommended repair", ""] + [f"- {r}" for r in recommended[:5]] + [""])
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    # Auto-repair on FAIL (safe, idempotent)
    REPAIR_LOG = REPO / "reports" / "data_integrity" / "data_feed_repair_attempts.jsonl"
    INCIDENTS_DIR = REPO / "reports" / "incidents"
    if verdict == "FAIL":
        repair_ts = datetime.now(timezone.utc).isoformat()
        repair_actions = []
        repair_success = False
        try:
            if not bars_ok:
                from data.bars_loader import load_bars
                date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                for sym in ["SPY", "QQQ"]:  # probe symbols
                    load_bars(sym, date_str, "1Min", use_cache=True, fetch_if_missing=True)
                repair_actions.append("bars_fetch_probe")
                repair_success = True
        except Exception as e:
            repair_actions.append(f"bars_fetch_failed:{e!s}")
        if not ws_ok and _is_market_hours_utc():
            repair_actions.append("restart_websocket_collector_recommended")
        try:
            if not uw_ok:
                from board.eod.root_cause import build_uw_root_cause
                date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                out_dir = REPO / "board" / "eod" / "out" / date_str
                out_dir.mkdir(parents=True, exist_ok=True)
                data = build_uw_root_cause(REPO, date_str, window_days=7)
                (out_dir / "uw_root_cause.json").write_text(json.dumps(data, default=str), encoding="utf-8")
                repair_actions.append("recompute_uw_root_cause")
                repair_success = True
        except Exception as e:
            repair_actions.append(f"recompute_uw_failed:{e!s}")
        REPAIR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with REPAIR_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": repair_ts, "verdict": verdict, "repair_actions": repair_actions, "repair_success": repair_success, "reasons": reasons}, default=str) + "\n")
        # Two consecutive failures → incident
        repair_lines = REPAIR_LOG.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        last_two = [json.loads(l) for l in repair_lines[-2:] if l.strip()]
        if len(last_two) >= 2 and not last_two[-1].get("repair_success") and not last_two[-2].get("repair_success"):
            INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
            inc_path = INCIDENTS_DIR / f"data_feed_incident_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
            inc_path.write_text(
                "# Data feed incident (auto)\n\nTwo consecutive contract FAILs with repair attempts unsuccessful.\n\n"
                f"- First: {last_two[-2].get('ts')} — {last_two[-2].get('repair_actions')}\n"
                f"- Second: {last_two[-1].get('ts')} — {last_two[-1].get('repair_actions')}\n\n"
                f"Reasons: {reasons}\n\nRecommended: {recommended}\n",
                encoding="utf-8",
            )
    print(f"Wrote {OUT_MD} and {OUT_JSON}; verdict={verdict}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
