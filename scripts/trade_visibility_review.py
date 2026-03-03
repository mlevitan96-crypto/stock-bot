#!/usr/bin/env python3
"""
Trade visibility review: executed trades since a cutoff (e.g. yesterday/today),
100-trade baseline progress (telemetry-backed for direction replay), and
entries, exits, sizing summary.

Usage:
  python scripts/trade_visibility_review.py [--since-hours 48] [--out report.md]
  python scripts/trade_visibility_review.py --since-date 2026-03-02

Reads: config.registry LogFiles.ATTRIBUTION, EXIT_ATTRIBUTION; state/direction_readiness.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.registry import Directories, LogFiles


def _parse_ts(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        s = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except Exception:
        return None


def load_closed_trades_since(
    base: Path,
    since_dt: datetime,
) -> List[Dict[str, Any]]:
    """Load closed trades from attribution log with ts >= since_dt."""
    path = (base / LogFiles.ATTRIBUTION).resolve()
    trades: List[Dict[str, Any]] = []
    if not path.exists():
        return trades
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get("type") != "attribution":
                continue
            trade_id = rec.get("trade_id") or ""
            if str(trade_id).startswith("open_"):
                continue
            ts = _parse_ts(rec.get("ts") or rec.get("timestamp"))
            if not ts or ts < since_dt:
                continue
            context = rec.get("context") or {}
            pnl = float(rec.get("pnl_usd", 0) or 0)
            close_reason = context.get("close_reason") or rec.get("close_reason") or ""
            if pnl == 0.0 and not close_reason:
                continue
            rec["_ts"] = ts
            trades.append(rec)
        except Exception:
            continue
    trades.sort(key=lambda t: t.get("_ts") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return trades


def count_telemetry_backed_exit_attribution(base: Path) -> Tuple[int, int]:
    """Count total and telemetry-backed records in exit_attribution.jsonl."""
    path = (base / LogFiles.EXIT_ATTRIBUTION).resolve()
    total = 0
    telemetry = 0
    if not path.exists():
        return 0, 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if not isinstance(rec, dict):
                continue
            total += 1
            embed = rec.get("direction_intel_embed")
            if isinstance(embed, dict):
                snap = embed.get("intel_snapshot_entry")
                if isinstance(snap, dict) and snap:
                    telemetry += 1
        except Exception:
            continue
    return total, telemetry


def load_direction_readiness(base: Path) -> Dict[str, Any]:
    """Load state/direction_readiness.json."""
    path = (base / Directories.STATE / "direction_readiness.json").resolve()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def summarize_trades(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Entries, exits, sizing, P&L summary."""
    if not trades:
        return {
            "count": 0,
            "wins": 0,
            "losses": 0,
            "win_rate_pct": 0.0,
            "total_pnl_usd": 0.0,
            "by_symbol": {},
            "by_close_reason": {},
            "sizing": {"qtys": [], "avg_qty": 0.0},
        }
    wins = sum(1 for t in trades if float(t.get("pnl_usd", 0) or 0) > 0)
    losses = sum(1 for t in trades if float(t.get("pnl_usd", 0) or 0) < 0)
    total_pnl = sum(float(t.get("pnl_usd", 0) or 0) for t in trades)
    by_symbol: Dict[str, int] = defaultdict(int)
    by_close_reason: Dict[str, int] = defaultdict(int)
    qtys: List[float] = []
    for t in trades:
        by_symbol[str(t.get("symbol", "?"))] += 1
        ctx = t.get("context") or {}
        reason = ctx.get("close_reason") or t.get("close_reason") or "unknown"
        by_close_reason[reason] += 1
        q = ctx.get("qty") or t.get("qty")
        if q is not None:
            try:
                qtys.append(float(q))
            except Exception:
                pass
    return {
        "count": len(trades),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": (100.0 * wins / len(trades)) if trades else 0.0,
        "total_pnl_usd": total_pnl,
        "by_symbol": dict(by_symbol),
        "by_close_reason": dict(by_close_reason),
        "sizing": {
            "qtys": qtys,
            "avg_qty": sum(qtys) / len(qtys) if qtys else 0.0,
            "min_qty": min(qtys) if qtys else None,
            "max_qty": max(qtys) if qtys else None,
        },
    }


def run(
    base: Path,
    since_dt: datetime,
    out_path: Optional[Path] = None,
) -> Tuple[Dict[str, Any], str]:
    """Run review and return (data dict, markdown string)."""
    trades = load_closed_trades_since(base, since_dt)
    total_exit, telemetry_exit = count_telemetry_backed_exit_attribution(base)
    readiness = load_direction_readiness(base)
    summary = summarize_trades(trades)

    telemetry_trades = readiness.get("telemetry_trades", telemetry_exit)
    total_trades_readiness = readiness.get("total_trades", total_exit)
    ready = readiness.get("ready", False)
    pct_telemetry = readiness.get("pct_telemetry") or (100.0 * telemetry_exit / total_exit if total_exit else 0.0)

    lines: List[str] = []
    lines.append("# Trade Visibility Review")
    lines.append("")
    lines.append(f"**Window:** since {since_dt.strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("")
    lines.append("## 1. Executed trades (closed) in window")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Trades closed | {summary['count']} |")
    lines.append(f"| Wins | {summary['wins']} |")
    lines.append(f"| Losses | {summary['losses']} |")
    lines.append(f"| Win rate | {summary['win_rate_pct']:.1f}% |")
    lines.append(f"| Total P&L (USD) | ${summary['total_pnl_usd']:.2f} |")
    lines.append("")
    if summary["by_symbol"]:
        lines.append("### By symbol")
        lines.append("")
        lines.append("| Symbol | Count |")
        lines.append("|--------|-------|")
        for sym, cnt in sorted(summary["by_symbol"].items(), key=lambda x: -x[1]):
            lines.append(f"| {sym} | {cnt} |")
        lines.append("")
    if summary["by_close_reason"]:
        lines.append("### By exit (close reason)")
        lines.append("")
        lines.append("| Close reason | Count |")
        lines.append("|--------------|-------|")
        for reason, cnt in sorted(summary["by_close_reason"].items(), key=lambda x: -x[1]):
            lines.append(f"| {reason} | {cnt} |")
        lines.append("")
    sizing = summary["sizing"]
    if sizing["qtys"]:
        lines.append("### Sizing (qty)")
        lines.append("")
        lines.append(f"- Avg qty: {sizing['avg_qty']:.1f}")
        if sizing.get("min_qty") is not None:
            lines.append(f"- Min qty: {sizing['min_qty']:.1f}")
        if sizing.get("max_qty") is not None:
            lines.append(f"- Max qty: {sizing['max_qty']:.1f}")
        lines.append("")
    lines.append("## 2. 100-trade baseline (direction replay)")
    lines.append("")
    lines.append("Direction replay runs after we have **>=100 telemetry-backed trades** in `logs/exit_attribution.jsonl` ")
    lines.append("(records with `direction_intel_embed.intel_snapshot_entry`). State: `state/direction_readiness.json`.")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Exit attribution records (total) | {total_exit} |")
    lines.append(f"| Telemetry-backed (have intel snapshot at entry) | {telemetry_exit} |")
    lines.append(f"| Progress to 100 | {telemetry_exit}/100 |")
    lines.append(f"| % telemetry | {pct_telemetry:.1f}% |")
    lines.append(f"| Ready for replay (>=100 & >=90%) | {ready} |")
    if readiness.get("ready_ts"):
        lines.append(f"| Ready at | {readiness['ready_ts']} |")
    lines.append("")
    lines.append("## 3. Recent closed trades (sample)")
    lines.append("")
    if not trades:
        lines.append("No closed trades in window.")
    else:
        lines.append("| Time (UTC) | Symbol | P&L (USD) | Close reason |")
        lines.append("|------------|--------|-----------|--------------|")
        for t in trades[:20]:
            ts = t.get("_ts")
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if ts else "—"
            sym = t.get("symbol", "?")
            pnl = float(t.get("pnl_usd", 0) or 0)
            ctx = t.get("context") or {}
            reason = ctx.get("close_reason") or t.get("close_reason") or "—"
            lines.append(f"| {ts_str} | {sym} | ${pnl:.2f} | {reason} |")
        if len(trades) > 20:
            lines.append(f"| … | … | … | (+{len(trades) - 20} more) |")
    lines.append("")

    md = "\n".join(lines)
    data = {
        "since_utc": since_dt.isoformat(),
        "executed_in_window": summary,
        "exit_attribution_total": total_exit,
        "telemetry_backed": telemetry_exit,
        "direction_ready": ready,
        "direction_readiness": readiness,
    }
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
    return data, md


def main() -> int:
    ap = argparse.ArgumentParser(description="Trade visibility review (executed trades, 100-trade baseline, entries/exits/sizing)")
    ap.add_argument("--since-hours", type=float, default=48, help="Look back hours (default 48)")
    ap.add_argument("--since-date", type=str, default=None, help="Start of window YYYY-MM-DD (UTC)")
    ap.add_argument("--out", type=str, default=None, help="Write markdown to this path")
    ap.add_argument("--repo", type=str, default=None, help="Repo root (default: parent of scripts/)")
    args = ap.parse_args()
    base = Path(args.repo).resolve() if args.repo else REPO_ROOT
    if args.since_date:
        try:
            since_dt = datetime.strptime(args.since_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Invalid --since-date: {args.since_date}", file=sys.stderr)
            return 1
    else:
        since_dt = datetime.now(timezone.utc) - timedelta(hours=args.since_hours)
    out_path = Path(args.out).resolve() if args.out else None
    if not out_path and (base / "reports" / "audit").exists():
        out_path = base / "reports" / "audit" / f"TRADE_VISIBILITY_REVIEW_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    data, md = run(base, since_dt, out_path)
    print(md)
    if out_path:
        print(f"\nWrote: {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
