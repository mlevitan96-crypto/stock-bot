# Alpha Upgrade Implemented — 2026-01-26

**Generated:** 2026-01-26

---

## What Changed in Live

1. **Displacement policy (min hold, min delta, thesis dominance)**
   - New module: `trading/displacement_policy.py` — `evaluate_displacement(current_position, challenger_candidate, context)`.
   - Before executing displacement, we run the policy. If **blocked** (min hold, delta too small, or no thesis dominance), we do **not** displace; we log `displacement_blocked` and block the new entry.
   - Config: `DISPLACEMENT_ENABLED`, `DISPLACEMENT_MIN_HOLD_SECONDS` (20 min), `DISPLACEMENT_MIN_DELTA_SCORE` (0.75), `DISPLACEMENT_REQUIRE_THESIS_DOMINANCE`, `DISPLACEMENT_LOG_EVERY_DECISION`.
   - Every evaluate (allowed or blocked) → `logs/system_events.jsonl`: `subsystem=displacement`, `event_type=displacement_evaluated`, `details={...}`.
   - On **allowed** displacement, `close_reason` extended with `|delta=<x>|age_s=<y>|thesis=<reason>`.

2. **Contracts and shorts**
   - `reports/CONTRACT_DISPLACEMENT_CURRENT.md`: documents current displacement logic, decision path, config, logs.
   - `reports/CONTRACT_SHORTS_CURRENT.md`: documents where shorts are allowed/blocked, config, runtime check contract.

---

## What Experiments Were Added

- **Shadow experiments:** Config and schema defined (e.g. `SHADOW_EXPERIMENTS_ENABLED`, `SHADOW_EXPERIMENTS`). Implementation in `telemetry/shadow_experiments.py` is **stubbed**; full multi-variant matrix and shadow logging can be wired next.
- **Feature snapshot:** `telemetry/feature_snapshot.py` — `build_feature_snapshot(enriched_signal, market_context, regime_state)`. Ready for use in trade_intent/exit_intent logging.
- **EOD alpha diagnostic:** `reports/_daily_review_tools/generate_eod_alpha_diagnostic.py` — produces `EOD_ALPHA_DIAGNOSTIC_<DATE>.md` (headline, displacement, data availability).

---

## How to Verify

1. **Run verification script (on droplet):**
   ```bash
   python scripts/verify_alpha_upgrade.py
   ```
   - Expect **PASS** for: displacement policy present, displacement config keys, feature snapshot exists, EOD generator exists.
   - **Displacement logging** and **shadow experiments** may **FAIL** until the bot has run with the new code (e.g. no `displacement_evaluated` events yet, or shadow disabled).

2. **Run EOD alpha diagnostic:**
   ```bash
   python reports/_daily_review_tools/generate_eod_alpha_diagnostic.py --date 2026-01-26
   ```
   - Confirms `reports/EOD_ALPHA_DIAGNOSTIC_2026-01-26.md` is produced.

3. **Toggle-back displacement (if needed):**
   - Set env: `DISPLACEMENT_MIN_HOLD_SECONDS=0`, `DISPLACEMENT_MIN_DELTA_SCORE=0`, `DISPLACEMENT_REQUIRE_THESIS_DOMINANCE=false`.
   - No code removal; revert by config only.

---

## Files Changed / Added

- **Added:** `trading/__init__.py`, `trading/displacement_policy.py`
- **Added:** `reports/CONTRACT_DISPLACEMENT_CURRENT.md`, `reports/CONTRACT_SHORTS_CURRENT.md`
- **Added:** `telemetry/feature_snapshot.py`
- **Added:** `reports/_daily_review_tools/generate_eod_alpha_diagnostic.py`
- **Added:** `scripts/verify_alpha_upgrade.py`
- **Added:** `reports/ALPHA_UPGRADE_IMPLEMENTED_2026-01-26.md`
- **Modified:** `main.py` — Config (new displacement keys), displacement loop (policy evaluate + system_events logging), `execute_displacement` (policy_diagnostics, close_reason suffix)
- **Modified:** `MEMORY_BANK.md` — new §6.9 (config, logs, toggle-back, verify, EOD, displacement/variant logs)
