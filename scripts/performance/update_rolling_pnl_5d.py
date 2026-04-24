#!/usr/bin/env python3
"""
Update 5-day rolling PnL state (append-only, prune by age).
Uses same unified-exits logic as Performance Engine (exit_attribution + attribution fallback).
Droplet-native, restart-safe, CSA-auditable. No backfilling; no smoothing.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Repo root
REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

RUN_LOG = (REPO / "logs" / "run.jsonl").resolve()

try:
    from config.registry import LogFiles, Directories
    ATTR_PATH = (REPO / LogFiles.ATTRIBUTION).resolve()
    EXIT_ATTR_PATH = (REPO / LogFiles.EXIT_ATTRIBUTION).resolve()
    STATE_DIR = (REPO / Directories.STATE).resolve()
except Exception:
    ATTR_PATH = (REPO / "logs" / "attribution.jsonl").resolve()
    EXIT_ATTR_PATH = (REPO / "logs" / "exit_attribution.jsonl").resolve()
    STATE_DIR = (REPO / "state").resolve()

ROLLING_PATH = (REPO / "reports" / "state" / "rolling_pnl_5d.jsonl").resolve()
REPORTS_AUDIT = REPO / "reports" / "audit"
WINDOW_DAYS = 5
SEC_PER_DAY = 86400


def _parse_ts(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        if isinstance(s, (int, float)):
            return datetime.fromtimestamp(s, tz=timezone.utc)
        s = str(s).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _load_unified_exits_5d() -> list[dict]:
    """Load closed equity exits in last 5 days: exit_attribution first, attribution fallback. Same logic as Performance Engine."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=WINDOW_DAYS)
    cutoff_ts = cutoff.timestamp()
    seen = set()
    rows = []

    # 1) Exit attribution (v2)
    if EXIT_ATTR_PATH.exists():
        try:
            for line in EXIT_ATTR_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-5000:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                symbol = str(rec.get("symbol", "")).upper()
                if not symbol or "TEST" in symbol:
                    continue
                ts_str = rec.get("timestamp") or rec.get("exit_timestamp") or ""
                ts = _parse_ts(ts_str)
                if ts is None or ts.timestamp() < cutoff_ts:
                    continue
                pnl = rec.get("pnl")
                pnl_usd = float(pnl) if pnl is not None else None
                key = (symbol, (ts_str or "")[:19])
                if key in seen:
                    continue
                seen.add(key)
                _tid = str(rec.get("trade_id") or "").strip()
                rows.append(
                    {
                        "ts": ts,
                        "ts_str": ts_str,
                        "pnl_usd": pnl_usd,
                        "source": "exit_attribution",
                        "trade_id": _tid or None,
                    }
                )
        except Exception:
            pass

    # 2) Attribution (fallback)
    if ATTR_PATH.exists():
        try:
            with ATTR_PATH.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("type") != "attribution":
                        continue
                    if str(rec.get("trade_id", "")).startswith("open_"):
                        continue
                    symbol = str(rec.get("symbol", "")).upper()
                    if not symbol or "TEST" in symbol:
                        continue
                    ts_str = rec.get("ts") or rec.get("timestamp") or ""
                    ts = _parse_ts(ts_str)
                    if ts is None or ts.timestamp() < cutoff_ts:
                        continue
                    pnl_usd = float(rec.get("pnl_usd", 0) or 0)
                    context = rec.get("context") or {}
                    close_reason = context.get("close_reason") or rec.get("close_reason") or ""
                    if pnl_usd == 0 and not (close_reason and close_reason not in ("unknown", "N/A", "")):
                        continue
                    key = (symbol, (ts_str or "")[:19])
                    if key in seen:
                        continue
                    seen.add(key)
                    _tid2 = str(rec.get("trade_id") or rec.get("trade_key") or "").strip()
                    rows.append(
                        {
                            "ts": ts,
                            "ts_str": ts_str,
                            "pnl_usd": pnl_usd,
                            "source": "attribution",
                            "trade_id": _tid2 or None,
                        }
                    )
        except Exception:
            pass

    rows.sort(key=lambda x: x["ts"].timestamp())
    return rows


def _load_shadow_chop_by_trade_id() -> dict:
    """
    Map trade_id -> last seen shadow_chop_block on trade_intent (entered).
    Used to compute hypothetical 5d PnL excluding chop-window entries.
    """
    out: dict = {}
    if not RUN_LOG.is_file():
        return out
    try:
        raw = RUN_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-200_000:]
    except Exception:
        return out
    for line in raw:
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("event_type") != "trade_intent":
            continue
        if str(o.get("decision_outcome", "")).lower() != "entered":
            continue
        tid = str(o.get("trade_id") or "").strip()
        if not tid:
            continue
        v = o.get("shadow_chop_block")
        if v is not None:
            out[tid] = bool(v)
    return out


def _baseline_equity() -> float:
    """Baseline for equity = daily_start_equity if available, else 0 (chart shows cumulative PnL)."""
    p = STATE_DIR / "daily_start_equity.json"
    if not p.exists():
        return 0.0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("date") == datetime.now(timezone.utc).date().isoformat():
            return float(data.get("equity", 0) or 0)
    except Exception:
        pass
    return 0.0


def main() -> int:
    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()
    cutoff_ts = now_ts - (WINDOW_DAYS * SEC_PER_DAY)

    exits = _load_unified_exits_5d()
    net_pnl = 0.0
    chop_excluded = 0.0
    chop_map = _load_shadow_chop_by_trade_id()
    for r in exits:
        p = r.get("pnl_usd")
        if p is not None and not (isinstance(p, float) and math.isnan(p)):
            net_pnl += float(p)
        tid = r.get("trade_id")
        if tid and bool(chop_map.get(str(tid))):
            if p is not None and not (isinstance(p, float) and math.isnan(p)):
                chop_excluded += float(p)

    baseline = _baseline_equity()
    equity = baseline + net_pnl
    net_pnl_no_chop = net_pnl - chop_excluded
    equity_shadow = baseline + net_pnl_no_chop

    point = {
        "ts": now.isoformat(),
        "equity": round(equity, 2),
        "pnl": round(net_pnl, 2),
        "pnl_excluding_chop_shadow": round(net_pnl_no_chop, 2),
        "equity_shadow": round(equity_shadow, 2),
        "chop_excluded_pnl_5d": round(chop_excluded, 2),
        "source": "unified_exits",
        "window": "5d",
    }

    # Append
    rolling_path = ROLLING_PATH
    rolling_path.parent.mkdir(parents=True, exist_ok=True)
    with rolling_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(point, default=str) + "\n")

    # Prune: remove points older than (now - 5 days)
    all_raw = rolling_path.read_text(encoding="utf-8", errors="replace").splitlines()
    kept = []
    for line in all_raw:
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            ts_str = obj.get("ts")
            t = _parse_ts(ts_str)
            if t is not None and t.timestamp() >= cutoff_ts:
                kept.append(line)
        except Exception:
            continue
    if len(kept) < len([x for x in all_raw if x.strip()]):
        rolling_path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")

    # Validate: monotonic ts, no NaNs, equity continuity (warn only)
    all_lines = rolling_path.read_text(encoding="utf-8", errors="replace").splitlines()
    points = []
    for line in all_lines:
        if not line.strip():
            continue
        try:
            points.append(json.loads(line))
        except Exception:
            continue
    prev_ts = None
    prev_equity = None
    for p in points:
        ts = _parse_ts(p.get("ts"))
        if ts is not None and prev_ts is not None and ts.timestamp() < prev_ts:
            print(f"[WARN] Non-monotonic timestamp: {p.get('ts')} < previous", flush=True)
        if ts is not None:
            prev_ts = ts.timestamp()
        e = p.get("equity")
        if e is not None:
            if isinstance(e, float) and math.isnan(e):
                print("[WARN] NaN equity in rolling state", flush=True)
            if prev_equity is not None and e != prev_equity and (e - prev_equity) != (p.get("pnl") or 0):
                print(f"[WARN] Equity gap/continuity: {prev_equity} -> {e}", flush=True)
            prev_equity = e

    # Summary artifact
    REPORTS_AUDIT.mkdir(parents=True, exist_ok=True)
    suffix = now.strftime("%Y-%m-%d_%H%M")
    artifact_path = REPORTS_AUDIT / f"ROLLING_PNL_5D_UPDATE_{suffix}.json"
    artifact = {
        "ts": now.isoformat(),
        "points_after_prune": len(points),
        "exits_in_window": len(exits),
        "net_pnl": round(net_pnl, 2),
        "equity": round(equity, 2),
        "baseline_equity": round(baseline, 2),
        "source": "unified_exits",
        "window_days": WINDOW_DAYS,
    }
    with artifact_path.open("w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
