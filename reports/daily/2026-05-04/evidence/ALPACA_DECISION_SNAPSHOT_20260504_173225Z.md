# Alpaca decision snapshot (frozen, dry-run)

**UTC:** 2026-05-04T17:32:25.505728+00:00  
**Evidence TS:** `20260504_173225Z`

## Snapshot JSON (decision inputs for replay)

```json
{
  "captured_utc": "2026-05-04T17:32:25.505728+00:00",
  "symbol": "TESTPATH",
  "reference_bid_ask_mid": 100.25,
  "indicator_stub_atr14": 1.05,
  "indicator_stub_rsi14": 52.3,
  "regime_label": "mixed",
  "policy_config_note": "Frozen read-only snippets from repo config below; not live market feed."
}
```

## Policy / config excerpts (read-only)

### strategies.yaml (prefix)

```
# Multi-strategy configuration.
# Both strategies share: repo, droplet, UW, cron, logging.
# All orders/logs/telemetry are tagged with strategy_id.

# Fixed strategy capital partitioning (authoritative). No strategy may consume the other's capital.
capital_allocation:
  mode: fixed
  strategies:
    wheel:
      allocation_pct: 25
      min_free_cash_pct: 0
    equity:
      allocation_pct: 75
      min_free_cash_pct: 0

strategies:
  equity:
    enabled: false
    # Wheel-only mode: legacy equity run_once path disabled in main run_all_strategies.

  wheel:
    enabled: true
    # Mid-cap wheel universe ($10–$50 band); see config/wheel_universe.yaml
    universe_source: config/wheel_universe.yaml
    universe_max_candidates: 10
    universe_min_liquidity_volume: 1500000
    universe_min_open_interest: 5000
    universe_max_spread_pct: 0.005
    universe_min_iv_proxy: 0.15
    # Mid-cap pivot: do not blanket-exclude Technology / Comm Services (names like PLTR, T, SNAP).
    # Sector concentration remains enforced via risk.max_sector_notional_fraction.
    universe_excluded_sectors: []
    # Per-position fraction of wheel slice (~25% of equity). ~0.52 supports ~$60/share CSP collater
```

### strategy_governance.json (prefix)

```
{
  "strategies": {
    "EQUITY": {
      "position_cap": 25,
      "capital_fraction": 1.0,
      "displacement_allowed": true,
      "can_displace": ["EQUITY"],
      "exit_policy": "equity_exit_v2",
      "promotion_metric": "regime_conditional_expectancy"
    }
  }
}

```

## Isolation

- No broker calls. No `main.py` engine. Snapshot is for documentation + replay inputs only.
