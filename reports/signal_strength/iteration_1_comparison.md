# Iteration 1 comparison (pre vs post weight adjustment)

## Weight changes applied
FLOW_WEIGHT_MULTIPLIER=1.15, UW_WEIGHT_MULTIPLIER=1.1

## Pre-change bucket_analysis (excerpt)
```
# Blocked-trade score bucket analysis

| bucket | n | mean_pnl_pct | win_rate | median_pnl_pct |
|--------|---|--------------|----------|----------------|
```

## Post-change bucket_analysis (excerpt)
```
# Blocked-trade score bucket analysis

| bucket | n | mean_pnl_pct | win_rate | median_pnl_pct |
|--------|---|--------------|----------|----------------|
| 0.0-0.5 | 1659 | -0.164 | 23.9% | -0.134 |
| 0.5-1.0 | 19 | -0.042 | 26.3% | -0.078 |
| 1.0-1.5 | 322 | -0.262 | 5.9% | -0.211 |
```

## Buckets 0.5-1.0, 1.0-1.5, 1.5-2.0
| bucket | pre_n | pre_mean_pnl | pre_win_rate | post_n | post_mean_pnl | post_win_rate |
|--------|-------|--------------|--------------|--------|---------------|---------------|
| 0.5-1.0 | - | - | - | 19 | -0.042 | 26.3% |
| 1.0-1.5 | - | - | - | 322 | -0.262 | 5.9% |
| 1.5-2.0 | - | - | - | - | - | - |