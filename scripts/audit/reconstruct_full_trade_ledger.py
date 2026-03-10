#!/usr/bin/env python3
"""
Reconstruct full trade ledger for a single day from droplet data.
Sources: logs/exit_attribution.jsonl, state/blocked_trades.jsonl, logs/score_snapshot.jsonl.
Output: single JSON with executed, blocked, counter_intel, summary.
Run on droplet for live data. See FULL_DAY_TRADING_INTELLIGENCE_AUDIT_RUNBOOK.md.
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


def _load_exit_attribution_day(base: Path, start_ts: int, end_ts: int) -> list[dict]:
    out = []
    for p in [
        base / "logs" / "exit_attribution.jsonl",
        base / "reports" / "audit" / "weekly_evidence_stage" / "logs" / "exit_attribution.jsonl",
    ]:
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


def _load_blocked_day(base: Path, start_ts: int, end_ts: int) -> list[dict]:
    out = []
    for p in [
        base / "state" / "blocked_trades.jsonl",
        base / "reports" / "audit" / "weekly_evidence_stage" / "state" / "blocked_trades.jsonl",
    ]:
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


def _is_counter_intel_reason(reason: str) -> bool:
    if not reason:
        return False
    r = (reason or "").lower()
    return "counter" in r or "counter_intel" in r or "ci_block" in r or "intel" in r


def _exit_to_event(r: dict) -> dict:
    ts = _parse_ts(r.get("exit_timestamp") or r.get("ts") or r.get("closed_at")) or 0
    return {
        "ts": ts,
        "ts_iso": _ts_iso(ts) if ts else "",
        "symbol": r.get("symbol", ""),
        "direction": r.get("direction", ""),
        "strategy_variant_id": r.get("strategy_variant_id") or r.get("variant_id", ""),
        "decision": "executed",
        "exit_reason": r.get("exit_reason", ""),
        "hold_time_minutes": r.get("time_in_trade_minutes"),
        "realized_pnl": r.get("pnl"),
        "realized_pnl_pct": r.get("pnl_pct"),
        "sizing": r.get("qty"),
        "entry_ts": _parse_ts(r.get("entry_timestamp")),
        "exit_ts": ts,
    }


def _blocked_to_event(r: dict) -> dict:
    ts = _parse_ts(r.get("timestamp") or r.get("ts")) or 0
    reason = r.get("reason") or r.get("block_reason") or ""
    return {
        "ts": ts,
        "ts_iso": _ts_iso(ts) if ts else "",
        "symbol": r.get("symbol", ""),
        "direction": r.get("direction", ""),
        "strategy_variant_id": r.get("strategy_variant_id", ""),
        "decision": "counter_intel_blocked" if _is_counter_intel_reason(reason) else "blocked",
        "reason_codes": [reason] if reason else [],
        "block_reason": reason,
        "sizing": r.get("size") or r.get("qty"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconstruct full trade ledger for one day")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--include-executed", action="store_true", default=True, help="Include executed trades")
    ap.add_argument("--include-blocked", action="store_true", default=True, help="Include blocked")
    ap.add_argument("--include-counter-intel", action="store_true", default=True, help="Include counter-intel blocked")
    ap.add_argument("--emit-would-have-pnl", action="store_true", help="Emit would-have PnL (stub: null)")
    ap.add_argument("--output", required=True, help="Output JSON path (e.g. reports/ledger/FULL_TRADE_LEDGER_<date>.json)")
    ap.add_argument("--base-dir", default=None, help="Repo root (default: script repo)")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO

    try:
        day_dt = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        print("Invalid --date", args.date, file=sys.stderr)
        return 1
    start_ts = int(day_dt.timestamp())
    end_ts = int((day_dt + timedelta(days=1)).timestamp()) - 1

    executed_rows = _load_exit_attribution_day(base, start_ts, end_ts) if args.include_executed else []
    blocked_rows = _load_blocked_day(base, start_ts, end_ts) if (args.include_blocked or args.include_counter_intel) else []

    executed = [_exit_to_event(r) for r in executed_rows]
    blocked_events = [_blocked_to_event(r) for r in blocked_rows]
    blocked = [e for e in blocked_events if e.get("decision") == "blocked"]
    counter_intel = [e for e in blocked_events if e.get("decision") == "counter_intel_blocked"]

    payload = {
        "date": args.date,
        "executed": executed,
        "blocked": blocked,
        "counter_intel": counter_intel,
        "would_have_pnl": None if not args.emit_would_have_pnl else [],
        "summary": {
            "executed_count": len(executed),
            "blocked_count": len(blocked),
            "counter_intel_count": len(counter_intel),
            "total_events": len(executed) + len(blocked) + len(counter_intel),
        },
    }

    out_path = base / args.output if not (Path(args.output).is_absolute()) else Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, "executed:", len(executed), "blocked:", len(blocked), "counter_intel:", len(counter_intel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
