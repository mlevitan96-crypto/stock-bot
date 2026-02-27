#!/usr/bin/env python3
"""
Multi-persona board review of exit grid search results.
Reads grid_results.json, writes board_review/ and GRID_RECOMMENDATION.json with top configs and rationale.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid_results", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--top_n", type=int, default=5)
    args = ap.parse_args()
    grid_path = Path(args.grid_results)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not grid_path.exists():
        rec = {
            "decision": "NO_GRID",
            "rationale": "Grid results file missing",
            "top_configs": [],
            "recommended_config": None,
        }
        (out_dir / "GRID_RECOMMENDATION.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return 1

    data = json.loads(grid_path.read_text(encoding="utf-8"))
    top_configs = data.get("top_configs", [])[: args.top_n]
    n_total = data.get("n_exits_total", 0)
    n_with_bars = data.get("n_exits_with_bars", 0)
    coverage = data.get("coverage_pct", 0)
    best = top_configs[0] if top_configs else {}

    # Prosecutor: require coverage and improvement
    prosecutor = [
        "# Prosecutor (Exit Grid)",
        "",
        "## Claim",
        "Grid search is only valid if bar coverage is sufficient and top config beats baseline (actual realized).",
        "",
        "## Evidence",
        f"- Exits total: {n_total}, with bars: {n_with_bars} ({coverage}% coverage)",
        f"- Best simulated total PnL%: {best.get('total_pnl_pct', 'N/A')}",
        "",
        "## Verdict",
        "**Adversarial:** If coverage < 50%, treat recommendations as suggestive only. Require paper/shadow validation before live.",
        "",
    ]
    (out_dir / "prosecutor_output.md").write_text("\n".join(prosecutor), encoding="utf-8")

    # Defender: grid is evidence for tuning
    defender = [
        "# Defender (Exit Grid)",
        "",
        "## Pushback",
        "Bar-based simulation is the right way to compare exit rules apples-to-apples. Top configs are candidates for apply_exit_signal_tuning.",
        "",
        "## Verdict",
        "**Defender:** Accept top configs as tuning inputs; promote to config/exit_candidate_signals.tuned.json and re-run historical review.",
        "",
    ]
    (out_dir / "defender_output.md").write_text("\n".join(defender), encoding="utf-8")

    # Quant: data quality
    quant = [
        "# Quant (Exit Grid)",
        "",
        "## Data",
        f"- Coverage: {coverage}% of exits had bars for simulation.",
        f"- Param sets evaluated: {data.get('n_param_sets', 0)}",
        "- Top 5 configs (trailing_stop_pct, profit_target_pct, stop_loss_pct, time_stop_minutes) in grid_results.json.",
        "",
        "## Verdict",
        "**Quant:** Proceed to recommendation; if coverage is low, recommend fetching more bars and re-running.",
        "",
    ]
    (out_dir / "quant_output.md").write_text("\n".join(quant), encoding="utf-8")

    # SRE: runnable next step
    sre = [
        "# SRE (Exit Grid)",
        "",
        "## Next step",
        "Apply top config to config/exit_candidate_signals.tuned.json and run CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh for validation.",
        "",
        "## Verdict",
        "**SRE:** No infra change; config-only tuning. Safe to iterate.",
        "",
    ]
    (out_dir / "sre_output.md").write_text("\n".join(sre), encoding="utf-8")

    # Board synthesis
    recommended = best if top_configs else None
    decision = "PROMOTE_TOP_CONFIG" if (top_configs and coverage >= 20) else "TUNE_OR_GET_MORE_BARS"
    rationale = (
        f"Top config: trailing_stop_pct={recommended.get('trailing_stop_pct')}, "
        f"profit_target_pct={recommended.get('profit_target_pct')}, "
        f"stop_loss_pct={recommended.get('stop_loss_pct')}, "
        f"time_stop_minutes={recommended.get('time_stop_minutes')}; "
        f"simulated total PnL%={recommended.get('total_pnl_pct')} over {recommended.get('n_simulated')} exits."
        if recommended
        else "No config to recommend."
    )
    rec = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "rationale": rationale,
        "coverage_pct": coverage,
        "n_exits_with_bars": n_with_bars,
        "n_exits_total": n_total,
        "top_configs": top_configs,
        "recommended_config": recommended,
    }
    (out_dir / "GRID_RECOMMENDATION.json").write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")

    board_md = [
        "# Board (Exit Grid)",
        "",
        "## Synthesis",
        "Multi-persona review complete. Best exit-rule config from grid search.",
        "",
        "## Recommendation",
        f"- **Decision:** {decision}",
        f"- **Rationale:** {rationale}",
        "",
        "## Next",
        "- If PROMOTE_TOP_CONFIG: write recommended_config to config/exit_candidate_signals.tuned.json and run tune+rerun.",
        "- If TUNE_OR_GET_MORE_BARS: increase bar coverage or expand grid and re-run.",
        "",
    ]
    (out_dir / "board_output.md").write_text("\n".join(board_md), encoding="utf-8")
    print(f"Board review -> {out_dir}, decision={decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
