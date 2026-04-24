# PAPER_EXTENSION_EVALUATION

See `PAPER_EXTENSION_EVALUATION.json` for full metrics (CF + EMU × caps off/on).

## Summary table

| Branch | total_pnl | trades | p05 | mdd | blocked | top fail codes |
|--------|-----------|--------|-----|-----|---------|----------------|
| QUANT_CF_001 baseline_caps_off | 2313.902031 | 5705 | -3.926003 | -496.669441 | 0 | — |
| QUANT_CF_001 caps_on | 113.709901 | 273 | -3.804878 | -84.413236 | 5432 | max_gross_usd:4470,max_net_usd:700,max_new_positions_per_cycle:252,max_per_symbol_usd:136 |
| QUANT_EMU_001 baseline_caps_off | 109.046631 | 5705 | -1.166619 | -196.464875 | 0 | — |
| QUANT_EMU_001 caps_on | 5.731017 | 273 | -1.969679 | -36.553671 | 5432 | max_gross_usd:4470,max_net_usd:700,max_new_positions_per_cycle:252,max_per_symbol_usd:136 |
