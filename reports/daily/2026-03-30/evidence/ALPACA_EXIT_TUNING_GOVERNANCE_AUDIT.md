# ALPACA EXIT TUNING GOVERNANCE AUDIT

## Git commits today (ET date `2026-03-30`) touching exit-related paths

```
823dbeb0 Alpaca full engine repair: peak equity sanity, freeze parity, liquidation runbook
7b00f0f9 truth warehouse: reach DATA_READY on paper (join, fees, corp API, slip/snap)

```

- log exit code: 0

## MEMORY_BANK.md — exit tuning / env knobs

```
- **Exit tuning (conservative):** Env-only knobs — `V2_EXIT_SCORE_THRESHOLD` (default 0.80), `STALE_TRADE_EXIT_MINUTES`, `TRAILING_STOP_PCT`, optional `EXIT_PRESSURE_*`. Sample: `deploy/alpaca_post_repair.env.sample`.
```

## .cursor/ALPACA_GOVERNANCE_LAYER.md — alpaca-exit-tuning-skill

**Not present on droplet** (common: `.cursor/` is dev-only and not deployed). Operator canon lives in local repo `.cursor/ALPACA_GOVERNANCE_LAYER.md` and **MEMORY_BANK.md** below.

## memory_bank/TELEMETRY_CHANGELOG.md — governance / exit telemetry (head)

```
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

```

## Verdict logic

- **No exit-path commits today:** empty `git log` output above → PASS for "no repo changes today" (droplet working tree may still be dirty — not covered).
- **Skill requirement documented:** GOVERNANCE_LAYER table references alpaca-exit-tuning-skill.
- **Telemetry changelog:** contains recent Alpaca governance entries (see excerpt).
