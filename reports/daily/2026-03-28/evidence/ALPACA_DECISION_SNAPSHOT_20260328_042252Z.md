# Alpaca decision snapshot (frozen, dry-run)

**UTC:** 2026-03-28T04:22:52.149313+00:00  
**Evidence TS:** `20260328_042252Z`

## Snapshot JSON (decision inputs for replay)

```json
{
  "captured_utc": "2026-03-28T04:22:52.149313+00:00",
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
# Single-strategy configuration (equity / Alpaca). Secondary options strategy removed.
capital_allocation:
  mode: fixed
  strategies:
    equity:
      allocation_pct: 100
      min_free_cash_pct: 0

strategies:
  equity:
    enabled: true

promotion:
  min_score_to_promote: 75
  min_weeks_of_data: 4
  require_positive_realized_pnl: true
  require_drawdown_below: 0.10
  require_yield_consistency: true

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
