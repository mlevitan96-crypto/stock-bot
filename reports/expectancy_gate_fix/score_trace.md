# Expectancy gate — Score flow trace

**Purpose:** Identify where composite score is computed, where it is compared to the 2.70 threshold, and what score is passed into `ExpectancyGate.should_enter`. Findings support the score-contract fix.

---

## 1. Where composite score is computed

- **Cluster composite:** Built earlier in the pipeline (composite scoring path). Clusters that reach `decide_and_execute` have `c["composite_score"]` set (e.g. 8.0 before sector/persistence boosts; DEBUG shows “composite_score=8.000”, then “Sector Tide boost +0.30”, “Persistence boost +0.50”, “Composite signal ACCEPTED … score=8.80”).
- **In decide_and_execute (main.py):**
  - **7592:** `score = c.get("composite_score", 0.0)` — initial score from cluster.
  - **7635–7637:** `score` is **overwritten** by `apply_signal_quality_to_score`, `apply_uw_to_score`, `apply_survivorship_to_score`. These can **reduce** score (e.g. to ~2.8–2.9).
  - **7765–7807:** If cluster has `composite_score` and source in (`composite`, `composite_v3`), `base_score = c["composite_score"]` and `score = base_score * regime_mult * macro_mult` (or `base_score` on exception). So after this block, `score` is the regime/macro-adjusted composite when that block runs; **but** the earlier adjustments (7635–7637) run **before** this block and already overwrote `score`. So the order is: initial composite → UW/signal_quality/survivorship **reduce** score → then composite block may set score = base_score * regime_mult * macro_mult. So for composite clusters the **final** `score` at the expectancy gate is the regime/macro-adjusted one **if** the composite block ran; otherwise it is the reduced (UW/survivorship) score.
- **Root cause:** For many symbols the composite block (7765+) may not run (e.g. source not "composite"/"composite_v3", or score <= 0), so `score` remains the **reduced** value from 7635–7637. That reduced value (e.g. 2.86) is what is passed to the expectancy gate, so `score < MIN_EXEC_SCORE` (3.0) is True → score_floor_breach → 100% block.

---

## 2. Where composite is compared to the 2.70 threshold

- **Prior gate (composite filter):** Clusters are built and filtered **before** `decide_and_execute`. DEBUG: “Composite signal ACCEPTED for {ticker}: score={score:.2f}, … threshold={get_threshold(ticker, 'base'):.2f}” (main.py ~10814). Threshold comes from `get_threshold(ticker, 'base')` (e.g. 2.70). So the **score that passed** is the composite (after sector/persistence boosts) used in that check.
- **Funnel / logging:** “Record scored signal (score > 2.7 threshold)” at 7675–7676 uses the **current** `score` (already possibly reduced by 7635–7637). So 2.70 is used in multiple places; the “prior gate” that admits clusters into the loop is the composite acceptance (e.g. 8.80 >= 2.70). The cluster’s `c["composite_score"]` is the canonical composite for that cluster (e.g. 8.0; boosts may be applied in logging/display).

---

## 3. What score is passed into ExpectancyGate.should_enter

- **Current code (main.py ~8190–8211):**
  - `expectancy = v32.ExpectancyGate.calculate_expectancy(composite_score=score, ...)`
  - `should_trade, gate_reason = v32.ExpectancyGate.should_enter(..., composite_score=score, score_floor_breach=(score < Config.MIN_EXEC_SCORE))`
- **So:** The variable `score` at this point is whatever it was **after** all adjustments (UW, signal_quality, survivorship, and possibly the composite block). When the composite block does **not** overwrite (e.g. non-composite source or earlier reduction not overwritten), `score` is the **reduced** value (e.g. 2.86). Hence `score < 3.0` → score_floor_breach → reject.
- **Cluster composite:** `c.get("composite_score")` is **not** used at the ExpectancyGate call; only `score` is. So the gate is evaluating a **different** score than the one that passed the composite filter.

---

## 4. Summary table (for EXPECTANCY_DEBUG=1)

| Field | Source | Current value at gate |
|-------|--------|------------------------|
| composite_score (cluster) | c.get("composite_score") | e.g. 8.0 (pre-boost) or cluster’s stored composite |
| score (variable) | After apply_uw, apply_signal_quality, apply_survivorship; possibly composite block | e.g. 2.86 (reduced) |
| score_used_by_expectancy | Currently `score` | 2.86 → floor breach |
| expectancy_floor | Config.MIN_EXEC_SCORE | 3.0 |
| decision | should_enter(..., score_floor_breach=True) | fail |

---

## 5. Fix (contract)

- **score_used_by_expectancy** must be the **same** composite that passed the prior gate.
- Use **cluster composite** at the gate: `composite_exec_score = c.get("composite_score", score)` and pass `composite_exec_score` into `ExpectancyGate.calculate_expectancy` and `ExpectancyGate.should_enter`; set `score_floor_breach=(composite_exec_score < Config.MIN_EXEC_SCORE)`.
- Then: score_used_by_expectancy = composite_exec_score (e.g. 8.0), expectancy_floor = 3.0, decision = pass (for expectancy logic); no change to thresholds.
