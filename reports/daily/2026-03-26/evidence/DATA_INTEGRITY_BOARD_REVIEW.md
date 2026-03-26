# Data Integrity — Board Review

## Personas

### Equity Skeptic: any hidden bias or look-ahead introduced?

**No.** All changes are telemetry and wiring only. No model inputs, scores, or execution paths were changed. Entry intel is captured at position open (same moment as metadata); exit intel is captured at close. No future or post-close data is used in trading decisions. Direction readiness and dashboard consume existing logs; they do not feed back into order flow.

---

### Risk Officer: any chance telemetry changes affect decisions or sizing?

**No.** Telemetry writes are best-effort (try/except, never raise). No branch in scoring, sizing, or exit logic depends on success of `capture_entry_intel_telemetry` or `capture_exit_intel_telemetry`. Canonical fields on exit_attribution are additive; legacy fields and readers unchanged. Single-append guard only prevents duplicate writes to the same file; it does not change what is written or when.

---

### Innovation Officer: does this unlock replay experiments cleanly?

**Yes.** Single source of truth for entry/exit intel: `intel_snapshot_entry.jsonl`, `intel_snapshot_exit.jsonl`, `direction_event.jsonl`, and `direction_intel_embed` on exit_attribution/exit_event. Replay loaders can rely on `direction`, `side`, `position_side` at top level. Entry snapshot keyed by same `entry_ts` as metadata so join at exit is deterministic. Direction readiness (100 telemetry-backed trades, 90%+) gates promotion of direction-aware replay.

---

### Customer Advocate: does this improve "why did we do X" explainability?

**Yes.** Exit records always carry `direction_intel_embed` (entry + exit intel snapshots and deltas). Canonical `direction`/`side`/`position_side` make it clear whether a trade was long/short and bullish/bearish. Board and audit reports can show telemetry coverage and readiness without parsing nested legacy fields.

---

### SRE: hot-path safety, disk growth, rotation, failure modes, rollback plan

**Hot-path safety:** All new writes are in try/except; failures are swallowed so trading never blocks. `prune_position_intel_snapshots` runs at end of exit capture (once per exit); it’s a single read/filter/write of one JSON file.

**Disk growth:** `position_intel_snapshots.json` is pruned to 30d; intel logs are append-only. No rotation implemented in this change; recommend adding log rotation/size caps for `intel_snapshot_*.jsonl` and `direction_event.jsonl` in a follow-up.

**Failure modes:** If entry capture fails, exit still runs; `direction_intel_embed` will be `{}` and readiness won’t count that trade. If exit capture fails, attribution/exit_event still get `direction_intel_embed = {}`. If prune fails, state file is unchanged.

**Rollback:**

1. Revert the data-integrity PR (main.py, direction_intel.py, master_trade_log.py, plus any new scripts/docs).
2. Redeploy; no schema migration needed (additive only).
3. Old readers continue to work; new canonical fields and `direction_intel_embed` may be missing on new records until re-applied.

**Monitoring:**

- **Disk:** Monitor size of `logs/intel_snapshot_entry.jsonl`, `intel_snapshot_exit.jsonl`, `direction_event.jsonl` and `state/position_intel_snapshots.json`; alert if growth exceeds threshold.
- **Missing file:** Alert if `state/position_intel_snapshots.json` is missing and trading is active (optional; file is created on first entry capture).
- **Readiness:** Dashboard or cron already surfaces direction_readiness (X/100); alert if telemetry_trades regresses to 0 after previously > 0.

---

*Generated as part of data-integrity orchestration. See reports/audit/DATA_INTEGRITY_PLAN.md and reports/audit/DATA_INTEGRITY_PROOF.md.*
