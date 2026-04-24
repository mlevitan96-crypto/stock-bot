# Alpaca synthetic strict audit (no relaxations)

**TS:** `20260330_200000Z`  
**Logic:** `telemetry.alpaca_strict_completeness_gate.evaluate_completeness` (same code path as live audits).  
**Lab root:** `synthetic_lab_root/`

---

## Parameters

- **`open_ts_epoch`:** 2026-03-30 **09:30 America/New_York** → UTC epoch (session floor for cohort).  
- **`audit=True`:** include reason histogram / incomplete machinery (none triggered).

---

## Results (captured)

Output file: **`strict_gate_result.json`** (same directory as this evidence).

| Field | Value |
|-------|--------|
| **LEARNING_STATUS** | **ARMED** |
| **trades_seen** | **2** |
| **trades_complete** | **2** |
| **trades_incomplete** | **0** |
| **learning_fail_closed_reason** | **null** |
| **reason_histogram** | **{}** |
| **precheck** | **[]** (empty — all required log files present) |

---

## Interpretability checks

| Check | Outcome |
|-------|---------|
| Unified joins (entry + exit + terminal) | **PASS** |
| Orders rows with `canonical_trade_id` | **PASS** |
| `trade_intent(entered)` joinable | **PASS** |
| `exit_intent` present | **PASS** |
| Economic closure (`pnl` present, `exit_price` > 0) | **PASS** |
| Lifecycle timestamps parseable from `trade_id` | **PASS** |

**PnL:** Realized economics represented as **`pnl`** + **`snapshot.pnl`** on exit rows (aligned with post-close / dashboard patterns).

---

## Conclusion

**AUDIT: PASS** on the synthetic lab cohort with **zero** relaxations to `evaluate_completeness`.

---

*Read-only evaluation of lab-generated logs.*
