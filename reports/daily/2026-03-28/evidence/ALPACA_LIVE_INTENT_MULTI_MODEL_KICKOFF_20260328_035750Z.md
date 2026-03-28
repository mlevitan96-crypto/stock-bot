# Alpaca live intent — multi-model kickoff (CSA / SRE / diff)

**UTC:** 2026-03-28T03:57:50Z  
**Evidence host:** repo workspace (pre-deploy)

## PASS A — CSA adversarial

| Risk | Mitigation |
|------|------------|
| Fabricated scores when trace missing | `MISSING_INTENT_BLOCKER` only; no invented components; numeric total required for `OK` or explicit blocker path |
| Synthetic repair passed as live | Audits reject `strict_backfilled`, `strict_backfill_trade_id`, `entry_intent_synthetic: true` |
| Double-learning from duplicate rows | `score_entry_decision_made_row` + `_pick_best_entry_decision_made` choose richest LIVE row per alias set |
| Kraken coupling | No Kraken imports; Alpaca-only module |

## PASS B — SRE adversarial

| Risk | Mitigation |
|------|------------|
| Silent skip | `emit_entry_decision_made` logs `entry_decision_made_emit_failed` and `emit_learning_blocker` on hard failure |
| Session / rotation | Same `run.jsonl` appender as `trade_intent`; `ts` from `jsonl_write` |
| Partial writes | Single atomic line append per event (existing pattern) |

## PASS C — Diff auditor (telemetry-only)

| Check | Result |
|-------|--------|
| `main.py` execution branch changes | None; only post-`mark_open` logging after successful `_emit_trade_intent` |
| Order routing / thresholds | Untouched |
| Strategy scoring | Untouched |

## Invariants

1. Every filled entry that emits `trade_intent(entered)` also attempts `entry_decision_made` on the same path.
2. `entry_intent_status=OK` implies contract fields present and non-synthetic.
3. Blocker rows fail audits by design.

## Acceptance criteria

- [x] LIVE rows marked `entry_intent_synthetic: false`, `entry_intent_source: live_runtime`
- [x] Strict gate enforces contract for opens ≥ `LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH`
- [x] Pytest covers OK, blocker, synthetic rejection, strict gate ARMED/BLOCKED
