"""
Phase 5 — Load and join attribution + exit_attribution for analysis.
Reproducible from: live logs, backtest outputs (backtest_exits.jsonl), synthetic lab.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side


def _day_utc(ts: Any) -> str:
    if ts is None:
        return ""
    s = str(ts)
    if len(s) >= 10:
        return s[:10]
    return ""


def entry_ts_bucket(ts: Any) -> str:
    if not ts:
        return ""
    s = str(ts).replace("Z", "").replace("+00:00", "")
    return s[:19].rstrip("Z") if len(s) >= 19 else s


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
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


def attr_entry_key(r: Dict[str, Any]) -> Optional[str]:
    """Key for entry (attribution) record: symbol + entry_ts bucket."""
    sym = (r.get("symbol") or "").upper()
    if not sym:
        return None
    ctx = r.get("context") or {}
    ts = ctx.get("entry_ts") or ctx.get("entry_timestamp") or r.get("entry_ts") or r.get("ts") or r.get("timestamp")
    if not ts:
        return None
    return f"{sym}|{entry_ts_bucket(ts)}"


def exit_key(r: Dict[str, Any]) -> Optional[str]:
    """Key for exit record: symbol + entry_timestamp bucket."""
    sym = (r.get("symbol") or "").upper()
    ts = r.get("entry_timestamp") or r.get("entry_ts")
    if not sym or not ts:
        return None
    return f"{sym}|{entry_ts_bucket(ts)}"


def load_joined_closed_trades(
    attribution_path: Path,
    exit_attribution_path: Path,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    *,
    date_from_exit: bool = True,
) -> List[Dict[str, Any]]:
    """
    Load attribution and exit_attribution, join on trade_id (primary) or symbol+entry_ts_bucket (fallback).

    Join key definition (prefer canonical ``build_trade_key`` / ``trade_key`` end-to-end):
    - Primary: ``trade_key`` or ``canonical_trade_id`` on the exit row matching entry context
      (``context.trade_key`` / ``context.canonical_trade_id``) when present.
    - Secondary: ``trade_id`` (``open_SYMBOL_<iso>``) on entry vs exit ``trade_id`` / ``decision_id``.
    - **Deprecated fallback:** ``symbol|entry_ts_bucket`` (19-char prefix) when ids are missing — may
      collide; prefer populating ``trade_key`` on both sides.

    Expected fields:
    - Attribution (entry): type=attribution, trade_id startswith "open_", context.entry_ts, context.entry_score,
      context.attribution_components, context.regime.
    - Exit_attribution: symbol, entry_timestamp (or entry_ts), trade_id (recommended for stable join), timestamp/ts.

    Returns list of joined records: each has exit record fields + entry_score, entry_attribution_components,
    entry_regime, entry_context from the matched attribution entry. quality_flags may include "join_fallback" if
    matched by key only.
    """
    attr_all = load_jsonl(attribution_path)
    exit_all = load_jsonl(exit_attribution_path)

    # Entry records: type=attribution, trade_id open_* (entry events), context with entry_ts.
    entry_by_key: Dict[str, Dict[str, Any]] = {}
    entry_by_trade_id: Dict[str, Dict[str, Any]] = {}
    entry_by_canonical: Dict[str, Dict[str, Any]] = {}
    for r in attr_all:
        if r.get("type") != "attribution":
            continue
        tid = str(r.get("trade_id") or "")
        if not tid.startswith("open_"):
            continue
        k = attr_entry_key(r)
        if not k:
            continue
        ctx = r.get("context") or {}
        entry_data = {
            "entry_timestamp": ctx.get("entry_ts") or r.get("ts") or r.get("timestamp"),
            "entry_score": ctx.get("entry_score"),
            "entry_attribution_components": ctx.get("attribution_components"),
            "entry_regime": ctx.get("regime") or ctx.get("market_regime"),
            "entry_context": ctx,
            "trade_id": tid,
        }
        if k not in entry_by_key:
            entry_by_key[k] = entry_data
        entry_by_trade_id[tid] = entry_data
        entry_canon: Optional[str] = None
        for ck in (ctx.get("trade_key"), ctx.get("canonical_trade_id")):
            if ck and str(ck).strip():
                s = str(ck).strip()
                parts = s.split("|")
                if len(parts) >= 3:
                    try:
                        int(parts[-1])
                        entry_canon = s
                        break
                    except ValueError:
                        pass
        if entry_canon is None:
            sym = (r.get("symbol") or "").upper()
            ets = ctx.get("entry_ts") or r.get("ts") or r.get("timestamp")
            if sym and ets:
                try:
                    entry_canon = build_trade_key(
                        sym,
                        normalize_side(ctx.get("side") or r.get("side") or "buy"),
                        ets,
                    )
                except Exception:
                    entry_canon = None
        if entry_canon:
            entry_by_canonical[entry_canon] = entry_data

    def in_range(r: Dict[str, Any], ts_keys: Tuple[str, ...] = ("timestamp", "ts")) -> bool:
        ts = None
        for key in ts_keys:
            ts = r.get(key)
            if ts is not None:
                break
        if ts is None:
            ts = r.get("entry_timestamp")
        d = _day_utc(ts)
        if not d:
            return True
        if start_date and d < start_date:
            return False
        if end_date and d > end_date:
            return False
        return True

    joined: List[Dict[str, Any]] = []
    for ex in exit_all:
        if not in_range(ex, ("timestamp", "ts", "exit_timestamp", "entry_timestamp")):
            continue
        k = exit_key(ex)
        if not k:
            continue
        tid = ex.get("trade_id") or ex.get("decision_id")
        exit_canon: Optional[str] = None
        for ck in (ex.get("trade_key"), ex.get("canonical_trade_id")):
            if ck and str(ck).strip():
                s = str(ck).strip()
                parts = s.split("|")
                if len(parts) >= 3:
                    try:
                        int(parts[-1])
                        exit_canon = s
                        break
                    except ValueError:
                        pass
        if exit_canon is None:
            sym_ex = (ex.get("symbol") or "").upper()
            ets_ex = ex.get("entry_timestamp") or ex.get("entry_ts")
            if sym_ex and ets_ex:
                try:
                    exit_canon = build_trade_key(
                        sym_ex,
                        normalize_side(ex.get("position_side") or ex.get("side") or "buy"),
                        ets_ex,
                    )
                except Exception:
                    exit_canon = None
        entry = entry_by_canonical.get(exit_canon) if exit_canon else None
        used_canonical = bool(entry)
        used_trade_id = False
        if not entry and tid:
            entry = entry_by_trade_id.get(str(tid))
            used_trade_id = bool(entry)
        if not entry:
            entry = entry_by_key.get(k)
        row: Dict[str, Any] = dict(ex)
        row["_join_key"] = k
        if used_canonical:
            row["quality_flags"] = list(row.get("quality_flags") or []) + ["join_canonical_trade_key"]
        elif not used_trade_id and (entry or k):
            row["quality_flags"] = list(row.get("quality_flags") or []) + ["join_fallback"]
        if entry:
            row["entry_score"] = entry.get("entry_score")
            row["entry_attribution_components"] = entry.get("entry_attribution_components")
            row["entry_regime"] = entry.get("entry_regime")
            row["entry_context"] = entry.get("entry_context")
        joined.append(row)
    return joined


def load_from_backtest_dir(backtest_dir: Path) -> List[Dict[str, Any]]:
    """
    Load closed trades from backtest outputs: backtest_trades.jsonl + backtest_exits.jsonl.
    Backtest exits have same shape as exit_attribution (with optional Phase 4 fields).
    """
    trades_path = backtest_dir / "backtest_trades.jsonl"
    exits_path = backtest_dir / "backtest_exits.jsonl"
    if not exits_path.exists():
        return []
    exits = load_jsonl(exits_path)
    trades = load_jsonl(trades_path)
    # Backtest trades may have timestamp, symbol, context; exits have entry_timestamp, symbol
    entry_by_key: Dict[str, Dict[str, Any]] = {}
    for r in trades:
        sym = (r.get("symbol") or "").upper()
        ts = r.get("timestamp") or r.get("ts")
        ctx = r.get("context") or {}
        if sym and ts:
            k = f"{sym}|{entry_ts_bucket(ts)}"
            if k not in entry_by_key:
                entry_by_key[k] = {
                    "entry_score": ctx.get("entry_score") or r.get("entry_score"),
                    "entry_attribution_components": ctx.get("attribution_components"),
                    "entry_regime": ctx.get("regime"),
                }
    joined: List[Dict[str, Any]] = []
    for ex in exits:
        k = exit_key(ex)
        if not k:
            continue
        row = dict(ex)
        row["_join_key"] = k
        entry = entry_by_key.get(k)
        # Phase 8: backtest join is always (symbol, entry_ts); no trade_id in backtest outputs today → join_fallback
        row["quality_flags"] = list(row.get("quality_flags") or []) + ["join_fallback"]
        if entry:
            row["entry_score"] = entry.get("entry_score")
            row["entry_attribution_components"] = entry.get("entry_attribution_components")
            row["entry_regime"] = entry.get("entry_regime")
        joined.append(row)
    return joined
