# Integrity arm + coverage wiring — implementation (minimal, reversible)

## Goal

Make **`arm_epoch_utc`** set when precheck passes, and align coverage discovery with smoke checks.

## Changes (commits)

| Area | Change | Rollback |
|------|--------|----------|
| **Coverage discovery** | `telemetry/alpaca_telegram_integrity/warehouse_summary.py` — `_latest_coverage_file` also glob `reports/daily/**/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md` | Revert file; redeploy |
| **Telegram authority** | `deploy/systemd/alpaca-postclose-deepdive.service` and `telegram-failure-detector.service` — `Environment=TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1` after `EnvironmentFile` | Remove lines; `systemctl daemon-reload`; restore units from prior rev |
| **Tests** | `tests/test_alpaca_telegram_integrity.py::test_load_latest_coverage_finds_daily_subdir` | Revert test |
| **Ops helper** | `scripts/audit/collect_alpaca_integrity_closure_evidence.py` (optional re-run) | N/A |

**Main:** `e8133504` (and follow-up comment tweak if committed separately).

## Droplet apply steps (executed)

1. Resolve `git pull` conflict (untracked snapshot JSON → `/tmp`).
2. `git pull origin main` → **`e8133504`**.
3. `cp deploy/systemd/alpaca-postclose-deepdive.service /etc/systemd/system/`
4. `cp deploy/systemd/telegram-failure-detector.service /etc/systemd/system/`
5. `systemctl daemon-reload`

**No `stock-bot` restart** (constraint: live trading stability).

## Safe integrity re-run

```bash
cd /root/stock-bot && PYTHONPATH=. python3 scripts/run_alpaca_telegram_integrity_cycle.py --dry-run --skip-warehouse --no-self-heal
```

`--dry-run` suppresses Telegram HTTP; **`update_integrity_arm_state` still runs** (state write is not gated on dry-run in `runner_core`).

## Evidence

- `ALPACA_INTEGRITY_CYCLE_DRYRUN_POSTFIX.json` — `checkpoint_100_precheck_ok`, `milestone_integrity_arm`
- `ALPACA_ARM_STATE_PROOF.md`
