"""
Command Center (static SPA) metrics: immutable UTC daily trade ledger + dual-barrel cumulative PnL.

Read-only except ``state/daily_trade_ledger.json`` append-only style locks for past UTC days.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Set

TailFn = Callable[[Path, int, int], List[str]]


def _default_tail_lines(path: Path, max_lines: int = 80_000, max_chunk_bytes: int = 20_000_000) -> List[str]:
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            size = path.stat().st_size
            chunk = min(max_chunk_bytes, size)
            if size > chunk:
                f.seek(max(0, size - chunk))
                f.readline()
            lines = f.read().splitlines()
            return lines[-max_lines:] if len(lines) > max_lines else lines
    except OSError:
        return []


def _parse_iso_date_utc(s: Any) -> Optional[date]:
    if s is None:
        return None
    raw = str(s).strip()
    if not raw:
        return None
    try:
        raw = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).date()
    except (TypeError, ValueError):
        return None


def _ledger_path(root: Path) -> Path:
    p = (root / "state" / "daily_trade_ledger.json").resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_ledger(root: Path) -> dict:
    path = _ledger_path(root)
    if not path.is_file():
        return {"version": 1, "days": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"version": 1, "days": {}}
        data.setdefault("version", 1)
        data.setdefault("days", {})
        if not isinstance(data["days"], dict):
            data["days"] = {}
        return data
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "days": {}}


def _atomic_write_json(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


def finalize_past_utc_days_in_ledger(
    root: Path,
    live_counts_by_day: Dict[str, int],
    today_utc: date,
) -> Dict[str, Any]:
    """
    For each calendar day strictly before ``today_utc``, if missing from ledger.days,
    record trade_count once and set locked_at_utc. Never overwrites an existing day.
    """
    path = _ledger_path(root)
    data = _load_ledger(root)
    days: Dict[str, Any] = data["days"]
    now_iso = datetime.now(timezone.utc).isoformat()
    changed = False
    for day_iso, cnt in live_counts_by_day.items():
        try:
            d = date.fromisoformat(day_iso)
        except ValueError:
            continue
        if d >= today_utc:
            continue
        if day_iso in days:
            continue
        days[day_iso] = {"trade_count": int(cnt), "locked_at_utc": now_iso}
        changed = True
    if changed:
        _atomic_write_json(path, data)
    return data


def _exit_row_dedupe_id(rec: dict) -> Optional[str]:
    from src.telemetry.alpaca_trade_key import build_trade_key

    for k in ("trade_id", "canonical_trade_id", "trade_key"):
        v = rec.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    sym = rec.get("symbol")
    side = rec.get("side") or rec.get("position_side")
    et_ent = rec.get("entry_ts") or rec.get("entry_timestamp")
    try:
        return build_trade_key(sym, side, et_ent)
    except Exception:
        return None


def _v3_shadow_map_from_run_jsonl(
    root: Path,
    tail_lines: TailFn,
) -> Dict[str, Any]:
    """Last-write-wins map trade_id / trade_key -> ai_approved_v3_shadow (True/False/None)."""
    run_path = (root / "logs" / "run.jsonl").resolve()
    out: Dict[str, Any] = {}
    for line in tail_lines(run_path, 120_000, 25_000_000):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if str(rec.get("event_type") or "") != "trade_intent":
            continue
        if str(rec.get("decision_outcome") or "").lower() != "entered":
            continue
        v3 = rec.get("ai_approved_v3_shadow")
        for k in ("trade_id", "trade_key", "canonical_trade_id"):
            v = rec.get(k)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                out[s] = v3
    return out


def daily_trade_volume_utc_with_ledger(
    root: Path,
    days: int,
    *,
    tail_lines: Optional[TailFn] = None,
) -> dict:
    """
    UTC calendar-day counts: unique trade keys that **opened** (trade_intent entered) or **closed**
    (exit_attribution) that UTC day — ``|opens ∪ closes|``.

    Past UTC days (strictly before today) are served from ``state/daily_trade_ledger.json`` when
    present; otherwise the live scan count is written once into the ledger (first lock wins).
    """
    from src.governance.canonical_trade_count import _parse_exit_epoch
    from utils.era_cut import learning_excluded_for_exit_record

    tail = tail_lines or _default_tail_lines
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    d_win = max(1, min(int(days), 90))
    start_d = today - timedelta(days=d_win - 1)

    opens_by_day: DefaultDict[str, Set[str]] = defaultdict(set)
    closes_by_day: DefaultDict[str, Set[str]] = defaultdict(set)

    exit_path = (root / "logs" / "exit_attribution.jsonl").resolve()
    for line in tail(exit_path, 80_000, 20_000_000):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if learning_excluded_for_exit_record(rec):
            continue
        ex = _parse_exit_epoch(rec)
        if ex is None:
            continue
        d_exit = datetime.fromtimestamp(float(ex), tz=timezone.utc).date()
        if not (start_d <= d_exit <= today):
            continue
        tid = _exit_row_dedupe_id(rec)
        if tid:
            closes_by_day[d_exit.isoformat()].add(tid)

    run_path = (root / "logs" / "run.jsonl").resolve()
    for line in tail(run_path, 120_000, 25_000_000):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if str(rec.get("event_type") or "") != "trade_intent":
            continue
        if str(rec.get("decision_outcome") or "").lower() != "entered":
            continue
        d_open = _parse_iso_date_utc(rec.get("timestamp") or rec.get("ts"))
        if d_open is None or not (start_d <= d_open <= today):
            continue
        keys: List[str] = []
        for k in ("trade_id", "trade_key", "canonical_trade_id"):
            v = rec.get(k)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                keys.append(s)
        if not keys:
            continue
        k0 = keys[0]
        opens_by_day[d_open.isoformat()].add(k0)

    live_union: Dict[str, int] = {}
    cur = start_d
    while cur <= today:
        ds = cur.isoformat()
        u = set(opens_by_day.get(ds, set())) | set(closes_by_day.get(ds, set()))
        live_union[ds] = len(u)
        cur = cur + timedelta(days=1)

    finalize_past_utc_days_in_ledger(root, live_union, today)
    ledger = _load_ledger(root)
    locked = ledger.get("days") or {}

    series: List[dict] = []
    cur = start_d
    while cur <= today:
        ds = cur.isoformat()
        if cur < today and ds in locked and isinstance(locked[ds], dict) and locked[ds].get("trade_count") is not None:
            cnt = int(locked[ds]["trade_count"])
        else:
            cnt = int(live_union.get(ds, 0))
        series.append({"date": ds, "label": ds, "trade_count": cnt})
        cur = cur + timedelta(days=1)

    return {
        "ok": True,
        "generated_at_utc": now_utc.isoformat(),
        "timezone": "UTC",
        "calendar_basis": "UTC",
        "days_requested": d_win,
        "days_in_series": len(series),
        "calendar_today_date": today.isoformat(),
        "calendar_today_label": today.isoformat(),
        "calendar_today_trade_count": int(live_union.get(today.isoformat(), 0)),
        "source": "logs/exit_attribution.jsonl + logs/run.jsonl (union by trade id/key)",
        "scan_note": (
            "Unique trade keys per UTC day: union of trade_intent entered (open) and "
            "exit_attribution closes (same tail bounds as prior chart). "
            "Past UTC days after first lock are read from state/daily_trade_ledger.json only."
        ),
        "series": series,
        "ledger_path": "state/daily_trade_ledger.json",
        "does_not_claim": [
            "learning_certification",
            "tail_completeness_for_ancient_history",
        ],
    }


def dual_barrel_cumulative_pnl_series(
    root: Path,
    *,
    max_points: int = 600,
    tail_lines: Optional[TailFn] = None,
) -> dict:
    """
    Cumulative realized USD PnL (live vs V3-shadow lane).

    **Primary:** ``state/continuous_pnl_ledger.jsonl`` (append-only, survives epoch log truncates).
    **Fallback:** volatile ``exit_attribution`` + ``run.jsonl`` tails when the ledger is empty.
    """
    from telemetry.continuous_pnl_ledger import (
        read_dual_barrel_series_from_persistent_ledger,
        reconstruct_dual_barrel_cumulative_from_logs,
    )

    tail = tail_lines or _default_tail_lines
    pts, meta = read_dual_barrel_series_from_persistent_ledger(
        root, max_points=max_points, tail_lines=tail
    )
    if pts:
        return {
            "ok": True,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "points": pts,
            "source": meta.get("source"),
            "ledger_path": meta.get("ledger_path"),
            "ledger_row_count": meta.get("row_count"),
            "does_not_claim": [
                "ledger_tail_window_caps_very_long_history",
                "duplicate_trade_key_keeps_last_row_only",
            ],
        }
    return reconstruct_dual_barrel_cumulative_from_logs(root, max_points=max_points, tail_lines=tail)
