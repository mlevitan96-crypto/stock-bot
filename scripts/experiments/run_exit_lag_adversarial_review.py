#!/usr/bin/env python3
"""
Adversarial review of exit-lag multi-day evidence. Run after multi-day validation.
Reads EXIT_LAG_MULTI_DAY_RESULTS.json, CSA_EXIT_LAG_MULTI_DAY_VERDICT.json, REGIME_BREAKDOWN.
Challenges: overfitting, regime bias, sample size, tail risk, cherry-picking.
SRE/CSA: no live changes; review only. Output: EXIT_LAG_ADVERSARIAL_REVIEW.md
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
    ap = argparse.ArgumentParser(description="Adversarial review of exit-lag multi-day evidence")
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    exp_dir = base / "reports" / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)

    results_path = exp_dir / "EXIT_LAG_MULTI_DAY_RESULTS.json"
    audit_dir = base / "reports" / "audit"
    verdict_path = audit_dir / "CSA_EXIT_LAG_MULTI_DAY_VERDICT.json"
    if not results_path.exists():
        print("BLOCKER: EXIT_LAG_MULTI_DAY_RESULTS.json not found. Run multi-day validation first.", file=sys.stderr)
        return 1

    data = json.loads(results_path.read_text(encoding="utf-8"))
    verdict = {}
    if verdict_path.exists():
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))

    n_days = data.get("date_range", {}).get("n_days", 0)
    best = verdict.get("best_variant") or (data.get("variants") and max(data["variants"].keys(), key=lambda v: data["variants"][v].get("cumulative_delta_vs_current_usd", 0)))
    best_delta = data.get("variants", {}).get(best, {}).get("cumulative_delta_vs_current_usd", 0)
    best_pct = data.get("variants", {}).get(best, {}).get("pct_days_improved", 0)

    challenges = []
    mitigations = []

    if n_days < 5:
        challenges.append("**Sample size:** Only {} days. Improvement could be noise or single-regime luck.".format(n_days))
        mitigations.append("Backfill more days (5–10) and re-run multi-day validation before any promotion.")
    else:
        mitigations.append("Sample size ({} days) is at least 5; still prefer 10+ for regime diversity.".format(n_days))

    if n_days == 1 and best_delta > 0:
        challenges.append("**Overfitting risk:** One day only. Best variant may not generalize.")
        mitigations.append("Do not promote on one day. Require multi-day consistency.")

    if best and data.get("variants", {}).get(best, {}).get("worst_day_delta_usd", 0) < -20:
        challenges.append("**Tail risk:** Best variant has a worst-day delta < -$20; could hurt in bad days.")
        mitigations.append("Monitor worst-day delta; consider conditional promotion only when drawdown SLO is met.")

    challenges.append("**Regime bias:** If most days are red (or green), improvement may be regime-specific.")
    mitigations.append("Review EXIT_LAG_REGIME_BREAKDOWN.md; prefer variants that improve in both green and red.")

    challenges.append("**Cherry-picking:** Backfill uses available trace/attribution; missing days may differ.")
    mitigations.append("SRE: document which dates were skipped (data missing) in backfill manifest.")

    verdict_promote = verdict.get("verdict") == "PROMOTE_TO_LIMITED_PAPER_AB"
    if verdict_promote and n_days < 5:
        challenges.append("**CSA verdict vs evidence:** Verdict is PROMOTE but n_days < 5; possible logic error.")
        mitigations.append("CSA: re-check promotion rule (n_days >= 5 required).")

    lines = [
        "# Exit-Lag Adversarial Review",
        "",
        "**Role:** Adversarial Reviewer. Challenge overfitting, regime bias, and hidden risk.",
        "",
        "## Challenges",
        "",
    ]
    for c in challenges:
        lines.append("- " + c)
    lines.extend([
        "",
        "## Mitigations / Recommendations",
        "",
    ])
    for m in mitigations:
        lines.append("- " + m)
    lines.extend([
        "",
        "## Summary",
        "",
        "Verdict remains **CONTINUE_SHADOW** until sample size and regime diversity are sufficient and no adversarial challenge blocks promotion. SRE and CSA should incorporate this review before any PROMOTE decision.",
        "",
    ])

    out_path = exp_dir / "EXIT_LAG_ADVERSARIAL_REVIEW.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
