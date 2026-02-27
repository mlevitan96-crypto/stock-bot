# Deprecations: Legacy truth paths → Canonical Truth Root (CTR)

**Purpose:** Map legacy paths to CTR paths; removal gate and migration notes for custom scripts.

## Legacy → CTR mapping

| Legacy path | CTR path | Removal gate |
|-------------|----------|--------------|
| `logs/exit_attribution.jsonl` | `<STOCKBOT_TRUTH_ROOT>/exits/exit_attribution.jsonl` | After G5 (mirror parity) + G6 (rollback validated) |
| `logs/exit_truth.jsonl` | `<STOCKBOT_TRUTH_ROOT>/exits/exit_truth.jsonl` | Same |
| `logs/expectancy_gate_truth.jsonl` | `<STOCKBOT_TRUTH_ROOT>/gates/expectancy.jsonl` | Same |
| `logs/signal_health.jsonl` | `<STOCKBOT_TRUTH_ROOT>/health/signal_health.jsonl` | Same |
| `logs/signal_score_breakdown.jsonl` | `<STOCKBOT_TRUTH_ROOT>/health/signal_score_breakdown.jsonl` | Same |
| `state/score_telemetry.json` | `<STOCKBOT_TRUTH_ROOT>/telemetry/score_telemetry.json` | Same |
| `logs/score_snapshot.jsonl` | `<STOCKBOT_TRUTH_ROOT>/telemetry/score_snapshot.jsonl` | Same |

Default `STOCKBOT_TRUTH_ROOT`: `/var/lib/stock-bot/truth` (override via env).

## Removal date / gate

- **No removal of legacy paths in Phase 1 or Phase 2.** Legacy writes continue until promotion gates pass (G1–G6).
- **After gates pass:** Set `TRUTH_ROUTER_MIRROR_LEGACY=0` to stop dual-write. Legacy paths will no longer be updated; readers must use CTR (contract already points to CTR when `TRUTH_USE_CTR=1`).
- **Deletion of legacy files:** Not required; can retain for audit. If you delete, do so only after a full cycle with readers on CTR and no regressions.

## Migrating custom scripts

1. **Read from CTR:** Use `STOCKBOT_TRUTH_ROOT` (default `/var/lib/stock-bot/truth`) and the CTR paths above. Example: `"${STOCKBOT_TRUTH_ROOT}/gates/expectancy.jsonl"`.
2. **Freshness:** Check `meta/last_write_heartbeat.json` or `health/freshness.json` to ensure data is fresh before relying on it.
3. **When CTR is off:** If `TRUTH_ROUTER_ENABLED=0`, CTR streams may be missing or stale; scripts should fail loudly (no silent inference) or explicitly fall back to legacy paths during deprecation window.
