# Telemetry Changelog (append-only)

Contract changes, new truth roots, and deprecations. See `TELEMETRY_STANDARD.md` for current contract.

---

## 2026-03-30 — FULL ENGINE & DATA REPAIR (Alpaca droplet)

- **Risk:** `risk_management.sanitize_peak_equity_vs_broker()` rebases `state/peak_equity.json` when stored peak exceeds live equity × `PEAK_EQUITY_SANITY_MAX_RATIO` (default 1.28); extra logging before `max_drawdown_exceeded` freeze.
- **Ops scripts:** `scripts/reset_peak_equity_to_broker.py` (`--dry-run` / `--apply`), `scripts/clear_drawdown_governor_freeze.py`, `scripts/repair/alpaca_full_repair_snapshot.py`, `scripts/repair/alpaca_controlled_liquidation.py`, `scripts/repair/repair_position_metadata_from_logs.py`, `scripts/repair/alpaca_full_repair_orchestrator.py`.
- **Governor freezes:** `monitoring_guards.check_freeze_state` and `failure_point_monitor` treat dict-shaped freezes with `active: true` as blocking (parity with `risk_management.freeze_trading`).
- **Exits:** `V2_EXIT_SCORE_THRESHOLD` env (default 0.80) gates v2 exit promotion in `main.py`.
- **Recovery:** `utils.entry_score_recovery` falls back to last `composite_calculated` per symbol in `logs/scoring_flow.jsonl`.
- **Dashboard:** `/api/positions` rows include `metadata_instrumented`, `metadata_reconciled_repair_only`, `metadata_gap_flags`; composite fallback uses `compute_composite_score_v2`.
- **Sample env:** `deploy/alpaca_post_repair.env.sample` for optional paper tuning (not auto-sourced).
- **Rollback:** See `reports/daily/<ET>/evidence/ALPACA_FULL_REPAIR_ROLLBACK_<TS>.md` from orchestrator run.
- **Scope:** Alpaca venue; repair/tuning only — no new strategies or signals.

---

## 2026-03-30 — Liquidation script: SDK `close_position` parity + flat verification

- **Fixed:** `scripts/repair/alpaca_controlled_liquidation.py` — `TypeError` fallback when `REST.close_position(..., cancel_orders=True)` is unsupported (older `alpaca_trade_api` on droplet); pre-close `cancel_all_orders()`; poll `list_positions` after closes; optional **second** close wave on any remaining symbols after the first poll loop; **do not** wipe `position_metadata.json` unless flat; exit code **3** if not flat; JSON stdout includes `positions_after`, `flat`.
- **Orchestrator:** liquidation step uses non-fatal exit code — peak reset, freeze clear, metadata repair, and evidence MDs still run; `ALPACA_RISK_PEAK_EQUITY_REPAIR_*` records liquidation subprocess exit code.
- **Doc:** `MEMORY_BANK.md` Alpaca repair bullet documents SDK behavior and **stop `stock-bot` before liquidation** so the trading loop cannot re-open positions mid-reset.

---

## 2026-03-30 — Milestone counting floor: integrity_armed (Alpaca)

- **Changed:** Default **`milestone_counting_basis`** in `config/alpaca_telegram_integrity.json` is **`integrity_armed`**: **100** and **250** trade counts use canonical `trade_key` only for exits **on or after** the first cycle in the ET session anchor where the **100-trade pre-check** passes (DATA_READY + coverage + strict ARMED + exit tail probe). Until armed, displayed count is **0** even if exits exist since 09:30 ET.
- **State:** `state/alpaca_milestone_integrity_arm.json` (`session_anchor_et`, `arm_epoch_utc`, `armed_at_utc_iso`).
- **Rollback:** Set `milestone_counting_basis` to **`session_open`** (prior behavior: count since US regular session open only).
- **Templates:** 100-trade checkpoint no longer prints a false “on track for 250” line when the integrity pre-check fails (including `[TEST]` sends).

---

## 2026-03-30 — 100-trade informational checkpoint (Alpaca integrity cycle)

- **Added:** Pre-send integrity gate for a **100-trade** session checkpoint (canonical `trade_key` count vs US regular session open): requires **DATA_READY YES**, coverage thresholds, fresh coverage artifact, **strict LEARNING_STATUS ARMED**, clean exit tail probe. If degraded, **one** deferred Telegram per session anchor; when green, sends **`[ALPACA] 100-TRADE CHECKPOINT`** (informational, on-track for 250 messaging).
- **State:** `state/alpaca_100trade_sent.json` (separate from `alpaca_milestone_250_state.json`).
- **CLI:** `--send-test-100trade` on `scripts/run_alpaca_telegram_integrity_cycle.py`.
- **Config:** `checkpoint_100_enabled`, `checkpoint_100_trade_count` in `config/alpaca_telegram_integrity.json`.
- **Alpaca-only;** no strategy/signal changes.

---

## 2026-03-30 — Alpaca Telegram + data integrity cycle (systemd)

- **Added:** `telemetry/alpaca_telegram_integrity/` — session-open clock (09:30 ET, weekday-aware), milestone 250 unique `trade_key` since session open, parse latest `ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md`, throttled subprocess truth warehouse during US RTH, strict `evaluate_completeness` + exit_attribution tail probe, Telegram templates, safe self-heal (mkdir; try-restart failed `alpaca-postclose-deepdive.service` only).
- **Added:** `scripts/run_alpaca_telegram_integrity_cycle.py`, `config/alpaca_telegram_integrity.json`, state files under `state/`, append log `logs/alpaca_telegram_integrity.log`.
- **Added:** `deploy/systemd/alpaca-telegram-integrity.service` + `.timer` (10 min); `scripts/install_alpaca_telegram_integrity_on_droplet.sh`; units load `.env` and `/root/.alpaca_env`.
- **Deprecated:** `scripts/notify_alpaca_trade_milestones.py` (no-op stub); `install_cron_alpaca_notifier.py` strips legacy crontab lines only; `install_alpaca_notifier_cron.sh` exits with deprecation message.
- **Changed:** `telegram_failure_detector` auto-heal milestone hook runs `run_alpaca_telegram_integrity_cycle.py --skip-warehouse --no-self-heal`; milestone freshness log prefers `alpaca_telegram_integrity.log`.
- **Scope:** Alpaca venue only; no Kraken; no strategy or signal changes.

---

## 2026-03-30 — Truth warehouse DATA_READY baseline (MEMORY_BANK)

- **Documented:** `MEMORY_BANK.md` section **1.2** — canonical Alpaca **truth warehouse** path: `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py`, droplet command, API key merge order (`ALPACA_KEY` / `ALPACA_SECRET` supported), env windows and paper vs live coverage thresholds, corporate-actions and broker REST expectations, timestamped outputs under `reports/` and `replay/`.
- **Clarified:** **`DATA_READY: YES`** (warehouse join/coverage gates) is **not** the same as **`telemetry.alpaca_strict_completeness_gate`** **`LEARNING_STATUS: READY`**; external comms must not conflate them.
- **Clarified:** Paper execution join at 100% may include **economic-closure** fallbacks; that supports attribution math, not a blanket claim that every exit matched a broker `order_id` in logs.
- **Runbook:** `docs/DATA_READY_RUNBOOK.md` links to MEMORY_BANK section 1.2 as anti-drift canon.
- **Strategy doc:** MEMORY_BANK multi-strategy section updated — **equity** active in repo; **wheel** codepaths removed (historical logs may still show `strategy_id=wheel`).
- **No schema deprecations.** Documentation and interpretation contract only.

---

## 2026-03-03 — Droplet Data Authority

- **Added:** Droplet Data Authority rule in `TELEMETRY_STANDARD.md`: droplet is the single source of truth for trade data, telemetry, attribution, backtests, replays, governance decisions.
- **Enforced:** Droplet-only validity for analysis, replay, and backtesting; local runs restricted to schema/debug only and must be labeled non-authoritative.
- **Rule:** "NO DATA REVIEW WITHOUT DROPLET EXECUTION." If droplet execution did not occur, the task is FAILED, not pending.
- **Checklist:** Data Review & Analysis Requirements added to `TELEMETRY_ADDING_CHECKLIST.md`; code enforcement via `src/governance/droplet_authority.py` guard.

---

## 2026-03-03 — Institutionalized telemetry standard

- **Added:** Memory Bank telemetry standard (`TELEMETRY_STANDARD.md`), adding checklist (`TELEMETRY_ADDING_CHECKLIST.md`), and this changelog.
- **Added:** Canonical truth roots and required fields documented; non-empty contract for `direction_intel_embed.intel_snapshot_entry` for readiness counting.
- **Added:** `scripts/audit/telemetry_integrity_gate.py`; `make telemetry_gate`; dashboard `/api/telemetry_health` and Telemetry Health visibility.
- **Added:** Droplet verification hardening (PASS/FAIL verdict, required gates).
- **No deprecations.** Additive only.

---

## 2026-03-03 — Data integrity wiring (prior session)

- **Added:** Entry capture in `mark_open` with same entry_ts as metadata; exit always sets `direction_intel_embed` (dict or {}); canonical top-level `direction`, `side`, `position_side` on exit_attribution; single-append guard for master_trade_log; prune `position_intel_snapshots.json` by 30d.
- **Ref:** `docs/DATA_CONTRACT_CHANGELOG.md`, `reports/audit/DATA_INTEGRITY_PROOF.md`.
- **No deprecations.** Legacy nesting retained.

---

*Append new entries at the top. Include date, summary, and deprecation/dual-read notes when applicable.*
