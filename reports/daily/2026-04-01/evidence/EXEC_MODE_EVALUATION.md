# EXEC_MODE_EVALUATION

**TEST DAY (ET):** `2026-04-01` — metrics below are **test day only**.

**Plumbing days (ET):** 2026-03-30, 2026-03-31 — validation JSON only; no optimization.

| policy | filled | fill_rate | mean_pnl | median_pnl | p05 | mdd | mean_slip/share | no_fill | opp_loss_vs_P0 |
|--------|--------|-----------|----------|------------|-----|-----|-----------------|---------|----------------|
| P0_MARKETABLE|ttl=na | 143 | 1.0 | -0.217971 | -0.07493 | -3.3 | -46.30011 | 0.00836231 | 0 | 0.0 |
| P1_PASSIVE_MID|ttl=1 | 133 | 0.93007 | -0.189605 | -0.06 | -3.94 | -46.8384 | 0.0 | 10 | -1.79045 |
| P1_PASSIVE_MID|ttl=2 | 138 | 0.965035 | -0.21625 | -0.06 | -3.94 | -46.4184 | 0.0 | 5 | 3.1705 |
| P1_PASSIVE_MID|ttl=3 | 141 | 0.986014 | -0.210113 | -0.06 | -3.24 | -46.4184 | 0.0 | 2 | 3.2775 |
| P2_PASSIVE_THEN_CROSS|ttl=1 | 143 | 1.0 | -0.21222 | -0.06 | -3.379975 | -47.1324 | 0.0100335 | 0 | 0.0 |
| P2_PASSIVE_THEN_CROSS|ttl=2 | 143 | 1.0 | -0.200166 | -0.06 | -3.24 | -46.4184 | 0.00573962 | 0 | 0.0 |
| P2_PASSIVE_THEN_CROSS|ttl=3 | 143 | 1.0 | -0.188817 | -0.06 | -3.24 | -46.4184 | 0.00236713 | 0 | 0.0 |
