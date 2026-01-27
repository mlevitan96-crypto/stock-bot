# Phase-2 Verification Summary - 2026-01-26

**Generated:** 2026-01-27T00:55:54.959695+00:00
**Data source:** local

---

## PASS / FAIL by section

- **B1 trade_intent:** PASS (count=0)
- **B2 exit_intent:** PASS (count=0)
- **B3 directional_gate:** PASS (blocks=0)
- **C displacement:** FAIL (evaluated=0, allowed=0, blocked=0)
- **D shadow:** PASS (decisions=0, variants=[])
- **E high-vol cohort:** PASS (HIGH_VOL count=0)
- **F EOD data-backed:** FAIL (exists=True)

---

## Failure reasons (if any)

- **c:**
  - displacement_evaluated never appears

- **f:**
  - EOD section missing or placeholder: Winners vs Losers
  - EOD section missing or placeholder: High-Volatility Alpha
  - EOD section missing or placeholder: Shadow Scoreboard

---

## What is wired vs what is firing

- **trade_intent:** 0 emitted (all with snapshot+tags)
- **exit_intent:** 0 emitted (all with thesis_break_reason+snapshot)
- **directional_gate:** 0 blocks logged
- **displacement_evaluated:** 0 evaluations, allowed=0, blocked=0
- **shadow_variant_decision:** 0 events, variants=[]
- **HIGH_VOL cohort:** 0 symbols

---

## Confidence: **MEDIUM**

---

## Generated CSVs (exports/)

- `VERIFY_trade_intent_samples.csv`
- `VERIFY_exit_intent_samples.csv`
- `VERIFY_directional_gate_blocks.csv`
- `VERIFY_displacement_decisions.csv`
- `VERIFY_shadow_variant_activity.csv`
- `VERIFY_high_vol_cohort.csv`

---

## Executive summary

Is Phase-2 Alpha Discovery actually operating in live trading? Data source: local or partial (droplet is source of truth). Audited against local logs/state only; droplet was not fully used. 2 section(s) FAIL. Phase-2 Alpha Discovery is NOT fully operating in live: c=FAIL, f=FAIL. Confidence: MEDIUM.
