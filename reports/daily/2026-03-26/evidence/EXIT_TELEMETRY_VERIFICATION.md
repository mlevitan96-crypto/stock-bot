# Exit Telemetry Verification

**Source:** `logs/exit_event.jsonl`
**Records checked:** 0
**Records with all required fields:** 0 (0.0%)

## Required fields (exit_event)

| Field | Present |
|-------|--------|
| event_type | 0/0 |
| trade_id | 0/0 |
| symbol | 0/0 |
| entry_ts | 0/0 |
| exit_ts | 0/0 |
| entry_price | 0/0 |
| exit_price | 0/0 |
| exit_reason_code | 0/0 |
| exit_components | 0/0 |
| entry_signal_snapshot | 0/0 |
| exit_signal_snapshot | 0/0 |
| entry_exit_deltas | 0/0 |
| exit_quality_metrics | 0/0 |
| regime_at_entry | 0/0 |
| regime_at_exit | 0/0 |
| uw_conviction_entry | 0/0 |
| uw_conviction_exit | 0/0 |
| composite_at_entry | 0/0 |
| composite_at_exit | 0/0 |
| composite_components_entry | 0/0 |
| composite_components_exit | 0/0 |

## Exit quality metrics (must be present)

| Key | Present |
|-----|--------|
| mfe | 0/0 |
| mae | 0/0 |
| high_water | 0/0 |
| low_water | 0/0 |
| time_in_trade_sec | 0/0 |
| giveback | 0/0 |
| saved_loss | 0/0 |
| left_money | 0/0 |

## Entry→exit deltas

| Delta | Present |
|-------|--------|
| delta_composite | 0/0 |
| delta_flow_conviction | 0/0 |
| delta_dark_pool_notional | 0/0 |
| delta_sentiment | 0/0 |
| delta_regime | 0/0 |
| delta_gamma | 0/0 |
| delta_vol | 0/0 |
| delta_iv_rank | 0/0 |
| delta_squeeze_score | 0/0 |
| delta_sector_strength | 0/0 |

## Exit components (canonical vector)

| Component | Present |
|-----------|--------|
| exit_flow_deterioration | 0/0 |
| exit_volatility_spike | 0/0 |
| exit_regime_shift | 0/0 |
| exit_sentiment_reversal | 0/0 |
| exit_gamma_collapse | 0/0 |
| exit_dark_pool_reversal | 0/0 |
| exit_insider_shift | 0/0 |
| exit_sector_rotation | 0/0 |
| exit_time_decay | 0/0 |
| exit_microstructure_noise | 0/0 |
| exit_score_deterioration | 0/0 |

**exit_attribution.jsonl lines:** 36
