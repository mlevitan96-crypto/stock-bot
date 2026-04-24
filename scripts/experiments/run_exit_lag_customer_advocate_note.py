#!/usr/bin/env python3
"""
Customer advocate view on exit-lag evidence. Run after multi-day validation.
Reads EXIT_LAG_MULTI_DAY_RESULTS.json and CSA verdict. Answers: would customer PnL improve?
Whipsaw risk? Alignment with customer (profit capture) vs internal metrics?
SRE/CSA: no live changes. Output: EXIT_LAG_CUSTOMER_ADVOCATE_NOTE.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXPERIMENTS = REPO / "reports" / "experiments"
AUDIT = REPO / "reports" / "audit"


def main() -> int:
    ap = argparse.ArgumentParser(description="Customer advocate note on exit-lag multi-day evidence")
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    exp_dir = base / "reports" / "experiments"
    audit_dir = base / "reports" / "audit"
    exp_dir.mkdir(parents=True, exist_ok=True)

    results_path = exp_dir / "EXIT_LAG_MULTI_DAY_RESULTS.json"
    verdict_path = audit_dir / "CSA_EXIT_LAG_MULTI_DAY_VERDICT.json"
    if not results_path.exists():
        print("BLOCKER: EXIT_LAG_MULTI_DAY_RESULTS.json not found.", file=sys.stderr)
        return 1

    data = json.loads(results_path.read_text(encoding="utf-8"))
    verdict = {}
    if verdict_path.exists():
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))

    n_days = data.get("date_range", {}).get("n_days", 0)
    variants = data.get("variants", {})
    best = verdict.get("best_variant") or (max(variants.keys(), key=lambda v: variants[v].get("cumulative_delta_vs_current_usd", 0)) if variants else None)
    if not best:
        best = "A_first_eligibility"
    best_data = variants.get(best, {})
    delta_usd = best_data.get("cumulative_delta_vs_current_usd", 0)
    pct_improved = best_data.get("pct_days_improved", 0)
    worst_day_delta = best_data.get("worst_day_delta_usd", 0)
    dd_delta_avg = best_data.get("max_drawdown_delta_avg_usd", 0)

    lines = [
        "# Exit-Lag Customer Advocate Note",
        "",
        "**Role:** Customer / profit advocate. Focus: would the customer (portfolio PnL) benefit?",
        "",
        "## Would customer PnL improve?",
        "",
    ]
    if delta_usd > 0:
        lines.append("Yes, in shadow. Best variant (**{}**) would have improved cumulative realized PnL by **${:.2f}** over {} days ({}% of days improved).".format(best, delta_usd, n_days, pct_improved))
    else:
        lines.append("Shadow evidence does not show improvement over current (best delta ${:.2f}). Do not promote for customer benefit.".format(delta_usd))
    lines.extend([
        "",
        "## Whipsaw / tail risk for customer",
        "",
    ])
    if worst_day_delta < -10:
        lines.append("Worst-day delta is **${:.2f}** USD; in a bad day the variant could have hurt the customer more than current. Monitor before promotion.".format(worst_day_delta))
    else:
        lines.append("Worst-day delta **{:.2f}** USD; no single-day blow-up observed in shadow.".format(worst_day_delta))
    if dd_delta_avg > 5:
        lines.append("Average drawdown delta is **{:.2f}** USD (variant worse); customer could see deeper drawdowns.".format(dd_delta_avg))
    else:
        lines.append("Drawdown impact (avg delta {:.2f} USD) is acceptable.".format(dd_delta_avg))
    lines.extend([
        "",
        "## Alignment: customer outcome vs internal metrics",
        "",
        "Exit-on-first-eligibility (and variants) aim to **capture profit earlier** and reduce giveback. That aligns with customer outcome (higher realized PnL) provided we do not increase whipsaw or tail loss. Customer advocate supports promotion only when multi-day evidence shows consistent improvement and no material tail/drawdown degradation.",
        "",
        "## Recommendation",
        "",
    ])
    if delta_usd > 20 and pct_improved >= 60 and worst_day_delta > -15:
        lines.append("Evidence supports **limited paper A/B** from a customer-outcome perspective, subject to CSA verdict and SRE guardrails.")
    else:
        lines.append("**Continue shadow** until evidence is stronger (higher delta, more days improved, acceptable worst-day).")
    lines.append("")

    out_path = exp_dir / "EXIT_LAG_CUSTOMER_ADVOCATE_NOTE.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
