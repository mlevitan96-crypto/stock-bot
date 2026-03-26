# Alpaca Diagnostic Promotion — Evaluation Criteria (Quant + CSA)

**Tag:** `PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS`  
**Rule:** `SCORE_DETERIORATION_EMPHASIS`

---

## Evaluation window

| Parameter | Value |
|-----------|--------|
| **Window** | **48–72 trading hours** of paper operation (≈ **6–9** US regular sessions depending on overlap) |
| **Start** | First session after deploy **2026-03-20T00:22Z** (confirm first fill/exit row timestamp in `exit_attribution.jsonl` post-deploy) |
| **End** | T + 48–72h **trading time** (exclude weekends unless paper trades weekends — use **exit timestamps** to measure) |

---

## Success signals (any one can justify **KEEP**)

| # | Signal | How to measure |
|---|--------|----------------|
| 1 | **Lower average loss per losing trade** | Mean / median `pnl` where `pnl < 0` vs pre-window baseline (same symbol mix if possible) |
| 2 | **Lower daily drawdown** | Max peak-to-trough on cumulative `pnl` by **session day** |
| 3 | **Lower trade count** with **similar** notional/exposure proxy | Trades/day ↓ with similar `qty * entry_price` band |
| 4 | **Clear attribution shift** | ↑ share of `exit_reason_code == intel_deterioration` where `score_deterioration` component is material; ↓ unexplained `hold` on clear decay |

**Baseline:** Use last **N** trading days **before** deploy from frozen `exit_attribution` slice, or last `alpaca_edge_2000` TRADES_FROZEN if aligned.

---

## Failure signals (any → consider **MODIFY** or **REVERT**)

| # | Signal |
|---|--------|
| F1 | Average loss **unchanged or worse** on comparable cohort |
| F2 | **No** observable change in exit mix / score decay behavior |
| F3 | **Data gaps** (missing fields ↑) or **attribution ambiguity** (↑ rows with empty intel / missing codes) |

---

## Decision matrix (end of window)

| Outcome | Action |
|---------|--------|
| Success + clean data | **A) KEEP** — continue live paper with same overlay |
| Partial + hypothesis tweak | **B) MODIFY** — adjust weights slightly (e.g. ±0.02 on `score_deterioration`) with new version string |
| Failure or data issues | **C) REVERT** — restore baseline `exit_weights` / version; return diagnostic to SHADOW |

---

## CSA guardrails

- **Paper only** for this diagnostic.
- No **real-money** promotion from this document alone.
- **Revert** authority if integrity regressions appear in daily completeness log.

---

*Quant + CSA — criteria are advisory; human approval for MODIFY/KEEP on material changes.*
