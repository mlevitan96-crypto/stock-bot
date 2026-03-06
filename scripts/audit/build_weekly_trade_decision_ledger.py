#!/usr/bin/env python3
"""
Build weekly trade decision ledger from evidence (exit_attribution, blocked_trades, score_snapshot).
Output: WEEKLY_TRADE_DECISION_LEDGER_<date>.jsonl, WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_<date>.json.
Includes executed, blocked, counter_intel_blocked, validation_failed; weekly counts and rates.

Usage:
  python scripts/audit/build_weekly_trade_decision_ledger.py [--date YYYY-MM-DD] [--base-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _parse_ts(v) -> int | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return int(float(v))
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def _ts_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _load_exit_attribution_7d(base: Path, start_ts: int, end_ts: int) -> list[dict]:
    out = []
    for p in [base / "logs" / "exit_attribution.jsonl", base / "reports" / "audit" / "weekly_evidence_stage" / "logs" / "exit_attribution.jsonl"]:
        if not p.exists():
            continue
        for r in _iter_jsonl(p):
            ts = _parse_ts(r.get("exit_timestamp") or r.get("ts") or r.get("closed_at"))
            if ts is None:
                ts = _parse_ts(r.get("entry_timestamp"))
            if ts is not None and start_ts <= ts <= end_ts:
                out.append(r)
        break
    return out


def _load_blocked_7d(base: Path, start_ts: int, end_ts: int) -> list[dict]:
    out = []
    for p in [base / "state" / "blocked_trades.jsonl", base / "reports" / "audit" / "weekly_evidence_stage" / "state" / "blocked_trades.jsonl"]:
        if not p.exists():
            continue
        for r in _iter_jsonl(p):
            ts = _parse_ts(r.get("timestamp") or r.get("ts"))
            if ts is None:
                continue
            if start_ts <= ts <= end_ts:
                out.append(r)
        break
    return out


def _load_snapshots_7d(base: Path, start_ts: int, end_ts: int, limit: int | None) -> list[dict]:
    out = []
    for p in [base / "logs" / "score_snapshot.jsonl", base / "reports" / "audit" / "weekly_evidence_stage" / "logs" / "score_snapshot.jsonl"]:
        if not p.exists():
            continue
        for r in _iter_jsonl(p):
            ts = _parse_ts(r.get("ts") or r.get("ts_iso"))
            if ts is None:
                continue
            if start_ts <= ts <= end_ts:
                out.append(r)
        if limit:
            out = out[-limit:]
        break
    return out


def _is_counter_intel_reason(reason: str) -> bool:
    if not reason:
        return False
    r = (reason or "").lower()
    return "counter" in r or "counter_intel" in r or "ci_block" in r or "intel" in r


def _is_validation_failure(reason: str) -> bool:
    if not reason:
        return False
    r = (reason or "").lower()
    return "validation" in r or "order_validation" in r or "validat" in r


def exit_row_to_ledger_event(r: dict) -> dict:
    ts = _parse_ts(r.get("exit_timestamp") or r.get("ts") or r.get("closed_at")) or 0
    return {
        "ts": ts,
        "ts_iso": _ts_iso(ts) if ts else "",
        "symbol": r.get("symbol", ""),
        "direction": r.get("direction", ""),
        "strategy_variant_id": r.get("strategy_variant_id") or r.get("variant_id", ""),
        "decision": "executed",
        "reason_codes": [],
        "exit_reason": r.get("exit_reason", ""),
        "hold_time_minutes": r.get("time_in_trade_minutes"),
        "realized_pnl": r.get("pnl"),
        "realized_pnl_pct": r.get("pnl_pct"),
        "regime_tags": [r.get("entry_regime", ""), r.get("exit_regime", "")],
        "sizing": r.get("qty"),
        "entry_features_ref": r.get("entry_timestamp"),
        "exit_features_ref": r.get("exit_timestamp"),
    }


def blocked_row_to_ledger_event(r: dict) -> dict:
    ts = _parse_ts(r.get("timestamp") or r.get("ts")) or 0
    reason = r.get("reason") or r.get("block_reason") or ""
    ci = _is_counter_intel_reason(reason)
    val = _is_validation_failure(reason)
    if ci:
        decision = "counter_intel_blocked"
    elif val:
        decision = "validation_failed"
    else:
        decision = "blocked"
    return {
        "ts": ts,
        "ts_iso": _ts_iso(ts) if ts else "",
        "symbol": r.get("symbol", ""),
        "direction": r.get("direction", ""),
        "strategy_variant_id": r.get("strategy_variant_id", ""),
        "decision": decision,
        "reason_codes": [reason] if reason else [],
        "block_reason": reason,
        "entry_features_ref": None,
        "exit_features_ref": None,
        "hold_time_minutes": None,
        "realized_pnl": None,
        "regime_tags": [],
        "sizing": r.get("size") or r.get("qty"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build weekly trade decision ledger")
    ap.add_argument("--date", default=None, help="End date YYYY-MM-DD (default: today)")
    ap.add_argument("--base-dir", default=None, help="Repo or evidence stage root (default: REPO)")
    ap.add_argument("--days", type=int, default=7, help="Primary window days (default 7)")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    if args.date:
        try:
            end_dt = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print("Invalid --date", file=sys.stderr)
            return 1
    else:
        end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=args.days)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    date_str = end_dt.strftime("%Y-%m-%d")

    executed = _load_exit_attribution_7d(base, start_ts, end_ts)
    blocked_rows = _load_blocked_7d(base, start_ts, end_ts)
    snapshots = _load_snapshots_7d(base, start_ts, end_ts, limit=5000)

    events: list[dict] = []
    for r in executed:
        events.append(exit_row_to_ledger_event(r))
    for r in blocked_rows:
        events.append(blocked_row_to_ledger_event(r))

    # Optionally add snapshot-derived blocked events not already in blocked_trades (by ts+symbol)
    blocked_keys = {(e["ts"], e["symbol"]) for e in events if e.get("decision") != "executed"}
    for r in snapshots:
        ts = _parse_ts(r.get("ts") or r.get("ts_iso"))
        if ts is None:
            continue
        if start_ts <= ts <= end_ts:
            gates = r.get("gates", {})
            block_reason = gates.get("block_reason") or r.get("block_reason")
            if block_reason and (ts, r.get("symbol", "")) not in blocked_keys:
                ev = blocked_row_to_ledger_event({"ts": ts, "timestamp": ts, "symbol": r.get("symbol", ""), "reason": block_reason, "block_reason": block_reason})
                events.append(ev)
                blocked_keys.add((ts, ev["symbol"]))

    events.sort(key=lambda x: (x.get("ts") or 0, x.get("symbol", "")))

    # Summary counts
    by_decision = defaultdict(int)
    blocked_reasons: defaultdict[str, int] = defaultdict(int)
    ci_reasons: defaultdict[str, int] = defaultdict(int)
    validation_count = 0
    for e in events:
        d = e.get("decision", "other")
        by_decision[d] += 1
        if d == "blocked":
            for r in e.get("reason_codes") or []:
                if r:
                    blocked_reasons[r] += 1
        elif d == "counter_intel_blocked":
            for r in e.get("reason_codes") or []:
                if r:
                    ci_reasons[r] += 1
        elif d == "validation_failed":
            validation_count += 1

    total = len(events)
    executed_count = by_decision["executed"]
    blocked_count = by_decision["blocked"]
    ci_count = by_decision["counter_intel_blocked"]
    validation_failed_count = by_decision["validation_failed"]
    validation_rate = (validation_failed_count / total * 100) if total else 0

    summary = {
        "date": date_str,
        "window_start": start_dt.isoformat(),
        "window_end": end_dt.isoformat(),
        "window_days": args.days,
        "total_events": total,
        "executed_count": executed_count,
        "blocked_count": blocked_count,
        "counter_intel_blocked_count": ci_count,
        "validation_failed_count": validation_failed_count,
        "other_count": by_decision.get("other", 0),
        "validation_failure_rate_pct": round(validation_rate, 2),
        "top_blocked_reasons": dict(sorted(blocked_reasons.items(), key=lambda x: -x[1])[:15]),
        "top_ci_reasons": dict(sorted(ci_reasons.items(), key=lambda x: -x[1])[:10]),
        "opportunity_cost_proxy_note": "Blocked-when-shadow-would-profit requires shadow comparison; not computed here.",
    }

    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = audit_dir / f"WEEKLY_TRADE_DECISION_LEDGER_{date_str}.jsonl"
    summary_path = audit_dir / f"WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_{date_str}.json"

    with ledger_path.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, default=str) + "\n")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Ledger:", ledger_path, "events:", total)
    print("Summary:", summary_path)
    print("  executed:", executed_count, "blocked:", blocked_count, "CI_blocked:", ci_count, "validation_failed:", validation_failed_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
