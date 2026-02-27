# Thresholds and units

## Runtime thresholds (droplet)
- MIN_EXEC_SCORE: 2.5 (from config/registry or .env)
- Expectancy floor (score_floor): same as MIN_EXEC_SCORE in main.py expectancy gate
- Units: composite score is dimensionless (weighted sum of components); expectancy is in return units (decimal); time horizon is per-trade.

## Unit consistency
- Score and MIN_EXEC_SCORE are same scale (composite points). No percent vs dollars mismatch.
- Expectancy gate uses composite_score for score_floor_breach; entry_ev_floor is in EV units (decimal).