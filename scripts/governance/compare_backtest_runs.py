#!/usr/bin/env python3
"""
Phase 6 — Before/after backtest comparison.

Compares two effectiveness report directories (or two backtest output dirs).
Produces comparison artifact: PnL, win rate, MFE/MAE, profit_giveback, entry vs exit blame.

Usage:
  python scripts/governance/compare_backtest_runs.py --baseline reports/effectiveness_baseline --proposed reports/effectiveness_proposed [--out PATH]
  python scripts/governance/compare_backtest_runs.py --baseline backtests/30d_baseline --proposed backtests/30d_proposed

If dir is a backtest dir (has backtest_exits.jsonl), runs effectiveness report on it first, then compares.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def load_report_dir(path: Path) -> dict:
    """Load signal_effectiveness, exit_effectiveness, entry_vs_exit_blame, counterfactual from a dir."""
    out = {}
    for name in ("signal_effectiveness", "exit_effectiveness", "entry_vs_exit_blame", "counterfactual_exit"):
        f = path / f"{name}.json"
        if f.exists():
            try:
                out[name] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                out[name] = None
        else:
            out[name] = None
    return out


def aggregate_from_exits(exits_path: Path) -> dict:
    """Compute simple aggregates from backtest_exits.jsonl for comparison."""
    if not exits_path.exists():
        return {}
    total_pnl = 0.0
    wins = 0
    givebacks = []
    n = 0
    for line in exits_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            pnl = float(r.get("pnl") or 0)
            total_pnl += pnl
            if pnl > 0:
                wins += 1
            gb = r.get("exit_quality_metrics", {}).get("profit_giveback")
            if gb is not None:
                givebacks.append(float(gb))
            n += 1
        except Exception:
            continue
    return {
        "total_trades": n,
        "total_pnl_usd": round(total_pnl, 2),
        "win_rate": round(wins / n, 4) if n else 0,
        "avg_profit_giveback": round(sum(givebacks) / len(givebacks), 4) if givebacks else None,
    }


def ensure_effectiveness_reports(backtest_dir: Path) -> Path:
    """If dir has backtest_exits.jsonl, run effectiveness report into a subdir and return that path."""
    if (backtest_dir / "backtest_exits.jsonl").exists():
        out_sub = backtest_dir / "effectiveness"
        out_sub.mkdir(parents=True, exist_ok=True)
        if not (out_sub / "exit_effectiveness.json").exists():
            try:
                from scripts.analysis.run_effectiveness_reports import (
                    build_signal_effectiveness,
                    build_exit_effectiveness,
                    build_entry_vs_exit_blame,
                    build_counterfactual_exit,
                    write_md_summary,
                )
                from scripts.analysis.attribution_loader import load_from_backtest_dir
                joined = load_from_backtest_dir(backtest_dir)
                if joined:
                    sig = build_signal_effectiveness(joined)
                    exit_r = build_exit_effectiveness(joined)
                    blame = build_entry_vs_exit_blame(joined)
                    cf = build_counterfactual_exit(joined)
                    (out_sub / "signal_effectiveness.json").write_text(json.dumps(sig, indent=2))
                    (out_sub / "exit_effectiveness.json").write_text(json.dumps(exit_r, indent=2))
                    (out_sub / "entry_vs_exit_blame.json").write_text(json.dumps(blame, indent=2))
                    (out_sub / "counterfactual_exit.json").write_text(json.dumps(cf, indent=2))
                    write_md_summary(out_sub, sig, exit_r, blame, cf, len(joined))
            except Exception:  # noqa: BLE001
                pass  # leave empty; comparison will use aggregates from backtest_exits.jsonl
        return out_sub
    return backtest_dir


def compare(baseline_dir: Path, proposed_dir: Path) -> dict:
    """Produce comparison artifact between baseline and proposed."""
    base = ensure_effectiveness_reports(baseline_dir)
    prop = ensure_effectiveness_reports(proposed_dir)

    base_reports = load_report_dir(base)
    prop_reports = load_report_dir(prop)

    # Try to get aggregates from backtest_exits if present
    base_agg = aggregate_from_exits(baseline_dir / "backtest_exits.jsonl") or aggregate_from_exits(base.parent / "backtest_exits.jsonl")
    prop_agg = aggregate_from_exits(proposed_dir / "backtest_exits.jsonl") or aggregate_from_exits(prop.parent / "backtest_exits.jsonl")

    comparison = {
        "baseline_dir": str(baseline_dir),
        "proposed_dir": str(proposed_dir),
        "aggregates": {
            "baseline": base_agg,
            "proposed": prop_agg,
        },
        "deltas": {},
        "entry_vs_exit_blame": {
            "baseline": base_reports.get("entry_vs_exit_blame"),
            "proposed": prop_reports.get("entry_vs_exit_blame"),
        },
    }

    if base_agg and prop_agg:
        comparison["deltas"] = {
            "total_pnl_usd": round((prop_agg.get("total_pnl_usd") or 0) - (base_agg.get("total_pnl_usd") or 0), 2),
            "win_rate": round((prop_agg.get("win_rate") or 0) - (base_agg.get("win_rate") or 0), 4),
            "avg_profit_giveback": None,
        }
        if prop_agg.get("avg_profit_giveback") is not None and base_agg.get("avg_profit_giveback") is not None:
            comparison["deltas"]["avg_profit_giveback"] = round(
                (prop_agg.get("avg_profit_giveback") or 0) - (base_agg.get("avg_profit_giveback") or 0), 4
            )

    return comparison


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare baseline vs proposed backtest/effectiveness runs")
    ap.add_argument("--baseline", type=Path, required=True, help="Baseline report dir or backtest dir")
    ap.add_argument("--proposed", type=Path, required=True, help="Proposed report dir or backtest dir")
    ap.add_argument("--out", type=Path, default=None, help="Output dir for comparison.json and comparison.md")
    args = ap.parse_args()
    base = args.baseline.resolve()
    prop = args.proposed.resolve()
    if not base.exists():
        print(f"Baseline dir not found: {base}", file=sys.stderr)
        return 1
    if not prop.exists():
        print(f"Proposed dir not found: {prop}", file=sys.stderr)
        return 1

    result = compare(base, prop)
    out_dir = args.out
    if out_dir is None:
        out_dir = REPO / "reports" / "governance_comparison"
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "comparison.json").write_text(json.dumps(result, indent=2))
    md_lines = [
        "# Backtest / effectiveness comparison",
        "",
        f"- **Baseline:** {result['baseline_dir']}",
        f"- **Proposed:** {result['proposed_dir']}",
        "",
        "## Aggregates",
        "",
        "| Metric | Baseline | Proposed | Delta |",
        "|--------|----------|----------|-------|",
    ]
    agg_b = result.get("aggregates", {}).get("baseline", {})
    agg_p = result.get("aggregates", {}).get("proposed", {})
    deltas = result.get("deltas", {})
    for key in ("total_pnl_usd", "win_rate", "avg_profit_giveback", "total_trades"):
        vb = agg_b.get(key)
        vp = agg_p.get(key)
        d = deltas.get(key)
        md_lines.append(f"| {key} | {vb} | {vp} | {d} |")
    md_lines.extend(["", "## Entry vs exit blame (losers)", ""])
    blame_b = result.get("entry_vs_exit_blame", {}).get("baseline")
    blame_p = result.get("entry_vs_exit_blame", {}).get("proposed")
    if blame_b:
        md_lines.append(f"- Baseline: weak_entry_pct={blame_b.get('weak_entry_pct')}, exit_timing_pct={blame_b.get('exit_timing_pct')}")
    if blame_p:
        md_lines.append(f"- Proposed: weak_entry_pct={blame_p.get('weak_entry_pct')}, exit_timing_pct={blame_p.get('exit_timing_pct')}")
    (out_dir / "comparison.md").write_text("\n".join(md_lines))
    print(f"Wrote {out_dir / 'comparison.json'} and {out_dir / 'comparison.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
