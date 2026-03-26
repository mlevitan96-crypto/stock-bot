# PHASE 2 — Event Flow Audit (Quant + SRE)

**Timestamp:** 2026-03-26 ~16:22 UTC  
**Host:** `/root/stock-bot` on Alpaca droplet  
**Window:** Last **72 hours** (cutoff `2026-03-23T16:22:50Z` UTC)  
**Tool:** `scripts/audit/alpaca_event_flow_audit.py` (executed from `/tmp` on droplet; script added to repo in this certification).

---

## 1. Counts (authoritative files)

| Signal | Count |
|--------|------:|
| `alpaca_unified_events.jsonl` → `alpaca_entry_attribution` | 681 |
| `alpaca_unified_events.jsonl` → `alpaca_exit_attribution` (rows in window) | 252 |
| **Distinct `trade_id` with unified exit + `terminal_close`** | **252** |
| `run.jsonl` → `trade_intent` | 1,668 |
| `run.jsonl` → `trade_intent` + `decision_outcome=entered` | 455 |
| `run.jsonl` → `canonical_trade_id_resolved` | 81 |
| `run.jsonl` → `exit_intent` | 114 |
| `orders.jsonl` rows (window) | 3,996 |
| Rows with `order_id` or `type=order` (heuristic) | 3,580 |
| Rows marked filled / fill-type heuristic | 468 |
| **`exit_attribution.jsonl` closes (exit `timestamp` in window)** | **682** |

---

## 2. Ratios

| Ratio | Value | Interpretation |
|-------|-------|----------------|
| Unified terminal closes ÷ exit_attribution closes | **0.37** | **Major gap:** most closed trades in the window **do not** have a unified `alpaca_exit_attribution` with `terminal_close` in the same window-based slice. |
| Unified entry rows ÷ `trade_intent_entered` | **1.50** | More unified entries than “entered” intents (definitions differ; not 1:1 without alias resolution). |
| Filled heuristic ÷ order rows | **~0.12** | Heuristic is coarse; many rows are non-fill lifecycle events. |

---

## 3. Ten random `trade_id` traces (seed 42)

See `reports/ALPACA_EVENT_FLOW_COUNTS_20260326_1622Z.json` for full objects.

**Summary:** 2/10 had full unified entry + unified terminal + exit_attribution in the trace logic; many older opens closing in-window lacked unified terminal rows (historical emit gap) or canonical key linkage to orders in sample.

---

## 4. Machine-readable artifact

- **JSON:** `reports/ALPACA_EVENT_FLOW_COUNTS_20260326_1622Z.json`

---

## 5. Phase 2 verdict

**FAIL (data collection not homogenous):** unified terminal stream **does not** cover the same population as `exit_attribution.jsonl` over the 72h window (252 vs 682). This violates the **PERFECT DATA COLLECTION** clause **A/B** unless CSA explicitly excepts legacy/backfill.
