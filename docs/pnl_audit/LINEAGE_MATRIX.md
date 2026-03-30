# PnL audit lineage matrix (human)

Machine source: docs/pnl_audit/LINEAGE_MATRIX.json.

| field_name | group | source_of_truth | emitter | persistence | join_keys |
|------------|-------|-----------------|---------|-------------|-----------|
| score | A | engine_emit | main.py:_emit_trade_intent | logs/run.jsonl | canonical_trade_id, symbol_normalized, symbol |
| entry_score | A | engine_emit | main.py:log_attribution | logs/attribution.jsonl|state/position_metadata.j... | symbol, trade_id, canonical_trade_id |
| final_decision_primary_reason | A | engine_emit | main.py:_emit_trade_intent | logs/run.jsonl | decision_event_id, canonical_trade_id |
| blocked_reason | A | engine_emit | main.py:_emit_trade_intent_blocked | logs/run.jsonl | canonical_trade_id |
| market_regime | A | engine_emit | main.py:AlpacaExecutor.submit_entry | logs/orders.jsonl|logs/attribution.jsonl | symbol, ts |
| regime | A | engine_emit | main.py:log_attribution | logs/attribution.jsonl | trade_id, symbol |
| variant_id | A | engine_emit | src/exit/exit_attribution.py:build_exit_attribution_record | logs/exit_attribution.jsonl | symbol, entry_timestamp, timestamp |
| strategy_id | A | engine_emit | main.py:jsonl_write | logs/*.jsonl (injected on append) | symbol, ts |
| attribution_components | A | engine_emit | main.py:log_attribution | logs/attribution.jsonl | symbol, trade_id |
| decision_event_id | A | engine_emit | main.py:_emit_trade_intent | logs/run.jsonl | canonical_trade_id |
| canonical_trade_id | F | engine_emit | main.py:_emit_trade_intent | logs/run.jsonl|state/position_metadata.json | symbol, trade_key |
| trade_key | F | engine_emit | src/telemetry/alpaca_trade_key.py:build_trade_key | logs/run.jsonl | canonical_trade_id |
| feature_snapshot | A | engine_emit | main.py:_emit_trade_intent | logs/run.jsonl | decision_event_id, symbol |
| thesis_tags | A | engine_emit | telemetry/thesis_tags.py:derive_thesis_tags | logs/run.jsonl | decision_event_id |
| ts | G | engine_emit | main.py:jsonl_write | logs/*.jsonl | symbol+ts_proximity |
| order_id | B | broker_rest | alpaca_trade_api.REST (submit responses) | logs/orders.jsonl|broker API | id |
| client_order_id | B | engine_emit | main.py:AlpacaExecutor._submit_order_guarded | broker REST|logs/orders.jsonl (when logged) | client_order_id |
| order_status | B | broker_rest | alpaca_trade_api.REST.get_order | broker API|logs/orders.jsonl | order_id |
| created_at | B | broker_rest | alpaca_trade_api.REST.list_orders | broker API | order_id |
| filled_at | C | broker_rest | alpaca_trade_api.REST.list_orders | broker API | order_id |
| filled_avg_price | C | broker_rest | main.py:AlpacaExecutor.check_order_filled | broker API|logs/orders.jsonl | order_id |
| filled_qty | C | broker_rest | alpaca_trade_api.REST | broker API | order_id |
| commission | D | broker_rest|deterministic_paper_zero | scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py:order_row_t... | broker REST order|activities FILL|implicit 0 pap... | order_id |
| symbol | B | engine_emit|broker_rest | main.py:log_order | logs/orders.jsonl|broker | symbol |
| side | B | engine_emit|broker_rest | main.py:log_order | logs/orders.jsonl|broker | symbol, order_id |
| qty | B | engine_emit|broker_rest | main.py:log_order | logs/orders.jsonl|broker | order_id |
| pnl | E | engine_emit|derived | src/exit/exit_attribution.py:append_exit_attribution | logs/exit_attribution.jsonl | symbol, entry_timestamp, exit_order_id |
| pnl_pct | E | derived | src/exit/exit_attribution.py:build_exit_attribution_record | logs/exit_attribution.jsonl | symbol, timestamp |
| entry_order_id | F | engine_emit | main.py:log_attribution | logs/exit_attribution.jsonl|logs/attribution.jso... | order_id |
| exit_order_id | F | engine_emit | main.py:log_attribution | logs/exit_attribution.jsonl | order_id |
| unrealized_pl | E | broker_rest | dashboard.py:_api_positions_impl | GET /api/positions JSON|broker | symbol |
| avg_entry_price | E | broker_rest | dashboard.py:_api_positions_impl | GET /api/positions|logs/positions.jsonl | symbol |
| exit_reason | A | engine_emit | src/exit/exit_attribution.py:build_exit_attribution_record | logs/exit_attribution.jsonl | symbol, timestamp |
| v2_exit_score | E | engine_emit | src/exit/exit_attribution.py:build_exit_attribution_record | logs/exit_attribution.jsonl | symbol |
| is_open | G | broker_rest | main.py:is_market_open_now | broker clock API | n/a |
| next_open | G | broker_rest | alpaca_trade_api.REST.get_clock | broker API | n/a |
| reconcile_snapshot | E | dashboard_api | dashboard.py:api_pnl_reconcile | GET /api/pnl/reconcile|logs/pnl_reconciliation.j... | date |
| signal_context_row | A | engine_emit | main.py:CONTAINS:log_signal_context | logs/signal_context.jsonl | symbol, ts |

## Row details

### score (A)

- **Join direction:** intent → order → broker fill → exit_attribution
- **Freshness:** Each trade_intent row at decision time
- **Failure modes:** Missing if PHASE2_TELEMETRY_DISABLED or emit exception

### entry_score (A)

- **Join direction:** intent/metadata → exit row
- **Freshness:** On entry attribution write; metadata on fill reconcile
- **Failure modes:** submit_entry aborts if entry_score missing/≤0

### final_decision_primary_reason (A)

- **Join direction:** intent only
- **Freshness:** When intelligence_trace provided to emit
- **Failure modes:** Absent without trace; system_event missing_intelligence_trace CRITICAL

### blocked_reason (A)

- **Join direction:** intent
- **Freshness:** Blocked intents only
- **Failure modes:** N/A for entered path

### market_regime (A)

- **Join direction:** order row → attribution
- **Freshness:** At order submit
- **Failure modes:** Abort if regime unknown

### regime (A)

- **Join direction:** attribution → exit
- **Freshness:** Entry attribution
- **Failure modes:** Logged as data_integrity if zero entry_score

### variant_id (A)

- **Join direction:** exit row
- **Freshness:** On closed trade
- **Failure modes:** Optional kwargs from caller

### strategy_id (A)

- **Join direction:** all JSONL streams when strategy context set
- **Freshness:** Per append
- **Failure modes:** Omitted if context missing

### attribution_components (A)

- **Join direction:** attribution → exit enrich
- **Freshness:** At entry fill attribution
- **Failure modes:** May be synthesized from comps dict

### decision_event_id (A)

- **Join direction:** intent anchor
- **Freshness:** Each trade_intent
- **Failure modes:** From telemetry.attribution_emit_keys.new_decision_event_id

### canonical_trade_id (F)

- **Join direction:** intent ↔ metadata ↔ orders via merge_attribution_keys
- **Freshness:** At intent; copied to metadata on fill
- **Failure modes:** learning_blocker if build_trade_key fails

### trade_key (F)

- **Join direction:** same as canonical_trade_id
- **Freshness:** trade_intent
- **Failure modes:** Alias of canonical id string

### feature_snapshot (A)

- **Join direction:** intent
- **Freshness:** trade_intent
- **Failure modes:** Large nested object

### thesis_tags (A)

- **Join direction:** intent
- **Freshness:** trade_intent
- **Failure modes:** Derived from snapshot

### ts (G)

- **Join direction:** fallback join when ids missing
- **Freshness:** Every append
- **Failure modes:** Clock skew vs broker

### order_id (B)

- **Join direction:** broker authoritative; local may omit on some fill logs
- **Freshness:** After submit; stable forever
- **Failure modes:** Local fill rows historically sparse — join via broker list_orders

### client_order_id (B)

- **Join direction:** engine → broker
- **Freshness:** Submit
- **Failure modes:** Optional None

### order_status (B)

- **Join direction:** broker → local mirror
- **Freshness:** Updated until terminal state
- **Failure modes:** Paper may show accepted vs filled naming

### created_at (B)

- **Join direction:** broker
- **Freshness:** Order creation
- **Failure modes:** Read from REST object

### filled_at (C)

- **Join direction:** fill → exit timing
- **Freshness:** When fill completes
- **Failure modes:** May be null until filled

### filled_avg_price (C)

- **Join direction:** broker truth for PnL
- **Freshness:** Post-fill
- **Failure modes:** Do not use quote for realized

### filled_qty (C)

- **Join direction:** broker
- **Freshness:** Post-fill
- **Failure modes:** Partial fills aggregate on order

### commission (D)

- **Join direction:** activities ↔ order
- **Freshness:** Post-fill
- **Failure modes:** Often absent on paper REST — use deterministic zero contract

### symbol (B)

- **Join direction:** all surfaces
- **Freshness:** Always
- **Failure modes:** Normalize to upper in exit_attribution

### side (B)

- **Join direction:** order/fill
- **Freshness:** Submit
- **Failure modes:** long/short vs buy/sell context

### qty (B)

- **Join direction:** order/fill
- **Freshness:** Submit
- **Failure modes:** String vs int in SDK

### pnl (E)

- **Join direction:** closed trade spine
- **Freshness:** On exit
- **Failure modes:** Pre-fee unless enriched

### pnl_pct (E)

- **Join direction:** exit row
- **Freshness:** On exit
- **Failure modes:** Depends on entry/exit price quality

### entry_order_id (F)

- **Join direction:** entry ↔ broker
- **Freshness:** When caller supplies
- **Failure modes:** May be null if not threaded

### exit_order_id (F)

- **Join direction:** exit ↔ broker; duplicate as order_id on row
- **Freshness:** On exit
- **Failure modes:** Truth-warehouse join uses order_id

### unrealized_pl (E)

- **Join direction:** live snapshot
- **Freshness:** Each poll
- **Failure modes:** Not a historical ledger

### avg_entry_price (E)

- **Join direction:** position snapshot
- **Freshness:** Open position
- **Failure modes:** Flat book → empty

### exit_reason (A)

- **Join direction:** exit
- **Freshness:** Close
- **Failure modes:** Normalized in main close paths

### v2_exit_score (E)

- **Join direction:** exit analytics
- **Freshness:** Exit
- **Failure modes:** V2 exit stack

### is_open (G)

- **Join direction:** session context
- **Freshness:** Real-time
- **Failure modes:** Fallback ET heuristic if API fails

### next_open (G)

- **Join direction:** session
- **Freshness:** Clock poll
- **Failure modes:** None

### reconcile_snapshot (E)

- **Join direction:** read-only audit overlay
- **Freshness:** On request
- **Failure modes:** 503 if Alpaca not connected

### signal_context_row (A)

- **Join direction:** parallel to attribution
- **Freshness:** Per decision
- **Failure modes:** Optional path
