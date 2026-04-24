# ALPACA PnL LINEAGE — Droplet verification (SRE)

- Service user (systemctl): `root`
- Map check summary: `{'RESOLVED': 38, 'MOVED': 0, 'MISSING': 0}`
- Dashboard `/api/ping` HTTP: `401` (rc context: curl exit embedded)

## Broker REST sample (first order keys subset)

```json
{
  "id": "40fc55cc-13de-4793-b3c7-b7f61eb1a080",
  "client_order_id": "1165f7a8-eaeb-4f62-9086-c4dc67b38022",
  "created_at": "2026-03-30T21:16:01.148646927Z",
  "updated_at": "2026-03-30T21:16:01.149193477Z",
  "submitted_at": "2026-03-30T21:16:01.148646927Z",
  "filled_at": null,
  "expired_at": null,
  "canceled_at": null,
  "failed_at": null,
  "replaced_at": null,
  "replaced_by": null,
  "replaces": null,
  "asset_id": "092efc51-b66b-4355-8132-d9c3796b9a76",
  "symbol": "XOM",
  "asset_class": "us_equity",
  "notional": null,
  "qty": "1",
  "filled_qty": "0",
  "filled_avg_price": null,
  "order_class": "",
  "order_type": "market",
  "type": "market",
  "side": "buy",
  "position_intent": "buy_to_close",
  "time_in_force": "day"
}
```

## Per-field resolution (persistence + emitter)

| field | overall | persistence note | emitter note |
|-------|---------|------------------|-------------|
| `score` | **RESOLVED** | RESOLVED: logs/run.jsonl:file | RESOLVED: def _emit_trade_intent found |
| `entry_score` | **RESOLVED** | RESOLVED: logs/attribution.jsonl:file; state/position_metadata.json:file | RESOLVED: def log_attribution found |
| `final_decision_primary_reason` | **RESOLVED** | RESOLVED: logs/run.jsonl:file | RESOLVED: def _emit_trade_intent found |
| `blocked_reason` | **RESOLVED** | RESOLVED: logs/run.jsonl:file | RESOLVED: def _emit_trade_intent_blocked found |
| `market_regime` | **RESOLVED** | RESOLVED: logs/orders.jsonl:file; logs/attribution.jsonl:file | RESOLVED: method submit_entry present |
| `regime` | **RESOLVED** | RESOLVED: logs/attribution.jsonl:file | RESOLVED: def log_attribution found |
| `variant_id` | **RESOLVED** | RESOLVED: logs/exit_attribution.jsonl:file | RESOLVED: def build_exit_attribution_record found |
| `strategy_id` | **RESOLVED** | RESOLVED: logs/:dir_writable | RESOLVED: def jsonl_write found |
| `attribution_components` | **RESOLVED** | RESOLVED: logs/attribution.jsonl:file | RESOLVED: def log_attribution found |
| `decision_event_id` | **RESOLVED** | RESOLVED: logs/run.jsonl:file | RESOLVED: def _emit_trade_intent found |
| `canonical_trade_id` | **RESOLVED** | RESOLVED: logs/run.jsonl:file; state/position_metadata.json:file | RESOLVED: def _emit_trade_intent found |
| `trade_key` | **RESOLVED** | RESOLVED: logs/run.jsonl:file | RESOLVED: def build_trade_key found |
| `feature_snapshot` | **RESOLVED** | RESOLVED: logs/run.jsonl:file | RESOLVED: def _emit_trade_intent found |
| `thesis_tags` | **RESOLVED** | RESOLVED: logs/run.jsonl:file | RESOLVED: def derive_thesis_tags found |
| `ts` | **RESOLVED** | RESOLVED: logs/:dir_writable | RESOLVED: def jsonl_write found |
| `order_id` | **RESOLVED** | RESOLVED: logs/orders.jsonl:file; broker_declared | RESOLVED: external_broker_sdk |
| `client_order_id` | **RESOLVED** | RESOLVED: broker_declared; logs/orders.jsonl:file | RESOLVED: method _submit_order_guarded present |
| `order_status` | **RESOLVED** | RESOLVED: broker_declared; logs/orders.jsonl:file | RESOLVED: external_broker_sdk |
| `created_at` | **RESOLVED** | RESOLVED: broker_declared | RESOLVED: external_broker_sdk |
| `filled_at` | **RESOLVED** | RESOLVED: broker_declared | RESOLVED: external_broker_sdk |
| `filled_avg_price` | **RESOLVED** | RESOLVED: broker_declared; logs/orders.jsonl:file | RESOLVED: method check_order_filled present |
| `filled_qty` | **RESOLVED** | RESOLVED: broker_declared | RESOLVED: external_broker_sdk |
| `commission` | **RESOLVED** | RESOLVED: broker_declared; broker_declared | RESOLVED: def order_row_to_normalized found |
| `symbol` | **RESOLVED** | RESOLVED: logs/orders.jsonl:file; broker_declared | RESOLVED: def log_order found |
| `side` | **RESOLVED** | RESOLVED: logs/orders.jsonl:file; broker_declared | RESOLVED: def log_order found |
| `qty` | **RESOLVED** | RESOLVED: logs/orders.jsonl:file; broker_declared | RESOLVED: def log_order found |
| `pnl` | **RESOLVED** | RESOLVED: logs/exit_attribution.jsonl:file | RESOLVED: def append_exit_attribution found |
| `pnl_pct` | **RESOLVED** | RESOLVED: logs/exit_attribution.jsonl:file | RESOLVED: def build_exit_attribution_record found |
| `entry_order_id` | **RESOLVED** | RESOLVED: logs/exit_attribution.jsonl:file; logs/attribution.jsonl:file | RESOLVED: def log_attribution found |
| `exit_order_id` | **RESOLVED** | RESOLVED: logs/exit_attribution.jsonl:file | RESOLVED: def log_attribution found |
| `unrealized_pl` | **RESOLVED** | RESOLVED: api_declared; broker_declared | RESOLVED: def _api_positions_impl found |
| `avg_entry_price` | **RESOLVED** | RESOLVED: api_declared; logs/positions.jsonl:parent_writable | RESOLVED: def _api_positions_impl found |
| `exit_reason` | **RESOLVED** | RESOLVED: logs/exit_attribution.jsonl:file | RESOLVED: def build_exit_attribution_record found |
| `v2_exit_score` | **RESOLVED** | RESOLVED: logs/exit_attribution.jsonl:file | RESOLVED: def build_exit_attribution_record found |
| `is_open` | **RESOLVED** | RESOLVED: broker_declared | RESOLVED: def is_market_open_now found |
| `next_open` | **RESOLVED** | RESOLVED: broker_declared | RESOLVED: external_broker_sdk |
| `reconcile_snapshot` | **RESOLVED** | RESOLVED: api_declared; logs/pnl_reconciliation.jsonl:parent_writable | RESOLVED: def api_pnl_reconcile found |
| `signal_context_row` | **RESOLVED** | RESOLVED: logs/signal_context.jsonl:parent_writable | RESOLVED: substring:log_signal_context |

## File surfaces (mtime age sec, writable)

- `logs/run.jsonl` exists=True age_s=3146 writable=True
- `logs/attribution.jsonl` exists=True age_s=7807 writable=True
- `state/position_metadata.json` exists=True age_s=3451 writable=True
- `logs/orders.jsonl` exists=True age_s=7807 writable=True
- `logs/exit_attribution.jsonl` exists=True age_s=9235 writable=True
- `logs/positions.jsonl` exists=False age_s=n/a writable=True
- `logs/pnl_reconciliation.jsonl` exists=False age_s=n/a writable=True
- `logs/signal_context.jsonl` exists=False age_s=n/a writable=True
