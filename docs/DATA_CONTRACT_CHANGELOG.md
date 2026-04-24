# Data Contract Changelog (Telemetry / Data Integrity)

## Summary

Telemetry and data-integrity wiring changes. **No change to trading decisions.** Additive and backward-compatible where possible.

---

## What changed

### 1. Entry intelligence capture

- **Before:** `capture_entry_intel_telemetry` was called after `mark_open` in the fill path, using `datetime.utcnow()` for `entry_ts`, which did not match the `entry_ts` stored in position metadata. Exit could not find the entry snapshot (key mismatch).
- **After:**
  - `capture_entry_intel_telemetry` is called **inside** `mark_open` with `entry_ts=now.isoformat()` (same as metadata). So every position open (fill path) writes `intel_snapshot_entry.jsonl` and `state/position_intel_snapshots.json` with a key that exit can resolve.
  - Fill path passes `market_context` and `regime_posture` into `mark_open` for richer snapshots.
- **Readers updated:** None (additive). Governance `direction_readiness` and dashboard already read `exit_attribution`; they now get non-empty `direction_intel_embed.intel_snapshot_entry` when entry capture ran.

### 2. Exit attribution / exit event — direction_intel_embed

- **Before:** `rec["direction_intel_embed"]` and `evt["direction_intel_embed"]` were set only when `_direction_intel_embed` was truthy.
- **After:** Both records **always** carry `direction_intel_embed` (dict); empty `{}` when capture failed or no entry snapshot. Schema and readiness logic can assume the key exists.
- **Readers updated:** `direction_readiness` already checks `embed.get("intel_snapshot_entry")`; no change. Dashboard and replay can rely on key presence.

### 3. Canonical top-level fields (exit_attribution)

- **Added:** Top-level `direction`, `side`, `position_side` on every exit_attribution record (and thus available for replay/reports).
- **Source:** `context.side`, `context.position_side`, `info.direction`; normalized to `direction` (bullish/bearish/…), `side` (buy/sell), `position_side` (long/short).
- **Readers:** Replay and report generators can prefer these; legacy nesting kept for backward compatibility.

### 4. Master trade log — single-append contract

- **Before:** Multiple code paths could append to `master_trade_log.jsonl` for the same trade (entry stub + exit full record).
- **After:** `append_master_trade` uses an in-process set of appended `trade_id`s; same `trade_id` is written at most once per process.
- **Readers:** No change; consumers still see one row per trade when only exit appends, or one row per trade when guard prevents duplicate.

### 5. State hygiene — position_intel_snapshots

- **Added:** `prune_position_intel_snapshots(max_age_days=30)` in `src/intelligence/direction_intel.py`. Called at end of `capture_exit_intel_telemetry` to drop entries older than 30 days.
- **Readers:** Only `load_entry_snapshot_for_position` reads this file; pruning does not affect open positions (keyed by same `entry_ts` used at exit).

---

## What stayed compatible

- **attribution.jsonl:** Unchanged; no new writers or schema change.
- **exit_attribution.jsonl:** Additive fields only (`direction_intel_embed` always present, `direction`/`side`/`position_side` added). Existing fields and nesting unchanged.
- **exit_event.jsonl:** Additive (`direction_intel_embed` always present).
- **intel_snapshot_entry.jsonl / intel_snapshot_exit.jsonl / direction_event.jsonl:** Same schema; now populated on every open/close when capture runs.
- **Replay loaders:** Prefer canonical top-level fields when present; fallback to existing nesting.
- **Governance direction_readiness:** Logic unchanged; now receives non-empty `direction_intel_embed.intel_snapshot_entry` when entry capture ran with correct `entry_ts`.

---

## Deprecation notes

- None. Legacy fields and nesting retained; canonical fields added alongside.

---

## Files touched (implementation)

- `main.py`: entry capture in `mark_open`; exit `direction_intel_embed` always set; canonical fields on exit; fill path passes `market_context`/`regime_posture` to `mark_open`.
- `src/intelligence/direction_intel.py`: `prune_position_intel_snapshots()`; call from `capture_exit_intel_telemetry`.
- `utils/master_trade_log.py`: in-process single-append guard by `trade_id`.

---

*Generated as part of data-integrity orchestration. See reports/audit/DATA_INTEGRITY_PLAN.md and reports/audit/DATA_INTEGRITY_PROOF.md.*
