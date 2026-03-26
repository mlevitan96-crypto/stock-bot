# Adversarial review — Alpaca learning-ready final cert

**TS:** `20260327_0200Z`

## Attacks attempted

1. **Vacuous cohort:** Replay auto-era produced **89** strict cohort rows — **not vacuous**. Live forward poll remained vacuous vs deploy file; adversarial **PASS** on calling out the split (replay vs live).

2. **Hidden default epoch:** Policy C requires explicit epoch; replay bundle documents `era_selection_meta` — **PASS**.

3. **Replay cheating:** Same `evaluate_completeness` binary on droplet logs; no relaxed joins — **PASS**.

4. **Parity:** 89 econ vs 89 unified terminals for strict cohort — **PASS** (sets align).

5. **Traces:** 15 traces drawn only from **complete** trades; incomplete six never sampled — adversarial **FINDING:** traces do **not** disprove incomplete six; they prove a **substring** of cohort is healthy.

6. **Droplet proof:** Git sync, unit discovery, journals, gate JSON, cert bundle JSON, poll JSON captured — **PASS** for completeness of *artifacts*; live poll timed out as expected for short budget.

## Verdict

Cert bundle correctly fails `cert_ok` because **LEARNING_STATUS ≠ ARMED**. Adversarial review **supports STILL_BLOCKED** until `trades_incomplete==0`.
