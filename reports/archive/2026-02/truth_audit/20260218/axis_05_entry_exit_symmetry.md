# Axis 5 — Entry/Exit Symmetry

## attribution.jsonl keys (sample)
```
['ts', 'type', 'trade_id', 'symbol', 'entry_score', 'exit_pnl', 'market_regime', 'stealth_boost_applied', 'pnl_usd', 'pnl_pct', 'hold_minutes', 'context', 'strategy_id']

```

## exit_attribution.jsonl keys (sample)
```
['symbol', 'timestamp', 'entry_timestamp', 'exit_reason', 'pnl', 'pnl_pct', 'entry_price', 'exit_price', 'qty', 'time_in_trade_minutes', 'entry_uw', 'exit_uw', 'entry_regime', 'exit_regime', 'entry_sector_profile', 'exit_sector_profile', 'score_deterioration', 'relative_strength_deterioration', 'v2_exit_score', 'v2_exit_components', 'replacement_candidate', 'replacement_reasoning', 'composite_version', 'exit_regime_decision', 'exit_regime_reason', 'exit_regime_context', 'mode', 'strategy', 'regime_label', 'side', 'entry_ts', 'exit_ts', '_enriched_at']

```

## Result
**PASS**