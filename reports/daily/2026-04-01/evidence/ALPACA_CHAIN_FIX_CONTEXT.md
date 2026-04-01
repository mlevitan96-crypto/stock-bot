# Alpaca strict chain fix — mission context (evidence)

**Droplet:** `/root/stock-bot`  
**ET session anchor (integrity cycle):** `2026-04-01`  
**Git at verification:** `1d80fd43660118e2ba8996d40561a6bcdd93af83` (see `chain_fix_mission/phase0_git_head.txt`)

## What was broken

Strict completeness was **BLOCKED** with `incomplete_trade_chain`: zero usable `entry_decision_made`, `exit_intent`, and `canonical_trade_id_resolved` rows in the primary `run.jsonl` stream for the strict cohort, and almost no `canonical_trade_id` on `orders.jsonl`. Root-cause class: **A** — chain emitters were gated such that strict runlog events did not append in production (`PHASE2_TELEMETRY_ENABLED` off path); forward trades still had exit truth in `exit_attribution.jsonl`.

## What we changed (already on `main` before this run)

- `strict_runlog_effective()` / `STRICT_RUNLOG_TELEMETRY_ENABLED` so strict runlog emits without requiring Phase 2.
- Startup `system_events` banner (`telemetry_chain` / `startup_banner`) with effective flags and `run_jsonl_abspath`.
- Additive `scripts/audit/strict_chain_historical_backfill.py` to repair historical strict joins from `exit_attribution.jsonl` into `strict_backfill_*.jsonl` (no primary log mutation).

## Droplet actions (this verification)

1. `git pull origin main` (resolved untracked conflict by repo supplying tracked `reports/daily/2026-04-01/evidence/*` from upstream).
2. Strict audit **before** backfill → `ALPACA_STRICT_BASELINE.json` (also under `chain_fix_mission/`).
3. `systemctl restart stock-bot`.
4. Confirmed `startup_banner` in `logs/system_events.jsonl` with `strict_runlog_effective: true`.
5. `python3 scripts/audit/strict_chain_historical_backfill.py --root /root/stock-bot` → `backfill_count 341 applied`.
6. Strict audit **after** → `ALPACA_STRICT_AFTER_FIX.json`.
7. Truth warehouse: `python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --root /root/stock-bot --days 90 --max-compute`.
8. `parse_coverage_smoke_check.py` → JSON in `chain_fix_mission/ALPACA_COVERAGE_PARSE_AFTER.json`.
9. Integrity cycle dry-run (full and skip-warehouse) → JSON artifacts under `chain_fix_mission/`.

## Phase 0 raw captures

Under `chain_fix_mission/`: `phase0_*`, `phase0_systemctl_stock_bot.txt`, `phase0_ps_aux.txt`, `phase0_journal_stock_bot_tail600.txt`.

## Operational note (SRE)

`journalctl` showed `evaluate_exits` errors (`TypeError: 'str' object is not callable`) around scale-out persistence. A follow-up **defensive** guard was added in `main.py` to skip non-dict `opens` info (separate commit after chain verification).
