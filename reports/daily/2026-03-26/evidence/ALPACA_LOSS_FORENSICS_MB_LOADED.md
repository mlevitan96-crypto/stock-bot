# Alpaca Loss Forensics — Memory Bank Load (Phase 0)

**Generated:** 2026-03-18 (Cursor executor)  
**Governing contract:** `MEMORY_BANK.md`

## 1. Source integrity

| Field | Value |
|-------|--------|
| **File** | `MEMORY_BANK.md` (repo root) |
| **SHA256** | `605E72546DA23BE424898C0B8BDB43AC6571064795D281E8D9C929A598F2E271` |
| **Timestamp (mtime UTC)** | `2026-03-18T15:32:23.4790124Z` |
| **MB version line** | `2026-01-12 (SSH Deployment Verified); Alpaca governance current 2026-03-17` |

## 2. Alpaca canonical paths (droplet-relative to repo root, e.g. `/root/stock-bot`)

| Purpose | Path |
|---------|------|
| Closed-trade / PnL truth | `logs/exit_attribution.jsonl` |
| Secondary closed trades | `logs/attribution.jsonl` (exclude `trade_id` starting `open_` for open positions) |
| Fallback closed | `logs/master_trade_log.jsonl` (records with `exit_ts`) |
| Unified telemetry (entry + exit emits) | `logs/alpaca_unified_events.jsonl` |
| Entry attribution stream | `logs/alpaca_entry_attribution.jsonl` |
| Blocked / gating forensics | `state/blocked_trades.jsonl` |
| Config registry keys | `LogFiles.EXIT_ATTRIBUTION`, `ATTRIBUTION`, `MASTER_TRADE_LOG` |

## 3. Join keys (canonical)

- **Prefer:** `trade_id` (e.g. `live:SYMBOL:entry_ts` per `src/telemetry/alpaca_trade_key.build_trade_key`).
- **Fallback (MB-allowed):** surrogate — symbol + rounded timestamp bucket + side + lifecycle (`telemetry/snapshot_join_keys.py`).
- **Exit join:** `telemetry/snapshot_join_keys.py`, `telemetry/exit_join_reconciler.py` (time tolerance).

## 4. Schema versions

- Exit attribution: `ATTRIBUTION_SCHEMA_VERSION` = `1.0.0` in `src/exit/exit_attribution.py`.
- Exit-intel components: required keys under `v2_exit_components` per MB (flow/score/regime deterioration, etc.).

## 5. Truth Gate rules (decision-grade analysis)

Per **MEMORY_BANK §3.4 TRUTH GATE (ALPACA / DROPLET DATA)**:

1. **Droplet execution:** All production conclusions require droplet canonical logs; no local-only production claims.
2. **Missing required data:** Missing `exit_attribution` / `master_trade_log` when needed = **HARD FAILURE** — do not proceed to promote or tune.
3. **Join coverage:** Below threshold (direction_readiness / exit-join health / this mission: **≥80%** entry-exit join on frozen set, or MB stricter 98% when asserting promotion readiness) = **HARD FAILURE** when claiming readiness.
4. **Schema:** Unversioned or mismatched required fields = **HARD FAILURE**.
5. **Frozen artifacts only** for learning/tuning (frozen trade sets / EOD bundles).
6. **Retention:** `logs/exit_attribution.jsonl`, `logs/attribution.jsonl`, `logs/master_trade_log.jsonl`, `state/blocked_trades.jsonl` are append-only protected; rotation/truncation = forensic bias risk.

## 6. This mission Truth Gate checklist

| Check | Pass criterion |
|-------|----------------|
| T1 | `logs/exit_attribution.jsonl` exists, readable, ≥1 closed exit in window |
| T2 | Unified and/or entry attribution streams readable OR attribution.jsonl joinable |
| T3 | Entry↔exit join coverage ≥ **80%** on frozen N exits (mission floor; 98% = promotion-grade per edge pipeline) |
| T4 | `trade_id` / `trade_key` normalization consistent (no mass duplicate-key collision) |
| T5 | Schema fields present for decomposition (PnL, side, exit_reason, timestamps) |
| T6 | No evidence of log truncation dropping the frozen window (line counts, service restarts per SRE) |

**HARD FAILURE** → write `reports/audit/ALPACA_LOSS_FORENSICS_JOIN_BLOCKER_<ts>.md` (or reuse join coverage doc with BLOCKER header) and stop Phases 3–11 as decision-grade.

## 7. Droplet execution record (this mission)

| Field | Value |
|-------|--------|
| **Forensics executed on** | Alpaca droplet via SSH (`scripts/run_alpaca_loss_forensics_via_droplet.py`) |
| **Truth Gate result** | **HARD FAILURE** — entry-path intel 67.55% < 80% (see `ALPACA_LOSS_FORENSICS_JOIN_BLOCKER_LATEST.md`) |
| **Artifact sync** | Reports under `reports/audit/ALPACA_LOSS_FORENSICS_*` fetched from droplet after run |

---
*READ-ONLY mission — no live/config/strategy changes.*
