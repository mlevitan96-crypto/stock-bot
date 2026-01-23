#!/usr/bin/env python3
"""
Live vs Shadow PnL Telemetry (computed)
======================================

Produces a rolling window comparison between:
- v1 live trades (logs/attribution.jsonl)
- v2 shadow realized exits (logs/exit_attribution.jsonl)

Contract:
- Additive only; read-only over existing logs.
- Must never raise inside telemetry pipelines (caller should still wrap).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts_any(v: Any) -> Optional[datetime]:
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).strip()
        if not s:
            return None
        s = s.replace("Z", "+00:00")
        if "T" not in s and " " in s:
            s = s.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _safe_float(v: Any) -> float:
    try:
        if v is None:
            return 0.0
        return float(v)
    except Exception:
        return 0.0


def _iter_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        if not path.exists():
            return out
        for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
                if isinstance(obj, dict):
                    out.append(obj)
            except Exception:
                continue
    except Exception:
        return out
    return out


def _window_stats(trades: List[Tuple[str, float]]) -> Dict[str, Any]:
    # trades: [(symbol, pnl_usd), ...]
    n = int(len(trades))
    pnl = float(sum(float(p) for _, p in trades)) if trades else 0.0
    wins = int(sum(1 for _, p in trades if float(p) > 0.0))
    win_rate = float(wins / n) if n > 0 else 0.0
    expectancy = float(pnl / n) if n > 0 else 0.0
    return {
        "pnl_usd": float(pnl),
        "expectancy_usd": float(expectancy),
        "trade_count": int(n),
        "win_rate": float(win_rate),
    }


def build_live_vs_shadow_pnl(
    *,
    attribution_log_path: str = "logs/attribution.jsonl",
    shadow_exit_attribution_log_path: str = "logs/exit_attribution.jsonl",
    as_of_ts: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns:
    {
      "as_of_ts": "<ISO8601>",
      "windows": { "24h": {...}, "48h": {...}, "5d": {...} },
      "per_symbol": [...],
    }
    """
    as_of_dt = _parse_ts_any(as_of_ts) if as_of_ts else None
    if as_of_dt is None:
        as_of_dt = _now_utc()
    as_of_iso = as_of_dt.isoformat()

    windows = {
        "24h": timedelta(hours=24),
        "48h": timedelta(hours=48),
        "5d": timedelta(days=5),
    }

    # Gather trade events for both sides with timestamps.
    live_events: List[Tuple[datetime, str, float]] = []
    shadow_events: List[Tuple[datetime, str, float]] = []

    # Live: closed attribution records (trade_id not open_*).
    for rec in _iter_jsonl(Path(attribution_log_path)):
        try:
            if str(rec.get("type", "") or "") != "attribution":
                continue
            tid = str(rec.get("trade_id", "") or "")
            if tid.startswith("open_"):
                continue
            ts_dt = _parse_ts_any(rec.get("ts") or rec.get("timestamp") or rec.get("_ts"))
            if ts_dt is None:
                continue
            sym = str(rec.get("symbol", "") or "").upper()
            if not sym:
                continue
            pnl = _safe_float(rec.get("pnl_usd"))
            # Only consider "closed" trades: keep PnL=0 trades only if we have a close_reason.
            ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
            close_reason = str((ctx or {}).get("close_reason", "") or "")
            if pnl == 0.0 and not close_reason:
                continue
            live_events.append((ts_dt, sym, float(pnl)))
        except Exception:
            continue

    # Shadow: exit attribution records with realized pnl.
    for rec in _iter_jsonl(Path(shadow_exit_attribution_log_path)):
        try:
            ts_dt = _parse_ts_any(rec.get("timestamp") or rec.get("ts") or rec.get("_ts"))
            if ts_dt is None:
                continue
            sym = str(rec.get("symbol", "") or "").upper()
            if not sym:
                continue
            pnl = rec.get("pnl")
            if pnl is None:
                pnl = rec.get("pnl_usd")
            shadow_events.append((ts_dt, sym, float(_safe_float(pnl))))
        except Exception:
            continue

    out_windows: Dict[str, Any] = {}
    per_symbol_rows: List[Dict[str, Any]] = []

    for wname, wdelta in windows.items():
        cutoff = as_of_dt - wdelta
        live_w = [(sym, pnl) for (dt, sym, pnl) in live_events if dt >= cutoff]
        shadow_w = [(sym, pnl) for (dt, sym, pnl) in shadow_events if dt >= cutoff]

        live_stats = _window_stats(live_w)
        shadow_stats = _window_stats(shadow_w)

        delta_stats = {
            "pnl_usd": float(shadow_stats["pnl_usd"] - live_stats["pnl_usd"]),
            "expectancy_usd": float(shadow_stats["expectancy_usd"] - live_stats["expectancy_usd"]),
            "trade_count": int(shadow_stats["trade_count"] - live_stats["trade_count"]),
            "win_rate": float(shadow_stats["win_rate"] - live_stats["win_rate"]),
        }

        out_windows[wname] = {
            "live": live_stats,
            "shadow": shadow_stats,
            "delta": delta_stats,
            "insufficient_data": bool(live_stats["trade_count"] == 0 or shadow_stats["trade_count"] == 0),
        }

        # Per-symbol rows for this window (only symbols with activity).
        syms = sorted({s for s, _ in live_w} | {s for s, _ in shadow_w})
        if syms:
            # Aggregate by symbol
            live_by = {s: {"pnl": 0.0, "n": 0} for s in syms}
            sh_by = {s: {"pnl": 0.0, "n": 0} for s in syms}
            for s, p in live_w:
                live_by[s]["pnl"] += float(p)
                live_by[s]["n"] += 1
            for s, p in shadow_w:
                sh_by[s]["pnl"] += float(p)
                sh_by[s]["n"] += 1

            for s in syms:
                lp = float(live_by[s]["pnl"])
                sp = float(sh_by[s]["pnl"])
                per_symbol_rows.append(
                    {
                        "symbol": s,
                        "window": wname,
                        "live_pnl_usd": float(lp),
                        "shadow_pnl_usd": float(sp),
                        "delta_pnl_usd": float(sp - lp),
                        "live_trade_count": int(live_by[s]["n"]),
                        "shadow_trade_count": int(sh_by[s]["n"]),
                    }
                )

    return {
        "as_of_ts": as_of_iso,
        "windows": out_windows,
        "per_symbol": per_symbol_rows,
    }

