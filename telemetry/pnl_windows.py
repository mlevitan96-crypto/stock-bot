#!/usr/bin/env python3
"""
PnL windows telemetry (v2-only, additive)
=======================================

Contract (SYSTEM_CONTRACT.md / MEMORY_BANK.md):
- Output schema (returned dict) must include:
  - as_of_ts (UTC ISO)
  - windows: { "24h": {...}, "48h": {...}, "5d": {...} }
  - per_symbol: [ {symbol, window, pnl_usd, trade_count, win_rate} ... ]
- Derived from v2 realized exits in logs/master_trade_log.jsonl (read-only).
- Safe-by-default: never raises; returns empty-but-valid schema on errors.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: Any) -> Optional[datetime]:
    try:
        s = str(ts or "").strip().replace("Z", "+00:00")
        if not s:
            return None
        if "T" not in s and " " in s:
            s = s.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    try:
        if not path.exists() or not path.is_file():
            return
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                ln = (ln or "").strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                except Exception:
                    continue
                if isinstance(obj, dict):
                    yield obj
    except Exception:
        return


def _closed_trade_records(master_trade_log_path: Path) -> List[Dict[str, Any]]:
    """
    Return only records that represent closed trades (have exit_ts and realized pnl).
    Best-effort; if pnl missing, we still include the record with pnl=0.0.
    """
    out: List[Dict[str, Any]] = []
    for rec in _iter_jsonl(master_trade_log_path):
        exit_ts = rec.get("exit_ts") or rec.get("exit_timestamp") or rec.get("exit_time")
        dt = _parse_iso(exit_ts)
        if dt is None:
            continue
        pnl = _safe_float(rec.get("realized_pnl_usd"))
        if pnl is None:
            # tolerate older schemas
            pnl = _safe_float(rec.get("pnl_usd")) or _safe_float(rec.get("pnl")) or 0.0
        sym = str(rec.get("symbol", "") or "").upper()
        if not sym:
            continue
        out.append({"symbol": sym, "exit_dt": dt, "pnl_usd": float(pnl)})
    return out


@dataclass(frozen=True)
class _Window:
    name: str
    delta: timedelta


def _window_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    pnls = [float(r.get("pnl_usd") or 0.0) for r in rows]
    n = len(pnls)
    wins = len([p for p in pnls if p > 0])
    pnl_total = sum(pnls) if pnls else 0.0
    expectancy = (pnl_total / float(n)) if n else 0.0
    win_rate = (wins / float(n)) if n else 0.0
    return {
        "pnl_usd": float(round(pnl_total, 6)),
        "expectancy_usd": float(round(expectancy, 6)),
        "trade_count": int(n),
        "win_rate": float(round(win_rate, 6)),
        "insufficient_data": bool(n < 1),
    }


def build_pnl_windows(*, master_trade_log_path: str) -> Dict[str, Any]:
    """
    Build rolling PnL window telemetry from the master trade log.
    Never raises.
    """
    try:
        path = Path(str(master_trade_log_path))
        now = datetime.now(timezone.utc)
        rows = _closed_trade_records(path)

        windows = [
            _Window("24h", timedelta(hours=24)),
            _Window("48h", timedelta(hours=48)),
            _Window("5d", timedelta(days=5)),
        ]

        out_windows: Dict[str, Any] = {}
        per_symbol: List[Dict[str, Any]] = []

        for w in windows:
            cutoff = now - w.delta
            w_rows = [r for r in rows if isinstance(r.get("exit_dt"), datetime) and r["exit_dt"] >= cutoff]
            out_windows[w.name] = _window_stats(w_rows)

            # Per-symbol breakdown (for this window)
            by: Dict[str, List[Dict[str, Any]]] = {}
            for r in w_rows:
                by.setdefault(str(r["symbol"]), []).append(r)
            for sym, srows in sorted(by.items()):
                st = _window_stats(srows)
                per_symbol.append(
                    {
                        "symbol": sym,
                        "window": w.name,
                        "pnl_usd": st["pnl_usd"],
                        "trade_count": st["trade_count"],
                        "win_rate": st["win_rate"],
                    }
                )

        return {"as_of_ts": _now_iso(), "windows": out_windows, "per_symbol": per_symbol}
    except Exception as e:
        return {"as_of_ts": _now_iso(), "windows": {}, "per_symbol": [], "error": f"{type(e).__name__}: {e}"}

