# Alpaca decision snapshot (frozen, dry-run)

**UTC:** 2026-05-01T22:17:21.723075+00:00  
**Evidence TS:** `20260501_221721Z`

## Snapshot JSON (decision inputs for replay)

```json
{
  "captured_utc": "2026-05-01T22:17:21.723075+00:00",
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
    enabled: true
    # Existing equity config (no behavior change)

  wheel:
    enabled: true
    universe_source: config/universe_wheel_expanded.yaml
    universe_max_candidates: 10
    universe_min_liquidity_volume: 3000000
    universe_min_open_interest: 5000
    universe_max_spread_pct: 0.005
    universe_min_iv_proxy: 0.15
    universe_excluded_sectors:
      - Technology
      - Communication Services
    # Per-position limits are a fraction of wheel budget (25% of account). Paper: enable trading for learning.
    per_position_fraction_of_wheel_budget: 0.5   # allow up to 50% of wheel budget per CSP
    max_concurrent_positions: 5                  # allow multiple CSPs at a time for more data
    max_positions: 12                      
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
