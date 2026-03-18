# Alpaca Telemetry Repair Log (Phase 3)

## Scope

**Allowed:** Telemetry wiring and logging only.  
**Not changed:** Order sizing, signals, thresholds, exit logic, risk gates.

## Exact code changes

### 1. `main.py`

| Change | Detail |
|--------|--------|
| **XAI / filled gate** | `entry_status == "FILLED"` → `str(entry_status).lower() == "filled"` so explainable entry logging runs on actual fills. |
| **Removed** | Inline `emit_entry_attribution(...)` block that sat inside the (previously dead) `FILLED` branch. |
| **Added** | Immediately **after** `self.executor.mark_open(...)`, load `entry_ts` from `StateFiles.POSITION_METADATA` for `symbol`, build `trade_id = open_{SYMBOL}_{entry_ts}`, `trade_key = build_trade_key(...)`, call `emit_entry_attribution(...)` with same composite/components as before. |
| **Guardrail** | On emit failure, `log_event("telemetry", "emit_entry_attribution_failed", ...)` — **warning**, does not block trading. |

### 2. New operational scripts (repo)

| Script | Purpose |
|--------|---------|
| `scripts/write_alpaca_telemetry_repair_epoch.py` | Writes `state/alpaca_telemetry_repair_epoch.json` with `repair_iso_utc` + `commit_sha` at deploy. |
| `scripts/alpaca_telemetry_forward_proof.py` | Verifies ≥50 post-epoch exits each have entry attribution by `trade_id`. Exit 1 on failure. |
| `scripts/alpaca_telemetry_inventory_droplet.py` | Droplet file inventory → `ALPACA_TELEMETRY_INVENTORY.md` |

## Append-only

No changes to `deploy_supervisor.py` rotation for protected logs.

## Schema

Emitter schema remains `src/telemetry/alpaca_attribution_schema.py` **1.2.0**. No schema break.

## Deploy steps (operator)

1. Merge/push this commit.  
2. On droplet: `git pull`, restart `stock-bot.service`.  
3. **Before or immediately after restart:** `python3 scripts/write_alpaca_telemetry_repair_epoch.py`  
4. After ≥50 closed trades post-epoch: `python3 scripts/alpaca_telemetry_forward_proof.py`  
5. Only if exit 0: update certification to DATA_READY.
