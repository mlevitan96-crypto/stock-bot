# Telemetry Changelog (append-only)

Contract changes, new truth roots, and deprecations. See `TELEMETRY_STANDARD.md` for current contract.

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
