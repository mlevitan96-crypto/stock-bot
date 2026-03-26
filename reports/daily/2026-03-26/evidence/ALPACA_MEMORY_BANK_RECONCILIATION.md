# ALPACA MEMORY BANK RECONCILIATION (Phase 2)

**Mission:** ALPACA MEMORY BANK DISCOVERY, RECONCILIATION, AND INSTITUTIONALIZATION  
**Phase:** 2 — Compare MEMORY_BANK.md (frozen at Phase 0) vs ALPACA_DISCOVERED_TRUTH.md.  
**Authority:** Cursor executor. No silent reconciliation.

---

## Reconciliation table

| Section | Status | Evidence | Action Required |
|--------|--------|----------|-----------------|
| **Header version** | OUTDATED_IN_MEMORY_BANK | MEMORY_BANK line 3: "Version: 2026-01-12 (SSH Deployment Verified)". Many sections and Alpaca features are 2026-01-20 through 2026-03-17. | Update version line to reflect current governance scope (e.g. 2026-03-17 or "Alpaca governance current") or leave as "SSH Verified" and add a separate "Alpaca governance" date. |
| **Log path env overrides** | MISSING_IN_MEMORY_BANK | Discovered: `EXIT_ATTRIBUTION_LOG_PATH`, `MASTER_TRADE_LOG_PATH` in `src/exit/exit_attribution.py` and `utils/master_trade_log.py`. MEMORY_BANK §5.5 / §7.12 state canonical paths but do not mention env overrides. | Add one sentence in §5.5 or §7.12: override via env (EXIT_ATTRIBUTION_LOG_PATH, MASTER_TRADE_LOG_PATH) for regression/isolation; default = canonical paths. |
| **Exit attribution schema version** | MISSING_IN_MEMORY_BANK | Discovered: `ATTRIBUTION_SCHEMA_VERSION = "1.0.0"` in `src/exit/exit_attribution.py`. MEMORY_BANK does not cite this constant. | Optional: add to §7.12 or §8 that exit attribution records use schema version 1.0.0 (exit_attribution.py). |
| **Trade key builder** | MISSING_IN_MEMORY_BANK | Discovered: `src/telemetry/alpaca_trade_key.build_trade_key(symbol, side, entry_ts)` used for consistent trade_id. MEMORY_BANK §5 (join keys) names `telemetry/snapshot_join_keys.py` and trade_id precedence but not alpaca_trade_key. | Optional: add one line under join/exit attribution that trade_id is built via `alpaca_trade_key.build_trade_key` for Alpaca. |
| **Project dir canonical** | OUTDATED_IN_MEMORY_BANK | MEMORY_BANK §6.3: "Project dir `/root/stock-bot` or `/root/trading-bot-current` per deployment." Discovered and ARCHITECTURE_AND_OPERATIONS: canonical is `/root/stock-bot`; diagnose_cron_and_git auto-detects both. | Prefer single canonical: `/root/stock-bot`; note "or /root/stock-bot-current if symlink/alternate" only if still in use. |
| **Retention-protected set** | ALIGNED | MEMORY_BANK §5.5 and docs/DATA_RETENTION_POLICY list same five paths. deploy_supervisor.RETENTION_PROTECTED matches. | None. |
| **Droplet SSH / config** | ALIGNED | MEMORY_BANK §6.3 and discovered: alpaca alias, 104.236.102.57, droplet_config.json, connect_timeout 30, connect_retries 5. docs/DROPLET_SSH_CONNECTIVITY.md consistent. | None. |
| **Telemetry schemas** | ALIGNED | MEMORY_BANK §7.12, §8, memory_bank/TELEMETRY_STANDARD.md and src/contracts/telemetry_schemas.py agree on required fields and direction_intel_embed. | None. |
| **Join keys and reconciler** | ALIGNED | MEMORY_BANK §5 (Snapshot→Outcome, Exit Join) and discovered: snapshot_join_keys.py, exit_join_reconciler.py, trade_id precedence. | None. |
| **Board / convergence / gate / heartbeat** | ALIGNED | MEMORY_BANK Alpaca Tier 1+2+3, convergence, promotion gate, heartbeat, E2E, Telegram match discovered scripts and state paths. | None. |
| **Truth Gate (explicit term)** | MISSING_IN_MEMORY_BANK | Mission requires "Truth Gate" enforcement. MEMORY_BANK has the rules (droplet data only, readiness, no local-only reports) but does not use the phrase "Truth Gate" as the governing label. | Add a short "Truth Gate" subsection or sentence in §3 or §5: e.g. "Truth Gate: all reports and conclusions require droplet execution and canonical data; missing data = HARD FAILURE; join coverage below threshold = HARD FAILURE." |
| **CSA/SRE veto** | ALIGNED | MEMORY_BANK and discovered: review-only, veto on MEMORY_BANK updates, veto reasons documented. | None. |
| **Alpaca data sources** | ALIGNED | MEMORY_BANK §5 (Alpaca Data Sources) and config.registry.LogFiles match: exit_attribution.jsonl, attribution.jsonl, master_trade_log.jsonl. | None. |
| **Fast-lane / edge 2000 / data ready** | ALIGNED | MEMORY_BANK describes fast-lane cron, epoch, Telegram, edge 2000 pipeline, data ready blockers; discovered matches. | None. |

---

## Summary

- **Stale for Alpaca:** Partially. Header version is old; a few clarifications (env overrides, schema version, trade_key, Truth Gate label, project dir) are missing or outdated. No Alpaca *behavior* in code violates MEMORY_BANK.
- **Classification counts:** OUTDATED_IN_MEMORY_BANK: 2. MISSING_IN_MEMORY_BANK: 4 (2 optional). ALPACA_VIOLATES_MEMORY_BANK: 0. ALIGNED: 8.
- **Action:** Phase 3 proposes minimal diffs only for agreed updates; Phase 4 CSA/SRE must approve before any edit to MEMORY_BANK.md.

---

*End of Phase 2.*
