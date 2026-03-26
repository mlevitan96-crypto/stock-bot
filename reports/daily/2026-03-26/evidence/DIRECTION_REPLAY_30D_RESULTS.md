# Direction Replay 30D — Results

**Window:** 2026-02-01 to 2026-03-02. **Cohort:** 1 trades.

**Note:** Run on droplet (or with synced logs) for full 30d cohort. On droplet: `cd /root/stock-bot && python3 scripts/replay/load_30d_backtest_cohort.py && python3 scripts/replay/reconstruct_direction_30d.py && python3 scripts/replay/run_direction_replay_30d.py`

## Scenario summary

| Scenario | Total PnL | PnL Δ vs baseline | Expectancy | Win rate | Max DD | Tail loss | N trades | N blocked |
|----------|-----------|-------------------|------------|----------|--------|-----------|----------|-----------|
| A_baseline | 0.0 | 0.0 | 0.0 | 0.0% | 0.0 | 0.0 | 1 | 0 |
| B_suppress_longs_crash | 0.0 | 0.0 | 0.0 | 0.0% | 0.0 | 0.0 | 1 | 0 |
| C_favor_shorts_crash | 0.0 | 0.0 | 0.0 | 0.0% | 0.0 | 0.0 | 1 | 0 |
| D_regime_conditioned | 0.0 | 0.0 | 0.0 | 0.0% | 0.0 | 0.0 | 1 | 0 |
| E_multi_signal_vote | 0.0 | 0.0 | 0.0 | 0.0% | 0.0 | 0.0 | 1 | 0 |
## Regime breakdown (baseline)

| Regime | Total PnL | Count | Win rate |
|--------|-----------|-------|----------|
| NEUTRAL | 0.00 | 1 | 0.0% |

## Would this have prevented being all-long on crash days?

- **B_suppress_longs_crash:** Blocks new longs when vol_regime==high and futures_direction==down; reduces exposure on crash days but does not open shorts.
- **C_favor_shorts_crash:** Flips long->short in that same condition; would have opened shorts on crash days (if flow had been long).
- **D_regime_conditioned:** Bear/crash regime -> shorts only; bull -> longs only; chop requires futures alignment. Strongest regime-based filter.
- **E_multi_signal_vote:** Direction from weighted vote of premarket, overnight, futures, vol, breadth, macro, UW; can flip some longs to shorts when vote < 0.

## Recommendation

**Promote / Do not promote:** See board persona appendix. **Safest first:** B (suppress longs on crash) is the least invasive; C and D change direction and need backtest validation on out-of-sample period before promotion.

---
## Phase 5 — Multi-model and board persona commentary

### Model A (implementation correctness)
- Reconstruction: When direction_intel_embed.intel_snapshot_entry exists, components are from live telemetry; otherwise synthetic from regime_at_entry. Synthetic mapping: bear/crash -> vol high, futures down; bull -> vol low, futures up.
- Scenarios B/C use vol_regime from volatility_direction.raw_value and futures_direction from components; if missing, default flat/mid.
- PnL for flipped short: (entry_price - exit_price) * qty. Blocked trades contribute zero PnL and reduce n_trades.

### Model B (strategy and overfitting risk)
- Single 30d cohort: results are in-sample. Promoting a scenario on this alone risks overfitting.
- B and C only act when vol_regime==high and futures_direction==down; if that combination was rare in the 30d window, the delta may be small or noisy.
- D is aggressive (bear/crash = shorts only); may improve in true bear periods but hurt in chop.
- Recommendation: Use this report for hypothesis generation; validate on a different 30d or walk-forward before any live change.

### Equity Skeptic
Replay shows hypothetical PnL under different direction rules. Without out-of-sample validation, do not promote. Prefer B (suppress longs) as first experiment; C/D change sign of exposure and need regime accuracy.

### Risk Officer
B reduces long exposure in crash conditions without adding short risk. C and D add short exposure; ensure sizing and risk limits are defined before any promotion. Tail loss and max_drawdown in the table should inform capital allocation.

### Innovation Officer
Run the same scenarios on a different 30d window (e.g. prior 30d) and compare. If B consistently improves or holds PnL with lower drawdown, propose a 1-week paper test with B only.

### Customer Advocate
If baseline was 'all long on crash days,' B would have blocked some of those longs; C would have flipped them to short. The table quantifies the hypothetical effect. Transparency: document which scenario (if any) is chosen for a future test and why.

### SRE
Replay is offline; no operational impact. If a scenario is promoted to config, add feature flag and kill switch; log which rule applied per trade for audit.
