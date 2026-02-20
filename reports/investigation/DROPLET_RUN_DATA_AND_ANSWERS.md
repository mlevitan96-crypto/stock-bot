# Droplet run — data and answers

**Run time:** 2026-02-20 (via `scripts/run_investigation_on_droplet_and_fetch.py`).  
**Source:** Commands executed on droplet via SSH; reports fetched from `reports/signal_review/` and `reports/investigation/fetched/`.

---

## What ran on the droplet

| Step | Script | Result |
|------|--------|--------|
| Git pull | `git pull origin main` | Already up to date |
| Baseline snapshot | `investigation_baseline_snapshot_on_droplet.py` | **Not run** — script not on droplet (not yet pushed) |
| Full signal review | `full_signal_review_on_droplet.py --days 7` | **OK** — funnel and adversarial review generated |
| Closed loops checklist | `run_closed_loops_checklist_on_droplet.py` | **Not run** — script not on droplet |
| Signal breakdown summary | `signal_score_breakdown_summary_on_droplet.py` | **Skipped** — `logs/signal_score_breakdown.jsonl` has 0 lines (need 100) |

---

## Data from the droplet (7-day window)

- **Total candidates (ledger):** 2,922  
- **Dominant choke:** Stage **5_expectancy_gate**, reason **expectancy_gate:score_floor_breach**  
- **Choke count:** 2,922 (100%)  
- **Post-adjust score (composite at gate):** p10 = 0.172, p50 = 0.172, p90 = 0.316  
- **% above MIN_EXEC_SCORE (2.5):** pre = 0.0%, post = 0.0%  
- **Pre-adjust:** p50 = 0.000, count = 0 (pre_score not in ledger; **pre_score_availability_rate = 0%**)  
- **Join coverage (droplet funnel):** ledger 0.0%, snapshots 77.2%, UW 100.0%, adjustments (pre_norm) 0.0%  
- **Order stage (from orders.jsonl):** filled = 6,382, rejected = 530  

**Example scores at gate (from funnel):** DIA 0.316, COIN 0.172, SPY 1.055, CAT 1.055, NVDA 0.316, TSLA 0.316 — all below 2.5 except SPY/CAT at 1.055.

---

## Answers (from droplet evidence)

**1. Why are there 0 submits?**  
The expectancy gate blocks every candidate: **100%** of the 2,922 candidates fail with **score_floor_breach** (composite &lt; MIN_EXEC_SCORE 2.5). Post-adjust median is **0.172**; no candidate is above 2.5 in this window.

**2. Is the composite genuinely low?**  
Yes. Score distribution at the gate is p50 = 0.172, p90 = 0.316. Even the highest examples (SPY, CAT at 1.055) are below 2.5. The gate is behaving as designed; the blocker is **score level**, not gate logic.

**3. Why is “Trades (paper)” 6,382 while submits are 0?**  
Contradiction in **metric definition / time window**. The funnel’s “filled: 6382” comes from **orders.jsonl** (all filled events in the window), not from “candidates that passed the gate and led to a submit.” So 6,382 is historical or unrelated fills; **submit_entry / SUBMIT_ORDER_CALLED** for this run would be 0. Fix: use separate metrics — **candidates_evaluated**, **paper_orders_submitted** (from submit logs), **paper_fills** (from orders) — as in the new paper_trade_metric_reconciliation (script not yet on droplet).

**4. Why is ledger join coverage 0% and pre-adjust 0?**  
Ledger events do not contain **score_components** (or the join path is wrong), so “ledger 0.0%.” Pre-adjust **composite_pre_norm** is not present in the ledger for any candidate (pre_score_availability_count = 0), so pre-adjust median is 0.000. So: **missing field or wrong join** for ledger → snapshot/components; need gate truth log and/or fixed ledger schema so pre-adjust and components are present or joined correctly.

**5. Is the score being “crushed” artificially?**  
From this run we cannot tell from the funnel alone: pre-adjust is **unobserved** (0% availability). To answer we need either (a) **expectancy_gate_truth.jsonl** (with score_pre_adjust) and/or (b) **signal_score_breakdown.jsonl** (with per-signal contribution). Both require the new instrumentation to be deployed and run on the droplet.

---

## Board verdict (from adversarial review)

- **ONE dominant cause:** **5_expectancy_gate — score_floor_breach**. Composite score below MIN_EXEC_SCORE (2.5); post-adjust median 0.17.  
- **ONE minimal reversible experiment:** Enable expectancy-gate truth log (and optionally signal breakdown) for 50–100 candidates; confirm pre vs post and per-signal contributions. No threshold or weight changes.  
- **Numeric acceptance criteria:** (1) Gate truth log has ≥50 lines with (composite_score, MIN_EXEC_SCORE, gate_outcome). (2) Post-adjust median and % above 2.5 match funnel for same window.

---

## What to do next (to get full data and close loops)

1. **Push** the new scripts (baseline snapshot, closed loops checklist, expectancy gate truth, signal breakdown, funnel updates, paper reconciliation) to **origin/main** so the droplet gets them on `git pull`.  
2. **On droplet:** Run baseline snapshot, then run paper/live with **EXPECTANCY_GATE_TRUTH_LOG=1** until ≥200 lines, then **SIGNAL_SCORE_BREAKDOWN_LOG=1** until ≥100 candidates.  
3. **Re-run** full signal review, expectancy_gate_truth_report_200, signal_score_breakdown_summary, and run_closed_loops_checklist so gate truth coverage, pre-adjust, and signal breakdown are all populated and the checklist can reach PASS.

---

## DROPLET COMMANDS (executed)

```bash
cd /root/stock-bot
git fetch origin && git pull origin main
python3 scripts/full_signal_review_on_droplet.py --days 7
# baseline_snapshot and run_closed_loops_checklist not run (scripts not on droplet)
# signal_score_breakdown_summary skipped (logs/signal_score_breakdown.jsonl has 0 lines)
```

Evidence paths on droplet: `reports/signal_review/signal_funnel.json`, `signal_funnel.md`, `multi_model_adversarial_review.md`.
