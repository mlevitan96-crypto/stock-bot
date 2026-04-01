# Alpaca chain fix — final verdict

| Question | Answer |
|----------|--------|
| **Strict status** | **ARMED** (`ALPACA_STRICT_AFTER_FIX.json`, `--open-ts-epoch 1774458080`) |
| **If anything still blocked for milestones** | **DATA_READY: NO** — single blocker for integrity precheck / `arm_epoch_utc` (`blocked_candidate_coverage_pct` ≈ 21.66% in `ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1745.md`) |
| **Coverage DATA_READY** | **NO** — parse smoke **OK** (`parse_ok: true`, `data_ready_yes: false` in `ALPACA_COVERAGE_PARSE_AFTER_FIX.json`) |
| **Integrity armed (`arm_epoch_utc`)** | **NO** — `milestone_integrity_arm.arm_epoch_utc: null` in full dry-run JSON |
| **Milestone `unique_closed_trades` floored to 0** | **YES** — expected until integrity arms under `integrity_armed` basis |
| **Commits** | Chain telemetry + backfill: **`1d80fd43`**. Evidence bundle + `evaluate_exits` non-dict guard: tip of `main` with subject `fix: skip non-dict opens info in evaluate_exits; chain fix evidence 2026-04-01` (run `git log -1 --oneline` after `git pull`). |
| **Rerun verification** | Droplet: `git pull && sudo systemctl restart stock-bot` → `python3 scripts/alpaca_strict_completeness_gate.py --root /root/stock-bot --audit --open-ts-epoch 1774458080` → `python3 scripts/audit/strict_chain_historical_backfill.py --root /root/stock-bot` (idempotent) → warehouse mission → `parse_coverage_smoke_check.py` → `run_alpaca_telegram_integrity_cycle.py --dry-run`. |

**PASS/FAIL vs mission hard gate**

- **Strict flip to ARMED:** **PASS**
- **Integrity arm + non-zero milestone snapshot under current config:** **FAIL (explained)** — blocked solely by **DATA_READY NO** until warehouse blocked-bucket coverage meets policy.

Evidence bundle: `reports/daily/2026-04-01/evidence/` and `reports/daily/2026-04-01/evidence/chain_fix_mission/`.
