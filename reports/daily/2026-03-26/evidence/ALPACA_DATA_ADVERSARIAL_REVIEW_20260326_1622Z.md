# STOP-GATE 1 — Adversarial Review (mandatory)

**Persona:** Assume the data pipeline is **broken** until proven otherwise.  
**Evidence used:** Phases 1–5 artifacts on 2026-03-26.

---

## 1. Attempts to disprove “complete / joinable / fresh”

1. **Unified exit is a subset of truth.**  
   252 terminal unified exits vs 682 `exit_attribution` closes (72h) **proves** the unified stream is **not** a complete mirror of economic closure. Any analysis using **only** `alpaca_unified_events.jsonl` **will under-count** closes.

2. **Strict gate fails majority of post-epoch trades.**  
   116/192 incomplete under `telemetry/alpaca_strict_completeness_gate.py` — the repo’s own **fail-closed** standard says learning / causal claims are **not** certified.

3. **`trade_intent entered` join is the bottleneck.**  
   Many incomplete rows show `trade_intent_entered_present: false` while **other** signals exist (unified entry, orders). That means either: (a) intents are logged without `decision_outcome=entered` when trades actually open, (b) canonical IDs don’t propagate into intent records, or (c) the gate’s definition is **stricter than runtime reality**. Any of these breaks “decision → execution → terminal” **as defined by the gate**.

4. **HOOD canonical mismatch in live tail.**  
   `trade_key` vs `canonical_trade_id` seconds differ in a unified exit line — adversarial hypothesis: **double bookkeeping** or **wrong canonical** attached to exit; joins that assume equality will **silently split** one trade into two keys.

5. **Orders “fill” ratio is tiny under heuristic.**  
   468 / 3996 — without a schema-level definition of submit vs fill, we **cannot** prove every submit got a fill row from logs alone (partial fills, cancellations, or different row shapes).

6. **Position drift warning.**  
   “Positions in Alpaca but not in local state” — adversarial read: **some live exposure is invisible to local attributors** at that instant → execution logs may not tell the whole story.

7. **72h window sampling bias.**  
   Window filters on **exit timestamp** for `exit_attribution` but unified terminal may key off **emit time** — could exaggerate or hide gaps; **no Monte Carlo across windows** was run.

8. **Droplet-only snapshot.**  
   Single-host sample at one minute — **no proof** of cross-region replay or backup integrity.

---

## 2. What could still be wrong (untested / weakly tested)

- **Partial JSONL lines** under crash (last line corrupt) — not scanned.  
- **Disk full / inode exhaustion** — not checked.  
- **Clock skew** between bot and broker — not measured.  
- **Shadow vs live** mixing in `orders.jsonl` — not classified in this audit.  
- **Alpaca paper vs live** endpoint confusion in downstream tools — not in scope but could mislead operators.

---

## 3. Adversarial conclusion

The quantitative evidence **refutes** “perfect, joinable Alpaca trade data collection” under the stated CSA mapping and strict gate. **Do not** treat profitability-only logs (`exit_attribution`) as sufficient for **unified causal certification** without accepting explicit exceptions.
