# Multi-model adversarial reviews — why trades are blocked

**Root cause (droplet run 2026-02-20):** Trades are blocked because **every candidate fails the expectancy gate with reason score_floor_breach**. Composite scores are below MIN_EXEC_SCORE (2.5): scores in the ledger range 0.17–1.04 (mean 0.21). So the pipeline is working as designed; the issue is that composite scores are too low, not a gate bug or silent drop.

Three distinct model perspectives plus a board synthesis. Evidence from `blocked_attribution_summary.md`, `score_distribution.md`, and `top_50_blocked_examples.md`.



---



## 1) Model A — "Prosecution"



*Argue the strongest case for why trades are blocked (top 3 hypotheses). Cite evidence from artifacts (gate counts, score distances, examples).*



**Hypothesis 1:** [Dominant blocker from blocked_attribution_summary: gate+reason with highest count.]  

Evidence: Gate counts show …; top blocked examples show measured values …



**Hypothesis 2:** [Runner-up blocker or score distribution.]  

Evidence: Score distribution shows mean distance to threshold …; …



**Hypothesis 3:** [Third factor, e.g. composite_gate vs expectancy_gate.]  

Evidence: …



---



## 2) Model B — "Defense"



*Argue why the prosecution is wrong; propose alternative root causes. Cite evidence.*



- Prosecution overstates … because …

- Alternative root cause 1: … (evidence: …)

- Alternative root cause 2: … (evidence: …)



---



## 3) Model C — "SRE/Operations"



*Look for pipeline/telemetry/ordering bugs (silent skips, missing events, config drift). Cite evidence.*



- Silent skips: Are there candidates that never appear in the ledger? …

- Missing events: Do all blocked events have explicit gate_name + reason + measured + params? …

- Config drift: Thresholds in ledger vs current config …



---



## 4) Synthesis — "Board Verdict"



- **Single dominant blocker (gate+reason):** **expectancy_gate:score_floor_breach** — 3037/3037 blocks (100%). Composite score is below MIN_EXEC_SCORE (2.5) at the expectancy gate, so the gate correctly blocks.

- **Runner-up blocker:** None in this window. No other gate fires as first fail.

- **Minimal next experiment (one change, NO threshold tuning yet):** Log composite_score and MIN_EXEC_SCORE at expectancy gate entry for 50 consecutive candidates (one cycle). Confirm score_floor_breach is set when composite_exec_score < MIN_EXEC_SCORE and that scores are in the 0.2–1.0 range. If confirmed, next step is signal/score investigation (why composite scores are so low), not gate logic.



---



**Droplet run 2026-02-20:** Ledger 3037 events (all blocked). Window 2026-02-13 to 2026-02-20. Threshold 2.5; score max 1.039, mean 0.211.

