# Multi-model adversarial review (Phase 2)

Generated: 2026-02-20 21:25 UTC

Evidence: reports/signal_review/signal_funnel.json, signal_funnel.md, top_50_end_to_end_traces.md.

---

## 1) Prosecution

**Strongest case for single dominant blocker.**

- Dominant choke point: **5_expectancy_gate** — reason **expectancy_gate:score_floor_breach** (count=2922, 100.0%).
- Funnel: total candidates = 2922; expectancy pre-adjust median = 0.000, post-adjust median = 0.172; % above MIN_EXEC_SCORE pre = 0.0%, post = 0.0%. Gate truth coverage: 0.0%.
- Trace evidence (trace_id): 1, 2, 3, 4, 5 (and 5 more) (see top_50_end_to_end_traces.md). Each shows score_post_adjust < 2.5 and first failing gate expectancy_gate:score_floor_breach.

Conclusion: Composite scores are below threshold at the expectancy gate; the gate correctly blocks. The blocker is score level, not gate logic.

---

## 2) Defense

**Alternative root causes + falsification tests.**

- **Alternative 1:** Data/feature pipeline (bars or UW) produces low-quality inputs → low composite. **Falsified if:** bars and UW root cause are fresh and complete; score_components show healthy contributions; pre-adjust distribution is high.
- **Alternative 2:** Adjustment chain (signal_quality, UW, survivorship) over-penalizes. **Falsified if:** top_50 traces show small deltas (pre - post); post-adjust % above 2.5 is similar to pre-adjust.

---

## 3) SRE/Operations

**Data freshness, telemetry, join coverage, contract health.**

- **Join coverage:** ledger 0.0%, snapshots 100.3%, UW 100.0%, adjustments (pre_norm) 0.0%, **gate truth** 0.0%.
- Silent skips: Candidates in score_snapshot appear in ledger. No evidence of silent drop before snapshot.
- Missing events: Blocked events have gate_name + reason + measured (see traces).
- Config drift: Compare ledger expectancy_floor to MIN_EXEC_SCORE (2.5) in config.

---

## 4) Board verdict

- **ONE dominant choke point:** 5_expectancy_gate — expectancy_gate:score_floor_breach. Composite score below MIN_EXEC_SCORE (2.5); post-adjust median 0.17. Gate truth coverage: 0.0%. Do not claim "100% expectancy choke" unless gate truth coverage >= 95%.

- **ONE minimal paper-only experiment (single reversible change):** Enable detailed expectancy-gate logging for 50 consecutive candidates (composite_score, MIN_EXEC_SCORE, score_pre_adjust when available). No threshold change. Reversible by turning log off.

- **Acceptance criteria:** (1) 50 log lines with (composite_score, MIN_EXEC_SCORE, gate_outcome). (2) If pre_adjust is logged, confirm pre vs post deltas; exact numbers: post-adjust median and % above 2.5 must match funnel report for same window.

- **24-hour monitoring plan:** Daily run of run_closed_loops_checklist_on_droplet.py (exit 0 only if gate truth coverage ≥95%, stage 5 from gate truth). Check logs/expectancy_gate_truth.jsonl line count and reports/signal_review/signal_funnel.json gate_truth_coverage_pct. Alert on non-zero exit or coverage drop.

## DROPLET COMMANDS

```bash
cd /root/stock-bot
python3 scripts/full_signal_review_on_droplet.py --days 7
# Optional: capture ledger first
python3 scripts/full_signal_review_on_droplet.py --days 7 --capture
```