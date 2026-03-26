# PHASE 3 — Join Integrity Audit (Quant)

**Timestamp:** 2026-03-26 ~16:23 UTC  
**Cohort:** Post strict epoch `open_ts_epoch = 1774458080` (2026-03-25T17:01:20Z) — `exit_attribution.jsonl` rows with open-time ≥ floor (see gate output).  
**Tool:** `telemetry/alpaca_strict_completeness_gate.py --audit --open-ts-epoch 1774458080` on droplet.

---

## 1. Headline results

| Metric | Value |
|--------|------:|
| Trades in strict cohort (`trades_seen`) | 192 |
| **Complete chains** | **76** |
| **Incomplete chains** | **116** |
| Gate status | **BLOCKED** (`incomplete_trade_chain`) |

**Artifact:** abbreviated `reports/ALPACA_STRICT_COMPLETENESS_GATE_20260326_1622Z.json` (full stdout captured in certification transcript).

---

## 2. Failure reasons (histogram)

| Reason | Count |
|--------|------:|
| `entry_decision_not_joinable_by_canonical_trade_id` | 116 |
| `missing_exit_intent_for_canonical_trade_id` | 92 |
| `missing_unified_entry_attribution` | 22 |
| `no_orders_rows_with_canonical_trade_id` | 22 |

*Rows can accumulate multiple reasons; histogram counts reason occurrences across trades.*

---

## 3. Concrete examples

### 3.1 Incomplete (representative)

| `trade_id` | Missing / broken leg |
|------------|----------------------|
| `open_GM_2026-03-25T17:35:44.149365+00:00` | `trade_intent entered` not joinable; `exit_intent` missing — yet matrix shows unified entry + orders + unified exit terminal + exit_attribution (**telemetry join definition mismatch**). |
| `open_AAPL_2026-03-25T17:42:31.283565+00:00` | Same pattern as GM. |
| `open_AMD_2026-03-25T18:27:28.289799+00:00` | `missing_unified_entry_attribution`, `no_orders_rows_with_canonical_trade_id` (per gate list). |

### 3.2 Complete (sanity)

| `trade_id` | Note |
|------------|------|
| `open_LOW_2026-03-26T14:24:51.823612+00:00` | All matrix flags true; alias set includes intent+fill trade_keys. |
| `open_WMT_2026-03-26T14:25:04.753797+00:00` | Same. |

---

## 4. Duplicate / mismatch notes

- **Canonical ID drift:** Sample unified exit for `HOOD` showed `trade_key` vs `canonical_trade_id` **different second bucket** in tail inspection (`trade_key` `HOOD|LONG|1774540298` vs `canonical_trade_id` `HOOD|LONG|1774539960`) — **potential duplicate-key / mismatch** surface for joins (needs CSA whether acceptable as alias or bug).  
- **Multiple exit lines per trade_id** possible in unified history; strict gate keeps latest terminal per `trade_id`.

---

## 5. Phase 3 verdict

**FAIL:** 60% of post-epoch closed trades (116/192) **do not** satisfy the strict join matrix. Data is **not** provably joinable under the repo’s **fail-closed** learning gate.
