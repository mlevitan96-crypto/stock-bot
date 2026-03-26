# ALPACA DISCOVERED TRUTH (Phase 1)

**Mission:** ALPACA MEMORY BANK DISCOVERY, RECONCILIATION, AND INSTITUTIONALIZATION  
**Phase:** 1 — Alpaca system truth discovery (re-derived from code and config only; MEMORY_BANK.md not referenced for this phase).  
**Authority:** Cursor executor.

---

## 1. Droplet & Infra

### SSH access
- **Preferred:** SSH alias **alpaca** (`"host": "alpaca"`, `"use_ssh_config": true` in `droplet_config.json`). Host resolved via `~/.ssh/config` (HostName, User, IdentityFile).
- **Alternative:** Direct IP `104.236.102.57`, `use_ssh_config: false`, `key_file` set (e.g. `C:/Users/markl/.ssh/id_ed25519`).
- **Client:** `droplet_client.py` — loads `droplet_config.json`; overrides from env: `DROPLET_HOST`, `DROPLET_PORT`, `DROPLET_USER`, `DROPLET_KEY_FILE`, `DROPLET_PROJECT_DIR`, `DROPLET_CONNECT_TIMEOUT` (default 30), `DROPLET_CONNECT_RETRIES` (default 5).
- **Docs:** `docs/DROPLET_SSH_CONNECTIVITY.md`. No secrets in repo; credentials in `/root/stock-bot/.env` on droplet.

### Droplet directory and roles
- **Project dir:** `/root/stock-bot` (configurable via `project_dir` / `DROPLET_PROJECT_DIR`).
- **Orchestrator:** `deploy_supervisor.py` — starts dashboard (port 5000), `uw_flow_daemon.py`, `main.py` (trading engine). Systemd: `stock-bot.service`.
- **Entry points:** `main.py` (engine), `dashboard.py` (5000), `uw_flow_daemon.py` (UW ingestion), `heartbeat_keeper.py` (health).

### Log locations and retention
- **Retention-protected (never truncate/rotate):**  
  `deploy_supervisor.py` defines `RETENTION_PROTECTED`:
  - `logs/exit_attribution.jsonl`
  - `logs/attribution.jsonl`
  - `logs/master_trade_log.jsonl`
  - `state/blocked_trades.jsonl`
  - `reports/state/exit_decision_trace.jsonl`
- **Behavior:** `rotate_logs()` and `startup_cleanup()` glob `logs/*.jsonl`, `state/*.jsonl`, etc.; **skip** any path in `RETENTION_PROTECTED`. Rotation: max 5MB / 2000 lines (rotate), startup cleanup: 10MB / 3000 lines.
- **Policy doc:** `docs/DATA_RETENTION_POLICY.md` — 30-day target for protected files; safe cleanup via `scripts/governance/droplet_disk_cleanup.py` (must not touch protected paths).

---

## 2. Data & Telemetry

### Entry/exit emitters
- **Master trade log:** `utils/master_trade_log.py` — `append_master_trade(rec)`. Path from env `MASTER_TRADE_LOG_PATH` or default `logs/master_trade_log.jsonl`. Called from `main.py` at full close (multiple sites ~1845, ~2203, ~2452).
- **Exit attribution:** `src/exit/exit_attribution.py` — `append_exit_attribution(rec)`. Path from env `EXIT_ATTRIBUTION_LOG_PATH` or default `logs/exit_attribution.jsonl`. Enriches via `enrich_exit_row`; also calls `emit_exit_attribution` (alpaca_attribution_emitter) for telemetry.
- **Attribution (entry/closed):** `logs/attribution.jsonl` — written by engine (e.g. log_attribution in main); path from config/registry `LogFiles.ATTRIBUTION`.

### Attribution files and schemas
- **Config registry:** `config/registry.py` — `LogFiles.ATTRIBUTION`, `LogFiles.EXIT_ATTRIBUTION`, `LogFiles.MASTER_TRADE_LOG` (all under `Directories.LOGS`).
- **Schema authority:** `src/contracts/telemetry_schemas.py`:
  - **master_trade_log:** required `trade_id`, `symbol`, `entry_ts`, `exit_ts`, `source`.
  - **attribution:** required `type` = "attribution", `ts` or `timestamp`.
  - **exit_attribution:** required `symbol`, `timestamp`, `entry_timestamp`, `exit_reason`; `direction_intel_embed` if present must be dict; `intel_snapshot_entry` must be dict.
  - **exit_event:** required `trade_id`, `symbol`, `entry_ts`, `exit_ts`, `exit_reason_code`.
- **Memory bank telemetry standard:** `memory_bank/TELEMETRY_STANDARD.md` — canonical truth roots, required fields, non-empty contract for `direction_intel_embed.intel_snapshot_entry` (readiness counts only non-empty).

### Required fields actually emitted
- **Master trade:** `append_master_trade` in `utils/master_trade_log.py` writes dict with `trade_id`, `symbol`, `entry_ts`, `exit_ts`, `source` (and others); validators expect the four required keys.
- **Exit attribution:** `exit_attribution.py` and `build_exit_attribution_record` (in main or exit module) produce records with `symbol`, `timestamp`, `entry_timestamp`, `exit_reason`, and optionally `trade_id`, `direction_intel_embed`, etc. Exit attribution naming: `attribution_components[].signal_id` must start with `exit_` (per MEMORY_BANK §7.12 and audit EXIT_ATTRIBUTION_PREFIX_FIX_VERIFICATION).

### Signal granularity and adjustability
- **Composite weights:** `config/registry.py` — `COMPOSITE_WEIGHTS_V2` with version key; config-driven weights and score-shaping (optional).
- **Adjustability:** Tunable thresholds in `config/registry.py` (e.g. `MIN_EXEC_SCORE`, `MAX_CONCURRENT_POSITIONS`); overlay configs (e.g. `config/overlays/`, `config/tuning/active.json`).

---

## 3. Pipelines

### Dataset builders and freeze steps
- **EOD bundle:** `scripts/eod_bundle_manifest.py` — validates 8-file canonical bundle; `board/eod/run_stock_quant_officer_eod.py` uses repo root + canonical paths.
- **Stockbot daily:** `scripts/run_stockbot_daily_reports.py` — produces `reports/stockbot/YYYY-MM-DD/` (e.g. STOCK_EOD_SUMMARY, attribution, profitability, MEMORY_BANK_SNAPSHOT).
- **Alpaca edge 2000:** `scripts/alpaca_edge_2000_pipeline.py` — frozen dataset (up to 2000 trades from `logs/exit_attribution.jsonl`), baseline metrics, studies; output under `reports/alpaca_edge_2000_<TS>/`.
- **Fast-lane:** Reads from `logs/exit_attribution.jsonl` (or `logs/alpaca_unified_events.jsonl` if present); writes only to `state/fast_lane_experiment/`, `logs/fast_lane_shadow.log`.

### Join contracts and trade_key derivation
- **Join keys:** `telemetry/snapshot_join_keys.py` — `build_join_key()`: prefer `trade_id` (e.g. `live:SYMBOL:entry_ts`); fallback surrogate: symbol + rounded_ts_bucket + side + lifecycle_event. Exit join: position_id, trade_id, or symbol+side+entry_ts_bucket+intent_id.
- **Trade key:** `src/telemetry/alpaca_trade_key.py` — `build_trade_key(symbol, side, entry_ts)` used for consistent trade_id across attribution/exit.
- **Reconciliation:** `telemetry/exit_join_reconciler.py` — reconciles EXIT_DECISION/EXIT_FILL snapshots to master_trade_log and exit_attribution with time-window tolerance (default 5 min).
- **Reports:** `scripts/generate_exit_join_health_report.py` — loads `master_trade_log.jsonl`, `exit_attribution.jsonl`; join quality in `reports/EXIT_JOIN_HEALTH_<DATE>.md`.

### Board and audit runners
- **Tier 1/2/3:** `scripts/run_alpaca_board_review_tier1.py`, `tier2`, `tier3` — packet dirs `reports/ALPACA_TIER1_REVIEW_<ts>/`, `ALPACA_TIER2_REVIEW_<ts>/`, `ALPACA_BOARD_REVIEW_<ts>/`; state in `state/alpaca_board_review_state.json`.
- **Convergence:** `scripts/run_alpaca_convergence_check.py` → `state/alpaca_convergence_state.json`.
- **Promotion gate:** `scripts/run_alpaca_promotion_gate.py` → `state/alpaca_promotion_gate_state.json`.
- **Heartbeat:** `scripts/run_alpaca_board_review_heartbeat.py` → `state/alpaca_heartbeat_state.json`.
- **E2E audit:** `scripts/run_alpaca_e2e_audit_on_droplet.py` — Tier 1→2→3→convergence→promotion gate→heartbeat; Telegram; CSA/SRE reviews.
- **Data readiness:** `scripts/run_alpaca_data_ready_on_droplet.py` / `run_alpaca_data_ready_via_droplet.py`; blockers: SAMPLE_SIZE, JOIN_INTEGRITY, ATTRIBUTION_MISSING; Telegram only when DATA_READY.

---

## 4. Governance

### Truth Gate enforcement
- **Data source rule:** Reports must use production data from droplet; no local-only report data (ReportDataFetcher, validate_report_data).
- **Readiness:** `src/governance/direction_readiness.py` — uses `logs/exit_attribution.jsonl` (sample_size default 100); telemetry-backed count only when `direction_intel_embed.intel_snapshot_entry` is non-empty. State: `state/direction_readiness.json`.
- **Truth audit:** `scripts/run_truth_audit_on_droplet.py` — Axis 5 (entry/exit symmetry) requires attribution and exit_attribution with join keys (trade_id).
- **Data integrity:** `scripts/run_data_integrity_verification_on_droplet.py` — at least one exit_attribution record must have non-empty `direction_intel_embed.intel_snapshot_entry`.

### CSA/SRE veto points
- **CSA:** Reviews governance correctness, invariants, Truth Gate alignment; produces findings/verdicts (e.g. `reports/audit/CSA_FINDINGS_*.md`, `CSA_VERDICT_*.md`, `CSA_REVIEW_*.md`). No execution gating from artifacts.
- **SRE:** Reviews infra accuracy, append-only guarantees, operational safety; produces verdicts (e.g. `reports/audit/SRE_VERDICT_*.md`, `SRE_REVIEW_*.md`, `SRE_STATUS.json`).
- **Veto:** If either vetoes a MEMORY_BANK update, MEMORY_BANK.md must not be updated; veto reasons documented.

### Audit cadence and readiness checks
- **EOD:** 21:30 UTC weekdays; sync/audit 21:32 UTC (`scripts/run_droplet_audit_and_sync.sh`).
- **Pre-open readiness:** `scripts/run_preopen_readiness_check.py` — universe, premarket intel, regime, daemon health; must pass before session; fail if daemon critical.
- **Alpaca experiment 1:** `scripts/run_alpaca_experiment_1_daily_checks.py` (validate + break alert); daily governance: `scripts/run_alpaca_daily_governance.py` (Telegram: NO CHANGE CANDIDATE / CHANGE CANDIDATE PRESENT).
- **Fast-lane cron:** Installed via `scripts/install_fast_lane_cron_on_droplet.py` — cycle 15 min, supervisor 4h; uses `/root/.alpaca_env`, `/root/stock-bot`.

---

## 5. Schema & Versioning

### Active schema files
- **Telemetry:** `src/contracts/telemetry_schemas.py` — validators for master_trade_log, attribution, exit_attribution, exit_event, intel snapshots, direction_event.
- **Exit attribution schema version:** `src/exit/exit_attribution.py` — `ATTRIBUTION_SCHEMA_VERSION = "1.0.0"`.
- **Memory bank standard:** `memory_bank/TELEMETRY_STANDARD.md` — version 1.0.0; references `src/contracts/telemetry_schemas.py` as schema authority.

### Version identifiers
- **Composite weights:** `COMPOSITE_WEIGHTS_V2["version"]` (e.g. `2026-01-20_wt1`) in `config/registry.py`.
- **System events:** `composite_version_used` in `logs/system_events.jsonl` includes `v2_weights_version`.

### Git SHA / change_id usage
- **Alpaca experiments:** change_id = Git commit SHA (canonical); tag with `scripts/tag_profit_hypothesis_alpaca.py YES|NO`. Experiment ledger: `state/governance_experiment_1_hypothesis_ledger_alpaca.json`.
- **Reports:** Many audit and board reports include deployed_commit or run_ts; droplet runs referenced by commit and timestamp.

---

## 6. Telegram and env (Alpaca)

- **Telegram vars on droplet:** (1) `/root/.alpaca_env` — cron and manual runs; (2) `/root/stock-bot/.env` — systemd for stock-bot.service. Sync: `scripts/sync_telegram_to_dotenv.py` copies from .alpaca_env into .env.
- **DATA_READY / E2E:** Scripts source `/root/.alpaca_env` (or document sourcing) before sending Telegram; `run_alpaca_data_ready_on_droplet.sh` and `run_alpaca_e2e_audit_on_droplet.py` source env as needed.
- **Helper:** `scripts/alpaca_telegram.py` — `send_governance_telegram(...)`; on failure appends to `TELEGRAM_NOTIFICATION_LOG.md`; never raises.

---

*End of Phase 1 — Discovered truth derived solely from codebase, config, and docs (no MEMORY_BANK content used for this document).*
