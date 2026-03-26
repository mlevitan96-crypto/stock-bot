# Alpaca Data Surface Inventory (SRE)

**Authority:** [MEMORY_BANK.md](../../MEMORY_BANK.md), [memory_bank/TELEMETRY_STANDARD.md](../../memory_bank/TELEMETRY_STANDARD.md)  
**Environment:** Droplet `/root/stock-bot`  
**Evidence:** `scripts/audit/collect_trade_data_inventory_on_droplet.py`, `wc -l`, `scripts/audit/alpaca_data_readiness_droplet_scan.py`  
**UTC:** 2026-03-20T00:08Z · **deployed_commit:** `28abc2a33e365caa58736b99a175ae360f9d1447`

---

## 1. Unified / lifecycle streams

| Source | Path | Role | Schema / version |
|--------|------|------|-------------------|
| Exit attribution (closed-trade v2) | `logs/exit_attribution.jsonl` | **Canonical closed-trade PnL + exit intel** | `attribution_schema_version` on record; exit components per MEMORY_BANK §5.5 |
| Entry/close attribution | `logs/attribution.jsonl` | Entry + closed `type=attribution` rows; strategy_id | Per TELEMETRY_STANDARD §2.1 |
| Master trade log | `logs/master_trade_log.jsonl` | Full lifecycle, scores, snapshots | One row per trade; `source` distinguishes lineage |
| Unified Alpaca emits | `logs/alpaca_unified_events.jsonl` | Optional unified entry/exit stream | Per `src/telemetry/alpaca_attribution_emitter.py` / ALPACA_TELEMETRY_CONTRACT |
| Alpaca-specific JSONL | `logs/alpaca_entry_attribution.jsonl`, `logs/alpaca_exit_attribution.jsonl` | Narrow Alpaca attribution schema | `schema_version` on record |

**Droplet line counts (observed):**

| Path | Lines | Notes |
|------|-------|--------|
| `logs/exit_attribution.jsonl` | 2,209 | Primary closed-trade audit surface |
| `logs/attribution.jsonl` | 2,465 | Includes `open_*` / `close_*` trade_id families |
| `logs/master_trade_log.jsonl` | 2,834 | Includes open + closed |
| `logs/alpaca_unified_events.jsonl` | 233 | Growing; partial vs exit_attribution volume |
| `logs/alpaca_entry_attribution.jsonl` | 233 | Matches unified emit cadence |
| `logs/alpaca_exit_attribution.jsonl` | 0 | Emitter path not populated |
| `logs/exit_event.jsonl` | 0 | TELEMETRY_STANDARD path; empty on droplet |
| `logs/signal_context.jsonl` | 0 | Optional deep context |

---

## 2. Signal attribution & snapshots

| Source | Path | Role |
|--------|------|------|
| Signal snapshots | `logs/signal_snapshots.jsonl` | Per lifecycle moment; join via `telemetry/snapshot_join_keys.py` |
| Direction events | `logs/direction_event.jsonl` | Entry/exit direction stream |
| Intel snapshots | `logs/intel_snapshot_entry.jsonl`, `logs/intel_snapshot_exit.jsonl` | Per TELEMETRY_STANDARD §1 |

**Droplet (observed):** `logs/signal_snapshots.jsonl` **2,088** lines; `logs/direction_event.jsonl` **3,330** lines.

---

## 3. Ledger, positions, governance

| Source | Path | Role |
|--------|------|------|
| Blocked trades | `state/blocked_trades.jsonl` | Blocks + intel linkage |
| Governance experiment (Alpaca) | `state/governance_experiment_1_hypothesis_ledger_alpaca.json` | Hypothesis tagging |
| Fast lane | `state/fast_lane_experiment/`, `logs/fast_lane_shadow.log` | Shadow experiments; cycle ledger |

**Droplet (observed):** `state/blocked_trades.jsonl` **6,341** lines; `logs/fast_lane_shadow.log` **1,012** lines.

---

## 4. Retention & cadence

| Topic | Policy |
|-------|--------|
| **Retention (protected)** | Append-only; **no truncate/rotate** on `exit_attribution`, `attribution`, `master_trade_log`, `blocked_trades`, `exit_decision_trace` per [docs/DATA_RETENTION_POLICY.md](../../docs/DATA_RETENTION_POLICY.md) — target **≥30 days** calendar history |
| **Update cadence** | **Continuous** during sessions (append on events); EOD bundles aggregate from same roots (MEMORY_BANK §5.5 / EOD flow) |
| **Schema versioning** | Additive changes; validators in `src/contracts/telemetry_schemas.py`; telemetry changelog `memory_bank/TELEMETRY_CHANGELOG.md` |

---

## 5. Join keys (contract)

| Key | Use |
|-----|-----|
| **`trade_id`** | `open_*` / `close_*` (attribution) vs **`live:SYMBOL:entry_ts`** (master_trade_log, stable id in `main.py`) |
| **Canonical `live:…` key** | **Second-precision** UTC: `src/telemetry/alpaca_trade_key.normalize_time` + `live:{SYMBOL}:{ts}` — used for cross-log matching when timestamps align |
| **Surrogate** | `telemetry/snapshot_join_keys.build_exit_join_key` — position_id preferred, then `live:`, then symbol + rounded time bucket |
| **timing_id** | Not a separate column; use **`trade_id`** or **`decision_id`** where present on exit rows |

**Important:** Raw `trade_id` strings **do not** match between `exit_attribution` (mostly `open_*`) and `master_trade_log` (mostly `live:*`). Cross-log joins must use **normalized `live:SYMBOL:entry_ts`** (or reconciler tooling), not raw string equality.

---

## 6. Shadow / diagnostic

| Source | Path |
|--------|------|
| Shadow snapshots | `logs/signal_snapshots_shadow_<DATE>.jsonl` (per profile) |
| Fast lane shadow | `logs/fast_lane_shadow.log` |

---

*End of inventory.*
