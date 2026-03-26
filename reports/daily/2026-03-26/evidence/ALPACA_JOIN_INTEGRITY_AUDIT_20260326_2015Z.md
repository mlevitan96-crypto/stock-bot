# Phase 3 — Join integrity audit (Quant)

**Artifact:** `ALPACA_JOIN_INTEGRITY_AUDIT_20260326_2015Z`  
**Evidence:** `reports/ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z.json`, direct inspection of `logs/exit_attribution.jsonl`, `logs/alpaca_unified_events.jsonl`.

---

## Join surfaces

| Surface | Key fields expected |
|---------|---------------------|
| Unified entry | `trade_id`, `canonical_trade_id`, `trade_key` |
| Unified exit | `trade_id`, `canonical_trade_id`, `trade_key`, `terminal_close` |
| exit_attribution | `trade_id` (strict), `symbol`, `timestamp`, … |
| orders.jsonl | `canonical_trade_id`, `order_id`, fill fields |

---

## Findings (workspace logs)

### 1) exit_attribution ↔ trade_id — **BROKEN / MISSING**

`logs/exit_attribution.jsonl` rows in this workspace **do not contain `trade_id`** (`rg trade_id logs/exit_attribution.jsonl` → no matches).  
**Impact:** Cannot join post-floor “terminal” economic attribution to `open_{SYM}_{ts}` or unified streams without a **reconstruction rule** (not applied in this certification).

### 2) Unified exit “terminal” coverage — **SEVERE GAP**

Only **1** distinct `trade_id` has a unified exit with `terminal_close: true` vs **36** exit_attribution rows counted in the audit window → unified stream is **not** a complete mirror of closures (consistent with prior audits, e.g. `ALPACA_DATA_ADVERSARIAL_REVIEW_20260326_1622Z.md`).

### 3) Duplicate unified rows (same trade_id)

`alpaca_unified_events.jsonl` contains **repeated** `alpaca_entry_attribution` / `alpaca_exit_attribution` lines for the same `trade_id` (e.g. TSLA fixture).  
**Impact:** Risk of **duplicate joins** if consumers count rows instead of distinct `trade_id` + event_type.

### 4) orders.jsonl ↔ canonical_trade_id — **NO DATA**

`logs/orders.jsonl` is **empty (0 bytes)**.  
**Impact:** **No** verifiable join from decision/unified → execution submit/fill in this workspace.

### 5) Concrete examples

| Example | Issue |
|---------|--------|
| `trade_id: ""` with `trade_key: "?|LONG|..."` in unified exit | **Mismatched / invalid key** — cannot join |
| `trade_id: "inv"` | Test/invalid rows mixed with real-shaped rows — pollutes certification unless filtered |

---

## Verdict (Phase 3)

**JOIN INTEGRITY: FAILED** on this workspace dataset. Droplet may differ; **re-run** with production logs and `trade_id`-complete `exit_attribution`.
