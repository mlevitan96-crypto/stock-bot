# Alpaca SRE failure classifier — specification

**Timestamp:** `20260327_SRE_AUTO_REPAIR_FINAL`

## Failure classes

| Class | Meaning |
|-------|---------|
| MISSING_ENTRY_LEG | `trade_intent(entered)` and/or unified entry not joinable |
| MISSING_EXIT_INTENT | `exit_intent` missing or not keyed to alias set |
| JOIN_KEY_DRIFT | Orders / `canonical_trade_id` / alias closure does not join exit `trade_key` |
| TEMPORAL_ORDER_VIOLATION | Exit timestamp before entry (strict temporal check) |
| EMITTER_REGRESSION | Code-level structural path (e.g. entered branch missing canonical in `main.py`) |
| UNKNOWN | No safe additive playbook; escalate |

## Inputs

1. **Strict gate JSON** (`evaluate_completeness` with `audit=True`): `incomplete_trade_ids_by_reason`, `reason_histogram`, `code_structural_trade_intent_no_canonical_on_entered`.
2. **Incident-style payload** (optional): sample `trade_id`s, recoverability hints.
3. **Sidecars:** presence of `strict_backfill_*` for `strict_backfill_trade_id` (enforced in repair layer, not classifier).

## Escalation reasons (→ UNKNOWN for additive layer)

`missing_unified_exit_attribution_terminal`, `missing_pnl_economic_closure`, `exit_attribution_missing_positive_exit_price`, `trade_id_schema_unexpected`.

## Classification precedence (per trade)

1. Any escalate reason → **UNKNOWN**  
2. Else `temporal_exit_before_entry` → **TEMPORAL_ORDER_VIOLATION**  
3. Else `missing_exit_intent_for_canonical_trade_id` → **MISSING_EXIT_INTENT**  
4. Else `entry_decision_not_joinable_by_canonical_trade_id` or `missing_unified_entry_attribution` → **MISSING_ENTRY_LEG**  
5. Else `no_orders_rows_with_canonical_trade_id` / `cannot_resolve_join_aliases` / `cannot_derive_trade_key` → **JOIN_KEY_DRIFT**  
6. Else → **UNKNOWN**

Implementation: `scripts/audit/alpaca_sre_repair_playbooks.py` (`classify_trade`, `reasons_for_trade_id`).
