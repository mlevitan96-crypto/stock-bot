# Alpaca Trade Sufficiency Verdict (Quant Officer)

**Data cut:** Droplet `logs/exit_attribution.jsonl` · **UTC:** 2026-03-20  
**Unique closed trades (canonical join key):** **2,204** (after dedup; 2,209 physical lines)

---

## 1. Volume summary

| Metric | Value |
|--------|-------|
| Total closed trades (unique keys) | 2,204 |
| Wins (pnl &gt; 0) | 892 |
| Losses (pnl &lt; 0) | 1,283 |
| Breakeven / unknown PnL | 29 |
| Trading days represented (exit date) | 12 (2026-03-04 … 2026-03-19) |
| Peak trades/day | 253 (2026-03-05) |

**Top symbols (count):** MRNA 68, COP 67, HOOD 66, INTC 66, NVDA 62, COIN 62, TSLA 62, …

**Exit reason (normalized code):**

| Code | Count |
|------|-------|
| `hold` | 2,068 |
| `intel_deterioration` | 135 |
| `other` / `unknown` | 2 |

---

## 2. Explicit sufficiency thresholds (this gate)

| Analysis | Minimum closed trades | This dataset |
|----------|------------------------|--------------|
| PnL attribution (expectancy, factor-style buckets) | **≥ 100** | **2,204** — **meets** |
| Signal contribution (component-level stability) | **≥ 200** | **2,204** — **meets** |
| Exit timing / regime slicing | **≥ 50** per major bucket where claimed | **Meets** global N; per-symbol slices vary (see top symbols) |

**Exclusions:** **2** rows with missing PnL/timestamps should be excluded from precision metrics until repaired.

---

## 3. Classification

### **A) SUFFICIENT_FOR_FULL_AUDIT**

**Rationale:** Trade count, day coverage, win/loss split, and exit-reason mix support **Kraken-style PnL + attribution** on **`exit_attribution.jsonl`** as the primary ledger. Cross-join to `master_trade_log` is a **separate** reconciliation problem (see integrity report), not a sample-size problem.

**Caveat:** Full “would-have” / bar-path analysis requires **bar cache + replay** artifacts for the same dates; sufficiency here is **trade-record** sufficiency, not bar completeness (not re-proven in this scan).

---

*Quant Officer — analytical validity assumes quarantine of the 2 defective exit rows.*
