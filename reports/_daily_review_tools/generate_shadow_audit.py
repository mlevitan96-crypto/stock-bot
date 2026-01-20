#!/usr/bin/env python3
"""
Generate a Shadow Trading Audit report from DROPLET production data.

Output:
- reports/SHADOW_TRADING_AUDIT_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from report_data_fetcher import ReportDataFetcher
from report_data_validator import validate_data_source, validate_report_data


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=False, help="YYYY-MM-DD (default: today UTC)")
    args = ap.parse_args()

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = Path("reports") / f"SHADOW_TRADING_AUDIT_{date}.md"

    with ReportDataFetcher(date=date) as fetcher:
        src = fetcher.get_data_source_info()
        validate_data_source(src)

        # Minimal validation: shadow may be empty early rollout; still write report.
        trades = fetcher.get_executed_trades()
        shadow = fetcher.get_shadow_events()
        gates = fetcher.get_gate_events()
        orders = fetcher.get_orders()
        blocked = fetcher.get_blocked_trades()
        signals = fetcher.get_signals()
        validate_report_data(trades, blocked, signals, date=date)

    # Summaries
    by_type = Counter()
    divergence = 0
    v2_candidate = 0
    v2_executed = 0
    v1_pass = 0
    v2_pass = 0
    deltas: List[float] = []
    shadow_realized_pnl_usd = 0.0
    unrealized_by_symbol: Dict[str, float] = {}
    realized_by_symbol: Dict[str, float] = {}

    for r in shadow:
        et = str(r.get("event_type", "") or "")
        by_type[et] += 1
        if et == "divergence":
            divergence += 1
        if et == "shadow_candidate":
            v2_candidate += 1
        if et == "shadow_executed":
            v2_executed += 1
        if et == "score_compare":
            if r.get("v1_pass") is True:
                v1_pass += 1
            if r.get("v2_pass") is True:
                v2_pass += 1
            ds = _safe_float(r.get("v2_score")) - _safe_float(r.get("v1_score"))
            deltas.append(ds)
        if et == "shadow_exit":
            sym = str(r.get("symbol") or "").upper()
            pnl = _safe_float(r.get("realized_pnl_usd"))
            shadow_realized_pnl_usd += pnl
            if sym:
                realized_by_symbol[sym] = realized_by_symbol.get(sym, 0.0) + pnl
        if et == "shadow_pnl_update":
            sym = str(r.get("symbol") or "").upper()
            if sym:
                unrealized_by_symbol[sym] = _safe_float(r.get("unrealized_pnl_usd"))

    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

    shadow_unrealized_pnl_usd = sum(unrealized_by_symbol.values()) if unrealized_by_symbol else 0.0
    shadow_total_pnl_usd = shadow_realized_pnl_usd + shadow_unrealized_pnl_usd

    # Real PnL (approx): sum final pnl_usd per trade_id for the day.
    pnl_by_trade_id: Dict[str, float] = {}
    for t in trades:
        tid = str(t.get("trade_id") or "")
        if not tid:
            continue
        pnl_by_trade_id[tid] = _safe_float(t.get("pnl_usd"))
    real_total_pnl_usd = sum(pnl_by_trade_id.values()) if pnl_by_trade_id else 0.0

    # Real vs shadow comparison
    real_symbols = set()
    for t in trades:
        sym = t.get("symbol") or (t.get("context", {}) if isinstance(t.get("context"), dict) else {}).get("symbol")
        if sym:
            real_symbols.add(str(sym).upper())

    shadow_exec_symbols = set()
    for r in shadow:
        if str(r.get("event_type", "") or "") != "shadow_executed":
            continue
        sym = r.get("symbol")
        if sym:
            shadow_exec_symbols.add(str(sym).upper())

    overlap = sorted(real_symbols & shadow_exec_symbols)
    real_only = sorted(real_symbols - shadow_exec_symbols)
    shadow_only = sorted(shadow_exec_symbols - real_symbols)

    lines: List[str] = []
    lines.append(f"# SHADOW_TRADING_AUDIT_{date}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- **shadow_events**: `{len(shadow)}`")
    lines.append(f"- **real_trades(attribution)**: `{len(trades)}`")
    lines.append(f"- **divergences**: `{divergence}`")
    lines.append(f"- **v2_candidates**: `{v2_candidate}`")
    lines.append(f"- **v2_hypothetical_executed**: `{v2_executed}`")
    lines.append(f"- **v1_pass_count(score_compare)**: `{v1_pass}`")
    lines.append(f"- **v2_pass_count(score_compare)**: `{v2_pass}`")
    lines.append(f"- **avg(v2_score - v1_score)**: `{avg_delta:.4f}`")
    lines.append("")
    lines.append("## Shadow PnL (hypothetical)")
    lines.append(f"- **shadow_realized_pnl_usd** (shadow_exit): `{shadow_realized_pnl_usd:.2f}`")
    lines.append(f"- **shadow_unrealized_pnl_usd** (latest): `{shadow_unrealized_pnl_usd:.2f}`")
    lines.append(f"- **shadow_total_pnl_usd**: `{shadow_total_pnl_usd:.2f}`")
    lines.append("")
    lines.append("## Real vs shadow PnL (approx)")
    lines.append(f"- **real_total_pnl_usd** (attribution, per trade_id): `{real_total_pnl_usd:.2f}`")
    lines.append(f"- **shadow_total_pnl_usd**: `{shadow_total_pnl_usd:.2f}`")
    lines.append("")
    if unrealized_by_symbol or realized_by_symbol:
        lines.append("## Shadow PnL by symbol (top 15 by abs total)")
        sym_totals: Dict[str, float] = {}
        for s, v in unrealized_by_symbol.items():
            sym_totals[s] = sym_totals.get(s, 0.0) + v
        for s, v in realized_by_symbol.items():
            sym_totals[s] = sym_totals.get(s, 0.0) + v
        for s, v in sorted(sym_totals.items(), key=lambda kv: abs(kv[1]), reverse=True)[:15]:
            lines.append(f"- `{s}`: `{v:.2f}` (realized `{realized_by_symbol.get(s, 0.0):.2f}`, unrealized `{unrealized_by_symbol.get(s, 0.0):.2f}`)")
        lines.append("")
    lines.append("## Real vs shadow (symbol overlap)")
    lines.append(f"- **real_symbols**: `{len(real_symbols)}`")
    lines.append(f"- **shadow_executed_symbols**: `{len(shadow_exec_symbols)}`")
    lines.append(f"- **overlap_symbols**: `{len(overlap)}`")
    lines.append(f"- **real_only_symbols**: `{len(real_only)}`")
    lines.append(f"- **shadow_only_symbols**: `{len(shadow_only)}`")
    lines.append("")
    if overlap:
        lines.append("### Overlap (up to 25)")
        lines.append("- " + ", ".join(overlap[:25]))
        lines.append("")
    if shadow_only:
        lines.append("### Shadow-only (up to 25)")
        lines.append("- " + ", ".join(shadow_only[:25]))
        lines.append("")
    if real_only:
        lines.append("### Real-only (up to 25)")
        lines.append("- " + ", ".join(real_only[:25]))
        lines.append("")
    lines.append("## Event types")
    for k, v in by_type.most_common():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("## Notes")
    lines.append("- This report is generated from droplet production logs via `ReportDataFetcher`.")
    lines.append("- Shadow is **read-only**: v2 does not submit real orders.")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

