# Data Review and Verifiable Next Steps — Profitability

**Review date:** After multiple backtest runs (3B–3G).  
**Purpose:** How things look, what we can figure out, whether we need changes, iteration speed, and verifiable next steps to improve profitability.

---

## 1. How things have “improved” based on the data

### P&L has not improved run-over-run (and that’s expected)

Every run (3B, 3C, 3D, 3E, 3F, 3G) over the **same 30-day window** (2026-01-15 → 2026-02-14) shows **identical** aggregate numbers:

| Metric        | Value    |
|---------------|----------|
| Trades        | 2,243    |
| Exits         | 2,815    |
| Blocks        | 2,000    |
| Total P&L     | -$162.15 |
| Win rate      | 15.16%   |
| Winning trades| 340      |
| Losing trades | 650      |

**Why:** All runs **replay the same historical logs** (attribution, blocked_trades, exit_attribution). We did not change which trades were taken in the past. We only changed **code** (signals, weights, gating) and **analysis** (signal edge). So we should not expect P&L to change between 3B and 3G on this window.

**Where improvement will show:** When we (1) use signal-edge data to **change weights/gating** (Block 3H), then (2) run a **new** backtest on a **new** window (or go live). Then we can compare P&L before vs after the change.

### What has improved: the pipeline

- **Stable replay:** Same inputs → same counts and P&L every time → reproducible.
- **Attribution:** Block 3E logs raw signals at entry and block; Block 3G adds replay-time injection so we can get full signal fields without waiting 30 days of live data.
- **Signal Edge Analysis:** Per-signal, per-regime bucketing and metrics exist; we’re one “3g run with injection” away from having real edge tables.
- **Automation:** Single command (droplet script) runs backtest + signal edge + commit/push. We can iterate by changing weights, re-running, comparing.

So **improvement so far is in capability**, not yet in P&L. The next step is to use that capability to tune and then measure P&L on a new window.

---

## 2. How it’s looking

### Aggregate

- **P&L:** -$162.15 over 2,243 trades (~−$0.07/trade). Unprofitable in this window.
- **Win rate:** 15.16% — low; most trades lose.
- **Regimes:** MIXED 2,233 trades, UNKNOWN 10. No BULL/BEAR/RANGE in the data yet, so regime-specific tuning is not yet data-driven.

### Exits

- **Exit regime:** normal 1,728, **fire_sale 1,087** — a large share of exits are fire_sale; worth inspecting whether that’s appropriate or too aggressive.
- **Exit reasons:** Dominated by **signal_decay** (many thresholds 0.6–0.9). Exits are mostly “signal decayed” rather than target or stop; could later analyze whether decay thresholds are too tight or too loose.

### Blocks

- **max_new_positions_per_cycle:** 1,041 — most blocks are capacity, not score.
- **expectancy_blocked:score_floor_breach:** 357 — score floor is blocking a meaningful number of candidates.
- **displacement_blocked:** 214, **max_positions_reached:** 282, **symbol_on_cooldown:** 63, **order_validation_failed:** 43.

So: capacity and score floor are the main block reasons; exit side is heavily signal_decay and fire_sale.

### Signal edge (current limitation)

- Only **regime_signal** and **entry_score** have non-missing buckets in the report.
- **Trend, momentum, volatility, sector, reversal, breakout, mean_reversion** are all **“missing”** because the one 3g run we have was done **before** replay-time injection was merged.
- So we **cannot** yet make data-driven “weight up / weight down” decisions from per-signal edge. We need one successful 3g run **with** injection to get that.

---

## 3. What we can figure out (with current data)

1. **Replay is consistent** — Same window → same results; we can trust the pipeline for before/after comparisons when we change logic.
2. **Exit mix** — Fire_sale and signal_decay dominate; we can later analyze decay thresholds and fire_sale rules for profitability impact.
3. **Block mix** — Capacity and score_floor dominate; we could later test relaxing/tightening score_floor or position limits and re-running.
4. **Regime** — Almost all MIXED; regime-specific tuning will need either more diverse regimes in the data or a 3g run with injection so we at least see per-signal buckets by current regime labels.

We **cannot** yet figure out which of trend/momentum/volatility/sector/reversal/breakout/mean_reversion help or hurt; that requires the 3g run with injection and the resulting edge report.

---

## 4. Do we need to make changes?

**Yes, in two stages.**

1. **Short term (unblock analysis):**  
   Get **one 3g backtest run with replay-time injection** to completion (on the droplet or locally with bars), so that:
   - `backtest_trades.jsonl` and `backtest_blocks.jsonl` have all signal fields populated, and  
   - Signal Edge Analysis produces **per-signal edge tables** (no “missing” for the main signals).

2. **Next (tune for profitability):**  
   Use that report to:
   - Choose 1–3 signals to **weight up** (better win rate or expectancy in a bucket),
   - Choose 1–3 signals to **weight down** or gate harder (worse expectancy),
   - Optionally add regime-specific adjustments when BULL/BEAR/RANGE appear.  
   Then implement Block 3H (weight/gate changes), run a **new** 30d backtest (new window or same window with new logic), and compare P&L.

---

## 5. Are we able to iterate faster now?

**Yes.**

- **Single command:** `python scripts/run_backtest_on_droplet_and_push.py` runs backtest + signal edge + commit/push (once droplet git/timeout issues are resolved).
- **Stable replay:** Same logs → same trades; only code and weights change.
- **Structured output:** backtest_summary.json, SIGNAL_EDGE_ANALYSIS_REPORT.md, BLOCK_*_MULTI_AI_REPORT.md give a clear before/after and per-signal view.
- **Replay-time injection:** When the 3g run with injection works, we don’t need to wait 30 days of live data to get full signal edge.

So: we can iterate by (1) changing weights/gates, (2) re-running the droplet backtest, (3) reading the new edge report and summary, (4) repeating. The bottleneck right now is **getting one full 3g run with injection** so we have the edge tables to act on.

---

## 6. Verifiable next steps to improve profitability

Concrete, testable steps (in order):

| # | Step | How to verify |
|---|------|----------------|
| 1 | **Get one 3g run with injection** (droplet or local with bars). | New dir `backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS/`; `SIGNAL_EDGE_ANALYSIS_REPORT.md` has **no “missing”** for trend, momentum, volatility, sector, reversal, breakout, mean_reversion. |
| 2 | **Extract recommendations from that report.** | Fill BLOCK_3G_MULTI_AI_REPORT Section 2: 1–3 signals to weight up, 1–3 to weight down, any regime-specific notes. |
| 3 | **Implement Block 3H:** Adjust weights/gates per Step 2 (small, conservative deltas). | Code review; unit tests pass; DEFAULT_SIGNAL_WEIGHTS_3D or regime/gate logic updated as intended. |
| 4 | **Re-run 30d backtest** (same window 2026-01-15 → 2026-02-14) with Block 3H code. | New backtest dir; compare `total_pnl_usd` and `win_rate_pct` to current baseline (-$162.15, 15.16%). Improvement = P&L higher (e.g. less negative) or win rate higher. |
| 5 | **Optional: second window.** Run backtest on a **different** 30d window (e.g. next 30 days). | Compare P&L and win rate on the new window with 3H vs same window without 3H (or vs current baseline). Reduces overfitting to one period. |
| 6 | **Exit-side tuning (later).** After signal weights are updated, analyze exit_reason and exit_regime (e.g. fire_sale share, signal_decay thresholds). | Hypotheses: e.g. “tighten decay threshold” or “reduce fire_sale sensitivity”; re-run backtest; compare P&L and drawdown. |
| 7 | **Block-side tuning (later).** Test score_floor or position limits (e.g. relax score_floor slightly). | Re-run backtest; compare trades count, blocks count, and P&L. |

**Immediate priority:** Step 1 (one 3g run with injection). Until that exists, Steps 2–4 cannot be done in a data-driven way.

---

## 7. Summary

- **Data:** Replay is stable; P&L has not improved run-over-run because we’re replaying the same history. Improvement will show when we change weights/gates and re-run (or go live).
- **Pipeline:** Attribution, signal edge analysis, and replay-time injection are in place; we’re one successful 3g run away from full per-signal edge.
- **Iteration:** We can iterate faster by changing code → running droplet backtest → reading reports; the blocker is getting the injection run to complete.
- **Verifiable next steps:** (1) Get 3g run with injection. (2) Use edge report for Block 3H weight/gate choices. (3) Implement 3H, re-run backtest, compare P&L. (4) Optionally validate on a second window and later tune exits/blocks.
