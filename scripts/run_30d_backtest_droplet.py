#!/usr/bin/env python3
"""
Full 30-day backtest (run on droplet only).
Replays from logs: attribution, exit_attribution, blocked_trades.
Applies config flags (exit_regimes, UW, survivorship, wheel, constraints, correlation) as metadata.
Writes:
  backtests/30d/backtest_trades.jsonl
  backtests/30d/backtest_exits.jsonl
  backtests/30d/backtest_blocks.jsonl
  backtests/30d/backtest_summary.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONFIG_PATH = REPO_ROOT / "backtests" / "config" / "30d_backtest_config.json"
OUT_DIR = REPO_ROOT / "backtests" / "30d"
TRADES_PATH = OUT_DIR / "backtest_trades.jsonl"
EXITS_PATH = OUT_DIR / "backtest_exits.jsonl"
BLOCKS_PATH = OUT_DIR / "backtest_blocks.jsonl"
SUMMARY_PATH = OUT_DIR / "backtest_summary.json"


def _day_utc(ts) -> str | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return None
    s = str(ts)
    if len(s) >= 10:
        return s[:10]
    return None


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=30)
        return {
            "start_date": str(start),
            "end_date": str(end),
            "mode": "paper",
            "use_exit_regimes": True,
            "use_uw": True,
            "use_survivorship": True,
            "use_constraints": True,
            "use_correlation_sizing": True,
            "use_wheel_strategy": True,
            "log_all_candidates": True,
            "log_all_exits": True,
            "log_all_blocks": True,
        }
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def run() -> int:
    cfg = _load_config()
    start_date = cfg.get("start_date") or ""
    end_date = cfg.get("end_date") or ""
    window_days = []
    try:
        start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
        d = start_d
        while d <= end_d:
            window_days.append(d.strftime("%Y-%m-%d"))
            d += timedelta(days=1)
    except Exception:
        # last 30 days
        end_d = datetime.now(timezone.utc).date()
        for i in range(30):
            d = end_d - timedelta(days=i)
            window_days.append(d.strftime("%Y-%m-%d"))
        window_days = list(dict.fromkeys(window_days))

    base = REPO_ROOT
    attr_path = base / "logs" / "attribution.jsonl"
    exit_attr_path = base / "logs" / "exit_attribution.jsonl"
    blocked_path = base / "state" / "blocked_trades.jsonl"

    # Load attribution (executed trades) in window
    trades = []
    for r in _iter_jsonl(attr_path):
        if r.get("type") != "attribution":
            continue
        day = _day_utc(r.get("timestamp") or r.get("ts"))
        if day not in window_days:
            continue
        trades.append({
            "timestamp": r.get("timestamp") or r.get("ts"),
            "symbol": r.get("symbol"),
            "entry_score": r.get("entry_score"),
            "pnl_usd": r.get("pnl_usd"),
            "pnl_pct": r.get("pnl_pct"),
            "hold_minutes": r.get("hold_minutes"),
            "context": r.get("context"),
            "source": "attribution",
        })

    # Load exit_attribution (exits with regime/reason) in window
    exits = []
    for r in _iter_jsonl(exit_attr_path):
        day = _day_utc(r.get("timestamp"))
        if day not in window_days:
            continue
        exits.append({
            "timestamp": r.get("timestamp"),
            "symbol": r.get("symbol"),
            "exit_reason": r.get("exit_reason"),
            "exit_regime_decision": r.get("exit_regime_decision"),
            "exit_regime_reason": r.get("exit_regime_reason"),
            "pnl": r.get("pnl"),
            "pnl_pct": r.get("pnl_pct"),
            "time_in_trade_minutes": r.get("time_in_trade_minutes"),
            "variant_id": r.get("variant_id"),
            "source": "exit_attribution",
        })

    # Load blocked_trades in window
    blocks = []
    for r in _iter_jsonl(blocked_path):
        day = _day_utc(r.get("timestamp") or r.get("ts"))
        if day not in window_days:
            continue
        blocks.append({
            "timestamp": r.get("timestamp") or r.get("ts"),
            "symbol": r.get("symbol"),
            "reason": r.get("reason") or r.get("block_reason"),
            "score": r.get("score"),
            "expected_value_usd": r.get("expected_value_usd"),
            "strategy": r.get("strategy") or r.get("variant_id"),
            "uw_signal_quality_score": r.get("uw_signal_quality_score"),
            "source": "blocked_trades",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def write_jsonl(path: Path, rows: list) -> None:
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, default=str) + "\n")

    write_jsonl(TRADES_PATH, trades)
    write_jsonl(EXITS_PATH, exits)
    write_jsonl(BLOCKS_PATH, blocks)

    # Summary
    total_pnl = sum(float(t.get("pnl_usd") or 0) for t in trades)
    wins = sum(1 for t in trades if (t.get("pnl_usd") or 0) > 0)
    losses = sum(1 for t in trades if (t.get("pnl_usd") or 0) < 0)
    exit_reasons = {}
    for e in exits:
        r = e.get("exit_reason") or "unknown"
        exit_reasons[r] = exit_reasons.get(r, 0) + 1
    regime_counts = {}
    for e in exits:
        r = e.get("exit_regime_decision") or "normal"
        regime_counts[r] = regime_counts.get(r, 0) + 1
    block_reasons = {}
    for b in blocks:
        r = b.get("reason") or "unknown"
        block_reasons[r] = block_reasons.get(r, 0) + 1

    summary = {
        "config": cfg,
        "window_start": start_date,
        "window_end": end_date,
        "trades_count": len(trades),
        "exits_count": len(exits),
        "blocks_count": len(blocks),
        "total_pnl_usd": round(total_pnl, 2),
        "winning_trades": wins,
        "losing_trades": losses,
        "win_rate_pct": round(wins / len(trades) * 100.0, 2) if trades else 0.0,
        "exit_reason_counts": exit_reasons,
        "exit_regime_counts": regime_counts,
        "block_reason_counts": block_reasons,
        "artifacts": {
            "backtest_trades": str(TRADES_PATH),
            "backtest_exits": str(EXITS_PATH),
            "backtest_blocks": str(BLOCKS_PATH),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    print("[30d BACKTEST] Done.")
    print(f"  Trades: {len(trades)}, Exits: {len(exits)}, Blocks: {len(blocks)}")
    print(f"  P&L: ${summary['total_pnl_usd']:.2f}, Win rate: {summary['win_rate_pct']}%")
    print(f"  Wrote: {TRADES_PATH}, {EXITS_PATH}, {BLOCKS_PATH}, {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
