# Weight Adjustment Plan v2 (Phase 6 — Synthesis)

## Top EDGE_POSITIVE (robust across models)


## Top EDGE_NEGATIVE


## Minimal reversible adjustments (only where all models agree)

Use env multipliers (default 1.0); apply only if adversarial review does not flag as noise:

- **UW_WEIGHT_MULTIPLIER**: 1.0 (increase to 1.1 if uw is top EDGE_POSITIVE and n sufficient).
- **REGIME_WEIGHT_MULTIPLIER**: 1.0 (increase to 1.1 if regime_macro is top EDGE_POSITIVE).
- **FLOW_WEIGHT_MULTIPLIER**: 1.0 (increase if flow/options_flow is top EDGE_POSITIVE).

After applying, restart paper with these env vars and re-run Phase 8.
