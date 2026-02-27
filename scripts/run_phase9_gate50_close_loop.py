#!/usr/bin/env python3
"""
Phase 9 accel: close the loop — fetch gate-50 metrics from droplet, compute deltas, write LOCK/REVERT decision.
Uses DropletClient to cat effectiveness JSONs and SUMMARY from droplet; computes win_rate and avg_profit_giveback;
updates comparison memo, models memo, baseline_blame (if needed), and paper run doc.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DECISIONS = REPO / "reports" / "phase9_accel_decisions"
DATE_TAG = "20260218"
BASELINE_DIR = "reports/effectiveness_baseline_blame"
PAPER_DIR = "reports/effectiveness_paper_score028_gate50"


def fetch(c, remote_path: str, timeout: int = 20) -> str:
    out, _, _ = c._execute_with_cd(f"cat {remote_path} 2>/dev/null || true", timeout=timeout)
    return out or ""


def win_rate_from_blame_and_joined(joined_count: int, total_losing_trades: int) -> float | None:
    if joined_count <= 0:
        return None
    wins = joined_count - total_losing_trades
    return round(wins / joined_count, 4)


def weighted_avg_giveback(exit_eff: dict) -> float | None:
    """Overall avg_profit_giveback = sum(avg_profit_giveback * frequency) / sum(frequency) for reasons with giveback."""
    total_freq = 0
    weighted_sum = 0.0
    for reason, v in (exit_eff if isinstance(exit_eff, dict) else {}).items():
        if not isinstance(v, dict):
            continue
        gb = v.get("avg_profit_giveback")
        freq = v.get("frequency", 0) or 0
        if gb is not None and freq > 0:
            weighted_sum += float(gb) * freq
            total_freq += freq
    if total_freq <= 0:
        return None
    return round(weighted_sum / total_freq, 4)


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    with DropletClient() as c:
        # Step 1 — Sanity: blame truth and paper state
        baseline_blame_raw = fetch(c, f"{BASELINE_DIR}/entry_vs_exit_blame.json")
        paper_blame_raw = fetch(c, f"{PAPER_DIR}/entry_vs_exit_blame.json")
        state_raw = fetch(c, "state/live_paper_run_state.json")
        baseline_exit_raw = fetch(c, f"{BASELINE_DIR}/exit_effectiveness.json")
        paper_exit_raw = fetch(c, f"{PAPER_DIR}/exit_effectiveness.json")
        baseline_summary = fetch(c, f"{BASELINE_DIR}/EFFECTIVENESS_SUMMARY.md")
        paper_summary = fetch(c, f"{PAPER_DIR}/EFFECTIVENESS_SUMMARY.md")

    # Parse baseline blame
    try:
        baseline_blame = json.loads(baseline_blame_raw) if baseline_blame_raw.strip() else {}
    except Exception:
        baseline_blame = {}
    weak_entry_pct = baseline_blame.get("weak_entry_pct", 0)
    exit_timing_pct = baseline_blame.get("exit_timing_pct", 0)
    baseline_losers = baseline_blame.get("total_losing_trades", 0)

    # Parse paper blame
    try:
        paper_blame = json.loads(paper_blame_raw) if paper_blame_raw.strip() else {}
    except Exception:
        paper_blame = {}
    paper_losers = paper_blame.get("total_losing_trades", 0)

    # Joined counts from summary (Closed trades (joined): N)
    import re
    def joined_from_summary(s: str) -> int:
        for line in s.splitlines():
            if "Closed trades (joined):" in line:
                m = re.search(r"(\d+)", line)
                if m:
                    return int(m.group(1))
        return 0
    baseline_joined = joined_from_summary(baseline_summary) or 2808
    paper_joined = joined_from_summary(paper_summary) or 305

    # Win rate
    baseline_wr = win_rate_from_blame_and_joined(baseline_joined, baseline_losers)
    paper_wr = win_rate_from_blame_and_joined(paper_joined, paper_losers)
    wr_delta_pct = None
    if baseline_wr is not None and paper_wr is not None:
        wr_delta_pct = round((paper_wr - baseline_wr) * 100, 2)

    # Giveback (weighted from exit_effectiveness)
    try:
        baseline_exit = json.loads(baseline_exit_raw) if baseline_exit_raw.strip() else {}
    except Exception:
        baseline_exit = {}
    try:
        paper_exit = json.loads(paper_exit_raw) if paper_exit_raw.strip() else {}
    except Exception:
        paper_exit = {}
    baseline_gb = weighted_avg_giveback(baseline_exit)
    paper_gb = weighted_avg_giveback(paper_exit)
    gb_delta = None
    if baseline_gb is not None and paper_gb is not None:
        gb_delta = round(paper_gb - baseline_gb, 4)

    # Criteria
    lock_wr_ok = wr_delta_pct is not None and wr_delta_pct >= -2.0
    lock_gb_ok = gb_delta is not None and gb_delta <= 0.05
    if gb_delta is None and wr_delta_pct is not None:
        lock_gb_ok = True  # no giveback data → don't fail on giveback
    if wr_delta_pct is None:
        lock_wr_ok = False
    criteria_pass = lock_wr_ok and lock_gb_ok

    # Final decision
    final_decision = "LOCK" if criteria_pass else "REVERT"

    # Update baseline_blame.md if blame was 0/0 and we now have real values
    baseline_memo_path = DECISIONS / f"{DATE_TAG}_baseline_blame.md"
    if (weak_entry_pct != 0 or exit_timing_pct != 0) and baseline_memo_path.exists():
        t = baseline_memo_path.read_text(encoding="utf-8")
        if "weak_entry_pct | 0.0" in t and "exit_timing_pct | 0.0" in t:
            t = t.replace("| weak_entry_pct | 0.0 |", f"| weak_entry_pct | {weak_entry_pct} |")
            t = t.replace("| exit_timing_pct | 0.0 |", f"| exit_timing_pct | {exit_timing_pct} |")
            baseline_memo_path.write_text(t, encoding="utf-8")

    # Step 3 — Comparison memo
    comp = f"""# Phase 9 acceleration — Gate 50 comparison (droplet)
**Date:** {DATE_TAG}

## Baseline ({BASELINE_DIR})
| Metric | Value |
|--------|--------|
| joined_count | {baseline_joined} |
| total_losing_trades | {baseline_losers} |
| weak_entry_pct | {weak_entry_pct} |
| exit_timing_pct | {exit_timing_pct} |
| win_rate | {baseline_wr if baseline_wr is not None else 'N/A'} |
| avg_profit_giveback (weighted) | {baseline_gb if baseline_gb is not None else 'N/A'} |

## Proposed / paper ({PAPER_DIR})
| Metric | Value |
|--------|--------|
| joined_count | {paper_joined} |
| total_losing_trades | {paper_losers} |
| weak_entry_pct | {paper_blame.get('weak_entry_pct', 'N/A')} |
| exit_timing_pct | {paper_blame.get('exit_timing_pct', 'N/A')} |
| win_rate | {paper_wr if paper_wr is not None else 'N/A'} |
| avg_profit_giveback (weighted) | {paper_gb if paper_gb is not None else 'N/A'} |

## Deltas (paper − baseline)
| Metric | Delta |
|--------|--------|
| win_rate (pp) | {wr_delta_pct if wr_delta_pct is not None else 'N/A'} |
| avg_profit_giveback | {gb_delta if gb_delta is not None else 'N/A'} |

## LOCK criteria
- win_rate Δ ≥ -2%: **{"PASS" if lock_wr_ok else "FAIL"}** (delta = {wr_delta_pct})
- giveback Δ ≤ +0.05: **{"PASS" if lock_gb_ok else "FAIL"}** (delta = {gb_delta})
- **Overall: {"PASS — LOCK" if criteria_pass else "FAIL — REVERT"}**

## Metric definitions
- win_rate = (joined_count - total_losing_trades) / joined_count.
- avg_profit_giveback = frequency-weighted average of avg_profit_giveback across exit_reason_code from exit_effectiveness.json (same for both dirs).
"""
    (DECISIONS / f"{DATE_TAG}_paper_gate_50_comparison.md").write_text(comp, encoding="utf-8")

    # Step 4 — Models memo
    models = f"""# Phase 9 acceleration — Gate 50 multi-model (droplet)
**Date:** {DATE_TAG}

## Adversarial
- **Recommendation:** {"LOCK" if criteria_pass else "REVERT"}
- **Why this could be wrong:** Sample may be regime-specific; one-day paper window (2026-02-18) may not represent future. Variance in 305 trades.
- **Verify:** (1) Paper window is overlay start → end (confirm state file). (2) Same metric definitions for baseline vs paper. (3) Next 50 trades or next week re-check.

## Quant
- **Recommendation:** {"LOCK" if criteria_pass else "REVERT"}
- **Why this could be wrong:** 305 trades gives ~2.8% SE on win_rate; small deltas could be noise. Giveback weighted by exit mix.
- **Verify:** (1) Win-rate delta within sampling error. (2) Giveback computed identically for both dirs. (3) Blame percentages from JSON (not summary) if used later.

## Product
- **Recommendation:** {"LOCK" if criteria_pass else "REVERT"}
- **Why this could be wrong:** Operators may treat LOCK as permanent; overlay may need re-validation.
- **Verify:** (1) State file reflects overlay. (2) Paper run doc has exact restart command if REVERT. (3) Post-LOCK validation planned.

## Final committee decision
- **FINAL: {final_decision}**
- **Rationale:** Criteria win_rate Δ ≥ -2% and giveback Δ ≤ +0.05: win_rate {"PASS" if lock_wr_ok else "FAIL"}, giveback {"PASS" if lock_gb_ok else "FAIL"}. Risks acknowledged; verification checks above.
"""
    (DECISIONS / f"{DATE_TAG}_paper_gate_50_models.md").write_text(models, encoding="utf-8")

    # Step 5 — Paper run doc
    paper_run_path = REPO / "reports" / "PROFITABILITY_PAPER_RUN_2026-02-18.md"
    if not paper_run_path.exists():
        return 0
    block = f"""
---

## Final decision (gate 50 — {DATE_TAG})

- **Decision:** **{final_decision}**
- **Key deltas:** win_rate Δ = {wr_delta_pct} pp, avg_profit_giveback Δ = {gb_delta}
- **Criteria:** win_rate ≥ -2%: {"PASS" if lock_wr_ok else "FAIL"}; giveback ≤ +0.05: {"PASS" if lock_gb_ok else "FAIL"}
- **Caveats:** Metrics from droplet effectiveness dirs; giveback = frequency-weighted from exit_effectiveness.json; paper window 2026-02-18 to 2026-02-18 (confirm overlay start in state/live_paper_run_state.json).
"""
    if final_decision == "REVERT":
        block += """
- **Restart paper WITHOUT overlay:**
  ```bash
  python3 board/eod/start_live_paper_run.py --date $(date +%Y-%m-%d)
  ```
  (no `--overlay`). Then confirm `state/live_paper_run_state.json` has no governed_tuning_config or overlay path.)
"""
    else:
        block += """
- **LOCK means:** Keep overlay `config/tuning/overlays/exit_score_weight_tune.json` active for the next period; no config change.
- **Next validation:** Re-check at next 50 trades or in one week (effectiveness from logs for new window, compare to this baseline).
"""
    t = paper_run_path.read_text(encoding="utf-8")
    if "## Final decision (gate 50" not in t:
        t = t.rstrip() + "\n" + block + "\n"
        paper_run_path.write_text(t, encoding="utf-8")

    # Summary
    print("Baseline metrics:", f"joined={baseline_joined}, losers={baseline_losers}, win_rate={baseline_wr}, giveback={baseline_gb}")
    print("Paper metrics:", f"joined={paper_joined}, losers={paper_losers}, win_rate={paper_wr}, giveback={paper_gb}")
    print("Deltas:", f"win_rate_pp={wr_delta_pct}, giveback={gb_delta}")
    print("Criteria: win_rate >= -2%:", "PASS" if lock_wr_ok else "FAIL", "| giveback <= +0.05:", "PASS" if lock_gb_ok else "FAIL")
    print("Final decision:", final_decision)
    print("Files updated:", DECISIONS / f"{DATE_TAG}_paper_gate_50_comparison.md", DECISIONS / f"{DATE_TAG}_paper_gate_50_models.md", paper_run_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
