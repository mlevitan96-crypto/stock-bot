# Alpaca SRE repair playbooks — registry

**Timestamp:** `20260327_SRE_AUTO_REPAIR_FINAL`  
**Code:** `scripts/audit/alpaca_sre_repair_playbooks.py` (`playbook_meta`, `registry_summary`).

| Class | Preconditions | Repair (additive) | Safety | Verify |
|-------|---------------|-------------------|--------|--------|
| MISSING_ENTRY_LEG | Econ exit + terminal unified exit; `build_lines_for_trade` non-empty | `trade_intent` entered + `alpaca_entry_attribution` keyed to exit family | `strict_backfilled: true`; primary logs untouched | Strict gate matrix |
| MISSING_EXIT_INTENT | Same | `exit_intent` with ts before terminal close | Timestamp clamps in builder | `exit_intent_keyed_present` |
| JOIN_KEY_DRIFT | Unified exit supplies `trade_key` | Synthetic `orders` row + aligned intents | `id=strict_backfill_order:<trade_id>` | Orders canonical present |
| TEMPORAL_ORDER_VIOLATION | Parseable timestamps | Same rows; ordering via builder clamps | No intent after terminal close | Gate clears temporal reason when data consistent |
| EMITTER_REGRESSION | Structural probe | None in sidecar | N/A | Fix `main.py` / emitters |
| UNKNOWN | Escalation reasons or unclassified | None | Do not mutate primary | INCIDENT |

All additive writes go to `logs/strict_backfill_*.jsonl` only.
