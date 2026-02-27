#!/usr/bin/env python3
"""
Phase 6 — Profitability baseline + first-change recommendation from Phase 5 effectiveness.

Reads an effectiveness report dir; writes:
- profitability_baseline.json (aggregates, blame, top weak signals, exit giveback)
- profitability_recommendation.md + recommended_overlay (evidence-based first change)

Run after run_effectiveness_reports.py (e.g. on droplet after 30d backtest).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def load_effectiveness(effectiveness_dir: Path) -> dict:
    out = {}
    for name in ("signal_effectiveness", "exit_effectiveness", "entry_vs_exit_blame", "counterfactual_exit"):
        f = effectiveness_dir / f"{name}.json"
        if f.exists():
            try:
                out[name] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                out[name] = None
        else:
            out[name] = None
    return out


def compute_baseline(reports: dict) -> dict:
    blame = reports.get("entry_vs_exit_blame") or {}
    exit_r = reports.get("exit_effectiveness") or {}
    sig_r = reports.get("signal_effectiveness") or {}
    cf = reports.get("counterfactual_exit") or {}

    total_trades = 0
    total_pnl = 0.0
    wins = 0
    for reason, v in (exit_r if isinstance(exit_r, dict) else {}).items():
        if isinstance(v, dict) and "frequency" in v:
            total_trades += v.get("frequency", 0)
        elif isinstance(v, (int, float)):
            total_trades += int(v)
    if total_trades == 0 and sig_r:
        for sid, v in sig_r.items():
            if isinstance(v, dict):
                total_trades += v.get("trade_count", 0)
        total_trades = total_trades // max(len([k for k in sig_r if isinstance(sig_r.get(k), dict)]), 1) if sig_r else 0
    # Prefer blame total for losers; approximate wins from exit report
    losers = blame.get("total_losing_trades") or 0
    for reason, v in (exit_r if isinstance(exit_r, dict) else {}).items():
        if isinstance(v, dict) and v.get("frequency"):
            n = v["frequency"]
            avg_pnl = v.get("avg_realized_pnl") or 0
            total_pnl += n * avg_pnl
            if avg_pnl and avg_pnl > 0:
                wins += n  # rough
    if total_trades == 0 and losers:
        total_trades = losers  # lower bound

    # Worst signals by win_rate (min 5 trades)
    weak_signals = []
    if isinstance(sig_r, dict):
        for sid, v in sig_r.items():
            if not isinstance(v, dict):
                continue
            tc = v.get("trade_count", 0)
            if tc < 5:
                continue
            wr = v.get("win_rate", 0) or 0
            giveback = v.get("avg_profit_giveback")
            weak_signals.append({
                "signal_id": sid,
                "trade_count": tc,
                "win_rate": wr,
                "avg_profit_giveback": giveback,
            })
        weak_signals.sort(key=lambda x: (x["win_rate"], -(x.get("avg_profit_giveback") or 0)))
        weak_signals = weak_signals[:10]

    # Exit reasons with high giveback
    high_giveback_exits = []
    if isinstance(exit_r, dict):
        for reason, v in exit_r.items():
            if not isinstance(v, dict):
                continue
            gb = v.get("avg_profit_giveback")
            if gb is not None and v.get("frequency", 0) >= 3:
                high_giveback_exits.append({
                    "exit_reason_code": reason,
                    "frequency": v.get("frequency"),
                    "avg_profit_giveback": gb,
                    "avg_realized_pnl": v.get("avg_realized_pnl"),
                })
        high_giveback_exits.sort(key=lambda x: -(x.get("avg_profit_giveback") or 0))
        high_giveback_exits = high_giveback_exits[:10]

    return {
        "total_trades": total_trades,
        "total_losing_trades": losers,
        "total_pnl_usd": round(total_pnl, 2),
        "weak_entry_pct": blame.get("weak_entry_pct"),
        "exit_timing_pct": blame.get("exit_timing_pct"),
        "weak_signals": weak_signals,
        "high_giveback_exits": high_giveback_exits,
        "hold_longer_would_help": cf.get("hold_longer_would_help_count", 0),
        "exit_earlier_would_save": cf.get("exit_earlier_would_save_count", 0),
    }


def recommend(baseline: dict, reports: dict) -> dict:
    """Suggest first overlay and reason from baseline + reports."""
    blame = reports.get("entry_vs_exit_blame") or {}
    exit_r = reports.get("exit_effectiveness") or {}
    weak_entry_pct = baseline.get("weak_entry_pct") or 0
    exit_timing_pct = baseline.get("exit_timing_pct") or 0
    high_giveback = baseline.get("high_giveback_exits") or []
    weak_signals = baseline.get("weak_signals") or []

    # Prefer exit-side change if exit timing dominates and we have high giveback on profit-like exits
    profit_like_high_gb = [e for e in high_giveback if (e.get("avg_realized_pnl") or 0) >= 0]
    if exit_timing_pct >= weak_entry_pct and profit_like_high_gb:
        # Suggest slight increase in flow_deterioration to exit earlier when flow deteriorates
        return {
            "recommended_overlay": "config/tuning/examples/exit_flow_weight_plus_0.02.json",
            "reason": "exit_timing_dominates",
            "evidence": {
                "exit_timing_pct": exit_timing_pct,
                "weak_entry_pct": weak_entry_pct,
                "high_giveback_exit_reasons": [e.get("exit_reason_code") for e in profit_like_high_gb[:3]],
            },
            "expected_impact": "Reduce profit giveback by exiting slightly earlier when flow deteriorates.",
        }
    if weak_entry_pct > exit_timing_pct and weak_signals:
        worst = weak_signals[0]
        return {
            "recommended_overlay": None,
            "reason": "weak_entry_dominates",
            "evidence": {
                "weak_entry_pct": weak_entry_pct,
                "exit_timing_pct": exit_timing_pct,
                "worst_signal_id": worst.get("signal_id"),
                "worst_signal_win_rate": worst.get("win_rate"),
            },
            "expected_impact": "Consider raising entry threshold or adding entry_weights_v3 overlay to down-weight worst signal (manual overlay).",
        }
    if high_giveback:
        return {
            "recommended_overlay": "config/tuning/examples/exit_flow_weight_plus_0.02.json",
            "reason": "high_giveback_on_exits",
            "evidence": {"high_giveback_exits": [e.get("exit_reason_code") for e in high_giveback[:3]]},
            "expected_impact": "Try exit flow weight increase; re-run backtest compare.",
        }
    return {
        "recommended_overlay": None,
        "reason": "insufficient_evidence",
        "evidence": {"weak_entry_pct": weak_entry_pct, "exit_timing_pct": exit_timing_pct},
        "expected_impact": "Collect more trades or run with proposed overlay manually and compare.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Profitability baseline + recommendation from effectiveness dir")
    ap.add_argument("--effectiveness-dir", type=Path, required=True, help="Dir with signal/exit/blame/counterfactual JSON")
    ap.add_argument("--out", type=Path, default=None, help="Output dir (default: same as effectiveness-dir)")
    args = ap.parse_args()
    eff_dir = args.effectiveness_dir.resolve()
    if not eff_dir.exists():
        print(f"Effectiveness dir not found: {eff_dir}", file=sys.stderr)
        return 1
    out_dir = args.out.resolve() if args.out else eff_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    reports = load_effectiveness(eff_dir)
    baseline = compute_baseline(reports)
    rec = recommend(baseline, reports)

    (out_dir / "profitability_baseline.json").write_text(
        json.dumps({"baseline": baseline, "recommendation": rec}, indent=2),
        encoding="utf-8",
    )

    md_lines = [
        "# Profitability baseline & recommendation",
        "",
        "## Baseline",
        "",
        f"- Total trades (approx): {baseline.get('total_trades', 0)}",
        f"- Total losing trades: {baseline.get('total_losing_trades', 0)}",
        f"- Total PnL (from exit report): ${baseline.get('total_pnl_usd', 0)}",
        f"- Weak entry % (losers): {baseline.get('weak_entry_pct')}%",
        f"- Exit timing % (losers): {baseline.get('exit_timing_pct')}%",
        "",
        "## Recommendation",
        "",
        f"- **Reason:** {rec.get('reason', '')}",
        f"- **Suggested overlay:** {rec.get('recommended_overlay') or 'None (manual)'}",
        f"- **Expected impact:** {rec.get('expected_impact', '')}",
        "",
        "## Next steps",
        "",
    ]
    if rec.get("recommended_overlay"):
        md_lines.append(f"1. Run 30d backtest with `GOVERNED_TUNING_CONFIG={rec['recommended_overlay']}` (proposed run).")
        md_lines.append("2. Run compare_backtest_runs.py --baseline <this_run> --proposed <proposed_run>.")
        md_lines.append("3. Run regression_guards.py. If comparison improves and guards pass, lock overlay or run paper.")
    else:
        md_lines.append("1. Review entry_vs_exit_blame and signal_effectiveness; create a manual tuning overlay if needed.")
        md_lines.append("2. Re-run effectiveness after more data or after applying an overlay.")
    (out_dir / "profitability_recommendation.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote {out_dir / 'profitability_baseline.json'} and {out_dir / 'profitability_recommendation.md'}")
    print(f"Recommendation: {rec.get('reason')} -> overlay: {rec.get('recommended_overlay')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
