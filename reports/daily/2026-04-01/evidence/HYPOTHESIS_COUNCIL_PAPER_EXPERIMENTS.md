# HYPOTHESIS_COUNCIL_PAPER_EXPERIMENTS (Phase 3)

## Sources

- `SECOND_CHANCE_PNL_EVALUATION.json`
- `PAPER_EXPERIMENT_RESULTS.json`
- `DISPLACEMENT_EXIT_EMULATOR_RESULTS.json`
- `DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json`

## Snapshot metrics (from JSON)

```json
{
  "CSA_SC_001": {
    "allowed_count": 5,
    "mean_60m_allowed_joined": -0.968325
  },
  "QUANT_CF_001": {
    "n_covered": 5705,
    "share_positive_60m": 0.570727,
    "pnl_60m_expectancy_usd": 0.405592
  },
  "QUANT_EMU_001": {
    "cells_positive": 11,
    "cells_total": 18,
    "majority_flag": true
  },
  "STRAT_SEP_001": {
    "conclusion_AB": "A) We can separate GOOD vs BAD displacement blocks with decision-time features (see top rules).",
    "n_rows": 5705
  }
}
```
