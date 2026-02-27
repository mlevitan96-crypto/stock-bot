# Signal & Exit Effectiveness Summary (Example)

Generated: Example output for Phase 5 deliverable.  
Closed trades (joined): 12

## 1. Signal effectiveness (top 15 by trade count)

| signal_id | trade_count | win_rate | avg_pnl | avg_MFE | avg_MAE | avg_giveback |
|-----------|-------------|----------|---------|---------|---------|--------------|
| uw.flow.premium | 12 | 0.5833 | 45.5 | 1.25 | 0.82 | 0.28 |
| internal.regime | 12 | 0.5 | -12.0 | None | None | None |
| exit.score_deterioration | 12 | 0.5833 | 45.5 | 1.25 | 0.82 | 0.28 |

## 2. Exit effectiveness by exit_reason_code

| exit_reason_code | frequency | avg_realized_pnl | avg_giveback | % saved_loss | % left_money |
|------------------|-----------|------------------|--------------|--------------|---------------|
| profit | 8 | 82.5 | 0.22 | 0 | 25 |
| intel_deterioration | 2 | -45.0 | 0.35 | 50 | 0 |
| stop | 2 | -62.0 | None | 100 | 0 |

## 3. Entry vs exit blame (losing trades)

- Total losing trades: 4
- % weak entry (entry_score < 3): 50.0
- % exit timing (high giveback / had MFE): 50.0

## 4. Counterfactual exit

- Hold longer would have helped: 3 trades
- Exit earlier would have saved loss: 2 trades
