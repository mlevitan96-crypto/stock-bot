# Weight Adjustment Plan (config-only, reversible)

## Env-driven multipliers (uw_composite_v2)

| Env var | Applies to | Default | Suggested (from edge ranking) |
|---------|------------|---------|-------------------------------|
| FLOW_WEIGHT_MULTIPLIER | options_flow | 1.0 | 1.15 if flow/uw edge positive |
| UW_WEIGHT_MULTIPLIER | dark_pool, insider, whale_persistence, event_alignment | 1.0 | 1.1 if uw edge positive |
| REGIME_WEIGHT_MULTIPLIER | regime_modifier, market_tide, calendar_catalyst, temporal_motif | 1.0 | 0.9 if regime edge negative |

## Constraints

- No logic changes. No new signals.
- Range 0.5x–2x. Small first step (e.g. 1.05–1.2 for positive, 0.85–0.95 for negative).
- Revert: unset env or set to 1.0.

## Application

On droplet, restart paper with env set, e.g.:

```bash
FLOW_WEIGHT_MULTIPLIER=1.15 UW_WEIGHT_MULTIPLIER=1.1 python3 main.py
```

After iteration 1 comparison, decide KEEP / TWEAK / REVERT.
