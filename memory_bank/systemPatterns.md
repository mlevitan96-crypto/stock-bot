# System Patterns (Memory Bank)

Cross-cutting architecture and data-integrity patterns for the stock-bot repo (Alpaca path emphasized).

---

## System Architecture

### Data Integrity

- **Harvester-era logs** under `logs/*.jsonl` are the primary *runtime* telemetry surface but are subject to rotation, purge, and host rebuilds. Downstream jobs must not assume a single volatile path is always populated after cold start.

- **Canonical Truth Root (CTR)**  
  The **ultimate source of truth for Alpaca terminal exits** (rich exit rows used for PnL / warehouse joins) is **not** the volatile `logs/` tree alone. Authoritative CTR path:

  - **`$STOCKBOT_TRUTH_ROOT/exits/exit_attribution.jsonl`**
  - Default when unset: **`/var/lib/stock-bot/truth/exits/exit_attribution.jsonl`**

  Production enables CTR via systemd (e.g. `TRUTH_ROUTER_ENABLED=1`, `STOCKBOT_TRUTH_ROOT=/var/lib/stock-bot/truth`). The Truth Router mirrors append-only exit rows into CTR; legacy `logs/exit_attribution.jsonl` should still be written on each close when the main process cwd and env are standard.

  **Warehouse & audit scripts must always consider CTR** when loading exit windows for `DATA_READY`, not only `logs/exit_attribution.jsonl`. Reference implementation: `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` (`load_exits_window` / `_exit_attribution_candidate_paths`).

- **Data coverage rules (truth warehouse)**  
  - Gates (execution join, fees, slippage, signal snapshot, corporate actions, UW presence, etc.) are defined in `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` and `docs/DATA_READY_RUNBOOK.md`.  
  - **Blocked-boundary coverage** compares 5-minute symbol buckets that have evaluation telemetry (score snapshots / trade intents) against buckets that have explicit block detail (blocked trades, blocked intents, or failing score_snapshot gates). A low overlap is possible in **low-volatility or low-block-volume** regimes even when execution joins are healthy.

  - **Operational waiver:** `ALPACA_TRUTH_BLOCKED_BOUNDARY_MIN_PCT` may be **temporarily** set to **`0`** via environment for the warehouse mission during **low-volatility cold starts** when evaluation buckets **legitimately** have **zero overlap** with blocked-risk events (no CPA claim that block forensics are absent—only that the strict **ratio gate** is waived for that run). This is a **temporary regime waiver**, not a permanent reduction in CPA / risk-documentation standards. Default remains **50**; document any waiver in runbooks or incident notes. Prefer restoring overlap (data path + blocked logging health) over leaving the waiver in place.

---

## Related canonical docs

- `MEMORY_BANK_ALPACA.md` §1.2 — Alpaca truth warehouse baseline and droplet command.  
- `docs/DATA_READY_RUNBOOK.md` — operator order of operations.  
- `src/infra/truth_router.py` — CTR append contract.
