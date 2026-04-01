# Strict quant edge analysis (actionable summary)

- **Generated (UTC):** 2026-04-01T18:57:48.535294+00:00
- **Root:** `/root/stock-bot`
- **open_ts_epoch:** 1774458080.0
- **LEARNING_STATUS:** ARMED
- **Strict cohort:** trades_seen=400 complete=400 incomplete=0
- **Exit rows matched:** 399 (missing exit rows for cohort ids: **0**)

## 1. PnL headline (strict cohort)

- Sum PnL (USD): **28.2933**
- Avg / median: **0.0709** / **0.18**
- Win rate: **0.5664**
- Avg hold (min): **65.99**
- Avg v2 exit score: **0.0786**

## 2. Directional truth (long vs short)

| Side | n | Sum PnL | Avg PnL | Win rate |
|------|---|---------|---------|----------|
| LONG | 279 | 28.5233 | 0.1022 | 0.5663 |
| SHORT | 120 | -0.23 | -0.0019 | 0.5667 |

## 3. Exit reason pressure (Workstream E)

| Exit reason (norm) | n | Sum PnL | Avg PnL | Win rate |
|--------------------|---|---------|---------|----------|
| signal_decay(0.84) | 28 | 16.3655 | 0.5845 | 0.75 |
| signal_decay(0.83) | 22 | 27.23 | 1.2377 | 0.8182 |
| signal_decay(0.93) | 21 | -28.4654 | -1.3555 | 0.5714 |
| signal_decay(0.85) | 20 | 27.61 | 1.3805 | 0.8 |
| signal_decay(0.92) | 19 | 13.45 | 0.7079 | 0.6316 |
| signal_decay(0.70) | 18 | 2.52 | 0.14 | 0.3889 |
| signal_decay(0.69) | 17 | 5.0067 | 0.2945 | 0.5882 |
| signal_decay(0.91) | 14 | 11.64 | 0.8314 | 0.7143 |
| signal_decay(0.63) | 13 | -4.3233 | -0.3326 | 0.3846 |
| signal_decay(0.65)+flow_reversal | 12 | -8.0333 | -0.6694 | 0.25 |
| signal_decay(0.64) | 10 | -13.9153 | -1.3915 | 0.2 |
| signal_decay(0.71) | 9 | 2.1867 | 0.243 | 0.6667 |
| signal_decay(0.94) | 8 | -13.3871 | -1.6734 | 0.25 |
| signal_decay(0.64)+flow_reversal | 8 | -1.1 | -0.1375 | 0.375 |
| signal_decay(0.90) | 8 | 0.17 | 0.0212 | 0.5 |
| signal_decay(0.87) | 7 | 3.7 | 0.5286 | 0.5714 |
| signal_decay(0.62) | 7 | -2.3068 | -0.3295 | 0.5714 |
| signal_decay(0.67) | 5 | 4.7583 | 0.9517 | 0.6 |
| signal_decay(0.86) | 5 | 1.9767 | 0.3953 | 1.0 |
| signal_decay(0.88) | 5 | -0.43 | -0.086 | 0.6 |
| signal_decay(0.89) | 5 | -3.02 | -0.604 | 0.6 |
| signal_decay(0.62)+flow_reversal | 4 | -1.03 | -0.2575 | 0.0 |
| signal_decay(0.60) | 4 | 0.93 | 0.2325 | 0.5 |
| signal_decay(0.65) | 4 | -6.73 | -1.6825 | 0.25 |
| signal_decay(0.92)+flow_reversal | 4 | 0.23 | 0.0575 | 0.75 |

## 4. Regime slices (entry / exit)

### Entry regime
| Regime | n | Sum PnL | Avg PnL |
|--------|---|---------|---------|
| mixed | 358 | 53.3925 | 0.1491 |
| unknown | 41 | -25.0992 | -0.6122 |

### Exit regime
| Regime | n | Sum PnL | Avg PnL |
|--------|---|---------|---------|
| mixed | 399 | 28.2933 | 0.0709 |

## 5. Suggested actions (heuristic — confirm with board)

1. **exit_reason / signal_decay(0.83)** — Exit reason `signal_decay(0.83)` contributes avg_pnl=1.2377 (n=22). Success review: test scale-up only if not regime-fragile.
   - Levers: `['KEEP', 'SIZE']` | confidence: **medium**
2. **exit_reason / signal_decay(0.93)** — Exit reason `signal_decay(0.93)` has avg_pnl=-1.3555 over n=21. Review v2 thresholds / time-exit vs stop mix; consider gating entries when this exit dominates.
   - Levers: `['CHANGE_EXIT', 'GATE']` | confidence: **medium**
3. **exit_reason / signal_decay(0.85)** — Exit reason `signal_decay(0.85)` contributes avg_pnl=1.3805 (n=20). Success review: test scale-up only if not regime-fragile.
   - Levers: `['KEEP', 'SIZE']` | confidence: **medium**
4. **exit_reason / signal_decay(0.65)+flow_reversal** — Exit reason `signal_decay(0.65)+flow_reversal` has avg_pnl=-0.6694 over n=12. Review v2 thresholds / time-exit vs stop mix; consider gating entries when this exit dominates.
   - Levers: `['CHANGE_EXIT', 'GATE']` | confidence: **medium**
5. **exit_reason / signal_decay(0.64)** — Exit reason `signal_decay(0.64)` has avg_pnl=-1.3915 over n=10. Review v2 thresholds / time-exit vs stop mix; consider gating entries when this exit dominates.
   - Levers: `['CHANGE_EXIT', 'GATE']` | confidence: **medium**
6. **exit_reason / signal_decay(0.94)** — Exit reason `signal_decay(0.94)` has avg_pnl=-1.6734 over n=8. Review v2 thresholds / time-exit vs stop mix; consider gating entries when this exit dominates.
   - Levers: `['CHANGE_EXIT', 'GATE']` | confidence: **medium**

## 6. Worst / best trades (PnL)

### Worst
- `NIO` pnl=-16.8 reason=signal_decay(0.93) side=LONG hold_min=30.869707016666666 id=open_NIO_2026-04-01T13:40:26.566742+00:00
- `SOFI` pnl=-13.5 reason=signal_decay(0.94) side=LONG hold_min=32.99713821666667 id=open_SOFI_2026-04-01T13:38:22.163308+00:00
- `MRNA` pnl=-12.9454 reason=signal_decay(0.93) side=LONG hold_min=30.4110567 id=open_MRNA_2026-04-01T13:40:41.159970+00:00
- `CVX` pnl=-8.71 reason=stale_alpha_cutoff(138min,-0.02%) side=LONG hold_min=139.81054241666666 id=open_CVX_2026-04-01T13:37:25.868030+00:00
- `COIN` pnl=-8.35 reason=signal_decay(0.94)+drawdown(5.0%) side=SHORT hold_min=113.48455263333334 id=open_COIN_2026-03-31T15:22:27.710142+00:00
- `SLB` pnl=-7.47 reason=signal_decay(0.68) side=LONG hold_min=60.5094187 id=open_SLB_2026-03-31T16:48:43.575840+00:00
- `TSLA` pnl=-6.86 reason=signal_decay(0.58) side=SHORT hold_min=118.4529548 id=open_TSLA_2026-03-31T14:47:20.012560+00:00
- `SOFI` pnl=-6.66 reason=signal_decay(0.65)+flow_reversal side=LONG hold_min=37.14093101666666 id=open_SOFI_2026-04-01T17:24:30.807439+00:00
- `XLE` pnl=-6.22 reason=stale_alpha_cutoff(141min,-0.02%) side=LONG hold_min=141.24556135 id=open_XLE_2026-04-01T13:35:00.556826+00:00
- `META` pnl=-6.1653 reason=signal_decay(0.64) side=LONG hold_min=32.450754583333335 id=open_META_2026-04-01T18:13:02.096467+00:00
- `XOM` pnl=-5.83 reason=stale_alpha_cutoff(139min,-0.02%) side=LONG hold_min=139.42129488333333 id=open_XOM_2026-04-01T13:37:04.521855+00:00
- `CVX` pnl=-5.79 reason=signal_decay(0.60) side=LONG hold_min=43.84876666666666 id=open_CVX_2026-03-31T17:04:53.648568+00:00

### Best
- `MRNA` pnl=10.8 reason=signal_decay(0.79)+drawdown(3.8%) side=LONG hold_min=92.55649956666666 id=open_MRNA_2026-03-31T16:16:24.796098+00:00
- `SOFI` pnl=9.62 reason=signal_decay(0.85) side=LONG hold_min=32.10728808333333 id=open_SOFI_2026-04-01T14:48:32.428287+00:00
- `MRNA` pnl=8.28 reason=signal_decay(0.91) side=SHORT hold_min=50.330908750000006 id=open_MRNA_2026-03-31T15:23:10.432329+00:00
- `META` pnl=8.17 reason=signal_decay(0.57) side=LONG hold_min=48.479392950000005 id=open_META_2026-03-31T15:57:27.072087+00:00
- `MRNA` pnl=7.74 reason=signal_decay(0.92) side=SHORT hold_min=34.178470749999995 id=open_MRNA_2026-04-01T18:10:58.231961+00:00
- `META` pnl=7.3193 reason=stale_alpha_cutoff(122min,0.01%) side=LONG hold_min=122.12483661666667 id=open_META_2026-03-31T13:36:51.116537+00:00
- `INTC` pnl=6.8 reason=signal_decay(0.94) side=LONG hold_min=31.376432116666667 id=open_INTC_2026-04-01T13:39:42.770076+00:00
- `INTC` pnl=5.2143 reason=signal_decay(0.67) side=LONG hold_min=50.15612765 id=open_INTC_2026-03-31T15:55:43.714455+00:00
- `META` pnl=5.174 reason=signal_decay(0.67) side=LONG hold_min=60.2160463 id=open_META_2026-03-31T16:50:46.492222+00:00
- `NIO` pnl=5.04 reason=signal_decay(0.64)+flow_reversal side=LONG hold_min=36.288728533333334 id=open_NIO_2026-04-01T16:43:57.320899+00:00
- `BAC` pnl=4.56 reason=signal_decay(0.60) side=LONG hold_min=76.89157780000001 id=open_BAC_2026-03-31T15:46:34.084598+00:00
- `JPM` pnl=4.48 reason=signal_decay(0.60) side=LONG hold_min=77.16141423333333 id=open_JPM_2026-03-31T15:46:23.583332+00:00

## 7. Exit v2 components (lowest avg PnL when present, n≥3)

| Component | n | Avg PnL | Sum PnL | Win rate |
|-----------|---|---------|---------|----------|
| darkpool_deterioration | 399 | 0.0709 | 28.2933 | 0.5664 |
| earnings_risk | 399 | 0.0709 | 28.2933 | 0.5664 |
| flow_deterioration | 399 | 0.0709 | 28.2933 | 0.5664 |
| overnight_flow_risk | 399 | 0.0709 | 28.2933 | 0.5664 |
| regime_shift | 399 | 0.0709 | 28.2933 | 0.5664 |
| score_deterioration | 399 | 0.0709 | 28.2933 | 0.5664 |
| sector_shift | 399 | 0.0709 | 28.2933 | 0.5664 |
| sentiment_deterioration | 399 | 0.0709 | 28.2933 | 0.5664 |
| thesis_invalidated | 399 | 0.0709 | 28.2933 | 0.5664 |
| vol_expansion | 399 | 0.0709 | 28.2933 | 0.5664 |

---
*Scope: strict cohort exit rows only. For full trade_facts / SPI / blocked opportunity, extend pipeline per docs/ALPACA_MASSIVE_QUANT_EDGE_REVIEW_FRAMEWORK.md.*
