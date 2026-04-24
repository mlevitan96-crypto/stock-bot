# Signal Path Intelligence (SPI)

Read-only analytics on executed Alpaca cohorts. **Not** forecasts, targets, or trade recommendations.
Governance: `MEMORY_BANK.md` (Alpaca Signal Path Intelligence). **SPI does not authorize behavior change.**

## Cohort

- spi_trade_rows: **2**
- profit thresholds (fractional): `[0.005, 0.01, 0.02]`
- fetch_bars_if_missing: **False** (default off; no cache writes)

## Aggregate (all signals)

```json
{
  "trade_count": 2,
  "mae_pct_hold": {
    "n": 0
  },
  "hold_minutes": {
    "n": 2,
    "min": 135.0,
    "p25": 135.0,
    "p50": 135.0,
    "p75": 180.0,
    "max": 180.0
  }
}
```

## Per-signal summary

```json
{
  "attribution_unknown": {
    "trade_count": 2,
    "hold_minutes": {
      "n": 2,
      "min": 135.0,
      "p25": 135.0,
      "p50": 135.0,
      "p75": 180.0,
      "max": 180.0
    },
    "mae_pct_hold": {
      "n": 0
    },
    "vol_ratio_path_vs_baseline": {
      "n": 0
    },
    "time_to_plus_0_5pct_min": {
      "n": 0
    },
    "path_archetype_counts": {
      "no_intraday_path_data": 2
    }
  }
}
```

## Top anomalies (descriptive only)

```json
[]
```

Distributions and descriptive buckets only; not forecasts, targets, or recommendations. SPI does not authorize behavior change (MEMORY_BANK.md).
