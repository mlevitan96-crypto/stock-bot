# Integrity arm root cause — `arm_epoch_utc` null (historical) vs current state

## `session_anchor_et` (current ET session)

**2026-04-01** (droplet `TZ=America/New_York date` in `ALPACA_INTEGRITY_CLOSURE_CONTEXT.md` addendum path).

## Production entrypoint that calls arming

- **systemd:** `alpaca-telegram-integrity.timer` → `alpaca-telegram-integrity.service` → `scripts/run_alpaca_telegram_integrity_cycle.py` → `telemetry/alpaca_telegram_integrity/runner_core.py::run_integrity_cycle`.
- **Arming call:** `update_integrity_arm_state(root, anchor_et, cp_ok)` when `milestone_counting_basis == "integrity_armed"` (`runner_core.py` ~336–338).

## Exact boolean gate (`cp_ok`)

Implemented in `_checkpoint_100_integrity_ok` (`runner_core.py` ~124–147):

| Condition | Effect if false |
|-----------|-----------------|
| Coverage path exists | `missing_coverage_artifact` |
| `cov.age_hours <= warehouse_coverage_file_max_age_hours` | `coverage_artifact_stale` |
| `cov.data_ready_yes is True` | `DATA_READY not YES (or unknown)` |
| Coverage vs `coverage_thresholds_pct` (execution_join, fee, slippage) | reasons via `_coverage_vs_thresholds` |
| `strict["LEARNING_STATUS"] == "ARMED"` | `strict LEARNING_STATUS is not ARMED` |
| Exit tail schema (`schema_reasons` empty) | e.g. missing required fields in tail |

`update_integrity_arm_state` sets `arm_epoch_utc` only when **`precheck_ok` (`cp_ok`) is true** and anchor matches (`milestone.py` ~75–78).

## Did integrity cycle run after strict became ARMED (session scope)?

**Yes — timer enabled** (`ALPACA_INTEGRITY_CLOSURE_CONTEXT.md` timers table: `alpaca-telegram-integrity.timer` active).  
Dry-run capture (`ALPACA_INTEGRITY_CYCLE_DRYRUN_POSTFIX.json`) shows `checkpoint_100_precheck_ok: true` and populated `milestone_integrity_arm.arm_epoch_utc`.

## Prior blocker (evidence-consistent narrative)

Earlier missions documented **`DATA_READY: NO`** / stale coverage and **`cp_ok: false`**, so `arm_epoch_utc` stayed `null`. Fresh warehouse output (`ALPACA_COVERAGE_BASELINE.md`, `ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1926.md`) shows **`DATA_READY: YES`** with thresholds at 100%, satisfying the parser and precheck.

### Wiring gap closed in repo (commit `e8133504`)

`load_latest_coverage` previously only scanned `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md`, while `parse_coverage_smoke_check.py` also scanned `reports/daily/**`. **`warehouse_summary._latest_coverage_file`** now includes `daily/**/` (parity with smoke check), reducing “unknown / missing” coverage when the newest artifact lives under `reports/daily/`.

## Strict semantics: two evaluations

| Caller | `open_ts_epoch` | Purpose |
|--------|------------------|---------|
| Integrity cycle `checks.run_strict_completeness` | `None` → **today’s US RTH open** (`alpaca_strict_completeness_gate.evaluate_completeness`) | Checkpoint / Telegram precheck |
| `export_strict_quant_edge_review_cohort.py` (default) | **`STRICT_EPOCH_START`** | Era / board cohort export |

So **`ALPACA_STRICT_BASELINE.json`** can show **BLOCKED** while integrity strict shows **ARMED** — not a logic bug; different cohort floors. Evidence: `ALPACA_STRICT_BASELINE.json` vs `ALPACA_INTEGRITY_CYCLE_DRYRUN_POSTFIX.json` `strict` block.

## Code pointers

- `_checkpoint_100_integrity_ok`: `telemetry/alpaca_telegram_integrity/runner_core.py`
- `update_integrity_arm_state`: `telemetry/alpaca_telegram_integrity/milestone.py`
- `open_ts` when `open_ts_epoch is None`: `telemetry/alpaca_strict_completeness_gate.py` (~206)
