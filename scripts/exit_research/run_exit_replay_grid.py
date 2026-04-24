#!/usr/bin/env python3
"""
Run the full exit replay grid: all scenarios, then rank and write grid summary + ranked scenarios.
Offline only; uses existing logs. Run on droplet for production data.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_config(base: Path) -> Dict[str, Any]:
    p = base / "scripts" / "exit_research" / "exit_replay_config.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_scenarios(base: Path, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    for candidate in [
        base / (config.get("scenario_grid") or "scripts/exit_research/exit_scenarios.json"),
        base / "scripts/exit_research/exit_scenarios.json",
        Path(__file__).resolve().parent / "exit_scenarios.json",
    ]:
        if candidate.exists():
            data = json.loads(candidate.read_text(encoding="utf-8"))
            out = data.get("scenarios") or (data if isinstance(data, list) else [])
            if out:
                return out
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None, help="Repo base path")
    ap.add_argument("--start", default=None, help="Override start_date")
    ap.add_argument("--end", default=None, help="Override end_date")
    ap.add_argument("--max-scenarios", type=int, default=0, help="Max scenarios to run (0 = all)")
    args = ap.parse_args()
    base = Path(args.base) if args.base else REPO
    config = _load_config(base)
    start_date = args.start or config.get("start_date") or "2026-02-01"
    end_date = args.end or config.get("end_date") or "2026-03-02"
    out_dir = base / (config.get("out_dir") or "reports/exit_research")
    scenarios_subdir = base / (config.get("scenarios_subdir") or "reports/exit_research/scenarios")
    scenarios_subdir.mkdir(parents=True, exist_ok=True)

    scenarios = _load_scenarios(base, config)
    if not scenarios:
        print("No scenarios found", file=sys.stderr)
        return 1
    if args.max_scenarios > 0:
        scenarios = scenarios[: args.max_scenarios]

    from scripts.exit_research.run_exit_replay_scenario import run_scenario

    summaries: List[Dict[str, Any]] = []
    for i, sc in enumerate(scenarios):
        name = sc.get("name") or f"scenario_{i}"
        print(f"Running scenario: {name}", file=sys.stderr)
        try:
            summary = run_scenario(base, config, sc, start_date, end_date)
            if summary.get("error"):
                print(f"  Error: {summary['error']}", file=sys.stderr)
                continue
            summaries.append(summary)
            scenario_out = scenarios_subdir / name
            scenario_out.mkdir(parents=True, exist_ok=True)
            (scenario_out / "summary.json").write_text(
                json.dumps(summary, indent=2, default=str), encoding="utf-8"
            )
        except Exception as e:
            print(f"  Exception: {e}", file=sys.stderr)

    if not summaries:
        print("No scenario summaries produced", file=sys.stderr)
        return 1

    # Rank: primary expectancy, secondary win_rate and tail_loss, tertiary avg_hold (prefer > 15–60)
    # Exclude 0-trade scenarios from "best" so deployable policies rank first
    def rank_key(s: Dict[str, Any]) -> tuple:
        n = s.get("total_trades_in_scenario") or 0
        exp = s.get("expectancy_per_trade") or 0
        wr = s.get("win_rate") or 0
        tail = s.get("tail_loss_5pct")
        tail_val = tail if tail is not None else 0
        hold = s.get("avg_hold_minutes")
        hold_val = hold if hold is not None else 0
        return (0 if n >= 10 else 1, -exp, -wr, tail_val, -hold_val)  # n>=10 first

    ranked = sorted(summaries, key=rank_key)
    baseline = next((s for s in ranked if s.get("scenario_name") == "baseline"), ranked[0])

    grid_summary = {
        "window_start": start_date,
        "window_end": end_date,
        "total_scenarios_run": len(summaries),
        "baseline": {
            "scenario_name": baseline.get("scenario_name"),
            "total_pnl": baseline.get("total_pnl"),
            "expectancy_per_trade": baseline.get("expectancy_per_trade"),
            "win_rate": baseline.get("win_rate"),
            "avg_hold_minutes": baseline.get("avg_hold_minutes"),
            "total_trades_in_scenario": baseline.get("total_trades_in_scenario"),
        },
        "all_summaries": summaries,
        "ranked": ranked,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "exit_replay_grid_summary.json").write_text(
        json.dumps(grid_summary, indent=2, default=str), encoding="utf-8"
    )

    # Ranked scenarios output
    (out_dir / "exit_replay_ranked_scenarios.json").write_text(
        json.dumps({"ranked": ranked, "baseline": baseline}, indent=2, default=str), encoding="utf-8"
    )

    # MD report
    md_lines = [
        "# Exit Replay Grid Summary",
        "",
        f"**Window:** {start_date} to {end_date}.",
        f"**Scenarios run:** {len(summaries)}.",
        "",
        "## Baseline (current live-like)",
        "",
        f"- Total PnL: ${baseline.get('total_pnl', 0):.2f}",
        f"- Expectancy/trade: {baseline.get('expectancy_per_trade', 0):.4f}",
        f"- Win rate: {baseline.get('win_rate', 0):.1%}",
        f"- Avg hold (min): " + (f"{baseline.get('avg_hold_minutes'):.1f}" if baseline.get("avg_hold_minutes") is not None else "N/A"),
        f"- Trades in scenario: {baseline.get('total_trades_in_scenario', 0)}",
        "",
        "## Top 5 scenarios (by expectancy, then win rate, then hold)",
        "",
    ]
    for i, s in enumerate(ranked[:5], 1):
        md_lines.append(f"### {i}. {s.get('scenario_name', '')}")
        md_lines.append("")
        md_lines.append(f"- **Params:** min_hold={s.get('scenario_params', {}).get('min_hold_minutes')} min, decay_threshold={s.get('scenario_params', {}).get('signal_decay_threshold')}, remove_components={s.get('scenario_params', {}).get('remove_components')}")
        md_lines.append(f"- Total PnL: ${s.get('total_pnl', 0):.2f} | Expectancy: {s.get('expectancy_per_trade', 0):.4f} | Win rate: {s.get('win_rate', 0):.1%} | Avg hold: {s.get('avg_hold_minutes')} min | Trades: {s.get('total_trades_in_scenario', 0)}")
        md_lines.append("")
    md_lines.extend([
        "## All scenarios (ranked)",
        "",
        "| Rank | Scenario | PnL | Expectancy | Win rate | Avg hold | Trades |",
        "|------|----------|-----|------------|----------|----------|--------|",
    ])
    for i, s in enumerate(ranked, 1):
        hold = s.get("avg_hold_minutes")
        hold_s = f"{hold:.1f}" if hold is not None else "N/A"
        md_lines.append(f"| {i} | {s.get('scenario_name', '')} | ${s.get('total_pnl', 0):.2f} | {s.get('expectancy_per_trade', 0):.4f} | {s.get('win_rate', 0):.1%} | {hold_s} | {s.get('total_trades_in_scenario', 0)} |")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("Per-regime and per-component insights: see `scenarios/<name>/summary.json`.")
    (out_dir / "exit_replay_grid_summary.md").write_text("\n".join(md_lines), encoding="utf-8")
    (out_dir / "exit_replay_ranked_scenarios.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Grid summary: {out_dir / 'exit_replay_grid_summary.json'}")
    print(f"Ranked: {out_dir / 'exit_replay_ranked_scenarios.json'}")
    print(f"MD: {out_dir / 'exit_replay_grid_summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
