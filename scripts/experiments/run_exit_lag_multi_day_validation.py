#!/usr/bin/env python3
"""
Exit-lag multi-day validation. Run ON DROPLET (or locally with artifacts).
Aggregates EXIT_LAG_SHADOW_RESULTS_<date>.json across last N days.
Produces: EXIT_LAG_MULTI_DAY_RESULTS.json, REGIME_BREAKDOWN.md, ROBUSTNESS_SCORECARD.md,
          CSA_EXIT_LAG_MULTI_DAY_VERDICT.json, EXIT_LAG_MULTI_DAY_BOARD_PACKET.md.
PAPER ONLY. No live exit logic or config changes.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXPERIMENTS = REPO / "reports" / "experiments"
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"

VARIANT_KEYS = ["A_first_eligibility", "B_persist_2m", "B_persist_5m", "B_persist_10m", "C_partial_50", "D_flow_reversal_only"]


def _discover_days(experiments_dir: Path, n: int) -> list[str]:
    """Return last N dates (YYYY-MM-DD) that have EXIT_LAG_SHADOW_RESULTS_<date>.json, sorted desc."""
    pattern = re.compile(r"EXIT_LAG_SHADOW_RESULTS_(\d{4}-\d{2}-\d{2})\.json$")
    dates = []
    for f in experiments_dir.glob("EXIT_LAG_SHADOW_RESULTS_*.json"):
        m = pattern.match(f.name)
        if m:
            dates.append(m.group(1))
    dates = sorted(set(dates), reverse=True)
    return dates[:n]


def main() -> int:
    ap = argparse.ArgumentParser(description="Exit-lag multi-day validation (paper only)")
    ap.add_argument("--days", type=int, default=10, help="Max number of trading days to aggregate")
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    exp_dir = base / "reports" / "experiments"
    audit_dir = base / "reports" / "audit"
    board_dir = base / "reports" / "board"
    exp_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    board_dir.mkdir(parents=True, exist_ok=True)

    dates = _discover_days(exp_dir, args.days)
    if not dates:
        print("BLOCKER: No EXIT_LAG_SHADOW_RESULTS_<date>.json found. Run single-day replay for at least one day.", file=sys.stderr)
        return 1
    if len(dates) < 2:
        print("WARNING: Only one day of data; robustness metrics are limited.", file=sys.stderr)

    # Load per-day results
    daily = []
    for d in dates:
        path = exp_dir / f"EXIT_LAG_SHADOW_RESULTS_{d}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            daily.append({"date": d, "data": data})
        except Exception as e:
            print(f"Skip {d}: {e}", file=sys.stderr)
            continue

    if not daily:
        print("BLOCKER: No valid daily results loaded.", file=sys.stderr)
        return 1

    # Phase 2: Multi-day aggregation per variant
    current_totals = []
    variant_daily_pnl = {v: [] for v in VARIANT_KEYS}
    variant_daily_dd = {v: [] for v in VARIANT_KEYS}
    variant_daily_tail = {v: [] for v in VARIANT_KEYS}
    daily_trade_count = []
    daily_current_pnl = []

    for rec in daily:
        d = rec["date"]
        data = rec["data"]
        variants = data.get("variants", {})
        cur = variants.get("current", {})
        cur_pnl = cur.get("total_realized_pnl_usd", 0)
        cur_dd = cur.get("max_drawdown_usd", 0)
        cur_tail = cur.get("tail_loss_sum", 0)
        trade_count = cur.get("trade_count", 0)
        current_totals.append(cur_pnl)
        daily_current_pnl.append(cur_pnl)
        daily_trade_count.append(trade_count)

        for v in VARIANT_KEYS:
            vdata = variants.get(v, {})
            variant_daily_pnl[v].append(vdata.get("total_realized_pnl_usd", cur_pnl))
            variant_daily_dd[v].append(vdata.get("max_drawdown_usd", cur_dd))
            variant_daily_tail[v].append(vdata.get("tail_loss_sum", cur_tail))

    n_days = len(daily)
    cumulative_current = sum(current_totals)
    cur_dds = [rec["data"].get("variants", {}).get("current", {}).get("max_drawdown_usd", 0) for rec in daily]
    cur_tails = [rec["data"].get("variants", {}).get("current", {}).get("tail_loss_sum", 0) for rec in daily]

    multi = {
        "date_range": {"first": daily[-1]["date"], "last": daily[0]["date"], "n_days": n_days},
        "variants": {},
    }

    for v in VARIANT_KEYS:
        pnls = variant_daily_pnl[v]
        dds = variant_daily_dd[v]
        tails = variant_daily_tail[v]
        cumulative_v = sum(pnls)
        delta_vs_current = cumulative_v - cumulative_current
        daily_deltas = [pnls[i] - current_totals[i] for i in range(n_days)]
        improved_days = sum(1 for d in daily_deltas if d > 0)
        mean_improvement = sum(daily_deltas) / n_days if n_days else 0
        sorted_deltas = sorted(daily_deltas)
        median_improvement = sorted_deltas[n_days // 2] if n_days else 0
        worst_day_delta = min(daily_deltas) if daily_deltas else 0
        dd_deltas = [dds[i] - cur_dds[i] for i in range(n_days)]
        tail_deltas = [tails[i] - cur_tails[i] for i in range(n_days)]
        multi["variants"][v] = {
            "cumulative_pnl_usd": round(cumulative_v, 4),
            "cumulative_delta_vs_current_usd": round(delta_vs_current, 4),
            "mean_daily_improvement_usd": round(mean_improvement, 4),
            "median_daily_improvement_usd": round(median_improvement, 4),
            "pct_days_improved": round(100.0 * improved_days / n_days, 1) if n_days else 0,
            "worst_day_delta_usd": round(worst_day_delta, 4),
            "max_drawdown_delta_avg_usd": round(sum(dd_deltas) / n_days, 4) if n_days else 0,
            "tail_loss_delta_avg_usd": round(sum(tail_deltas) / n_days, 4) if n_days else 0,
        }

    (exp_dir / "EXIT_LAG_MULTI_DAY_RESULTS.json").write_text(json.dumps(multi, indent=2), encoding="utf-8")

    # Phase 3: Regime breakdown
    median_trades = sorted(daily_trade_count)[n_days // 2] if n_days else 0
    regime_lines = [
        "# Exit-Lag Regime Breakdown",
        "",
        "**Authority:** Droplet. Shadow only; paper only.",
        "",
        "## Day classification",
        "",
        f"- Days: {n_days}; date range: {multi['date_range']['first']} to {multi['date_range']['last']}",
        f"- Median trade count: {median_trades} (high_volume = above median, low_volume = at or below)",
        "- Green day: current realized PnL ≥ 0; red day: < 0",
        "",
        "## Performance by regime",
        "",
    ]
    green_days = [i for i in range(n_days) if daily_current_pnl[i] >= 0]
    red_days = [i for i in range(n_days) if daily_current_pnl[i] < 0]
    high_vol_days = [i for i in range(n_days) if daily_trade_count[i] > median_trades]
    low_vol_days = [i for i in range(n_days) if daily_trade_count[i] <= median_trades]

    for v in VARIANT_KEYS:
        pnls = variant_daily_pnl[v]
        regime_lines.append(f"### {v}")
        regime_lines.append("")
        if green_days:
            green_improve = [pnls[i] - current_totals[i] for i in green_days]
            regime_lines.append(f"- Green days ({len(green_days)}): mean daily Δ vs current = {sum(green_improve)/len(green_improve):.2f} USD")
        if red_days:
            red_improve = [pnls[i] - current_totals[i] for i in red_days]
            regime_lines.append(f"- Red days ({len(red_days)}): mean daily Δ vs current = {sum(red_improve)/len(red_improve):.2f} USD")
        if high_vol_days:
            hv_improve = [pnls[i] - current_totals[i] for i in high_vol_days]
            regime_lines.append(f"- High volume ({len(high_vol_days)}): mean daily Δ = {sum(hv_improve)/len(hv_improve):.2f} USD")
        if low_vol_days:
            lv_improve = [pnls[i] - current_totals[i] for i in low_vol_days]
            regime_lines.append(f"- Low volume ({len(low_vol_days)}): mean daily Δ = {sum(lv_improve)/len(lv_improve):.2f} USD")
        regime_lines.append("")

    regime_lines.extend([
        "## Regime fragility",
        "",
        "Variants that improve only on green or only on high-volume days are conditionally useful; prefer variants that improve across regimes.",
        "",
    ])
    (exp_dir / "EXIT_LAG_REGIME_BREAKDOWN.md").write_text("\n".join(regime_lines), encoding="utf-8")

    # Phase 4: Robustness scorecard (1-5 scale, 5 best)
    def score(vkey: str) -> dict:
        m = multi["variants"][vkey]
        delta = m["cumulative_delta_vs_current_usd"]
        pct = m["pct_days_improved"]
        dd_delta = m["max_drawdown_delta_avg_usd"]
        tail_delta = m["tail_loss_delta_avg_usd"]
        expectancy = 5 if delta > 50 else (4 if delta > 20 else (3 if delta > 0 else (2 if delta > -20 else 1)))
        consistency = 5 if pct >= 80 else (4 if pct >= 60 else (3 if pct >= 50 else (2 if pct >= 30 else 1)))
        drawdown = 5 if dd_delta <= 0 else (4 if dd_delta <= 5 else (3 if dd_delta <= 10 else 2))
        tail = 5 if tail_delta >= 0 else (4 if tail_delta >= -5 else (3 if tail_delta >= -10 else 2))
        regime = 4  # default; could refine with green/red split
        simplicity = 5 if vkey == "A_first_eligibility" else (4 if vkey in ("C_partial_50", "D_flow_reversal_only") else 3)
        total = expectancy + consistency + drawdown + tail + regime + simplicity
        return {"expectancy": expectancy, "consistency": consistency, "drawdown": drawdown, "tail": tail, "regime": regime, "simplicity": simplicity, "total": total}

    scores = {v: score(v) for v in VARIANT_KEYS}
    ranked = sorted(VARIANT_KEYS, key=lambda x: -scores[x]["total"])
    clear_winner = ranked[0] if ranked and scores[ranked[0]]["total"] >= 22 else None
    conditional = [v for v in ranked[1:4] if scores[v]["total"] >= 18]
    rejected = [v for v in VARIANT_KEYS if scores[v]["total"] < 15]

    scorecard_lines = [
        "# Exit-Lag Robustness Scorecard",
        "",
        "**Authority:** Droplet. Paper only.",
        "",
        "## Scores (1–5, 5 best)",
        "",
        "| Variant | Expectancy | Consistency | Drawdown | Tail | Regime | Simplicity | Total |",
        "|----------|------------|-------------|----------|------|--------|------------|-------|",
    ]
    for v in VARIANT_KEYS:
        s = scores[v]
        scorecard_lines.append(f"| {v} | {s['expectancy']} | {s['consistency']} | {s['drawdown']} | {s['tail']} | {s['regime']} | {s['simplicity']} | {s['total']} |")
    scorecard_lines.extend([
        "",
        "## Rank",
        "",
        f"- **Clear winner:** {clear_winner or 'None (insufficient evidence)'}",
        f"- **Conditional winners:** {', '.join(conditional) or 'None'}",
        f"- **Rejected:** {', '.join(rejected) or 'None'}",
        "",
    ])
    (exp_dir / "EXIT_LAG_ROBUSTNESS_SCORECARD.md").write_text("\n".join(scorecard_lines), encoding="utf-8")

    # Phase 5: CSA verdict
    best = ranked[0] if ranked else None
    best_delta = multi["variants"][best]["cumulative_delta_vs_current_usd"] if best else 0
    best_pct = multi["variants"][best]["pct_days_improved"] if best else 0
    if n_days >= 5 and best_delta > 30 and best_pct >= 60 and best and scores[best]["drawdown"] >= 4:
        verdict_key = "PROMOTE_TO_LIMITED_PAPER_AB"
        variant_approved = best
        guardrails = "Paper only; single variant; monitor drawdown and tail for 5 days; no live promotion without further board approval."
    elif best_delta > 0 and best_pct >= 40:
        verdict_key = "CONTINUE_SHADOW"
        variant_approved = None
        guardrails = ""
    else:
        verdict_key = "REJECT_VARIANTS"
        variant_approved = None
        guardrails = "Insufficient improvement or consistency; or elevated risk."

    csa = {
        "verdict": verdict_key,
        "variant_approved_for_limited_paper_ab": variant_approved,
        "guardrails": guardrails,
        "n_days": n_days,
        "date_range": multi["date_range"],
        "best_variant": best,
        "best_cumulative_delta_usd": round(best_delta, 4) if best else None,
        "best_pct_days_improved": best_pct if best else None,
        "evidence_missing_if_continue": "More days and/or regime diversity; drawdown SLO; tail stress test." if verdict_key == "CONTINUE_SHADOW" else None,
        "adversarial_review_path": "reports/experiments/EXIT_LAG_ADVERSARIAL_REVIEW.md",
        "customer_advocate_note_path": "reports/experiments/EXIT_LAG_CUSTOMER_ADVOCATE_NOTE.md",
    }
    (audit_dir / "CSA_EXIT_LAG_MULTI_DAY_VERDICT.json").write_text(json.dumps(csa, indent=2), encoding="utf-8")

    # Adversarial review and customer advocate (SRE/CSA: part of process; verdict references above paths)
    for script in ["run_exit_lag_adversarial_review.py", "run_exit_lag_customer_advocate_note.py"]:
        subprocess.run(
            [sys.executable, f"scripts/experiments/{script}", "--base-dir", str(base)],
            cwd=base,
            capture_output=True,
            timeout=30,
        )

    # Phase 6: Board packet (include adversarial + customer advocate)
    board_lines = [
        "# Exit-Lag Multi-Day Board Packet",
        "",
        "## Multi-day evidence summary",
        "",
        f"- Days: {n_days}; range: {multi['date_range']['first']} to {multi['date_range']['last']}",
        f"- Cumulative current realized (baseline): {cumulative_current:.2f} USD",
        f"- Best variant: **{best or 'N/A'}** (cumulative Δ {best_delta:+.2f} USD, {best_pct}% days improved)",
        "",
        "## Recommended next step",
        "",
        verdict_key.replace("_", " ").title() + "." + (f" Variant: {variant_approved}. Guardrails: {guardrails}" if variant_approved else ""),
        "",
        "## Non-actions",
        "",
        "- Do not promote to live.",
        "- Do not change production exit config without explicit CSA + board approval.",
        "",
        "## Promotion guardrails (if approved)",
        "",
        guardrails or "N/A",
        "",
        "## Adversarial review",
        "",
        "See `reports/experiments/EXIT_LAG_ADVERSARIAL_REVIEW.md`. Challenges: sample size, overfitting, regime bias, tail risk. Mitigations must be addressed before promotion.",
        "",
        "## Customer advocate",
        "",
        "See `reports/experiments/EXIT_LAG_CUSTOMER_ADVOCATE_NOTE.md`. Customer outcome (realized PnL) and whipsaw/tail risk must align before limited paper A/B.",
        "",
    ]
    (board_dir / "EXIT_LAG_MULTI_DAY_BOARD_PACKET.md").write_text("\n".join(board_lines), encoding="utf-8")

    print("Wrote EXIT_LAG_MULTI_DAY_RESULTS.json, REGIME_BREAKDOWN.md, ROBUSTNESS_SCORECARD.md, CSA_EXIT_LAG_MULTI_DAY_VERDICT.json, EXIT_LAG_ADVERSARIAL_REVIEW.md, EXIT_LAG_CUSTOMER_ADVOCATE_NOTE.md, EXIT_LAG_MULTI_DAY_BOARD_PACKET.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
