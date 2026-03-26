# B2 Live Paper — Enable proof

**Generated (UTC):** 2026-03-06T20:35:22.321170+00:00

## Deployed commit

f4ebc22d71d0

## Evidence PAPER_MODE + B2 flag active

- **TRADING_MODE / PAPER:** True
- **FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true:** True

## .env snippet (no secrets)

```
ALPACA_BASE_URL=https://paper-api.alpaca.markets
FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true
TRADING_MODE=PAPER
```

## Health endpoint checks

- **/api/telemetry_health:** 200
- **/api/learning_readiness:** 200
