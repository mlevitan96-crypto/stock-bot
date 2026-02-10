#!/usr/bin/env python3
"""
Rolling window aggregates for EOD Board (1/3/5/7 day).
Read-only: reads logs/ and state/; no raw reprocessing beyond date filtering.
Exposes: win_rate_by_window, pnl_by_window, exit_reason_counts_by_window,
blocked_trade_counts_by_window, signal_decay_exit_rate_by_window.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Repo root: board/eod/rolling_windows.py -> parents[2]
BOARD_EOD_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOARD_EOD_DIR.parent.parent


def _day_utc(ts: Any) -> str:
    s = str(ts or "")[:10]
    return s if len(s) == 10 and s[4] == "-" else ""


def _iter_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def _load_attribution_window(base: Path, days: list[str]) -> list[dict]:
    raw = _iter_jsonl(base / "logs" / "attribution.jsonl")
    return [r for r in raw if _day_utc(r.get("ts") or r.get("timestamp")) in days]


def _load_exit_attribution_window(base: Path, days: list[str]) -> list[dict]:
    raw = _iter_jsonl(base / "logs" / "exit_attribution.jsonl")
    return [r for r in raw if _day_utc(r.get("ts") or r.get("timestamp") or r.get("exit_ts")) in days]


def _load_blocked_window(base: Path, days: list[str]) -> list[dict]:
    raw = _iter_jsonl(base / "state" / "blocked_trades.jsonl")
    return [r for r in raw if _day_utc(r.get("ts") or r.get("timestamp")) in days]


def _load_signal_events_window(base: Path, days: list[str]) -> list[dict]:
    """Load system_events.jsonl lines that are signal-related (signal_strength_evaluated, signal_trend_evaluated, etc.)."""
    raw = _iter_jsonl(base / "logs" / "system_events.jsonl")
    signal_types = {"signal_strength_evaluated", "signal_trend_evaluated", "signal_strength_skipped"}
    return [r for r in raw if r.get("event_type") in signal_types and _day_utc(r.get("timestamp")) in days]


def build_rolling_windows(
    base: Path,
    target_date: str,
    window_sizes: list[int] | None = None,
) -> dict[str, Any]:
    """
    Build 1/3/5/7 day rolling window aggregates ending on target_date.
    Returns a dict with first-class keys for the Board:
      win_rate_by_window, pnl_by_window, exit_reason_counts_by_window,
      blocked_trade_counts_by_window, signal_decay_exit_rate_by_window,
      and full multi_day_analysis for each window.
    """
    window_sizes = window_sizes or [1, 3, 5, 7]
    try:
        t = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return _empty_windows()

    win_rate_by_window: dict[str, float] = {}
    pnl_by_window: dict[str, float] = {}
    exit_reason_counts_by_window: dict[str, dict[str, int]] = {}
    blocked_trade_counts_by_window: dict[str, dict[str, int]] = {}
    signal_decay_exit_rate_by_window: dict[str, float] = {}
    windows_detail: dict[str, dict] = {}

    for w in window_sizes:
        start = t - timedelta(days=w - 1)
        days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(w)]
        key = f"{w}_day"

        attr = _load_attribution_window(base, days)
        exit_attr = _load_exit_attribution_window(base, days)
        blocked = _load_blocked_window(base, days)

        # PnL and win rate from attribution (or exit_attribution if preferred)
        pnls = [float(r.get("pnl_usd") or r.get("pnl") or 0) for r in attr]
        total_pnl = sum(pnls)
        wins = sum(1 for p in pnls if p > 0)
        total_trades = len(pnls) or 1
        win_rate = wins / total_trades if total_trades else 0.0

        pnl_by_window[key] = round(total_pnl, 2)
        win_rate_by_window[key] = round(win_rate, 4)

        # Exit reason counts (from exit_attribution; fallback attr for close_reason)
        exit_reasons: Counter[str] = Counter()
        for r in exit_attr + attr:
            reason = str(r.get("exit_reason") or r.get("close_reason") or r.get("reason") or "unknown").strip() or "unknown"
            exit_reasons[reason] += 1
        exit_reason_counts_by_window[key] = dict(exit_reasons.most_common(20))

        # Blocked trade counts by reason
        blocked_reasons: Counter[str] = Counter()
        for r in blocked:
            reason = str(r.get("reason") or r.get("blocked_reason") or "unknown").strip() or "unknown"
            blocked_reasons[reason] += 1
        blocked_trade_counts_by_window[key] = dict(blocked_reasons.most_common(20))

        # Signal decay exit rate: fraction of exits with reason indicating signal_decay
        decay_keywords = ("signal_decay", "decay", "signal_decay_exit", "signal_strength")
        decay_exits = sum(1 for r in exit_attr if any(kw in str(r.get("exit_reason") or r.get("close_reason") or "").lower() for kw in decay_keywords))
        total_exits = len(exit_attr) or 1
        signal_decay_exit_rate_by_window[key] = round(decay_exits / total_exits, 4)

        windows_detail[key] = {
            "window_days": days,
            "total_trades": len(attr),
            "total_exits": len(exit_attr),
            "total_blocked": len(blocked),
            "pnl_usd": round(total_pnl, 2),
            "win_rate": round(win_rate, 4),
            "signal_decay_exit_count": decay_exits,
        }

    return {
        "date": target_date,
        "win_rate_by_window": win_rate_by_window,
        "pnl_by_window": pnl_by_window,
        "exit_reason_counts_by_window": exit_reason_counts_by_window,
        "blocked_trade_counts_by_window": blocked_trade_counts_by_window,
        "signal_decay_exit_rate_by_window": signal_decay_exit_rate_by_window,
        "windows": windows_detail,
    }


def _empty_windows() -> dict[str, Any]:
    return {
        "date": "",
        "win_rate_by_window": {},
        "pnl_by_window": {},
        "exit_reason_counts_by_window": {},
        "blocked_trade_counts_by_window": {},
        "signal_decay_exit_rate_by_window": {},
        "windows": {},
    }


def get_rolling_windows_for_date(date_str: str, repo_root: Path | None = None) -> dict[str, Any]:
    """Convenience: build rolling windows for date using repo root."""
    base = repo_root or REPO_ROOT
    return build_rolling_windows(base, date_str)
