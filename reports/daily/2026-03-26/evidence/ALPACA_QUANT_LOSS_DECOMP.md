# Alpaca Quant Lab — Loss Mechanism Decomposition (QSA)

**Mission:** Phase 2 — For each closed position: entry vs exit attribution, MAE vs MFE, direction correctness, gap impact, regime mismatch.  
**Authority:** QSA.  
**Date:** 2026-03-18.

---

## 1. Questions Answered

- **Are we wrong early?** (Entry quality: score, regime, direction.)
- **Are exits giving back?** (MFE vs realized; exit reason and exit score.)
- **Are gaps killing us?** (Overnight/weekend gaps; bar gaps.)

---

## 2. Decomposition Framework

### 2.1 Per Closed Position (Required Fields)

| Dimension | Source | Notes |
|-----------|--------|--------|
| **Entry attribution** | entry_score (master_trade_log / exit_attribution context), entry_regime, entry composite components | When join coverage allows. |
| **Exit attribution** | exit_reason, v2_exit_score, v2_exit_components (exit_flow_deterioration, exit_score_deterioration, exit_regime_shift, etc.) | From exit_attribution → TRADES_FROZEN. |
| **MAE vs MFE** | TRADE_TELEMETRY.csv (step2) or exit_quality_metrics | Path-real from bars when available; else placeholder or null. |
| **Direction correctness** | side, realized_pnl_usd; price move (exit_price − entry_price) vs side | Long + positive move = correct; short + negative move = correct. |
| **Gap impact** | Bars over entry→exit; identify gap bars (e.g. overnight); PnL in gap vs in-session | Requires bar-level alignment. |
| **Regime mismatch** | entry_regime vs exit_regime; regime at entry vs realized outcome | Binary or categorical. |

### 2.2 Aggregates (Lab Outputs)

- **Wrong early:** % of losers with low entry score or wrong-side entry vs regime.
- **Exits giving back:** Mean (MFE − realized) for losers; distribution of exit_reason for losers (signal_decay, stale_alpha_cutoff, trail_stop, etc.).
- **Gaps:** % of loss from gap periods; count of trades with material gap drawdown.
- **Regime mismatch:** % of losers with entry_regime ≠ exit_regime or entry in adverse regime.

---

## 3. Data Requirements

- **TRADES_FROZEN.csv:** symbol, side, entry_time, exit_time, entry_price, exit_price, realized_pnl_usd, exit_reason, entry_regime, exit_regime, v2_exit_score.
- **TRADE_TELEMETRY.csv (step2):** mfe_pct, mae_pct, time_to_peak_min, time_to_trough_min.
- **Exit attribution (full):** v2_exit_components for top contributors per trade.
- **Entry score:** From master_trade_log or exit_attribution when present (see Phase 0 join coverage).

---

## 4. Findings (From Existing Loss Forensics)

Existing reports (ALPACA_LOSS_FORENSICS_ENTRY_CAUSES.md, ALPACA_LOSS_FORENSICS_EXIT_CAUSES.md) show:

- **Entry:** Many large losers have `entry composite_score: None` (entry attribution missing) or moderate scores (3–5); top entry contributions often flow, dark_pool, event, toxicity_penalty, greeks_gamma.
- **Exit:** Dominant exit drivers for losers: **sentiment_deterioration**, **regime_shift**, **sector_shift**, **vol_expansion**, **score_deterioration**. Exit reasons: signal_decay, stale_alpha_cutoff, trail_stop.
- **MAE/MFE:** Often 0.0000 in forensics (exit_quality_metrics or bar-based MFE/MAE not populated for those runs).

**Interpretation:**

- **Wrong early:** Partially — some losers had decent entry scores; others had missing entry data. Not all losses are “wrong direction” at entry.
- **Exits giving back:** Exit pressure (regime/sector/sentiment deterioration, vol expansion) frequently high on losers; signal_decay and stale_alpha_cutoff suggest exits triggered by time/decay, possibly giving back gains.
- **Gaps:** Not yet decomposed in existing forensics; requires bar-level gap detection.
- **Regime mismatch:** regime_shift = 1.0 on many losers indicates entry_regime ≠ exit_regime; regime mismatch is a material loss factor.

---

## 5. Recommended Next Steps

1. **Re-run step2** on latest frozen dataset to populate MFE/MAE where bars exist; then recompute “exits giving back” (MFE − realized) for losers.
2. **Gap detection:** For each trade, tag bars that span overnight/weekend; attribute PnL to in-session vs gap; report % loss from gaps.
3. **Direction correctness:** Add binary “direction_correct” per trade; tabulate win rate by direction_correct and by regime.
4. **Stratify loss decomp** by exit_reason, entry_regime, and symbol (top losers) and append to this document or a follow-up LOSS_DECOMP_DETAILED.md.
