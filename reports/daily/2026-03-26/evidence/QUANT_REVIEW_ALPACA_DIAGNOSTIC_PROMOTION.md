# Quant Officer Review — Alpaca Diagnostic Promotion

**Rule:** `SCORE_DETERIORATION_EMPHASIS`  
**Tag:** `PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS`

---

## Learning objective

Test whether emphasizing **composite decay** (`score_deterioration`) in **`compute_exit_score_v2`** produces:

- More **`intel_deterioration`**-labeled exits when entry vs now score diverges, and  
- **Lower average loss** on trades where decay is the dominant story.

---

## Analytical validity

- **Measurable:** `exit_reason_code`, `v2_exit_score`, `v2_exit_components`, `pnl` in `exit_attribution.jsonl`.
- **Controlled:** Single lever (exit weight vector); entry gates unchanged.
- **Attribution clarity:** `attribution_components` now reflect **merged** weights — aligns logs with the **same** weights used in the composite score (post `exit_score_v2` wiring).

---

## Outcome

**Pending** — see [ALPACA_DIAGNOSTIC_PROMOTION_REVIEW.md](./ALPACA_DIAGNOSTIC_PROMOTION_REVIEW.md) after **48–72h** trading window.

---

## Sign-off (pre-window)

**Hypothesis sound; evaluation criteria acceptable.** Quant Officer — **ACCEPT** diagnostic proceed.

---

*Quant Officer*
