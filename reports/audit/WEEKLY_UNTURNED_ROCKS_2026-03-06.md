# Weekly Unturned Rocks — Missing Visibility

**Date:** 2026-03-06

Inventory of missing data and baselines that prevented stronger conclusions. For each: why it matters economically, how to instrument, where it should appear (dashboard/cockpit).

---

## 1. Missing data fields

| Rock | Why it matters | How to instrument | Where to show |
|------|----------------|-------------------|---------------|
| **Blocked opportunity cost** | We do not know $ or % of profit left on the table when we block a trade that shadow would have won. | For each blocked event, join to shadow outcome (same symbol/ts window); compute would-be PnL. | Ledger summary: `blocked_opportunity_cost_proxy`; cockpit "Blocked & CI" section. |
| **CI false positive / false negative** | We do not know how often CI blocks a winner (FP) or allows a loser (FN). | Tag CI decisions with outcome when available (e.g. shadow or subsequent exit). | Board review; CSA findings; Learning tab. |
| **Validation failure reason (structured)** | Aggregation by reason (size, symbol, margin) is not possible. | Log `validation_failed` with `reason_code`, `symbol`, `size_requested`, `limit_used`. | Ledger summary top_validation_reasons; Execution persona memo. |
| **Entry/exit timestamps (fill vs submit)** | Latency and slippage proxy missing. | Add `order_submit_ts`, `fill_ts` to attribution/exit_attribution where available. | Ledger or Execution dashboard widget. |
| **Regime tag per event** | Cannot segment by regime (e.g. high vol vs low vol). | Add `regime` or `vix_bucket` to exit_attribution and ledger events. | Ledger summary by regime; Risk Officer memo. |

---

## 2. Missing baselines

| Rock | Why it matters | How to instrument | Where to show |
|------|----------------|-------------------|---------------|
| **Do-nothing baseline** | No comparison for "what if we did not trade?" | Define do-nothing (e.g. cash) and compute same-window return. | Board comparison; 30d vs last387. |
| **Buy-and-hold (per symbol)** | Benchmark for each name we trade. | For each symbol in cohort, compute buy-hold return over same window. | Comparative review JSON/MD. |
| **Time-window counterfactual** | "What if we had traded 7d earlier/later?" | Run shadow with shifted window; compare PnL. | Research Lead; experiment log. |

---

## 3. Missing cohort comparisons

| Rock | Why it matters | How to instrument | Where to show |
|------|----------------|-------------------|---------------|
| **7d vs 14d vs 30d nomination stability** | Same shadow/strategy should be best across windows for confidence. | Build ledger summary for 7d, 14d, 30d; compare top shadow and top blocked reasons. | Weekly board packet; CSA findings. |
| **Last 100 / 387 / 750** | Different cohort sizes may change conclusions. | Run board review and shadow for 100, 387, 750; report deltas. | Board comparative synthesis. |

---

## 4. Missing attribution dimensions

| Rock | Why it matters | How to instrument | Where to show |
|------|----------------|-------------------|---------------|
| **Time-of-day** | Morning vs afternoon edge may differ. | Add `entry_hour` or bucket to ledger; aggregate by hour. | Research / Innovation memo; dashboard. |
| **Volatility (VIX or proxy)** | Regime-specific sizing or pause. | Tag each exit with VIX or ATR bucket. | Risk Officer; pivot analysis. |
| **Sector** | Concentration and sector rotation. | Sector per symbol in attribution; aggregate PnL by sector. | Board review; Risk. |
| **Spread proxy** | Execution quality. | Log bid-ask or spread at entry/exit if available. | Execution Microstructure memo. |

---

*Generated for weekly board audit. Prioritize by economic impact and implementation cost.*
