# Massive quant edge review — root cause and action framework (Alpaca)

**This is a decision engine, not a report.**

---

## Purpose

This review exists to explain **why** we are winning or losing and **how** we will get better. It is a **root-cause investigation**, not a reporting exercise. **Every finding must result in a concrete action or an explicit decision to do nothing.**

---

## Scope

| In scope | Out of scope (for this review cycle) |
|----------|--------------------------------------|
| **Authoritative data source: strict-scope live trades only** — same cohort as `telemetry.alpaca_strict_completeness_gate.evaluate_completeness` for a declared `open_ts_epoch` (e.g. `STRICT_EPOCH_START` or session policy). | **Integrity weighting** and **warehouse truth** as *certifying* authority — **excluded until DATA_READY is YES.** |
| Logs under `logs/` plus strict backfill mirrors (`strict_backfill_*`). | Board or promotion decisions that **require** warehouse certification stay on a separate track. |

**Goal:** Identify **edge**, **anti-edge**, **conditional edge**, **execution leaks**, and **missed opportunity** using strict-log forensics first.

**Authoritative join rule:** Build all per-trade tables on **`canonical_trade_id` / `trade_key`** (and stable `open_SYM_*` trade ids where defined), not “latest fill per symbol.” See gate output `AUTHORITATIVE_JOIN_KEY_RULE` and `MEMORY_BANK_ALPACA.md` strict-era notes.

---

## Review law — WHY WHY WHY HOW

For **every** loss, drawdown, or underperforming slice, reviewers must answer:

| Step | Question |
|------|----------|
| **WHAT** | What happened (observable on strict cohort)? |
| **WHY** | Why did it happen (mechanism)? |
| **WHY** | Why does that cause exist (policy, threshold, data, structure)? |
| **HOW** | How do we **fix, gate, flip, size, or remove** it? |

**No chart, table, or metric is accepted without a HOW answer.**

---

## Board review rules

All board and quant reviewers must:

- Ask **WHY at least three times** for every material result.
- Identify the **mechanism**, not the symptom.
- Demand a **concrete lever** from this set (or justify none):
  - **Kill** — remove signal, rule, or path
  - **Gate** — add precondition, quorum, or regime filter
  - **Flip direction** — invert or separate long vs short policy
  - **Size up or down** — risk and notional
  - **Delay entry** — timing / staleness / confirmation
  - **Change exit logic** — trails, time exits, V2 thresholds, forced flatten

If **no lever** exists, classify explicitly as:

- **Unexploitable noise**, or  
- **Data gap requiring new telemetry** (open item with owner)

**Every slide must include:**

- Root cause  
- Proposed action  
- Confidence level  

---

## Workstream map — A through J

| ID | Name | Focus question | Repo / tooling |
|----|------|----------------|----------------|
| **A** | Canonical trade facts | Single source of truth per strict trade; count reconciles | `scripts/audit/export_strict_quant_edge_review_cohort.py`; actionable rollup: `scripts/audit/run_strict_quant_edge_analysis.py` (Markdown + JSON under `reports/`). Full `trade_facts` build still optional. |
| **B** | PnL decomposition | Where is alpha created and destroyed? | Break into: **signal correctness**, **execution impact**, **exit giveback**, **opportunity cost** (blocked / missed). Log-native fees/slippage when warehouse off. |
| **C** | Directional truth | Is one side structurally wrong? | Long vs short: win rate, expectancy, tail losses, drawdowns; **counterfactual flip** = model-only, labeled synthetic |
| **D** | Entry quality | Are entries wrong or are exits failing? | Quadrants: good/bad entry × good/bad exit; time to first profit, MAE, MFE, **MFE capture ratio** |
| **E** | Exit attribution | Are winners cut early and losers held late? | Normalize: profit taking, stop loss, time-based, forced/defensive, error/guardrail; PnL, giveback, tail by type |
| **F** | Blocked and missed opportunity | Where is hidden alpha suppressed? | Opportunity cost of blocked trades; over-conservatism; gating errors — **hypothesis** tier if warehouse-dependent |
| **G** | CSA signal edge map | Which signals drive edge and which destroy it? | Per signal: participation, expectancy present vs absent, directional interaction, exit interaction |
| **H** | Regime sensitivity | When to size up, down, or stand aside? | Volatility bucket, trend bucket, time of day, day of week |
| **I** | Required new axes | Ten cross-cutting views (below) | Each view: definition, cohort n, metric, **HOW** if actionable |
| **J** | Decision matrix | No analysis complete without a decision | **KEEP / KILL / GATE / SIZE** (+ **FLIP / DELAY / EXIT** as lever tags on rows). Template: `docs/ALPACA_QUANT_EDGE_REVIEW_DECISION_MATRIX_TEMPLATE.md` |

---

## Workstream A — Canonical trade_facts

Build a **single `trade_facts` table** (or equivalent Parquet/CSV) containing:

| Field | Notes |
|-------|--------|
| `canonical_trade_id` | Resolved strict join key |
| `symbol` | |
| `side` | Long or short (normalized) |
| `quantity` | |
| `intent_timestamp` | From `trade_intent` / `entry_decision_made` chain |
| `fill_timestamp` | From `orders.jsonl` / fills |
| `close_timestamp` | From `exit_attribution.jsonl` |
| `fill_price` | |
| `close_price` | |
| `fees` | Log proxy or broker field; document source |
| `realized_pnl` | Strict-consistent field |
| `holding_time` | |
| `maximum_favorable_excursion` | MFE — **gap** if no bar / high_water path |
| `maximum_adverse_excursion` | MAE — same |
| `exit_type_or_reason` | Normalized (Workstream E) |
| `signals_present` | Set / flags |
| `signal_strengths` | As available on entry or exit snapshot |
| `intent_to_fill_latency` | |
| `slippage_estimate` | Define formula; **gap** if no mid |
| `blocked` | If applicable to cohort definition |
| `blocked_reason` | If blocked |

**Acceptance condition:** Trade **count reconciles exactly** to strict **after-fix** totals:

- `COUNT(trade_facts)` **=** `trades_seen` from `evaluate_completeness(root, open_ts_epoch=…)` for the **same** root and epoch (and flags).  
- When analyzing **chain-complete** trades only: count **=** `trades_complete`.

**Command (cohort IDs + reconciliation):**

```bash
PYTHONPATH=. python3 scripts/audit/export_strict_quant_edge_review_cohort.py \
  --root /root/stock-bot --open-ts-epoch 1774458080 \
  --out-json reports/ALPACA_STRICT_QUANT_EDGE_COHORT.json
```

Exit code **1** if list lengths do not match gate counts.

---

## Workstream I — Required ten views

Every review must include these **ten axes** (each with a HOW if actionable):

1. Signal **agreement count** versus PnL  
2. Signal **disagreement penalty**  
3. **Latency** sensitivity  
4. **Exit optionality** loss  
5. **False positive cost** per signal  
6. **Asymmetry ratio** of wins to losses  
7. **Loss clustering** in time  
8. **Regime transition** trades  
9. **Signal persistence** during holding  
10. **Anti-signal** performance when signal is absent  

(See `docs/ALPACA_QUANT_EDGE_REVIEW_APPENDIX_TABLES_SPEC.md` — section I1 — for sheet-level specs.)

---

## Workstream J — Decision matrix

For **every** signal, exit type, direction, and regime slice, classify:

- **KEEP**  
- **KILL**  
- **GATE**  
- **SIZE**  

Use additional **lever tags** where needed: **FLIP**, **DELAY_ENTRY**, **CHANGE_EXIT**. Rows without a classification are **not** complete.

---

## Loss review template (per cluster)

| Field | Content |
|-------|---------|
| Loss cluster name | |
| Scope | Strict cohort, dates, filters |
| Net PnL impact | $ and % of cohort |
| Frequency | n trades, % of losers |
| WHY level one | |
| WHY level two | |
| WHY level three | |
| HOW — specific action | Kill / gate / flip / size / delay / exit / DO_NOTHING |
| Confidence | Low / med / high |
| Owner | |

---

## Success review (profitable pockets)

Profitable areas must answer:

- **Why does this work?**  
- **Is it fragile?**  
- **Is it regime dependent?**  
- **Can it be scaled safely?**  

**Profit without understanding is future loss.**

---

## Definition of done

- [ ] **Root causes** identified for **all major losses** (cover ≥80% of negative PnL or tail risk, or explicitly scoped out with reason).  
- [ ] **Concrete actions** proposed for **every** finding, or **explicit DO_NOTHING** with classification (noise vs telemetry gap).  
- [ ] **Top five profit levers** identified (with mechanism).  
- [ ] **Top five loss leaks** identified (with mechanism).  
- [ ] **Board alignment** on what to **kill, gate, flip, or scale**.  
- [ ] **Strict cohort reconciliation** passed (Workstream A).  

---

## Deliverables

| Deliverable | Location |
|-------------|----------|
| Framework (this doc) | `docs/ALPACA_MASSIVE_QUANT_EDGE_REVIEW_FRAMEWORK.md` |
| **Cursor execution block (procedure)** | `docs/ALPACA_STRICT_QUANT_EDGE_CURSOR_EXECUTION_BLOCK.md` |
| Board edge review summary | `docs/ALPACA_QUANT_EDGE_REVIEW_BOARD_SUMMARY_TEMPLATE.md` |
| Quant appendix (full tables) | `docs/ALPACA_QUANT_EDGE_REVIEW_APPENDIX_TABLES_SPEC.md` |
| Decision matrix | `docs/ALPACA_QUANT_EDGE_REVIEW_DECISION_MATRIX_TEMPLATE.md` |
| Cohort export (generated) | `reports/ALPACA_STRICT_QUANT_EDGE_COHORT.json` |
| Per-run decision packet (example path) | `reports/daily/YYYY-MM-DD/evidence/ALPACA_STRICT_QUANT_EDGE_DECISION_BLOCK_*Z.md` + `...DECISION_MATRIX_*Z.json` |

---

## Related code (non-exhaustive)

- `telemetry/alpaca_strict_completeness_gate.py` — strict cohort definition  
- `scripts/audit/export_strict_quant_edge_review_cohort.py` — cohort export + reconciliation  
- `scripts/audit/alpaca_pnl_massive_final_review.py` — PnL bundle / SPI-style sections (use with scope discipline)  
- `src/exit/exit_attribution.py`, `src/exit/exit_score_v2.py` — exit taxonomy inputs  

---

## Governance note

This review **does not** relax strict completeness or DATA_READY warehouse gates. It **consumes** strict cohort truth for **causal** and **operational** levers. When **DATA_READY** becomes YES, re-run decomposition workstreams that depend on warehouse joins for **second-pass reconciliation** with board packets — not as a substitute for strict-log forensics.
