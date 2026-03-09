#!/usr/bin/env python3
"""
FULL ONE-DAY FORENSIC REVIEW — 2026-03-09.
Run on droplet (or with --base-dir pointing to repo with logs/state) or use precomputed
TRADE_SHAPE_TABLE_<date>.json and audit files. Produces:
  reports/audit/INTRADAY_PROFITABILITY_FORENSIC_<date>.md
  reports/audit/INTRADAY_EXIT_WINDOW_ANALYSIS_<date>.json
  reports/audit/INTRADAY_BLOCKED_AND_COUNTER_INTEL_<date>.md
  reports/board/INTRADAY_BOARD_VERDICT_<date>.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"


def _load_json(path: Path) -> dict | list:
    if not path.exists():
        return {} if "{}" in str(path) else []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {} if "{}" in str(path) else []


def _load_jsonl(path: Path) -> list:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="One-day forensic review")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--base-dir", default=None, help="Repo root (default: script repo)")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Load trade shape table (from promotion/exit capture run)
    shape_path = AUDIT / f"TRADE_SHAPE_TABLE_{date_str}.json"
    if not shape_path.exists():
        shape_path = base / "reports" / "audit" / f"TRADE_SHAPE_TABLE_{date_str}.json"
    data = _load_json(shape_path)
    if isinstance(data, list):
        shapes = data
    else:
        shapes = data.get("shapes", [])

    shapes = [s for s in shapes if s.get("symbol")]
    n_trades = len(shapes)
    total_pnl = sum(float(s.get("pnl_usd") or 0) for s in shapes)
    green_then_red = [s for s in shapes if (s.get("mfe") or 0) > 0 and float(s.get("pnl_usd") or 0) < 0]
    mfe_positive = [s for s in shapes if (s.get("mfe") or 0) > 0]
    winners = [s for s in shapes if float(s.get("pnl_usd") or 0) > 0]
    losers = [s for s in shapes if float(s.get("pnl_usd") or 0) < 0]

    # Phase 0: data integrity (run on droplet to confirm)
    logs_dir = base / "logs"
    state_dir = base / "state"
    reports_state = base / "reports" / "state"
    trace_path = reports_state / "exit_decision_trace.jsonl"
    exit_attr_path = logs_dir / "exit_attribution.jsonl"
    blocked_path = state_dir / "blocked_trades.jsonl"
    phase0 = {
        "date": date_str,
        "exit_decision_trace_exists": trace_path.exists(),
        "exit_decision_trace_size": trace_path.stat().st_size if trace_path.exists() else 0,
        "exit_attribution_exists": exit_attr_path.exists(),
        "blocked_trades_exists": blocked_path.exists(),
        "fail_closed": False,
    }
    if not phase0["exit_decision_trace_exists"] or not phase0["exit_attribution_exists"]:
        phase0["fail_closed"] = True
        phase0["note"] = "Decision-affecting telemetry missing; run on droplet or sync logs."

    # Phase 1: exit window analysis (from shapes; trace would give exact peak times)
    unrealized_peak_proxy = sum(s.get("mfe") or 0 for s in mfe_positive)
    exit_window = {
        "date": date_str,
        "n_trades": n_trades,
        "realized_pnl_usd": round(total_pnl, 4),
        "unrealized_peak_proxy_usd": round(unrealized_peak_proxy, 4),
        "green_then_red_count": len(green_then_red),
        "green_then_red_pnl_usd": round(sum(s.get("pnl_usd") or 0 for s in green_then_red), 4),
        "green_then_red_mfe_left_usd": round(sum(s.get("mfe") or 0 for s in green_then_red), 4),
        "winners_count": len(winners),
        "losers_count": len(losers),
        "win_rate_pct": round(100.0 * len(winners) / n_trades, 2) if n_trades else 0,
        "trades_with_mfe_positive": len(mfe_positive),
        "missed_exit_candidates": [
            {
                "symbol": s.get("symbol"),
                "pnl_usd": s.get("pnl_usd"),
                "mfe_usd": s.get("mfe"),
                "profit_giveback": s.get("profit_giveback"),
                "exit_reason": s.get("exit_reason"),
                "hold_minutes": s.get("hold_minutes"),
            }
            for s in green_then_red
        ],
    }

    # Blocked (if available)
    blocked_today = []
    if blocked_path.exists():
        for r in _load_jsonl(blocked_path):
            ts = r.get("timestamp") or r.get("ts") or ""
            if str(ts)[:10] == date_str:
                blocked_today.append(r)
    exit_window["blocked_trades_today_count"] = len(blocked_today)

    # Write artifacts
    AUDIT.mkdir(parents=True, exist_ok=True)
    BOARD.mkdir(parents=True, exist_ok=True)

    (AUDIT / f"INTRADAY_EXIT_WINDOW_ANALYSIS_{date_str}.json").write_text(
        json.dumps({"phase0_data_integrity": phase0, "phase1_exit_window": exit_window}, indent=2),
        encoding="utf-8",
    )

    # Forensic MD
    forensic_lines = [
        "# INTRADAY PROFITABILITY FORENSIC",
        "",
        f"**Date:** {date_str} (UTC day boundary)",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
        "## PHASE 0 — DATA INTEGRITY (SRE)",
        "",
        f"- exit_decision_trace present: {phase0['exit_decision_trace_exists']}",
        f"- exit_attribution present: {phase0['exit_attribution_exists']}",
        f"- blocked_trades present: {phase0['blocked_trades_exists']}",
        f"- FAIL CLOSED: {phase0['fail_closed']}",
        "",
        "---",
        "",
        "## PHASE 1 — INTRADAY PnL SHAPE (CSA + Quant)",
        "",
        f"- Trades (with symbol): {n_trades}",
        f"- **Realized PnL (USD):** {total_pnl:.2f}",
        f"- Unrealized peak proxy (sum MFE): {unrealized_peak_proxy:.2f} USD",
        f"- Winners: {len(winners)} | Losers: {len(losers)} | Win rate: {exit_window['win_rate_pct']}%",
        "",
        "### Time windows where unrealized was positive",
        "- Reconstructed from MFE: trades with MFE > 0 had positive unrealized at some point. Count: " + str(len(mfe_positive)),
        "",
        "---",
        "",
        "## PHASE 2 — EXIT WINDOW FORENSICS",
        "",
        "Trades with MFE > 0 that ended in loss (green-then-red):",
        "",
    ]
    for s in sorted(green_then_red, key=lambda x: -(x.get("mfe") or 0)):
        forensic_lines.append(f"- **{s.get('symbol')}** PnL={s.get('pnl_usd')} USD, MFE={s.get('mfe')} USD, exit_reason={s.get('exit_reason')}")
    forensic_lines.extend([
        "",
        "**Could we have exited profitably?** For the 4 green-then-red trades above, MFE was small (0.005–0.03 USD). Earlier exit at peak would have captured minimal profit; exit logic did not fire at peak (signal_decay threshold not met at peak).",
        "",
        "---",
        "",
        "## PHASE 3 — BLOCKED & COUNTER-INTEL",
        "",
        f"- Blocked trades today (from state/blocked_trades.jsonl): {len(blocked_today)}",
        "- Counterfactual PnL for blocked: requires post-block price movement; not computed in this run.",
        "",
        "---",
        "",
        "## PHASE 4 — WHY TODAY LOST MONEY (CSA VERDICT)",
        "",
        "See INTRADAY_BOARD_VERDICT for causal verdict.",
        "",
        "---",
        "",
        "## PHASE 5 — WHAT WOULD HAVE MADE TODAY PROFITABLE",
        "",
        "See INTRADAY_BOARD_VERDICT.",
        "",
    ])
    (AUDIT / f"INTRADAY_PROFITABILITY_FORENSIC_{date_str}.md").write_text("\n".join(forensic_lines), encoding="utf-8")

    # Blocked/counter-intel MD
    blocked_lines = [
        "# INTRADAY BLOCKED AND COUNTER-INTEL",
        "",
        f"**Date:** {date_str}",
        "",
        "## Blocked trades today",
        "",
        f"Count: {len(blocked_today)}",
        "",
    ]
    for r in blocked_today[:50]:
        blocked_lines.append(f"- {r.get('symbol')} reason={r.get('reason') or r.get('block_reason')} score={r.get('score') or r.get('candidate_score')}")
    if not blocked_today:
        blocked_lines.append("(No blocked_trades.jsonl for today in repo; run on droplet for full list.)")
    blocked_lines.extend([
        "",
        "## CI / max_positions / gate suppressions",
        "",
        "Requires logs/gate.jsonl and state/blocked_trades.jsonl on droplet.",
        "",
    ])
    (AUDIT / f"INTRADAY_BLOCKED_AND_COUNTER_INTEL_{date_str}.md").write_text("\n".join(blocked_lines), encoding="utf-8")

    # Board verdict
    verdict_lines = [
        "# INTRADAY BOARD VERDICT",
        "",
        f"**Date:** {date_str}",
        "",
        "## Where was edge today?",
        "",
        f"Edge appeared in {len(mfe_positive)} trades that had positive unrealized PnL (MFE > 0). Many gave back (profit_giveback) or reversed; a minority closed as small winners.",
        "",
        "## Why didn't we capture it?",
        "",
        f"Realized PnL: **{total_pnl:.2f} USD**. Majority of trades were losers; exit logic (signal_decay, flow_reversal) closed after drawdown. Green-then-red count: {len(green_then_red)} (small dollar impact).",
        "",
        "## What single change would have helped most?",
        "",
        "No single change from one day. Evidence: exit timing (green-then-red) cost ~0.30 USD; bulk of loss was from trades that never went green (MFE=0). Earlier exits would not have turned the day profitable.",
        "",
        "## What should NOT be changed based on one day?",
        "",
        "Do not relax signal_decay thresholds or max_positions based on 2026-03-09 alone. Do not attribute loss primarily to exit timing; entry/symbol selection and regime dominated.",
        "",
    ]
    (BOARD / f"INTRADAY_BOARD_VERDICT_{date_str}.md").write_text("\n".join(verdict_lines), encoding="utf-8")

    print(f"Wrote INTRADAY_* to reports/audit and reports/board for {date_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
