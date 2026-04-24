# ALPACA PnL LINEAGE MAP CHECK

- schema_version: `1.0.0`
- fields: **38**
- summary: `RESOLVED=38` `MOVED=0` `MISSING=0`

| field | emitter | persistence | overall |
|-------|---------|-------------|--------|
| `score` | RESOLVED: def _emit_trade_intent found | RESOLVED: logs/run.jsonl:file | **RESOLVED** |
| `entry_score` | RESOLVED: def log_attribution found | RESOLVED: logs/attribution.jsonl:file; state/position_metadata.json:file | **RESOLVED** |
| `final_decision_primary_reason` | RESOLVED: def _emit_trade_intent found | RESOLVED: logs/run.jsonl:file | **RESOLVED** |
| `blocked_reason` | RESOLVED: def _emit_trade_intent_blocked found | RESOLVED: logs/run.jsonl:file | **RESOLVED** |
| `market_regime` | RESOLVED: method submit_entry present | RESOLVED: logs/orders.jsonl:file; logs/attribution.jsonl:file | **RESOLVED** |
| `regime` | RESOLVED: def log_attribution found | RESOLVED: logs/attribution.jsonl:file | **RESOLVED** |
| `variant_id` | RESOLVED: def build_exit_attribution_record found | RESOLVED: logs/exit_attribution.jsonl:file | **RESOLVED** |
| `strategy_id` | RESOLVED: def jsonl_write found | RESOLVED: logs/:dir_writable | **RESOLVED** |
| `attribution_components` | RESOLVED: def log_attribution found | RESOLVED: logs/attribution.jsonl:file | **RESOLVED** |
| `decision_event_id` | RESOLVED: def _emit_trade_intent found | RESOLVED: logs/run.jsonl:file | **RESOLVED** |
| `canonical_trade_id` | RESOLVED: def _emit_trade_intent found | RESOLVED: logs/run.jsonl:file; state/position_metadata.json:file | **RESOLVED** |
| `trade_key` | RESOLVED: def build_trade_key found | RESOLVED: logs/run.jsonl:file | **RESOLVED** |
| `feature_snapshot` | RESOLVED: def _emit_trade_intent found | RESOLVED: logs/run.jsonl:file | **RESOLVED** |
| `thesis_tags` | RESOLVED: def derive_thesis_tags found | RESOLVED: logs/run.jsonl:file | **RESOLVED** |
| `ts` | RESOLVED: def jsonl_write found | RESOLVED: logs/:dir_writable | **RESOLVED** |
| `order_id` | RESOLVED: external_broker_sdk | RESOLVED: logs/orders.jsonl:file; broker_declared | **RESOLVED** |
| `client_order_id` | RESOLVED: method _submit_order_guarded present | RESOLVED: broker_declared; logs/orders.jsonl:file | **RESOLVED** |
| `order_status` | RESOLVED: external_broker_sdk | RESOLVED: broker_declared; logs/orders.jsonl:file | **RESOLVED** |
| `created_at` | RESOLVED: external_broker_sdk | RESOLVED: broker_declared | **RESOLVED** |
| `filled_at` | RESOLVED: external_broker_sdk | RESOLVED: broker_declared | **RESOLVED** |
| `filled_avg_price` | RESOLVED: method check_order_filled present | RESOLVED: broker_declared; logs/orders.jsonl:file | **RESOLVED** |
| `filled_qty` | RESOLVED: external_broker_sdk | RESOLVED: broker_declared | **RESOLVED** |
| `commission` | RESOLVED: def order_row_to_normalized found | RESOLVED: broker_declared; broker_declared | **RESOLVED** |
| `symbol` | RESOLVED: def log_order found | RESOLVED: logs/orders.jsonl:file; broker_declared | **RESOLVED** |
| `side` | RESOLVED: def log_order found | RESOLVED: logs/orders.jsonl:file; broker_declared | **RESOLVED** |
| `qty` | RESOLVED: def log_order found | RESOLVED: logs/orders.jsonl:file; broker_declared | **RESOLVED** |
| `pnl` | RESOLVED: def append_exit_attribution found | RESOLVED: logs/exit_attribution.jsonl:file | **RESOLVED** |
| `pnl_pct` | RESOLVED: def build_exit_attribution_record found | RESOLVED: logs/exit_attribution.jsonl:file | **RESOLVED** |
| `entry_order_id` | RESOLVED: def log_attribution found | RESOLVED: logs/exit_attribution.jsonl:file; logs/attribution.jsonl:file | **RESOLVED** |
| `exit_order_id` | RESOLVED: def log_attribution found | RESOLVED: logs/exit_attribution.jsonl:file | **RESOLVED** |
| `unrealized_pl` | RESOLVED: def _api_positions_impl found | RESOLVED: api_declared; broker_declared | **RESOLVED** |
| `avg_entry_price` | RESOLVED: def _api_positions_impl found | RESOLVED: api_declared; logs/positions.jsonl:parent_writable | **RESOLVED** |
| `exit_reason` | RESOLVED: def build_exit_attribution_record found | RESOLVED: logs/exit_attribution.jsonl:file | **RESOLVED** |
| `v2_exit_score` | RESOLVED: def build_exit_attribution_record found | RESOLVED: logs/exit_attribution.jsonl:file | **RESOLVED** |
| `is_open` | RESOLVED: def is_market_open_now found | RESOLVED: broker_declared | **RESOLVED** |
| `next_open` | RESOLVED: external_broker_sdk | RESOLVED: broker_declared | **RESOLVED** |
| `reconcile_snapshot` | RESOLVED: def api_pnl_reconcile found | RESOLVED: api_declared; logs/pnl_reconciliation.jsonl:parent_writable | **RESOLVED** |
| `signal_context_row` | RESOLVED: substring:log_signal_context | RESOLVED: logs/signal_context.jsonl:parent_writable | **RESOLVED** |

## Legend

- **RESOLVED:** emitter symbol found in file and persistence path exists or parent writable / broker or API declared.
- **MOVED:** emitter file missing or persistence path unexpected.
- **MISSING:** def not found or required path not creatable.
