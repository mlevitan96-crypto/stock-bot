#!/usr/bin/env python3
"""
Learning rollups (stdlib-only).

Used by:
- dashboard.py (for UI/API rollups)
- main.py daily scheduler (persist rollups for learning engine)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _now_ts() -> int:
    return int(time.time())


def _parse_ts(rec: dict) -> Optional[int]:
    """
    Try multiple timestamp fields. Return epoch seconds or None.
    """
    for key in ("_ts", "ts", "timestamp"):
        v = rec.get(key)
        if v is None:
            continue
        # unix
        if isinstance(v, (int, float)):
            return int(v)
        # ISO string
        if isinstance(v, str):
            try:
                s = v.strip()
                # common format: 2025-12-16T23:30:36.123Z or with +00:00
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return int(dt.timestamp())
            except Exception:
                continue
    return None


def _read_jsonl(path: Path, limit_lines: int = 20000) -> List[dict]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    if limit_lines and len(lines) > limit_lines:
        lines = lines[-limit_lines:]
    out: List[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def compute_rollup(
    repo_dir: Path,
    window_days: int,
    now_ts: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute rolling window metrics over logs/state files.
    """
    now_ts = now_ts or _now_ts()
    cutoff = now_ts - int(window_days * 86400)

    logs_dir = repo_dir / "logs"
    state_dir = repo_dir / "state"
    data_dir = repo_dir / "data"

    attribution_path = logs_dir / "attribution.jsonl"
    blocked_path = state_dir / "blocked_trades.jsonl"
    monitoring_path = data_dir / "monitoring_summary.jsonl"

    attributions = _read_jsonl(attribution_path)
    blocks = _read_jsonl(blocked_path)
    monitoring = _read_jsonl(monitoring_path)

    # Filter by window
    win_attr = []
    for r in attributions:
        ts = _parse_ts(r)
        if ts is None or ts < cutoff:
            continue
        if r.get("type") == "attribution":
            win_attr.append(r)

    win_blocks = []
    for r in blocks:
        ts = _parse_ts(r)
        if ts is None or ts < cutoff:
            continue
        win_blocks.append(r)

    win_monitoring = []
    for r in monitoring:
        ts = _parse_ts(r)
        if ts is None or ts < cutoff:
            continue
        win_monitoring.append(r)

    # PnL metrics
    pnls = []
    by_symbol: Dict[str, Dict[str, float]] = {}
    trades: List[dict] = []
    for r in win_attr:
        sym = r.get("symbol") or r.get("ticker") or "UNKNOWN"
        pnl = float(r.get("pnl_usd", 0) or 0)
        pnls.append(pnl)
        by_symbol.setdefault(sym, {"pnl": 0.0, "trades": 0.0})
        by_symbol[sym]["pnl"] += pnl
        by_symbol[sym]["trades"] += 1.0
        trades.append({
            "ts": r.get("ts"),
            "symbol": sym,
            "pnl_usd": pnl,
            "context": r.get("context", {}),
        })

    trades_sorted = sorted(trades, key=lambda x: str(x.get("ts") or ""), reverse=True)
    wins = sum(1 for p in pnls if p > 0)
    total = len(pnls)
    total_pnl = sum(pnls)
    win_rate = (wins / total) if total else None

    top_symbols = sorted(
        [{"symbol": s, "pnl_usd": round(v["pnl"], 2), "trades": int(v["trades"])} for s, v in by_symbol.items()],
        key=lambda x: (x["pnl_usd"], x["trades"]),
        reverse=True,
    )[:10]

    # Block summary
    blocks_by_reason: Dict[str, int] = {}
    blocks_by_symbol: Dict[str, int] = {}
    for b in win_blocks:
        reason = str(b.get("reason") or "unknown")
        sym = str(b.get("symbol") or "UNKNOWN")
        blocks_by_reason[reason] = blocks_by_reason.get(reason, 0) + 1
        blocks_by_symbol[sym] = blocks_by_symbol.get(sym, 0) + 1

    top_block_reasons = sorted(
        [{"reason": r, "count": c} for r, c in blocks_by_reason.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    top_block_symbols = sorted(
        [{"symbol": s, "count": c} for s, c in blocks_by_symbol.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    # Executive review (heuristic)
    review: List[str] = []
    if total == 0:
        review.append("No completed trades in this window (PnL attribution empty).")
    else:
        review.append(f"PnL: ${total_pnl:,.2f} over {total} closes (win rate: {win_rate:.1%})." if win_rate is not None else f"PnL: ${total_pnl:,.2f} over {total} closes.")

    if top_block_reasons:
        review.append(f"Top block reason: {top_block_reasons[0]['reason']} ({top_block_reasons[0]['count']} events).")

    # Common actionable hints
    reasons = {x["reason"] for x in top_block_reasons}
    if any("max_positions" in r for r in reasons):
        review.append("Many blocks due to position limits: consider tightening symbol universe or raising MAX_CONCURRENT_POSITIONS only after execution costs are proven.")
    if any("spread" in r for r in reasons):
        review.append("Spread watchdog blocks are frequent: consider removing illiquid tickers or raising score threshold so only strongest trades attempt entry.")
    if any("theme_exposure" in r for r in reasons):
        review.append("Theme risk is blocking trades: validate theme map/limits; consider dynamic theme caps based on realized volatility.")
    if any("score_below_min" in r for r in reasons):
        review.append("Score gate blocks are frequent: verify scoring calibration; consider adaptive threshold tuning only with strong evidence.")

    # Monitoring summary highlights
    degraded_cycles = sum(1 for m in win_monitoring if (m.get("health_status") == "DEGRADED"))
    if degraded_cycles:
        review.append(f"Operational: {degraded_cycles} degraded cycles logged in monitoring_summary.jsonl.")

    return {
        "window_days": window_days,
        "now_ts": now_ts,
        "cutoff_ts": cutoff,
        "pnl": {
            "total_pnl_usd": round(total_pnl, 2),
            "trades_closed": total,
            "wins": wins,
            "win_rate": round(win_rate, 4) if win_rate is not None else None,
            "avg_pnl_usd": round((total_pnl / total), 2) if total else None,
        },
        "top_symbols": top_symbols,
        "recent_trades": trades_sorted[:50],
        "blocks": {
            "total": len(win_blocks),
            "top_reasons": top_block_reasons,
            "top_symbols": top_block_symbols,
        },
        "executive_review": review,
    }


def write_rollups(repo_dir: Path, windows: List[int] = [2, 5]) -> Dict[str, Any]:
    """
    Write rollups to data/learning_rollups.json (latest snapshot) and jsonl history.
    """
    repo_dir = repo_dir.resolve()
    data_dir = repo_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    now_ts = _now_ts()
    rollups = {str(w): compute_rollup(repo_dir, w, now_ts=now_ts) for w in windows}
    payload = {"_meta": {"ts": now_ts, "dt": datetime.now(timezone.utc).isoformat(), "windows": windows}, "rollups": rollups}

    latest = data_dir / "learning_rollups.json"
    latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    hist = data_dir / "learning_rollups.jsonl"
    _append = {"event": "LEARNING_ROLLUP", **payload}
    _append_jsonl(hist, _append)
    return payload

