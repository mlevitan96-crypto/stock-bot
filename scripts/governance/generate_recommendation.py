#!/usr/bin/env python3
"""
Phase 7 — Generate profitability_recommendation.md with:
- Top 5 harmful entry signals (by win_rate + MAE + pnl)
- Top 3 exit reasons with worst giveback
- Suggested single overlay candidates (not applied automatically)
- Explicit falsification criteria suggestions

Can be used standalone or after profitability_baseline_and_recommend.py (extends same dir).
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate profitability_recommendation.md with top harmful signals, exits, overlay candidates, falsification criteria")
    ap.add_argument("--effectiveness-dir", type=Path, default=None, help="Dir with signal/exit/blame/counterfactual JSON")
    ap.add_argument("--backtest-dir", type=Path, default=None, help="Backtest dir (effectiveness-dir = <backtest-dir>/effectiveness, out = <backtest-dir>)")
    ap.add_argument("--out", type=Path, default=None, help="Output dir (default: same as effectiveness-dir or backtest-dir)")
    args = ap.parse_args()
    if args.backtest_dir:
        args.backtest_dir = args.backtest_dir.resolve()
        eff_dir = args.backtest_dir / "effectiveness"
        out_dir = args.out.resolve() if args.out else args.backtest_dir
    elif args.effectiveness_dir:
        eff_dir = args.effectiveness_dir.resolve()
        out_arg = args.out.resolve() if args.out else None
        if out_arg and out_arg.suffix == ".json":
            out_dir = out_arg.parent
        else:
            out_dir = out_arg or eff_dir
    else:
        print("Either --effectiveness-dir or --backtest-dir is required", file=sys.stderr)
        return 1
    if not eff_dir.exists():
        print(f"Effectiveness dir not found: {eff_dir}", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    reports = load_effectiveness(eff_dir)
    sig = reports.get("signal_effectiveness") or {}
    exit_r = reports.get("exit_effectiveness") or {}
    blame = reports.get("entry_vs_exit_blame") or {}

    # Top 5 harmful entry signals (low win_rate, high MAE or negative avg_pnl)
    harmful = []
    for sid, v in (sig if isinstance(sig, dict) else {}).items():
        if not isinstance(v, dict) or v.get("trade_count", 0) < 3:
            continue
        wr = v.get("win_rate")
        pnl = v.get("avg_pnl")
        mae = v.get("avg_MAE")
        giveback = v.get("avg_profit_giveback")
        harmful.append({
            "signal_id": sid,
            "trade_count": v.get("trade_count"),
            "win_rate": wr,
            "avg_pnl": pnl,
            "avg_MAE": mae,
            "avg_profit_giveback": giveback,
        })
    harmful.sort(key=lambda x: (x.get("win_rate") or 1, -(x.get("avg_MAE") or 0), (x.get("avg_pnl") or 0)))
    top5_harmful = harmful[:5]

    # Top 3 exit reasons with worst giveback (min 3 trades)
    worst_exits = []
    for reason, v in (exit_r if isinstance(exit_r, dict) else {}).items():
        if not isinstance(v, dict) or v.get("frequency", 0) < 3:
            continue
        gb = v.get("avg_profit_giveback")
        if gb is None:
            continue
        worst_exits.append({
            "exit_reason_code": reason,
            "frequency": v.get("frequency"),
            "avg_profit_giveback": gb,
            "avg_realized_pnl": v.get("avg_realized_pnl"),
        })
    worst_exits.sort(key=lambda x: -(x.get("avg_profit_giveback") or 0))
    top3_exits = worst_exits[:3]

    # Overlay candidates (suggestions only)
    overlay_candidates = []
    if blame.get("exit_timing_pct", 0) >= (blame.get("weak_entry_pct") or 0) and top3_exits:
        overlay_candidates.append({
            "lever": "exit_weights.flow_deterioration",
            "suggestion": "Increase slightly (e.g. +0.02) to exit earlier when flow deteriorates",
            "evidence": "exit_timing_pct >= weak_entry_pct; high giveback on profit exits",
        })
    if blame.get("weak_entry_pct", 0) > (blame.get("exit_timing_pct") or 0) and top5_harmful:
        overlay_candidates.append({
            "lever": "entry_weights_v3 or entry_thresholds",
            "suggestion": "Down-weight worst signal or raise entry threshold",
            "evidence": f"weak_entry_pct > exit_timing_pct; worst signal: {top5_harmful[0].get('signal_id')}",
        })

    # Falsification criteria suggestions
    falsification = [
        "Win rate drops by more than 2% over next 7 days paper vs baseline.",
        "avg_profit_giveback increases by more than 0.05.",
        "Regression guards fail (attribution invariant or exit quality).",
    ]

    lines = [
        "# Profitability recommendation (generated)",
        "",
        "**Suggestion only — no auto-apply.**",
        "",
        "## Top 5 harmful entry signals (by win_rate, MAE, pnl)",
        "",
    ]
    for i, h in enumerate(top5_harmful, 1):
        lines.append(f"{i}. **{h.get('signal_id', '—')}** — trades: {h.get('trade_count')}, win_rate: {h.get('win_rate')}, avg_pnl: {h.get('avg_pnl')}, avg_MAE: {h.get('avg_MAE')}, giveback: {h.get('avg_profit_giveback')}")
    lines.extend([
        "",
        "## Top 3 exit reasons (worst giveback)",
        "",
    ])
    for i, e in enumerate(top3_exits, 1):
        lines.append(f"{i}. **{e.get('exit_reason_code', '—')}** — frequency: {e.get('frequency')}, avg_profit_giveback: {e.get('avg_profit_giveback')}, avg_pnl: {e.get('avg_realized_pnl')}")
    lines.extend([
        "",
        "## Suggested overlay candidates (do not apply automatically)",
        "",
    ])
    for c in overlay_candidates:
        lines.append(f"- **{c.get('lever')}**: {c.get('suggestion')}")
        lines.append(f"  Evidence: {c.get('evidence')}")
    if not overlay_candidates:
        lines.append("- No automatic suggestion. Review blame and effectiveness manually.")
    lines.extend([
        "",
        "## Falsification criteria (suggested)",
        "",
    ])
    for f in falsification:
        lines.append(f"- {f}")
    lines.append("")

    (out_dir / "profitability_recommendation.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_dir / 'profitability_recommendation.md'}")

    # next_lever for autopilot: entry if weak_entry > exit_timing, else exit
    weak_pct = blame.get("weak_entry_pct") or 0
    timing_pct = blame.get("exit_timing_pct") or 0
    next_lever = "entry" if weak_pct > timing_pct else "exit"
    recommendation = {
        "next_lever": next_lever,
        "weak_entry_pct": weak_pct,
        "exit_timing_pct": timing_pct,
        "total_losing_trades": blame.get("total_losing_trades"),
        "overlay_candidates": overlay_candidates,
        "top5_harmful": top5_harmful,
        "top3_exits": top3_exits,
    }
    rec_path = args.out if args.out and str(args.out).endswith(".json") else (out_dir / "recommendation.json")
    rec_path = Path(rec_path)
    rec_path.parent.mkdir(parents=True, exist_ok=True)
    rec_path.write_text(json.dumps(recommendation, indent=2), encoding="utf-8")
    print(f"Wrote {rec_path} (next_lever={next_lever})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
