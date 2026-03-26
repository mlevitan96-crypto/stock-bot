# STOP-GATE 0 — Data Completeness Contract (CSA)

**Audit ID:** ALPACA TRADE DATA COLLECTION CERTIFICATION — 2026-03-26  
**Scope:** Alpaca only.  
**Status:** **PROPOSED — awaiting human CSA explicit sign-off.**  
*(Automated runs cannot substitute for CSA approval; if CSA revises clauses below, downstream certification steps must be re-run.)*

---

## Definition: PERFECT DATA COLLECTION

All of the following must hold for **every** live trade in the certified window, unless a **documented exception** is approved by CSA.

### A) Lifecycle events (per live trade)

| CSA requirement | Authoritative implementation mapping (this repo) |
|-----------------|--------------------------------------------------|
| **entry_decision_made** | `logs/run.jsonl` → `event_type: trade_intent` with `decision_outcome: entered` **and/or** `logs/alpaca_unified_events.jsonl` → `event_type: alpaca_entry_attribution` with matching `trade_id` / `canonical_trade_id`. |
| **execution submit** | `logs/orders.jsonl` rows carrying `canonical_trade_id` (and/or `order_id`) for the trade’s join key family. |
| **execution fill(s)** | Same stream: rows indicating fill lifecycle (`status`, `type`, `filled_qty`, per `telemetry/alpaca_strict_completeness_gate.py` heuristics). |
| **terminal close** | `logs/exit_attribution.jsonl` row for the trade **and** (contract target) `logs/alpaca_unified_events.jsonl` → `alpaca_exit_attribution` with **`terminal_close: true`**. |

### B) Terminal close reflection

- **Execution sidecar logs:** Interpreted as **`logs/orders.jsonl`** (no separate systemd “sidecar” unit observed on droplet; execution telemetry is written from the trading process).  
- **Unified events:** `alpaca_exit_attribution` + `terminal_close: true` **or** a **written CSA exception** (e.g. legacy era pre-unified-emit) with explicit end date.

### C) Join keys

- **Primary:** `trade_id` (`open_{SYMBOL}_{entry_ts}` family) aligned across exit attribution, unified stream, and orders where present.  
- **Secondary / alias expansion:** `canonical_trade_id`, `trade_key`, and `canonical_trade_id_resolved` edges in `run.jsonl` per `AUTHORITATIVE_JOIN_KEY_RULE` in `telemetry/alpaca_strict_completeness_gate.py`.

### D) Timestamps

- Monotonic: exit timestamps ≥ entry timestamps where both parsed.  
- Latency bounds: CSA must set numeric SLA (not fixed in this document); SRE measures “time since last write” per surface.

### E) No silent drops

- No unexplained gaps between **exit_attribution closes** and **unified terminal_close** counts.  
- No empty `orders.jsonl` while live trading.  
- Strict completeness gate **ARMED** for the forward certification cohort.

---

## CSA action

- **APPROVE** — Use this mapping as the certification contract.  
- **REVISE** — Edit mappings/SLAs; **STOP** automated certification until revised contract is re-published.

**Automated assessment:** Contract text is internally consistent with `reports/audit/ALPACA_TELEMETRY_CONTRACT.md` and strict gate code. **Human CSA sign-off still required.**
