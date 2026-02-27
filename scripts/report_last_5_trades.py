#!/usr/bin/env python3
"""
Report the last 5 opened-and-closed trades with full trade flow detail:
- All entry signals captured, their scores, and how they were leveraged in the trading decision
- Exit decision: all signals that played into when to exit

Designed to run on the droplet (or locally with --base-dir) so logs/attribution.jsonl
and logs/exit_attribution.jsonl are used.

Usage:
  python scripts/report_last_5_trades.py [--base-dir PATH] [--n 5]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.analysis.attribution_loader import load_joined_closed_trades, load_jsonl


def _exit_ts_sort_key(r: dict) -> str:
    ts = r.get("timestamp") or r.get("ts") or r.get("exit_timestamp") or ""
    return str(ts)


def _format_components(components: list | dict | None) -> str:
    if not components:
        return "  (none recorded)"
    lines = []
    if isinstance(components, list):
        for c in components:
            sid = c.get("signal_id") or c.get("name") or "?"
            contrib = c.get("contribution_to_score")
            weight = c.get("weight")
            raw = c.get("raw_value")
            line = f"    - {sid}: contribution_to_score={contrib}"
            if weight is not None:
                line += f", weight={weight}"
            if raw is not None:
                line += f", raw_value={raw}"
            lines.append(line)
    elif isinstance(components, dict):
        for k, v in components.items():
            if isinstance(v, dict):
                contrib = v.get("contribution_to_score") or v.get("conviction") or v.get("score")
                lines.append(f"    - {k}: {contrib}")
            else:
                lines.append(f"    - {k}: {v}")
    return "\n".join(lines) if lines else "  (empty)"


def _format_exit_components(v2_exit_components: dict | None) -> str:
    if not v2_exit_components:
        return "  (none)"
    lines = []
    for k, v in sorted(v2_exit_components.items()):
        if isinstance(v, dict):
            lines.append(f"    - {k}: {json.dumps(v)[:80]}")
        else:
            lines.append(f"    - {k}: {v}")
    return "\n".join(lines) if lines else "  (none)"


def main() -> int:
    ap = argparse.ArgumentParser(description="Report last N closed trades with full signal/score/exit detail")
    ap.add_argument("--base-dir", type=Path, default=REPO, help="Repo root (logs/attribution.jsonl, logs/exit_attribution.jsonl)")
    ap.add_argument("--n", type=int, default=5, help="Number of last trades to report")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    attr_path = base / "logs" / "attribution.jsonl"
    exit_path = base / "logs" / "exit_attribution.jsonl"

    if not attr_path.exists():
        print(f"Missing {attr_path}", file=sys.stderr)
        return 1
    if not exit_path.exists():
        print(f"Missing {exit_path}", file=sys.stderr)
        return 1

    joined = load_joined_closed_trades(attr_path, exit_path)
    if not joined:
        print("No closed trades found (no joined entry+exit records).", file=sys.stderr)
        return 0

    sorted_joined = sorted(joined, key=_exit_ts_sort_key)
    last_n = sorted_joined[-args.n :]

    for i, row in enumerate(reversed(last_n), 1):
        symbol = (row.get("symbol") or "?").upper()
        entry_ts = row.get("entry_timestamp") or row.get("entry_ts") or "?"
        exit_ts = row.get("timestamp") or row.get("ts") or "?"
        pnl = row.get("pnl")
        pnl_pct = row.get("pnl_pct")
        entry_price = row.get("entry_price")
        exit_price = row.get("exit_price")
        qty = row.get("qty")
        hold_mins = row.get("time_in_trade_minutes")
        exit_reason = row.get("exit_reason") or "?"
        exit_reason_code = row.get("exit_reason_code") or exit_reason
        entry_score = row.get("entry_score")
        v2_exit_score = row.get("v2_exit_score")
        score_deterioration = row.get("score_deterioration")
        entry_regime = row.get("entry_regime") or "?"
        exit_regime = row.get("exit_regime") or "?"
        entry_components = row.get("entry_attribution_components")
        entry_context = row.get("entry_context") or {}
        entry_ctx_components = entry_context.get("components") or {}
        v2_exit_components = row.get("v2_exit_components") or {}
        exit_attribution_components = row.get("attribution_components")
        exit_quality = row.get("exit_quality_metrics") or {}

        print()
        print("=" * 80)
        print(f"TRADE {i} (newest first): {symbol}")
        print("=" * 80)
        print()
        print("--- SUMMARY ---")
        print(f"  Symbol: {symbol}  |  Entry: {entry_ts}  |  Exit: {exit_ts}")
        print(f"  Entry price: {entry_price}  |  Exit price: {exit_price}  |  Qty: {qty}")
        print(f"  P&L: {pnl} USD  |  P&L %: {pnl_pct}%  |  Hold: {hold_mins} min")
        print(f"  Close reason: {exit_reason}  (code: {exit_reason_code})")
        print()

        print("--- ENTRY: SIGNALS CAPTURED AND SCORES ---")
        print(f"  Entry composite score: {entry_score}")
        print(f"  Market regime at entry: {entry_regime}")
        print("  Attribution components (per-signal contribution to entry score):")
        print(_format_components(entry_components))
        if entry_ctx_components and not entry_components:
            print("  Raw entry context.components (legacy):")
            print(_format_components(entry_ctx_components))
        print()

        print("--- ENTRY: HOW SIGNALS WERE LEVERAGED IN THE TRADING DECISION ---")
        print("  The entry decision uses the composite entry score (above) and regime.")
        print("  Each component's contribution_to_score is weighted and summed; the total")
        print("  is compared to MIN_EXEC_SCORE / governance threshold to open the position.")
        if entry_score is not None:
            print(f"  This trade's entry_score {entry_score} was above threshold → position opened.")
        print()

        print("--- EXIT: SIGNALS THAT DETERMINED WHEN TO EXIT ---")
        print(f"  Exit composite score (v2): {v2_exit_score}")
        print(f"  Score deterioration (entry→exit): {score_deterioration}")
        print(f"  Exit regime: {exit_regime}")
        print("  Exit reason (primary):", exit_reason_code)
        print("  v2_exit_components (signals at exit that feed exit score):")
        print(_format_exit_components(v2_exit_components))
        if exit_attribution_components:
            print("  Exit attribution_components (per-factor contribution at exit):")
            print(_format_components(exit_attribution_components))
        if exit_quality:
            mfe = exit_quality.get("mfe")
            mae = exit_quality.get("mae")
            giveback = exit_quality.get("profit_giveback")
            print("  Exit quality metrics: MFE=%s, MAE=%s, profit_giveback=%s" % (mfe, mae, giveback))
        print()

    print("=" * 80)
    print("END OF REPORT")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
