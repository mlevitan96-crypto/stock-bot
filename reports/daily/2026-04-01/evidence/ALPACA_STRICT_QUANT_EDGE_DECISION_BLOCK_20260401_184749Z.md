# Strict quant edge — decision block (board summary)

**Run:** droplet `/root/stock-bot` · **generated_at_utc:** 2026-04-01T18:47:49Z  
**Tool outputs:** `reports/ALPACA_STRICT_QUANT_EDGE_ANALYSIS_20260401_184749Z.md` + `.json` (on droplet)  
**open_ts_epoch:** 1774458080  

---

## Certification and confidence

| Field | Value |
|-------|--------|
| **LEARNING_STATUS** | **BLOCKED** |
| **trades_seen** | 400 |
| **trades_complete** | 369 |
| **trades_incomplete** | 31 |
| **Strict cohort ids in analysis** | 399 (exit rows matched 399, 0 missing exit rows for those ids) |

**Verdict:** This packet is **review-only, not promotable** for learning or promotion until the strict gate is **ARMED** and incomplete count is **0** (or policy explicitly scopes a complete-only cohort — not done here).

**Overall confidence in forensic slices:** **Medium** (exit rows are rich; cohort is strict-scoped but gate BLOCKED; exit_v2_component expectancy is **not** discriminative today — every row carries the same component keys, see quant notes).

---

## Step 2 — Actionable extractions (from JSON)

### PnL headline

| Metric | Value |
|--------|--------|
| Trades in cohort | 399 |
| Sum PnL USD | **28.29** |
| Avg PnL USD | **0.071** |
| Median PnL USD | **0.18** |
| Win rate | **0.566** |
| Avg hold (min) | **66.0** |
| Avg v2 exit score | **0.079** |

### Long vs short

| Side | n | Sum PnL | Avg PnL | Win rate |
|------|---|---------|---------|----------|
| LONG | 279 | 28.52 | 0.102 | 0.566 |
| SHORT | 120 | -0.23 | -0.002 | 0.567 |

### Exit reason — largest negative buckets (material n)

| Exit reason (norm) | n | Sum PnL | Avg PnL |
|--------------------|---|---------|---------|
| signal_decay(0.93) | 21 | -28.47 | -1.36 |
| signal_decay(0.64) | 10 | -13.92 | -1.39 |
| signal_decay(0.94) | 8 | -13.39 | -1.67 |
| signal_decay(0.65)+flow_reversal | 12 | -8.03 | -0.67 |
| stale_alpha_cutoff(120min,-0.01%) | 3 | -7.86 | -2.62 |

### Entry / exit regime

| Entry regime | n | Sum PnL | Avg PnL |
|--------------|---|---------|---------|
| mixed | 358 | 53.39 | 0.149 |
| unknown | 41 | -25.10 | -0.612 |

| Exit regime | n | Sum PnL | Avg PnL |
|-------------|---|---------|---------|
| mixed | 399 | 28.29 | 0.071 |

### Best / worst trades (PnL)

**Worst:** NIO -16.80 (`signal_decay(0.93)`), SOFI -13.50 (`signal_decay(0.94)`), MRNA -12.95 (`signal_decay(0.93)`), CVX -8.71 (stale_alpha), COIN -8.35 (`signal_decay(0.94)+drawdown`), …  

**Best:** MRNA +10.80, SOFI +9.62, MRNA +8.28 (short), META +8.17, MRNA +7.74 (short), …  

### Heuristic levers (tool `suggested_actions`)

Tool flagged **positive** expectancy: `signal_decay(0.83)`, `signal_decay(0.85)` → KEEP/SIZE (with fragility review).  
Tool flagged **negative** expectancy: `signal_decay(0.93)`, `signal_decay(0.65)+flow_reversal`, `signal_decay(0.64)`, `signal_decay(0.94)` → CHANGE_EXIT / GATE.

---

## Step 3 — WHY ×3 + HOW (underperforming slices)

### A. `signal_decay(0.93)` / `(0.94)` (negative avg, large n)

| Level | Answer |
|-------|--------|
| **WHY 1** | Many exits label with high decay score; aggregate PnL for these buckets is **negative**. |
| **WHY 2** | High decay often coincides with **V2-driven exits** that cut positions after score deterioration — sometimes locking in losses or giving back winners too late. |
| **WHY 3** | Threshold surface maps a **wide** range of market states into the same string bucket; there is no separate gate for **trend vs chop** or **already-green PnL**. |
| **HOW** | **CHANGE_EXIT** — tighten distinction: require additional condition (e.g. min hold, MFE capture, or drawdown from peak) before firing at 0.93–0.94 band; **GATE** — reduce entries when regime telemetry is **unknown** (correlated with bad outcomes, see below). |

### B. `signal_decay(0.64)` / `(0.65)+flow_reversal`

| Level | Answer |
|-------|--------|
| **WHY 1** | Lower decay band exits still show **negative** expectancy when `flow_reversal` is appended. |
| **WHY 2** | **Flow reversal** as an exit trigger may fire in **noise** or **mean-reversion** favorable to the original thesis. |
| **WHY 3** | Exit composer treats reversal as urgent without **confirmation** (second bar, size of flow move, or regime). |
| **HOW** | **CHANGE_EXIT** — add hysteresis or quorum for flow_reversal; **DELAY_ENTRY** — avoid entries when flow is historically whipsawing for that symbol class. |

### C. `stale_alpha_cutoff` losers (e.g. 120–141 min, negative threshold)

| Level | Answer |
|-------|--------|
| **WHY 1** | Time-based stale exits sometimes close **large losers** after long holds. |
| **WHY 2** | Clock exit ignores **path** (never achieved MFE) vs **giveback** (had MFE). |
| **WHY 3** | Single rule for “stale” without **path-dependent** branch. |
| **HOW** | **CHANGE_EXIT** — branch stale exit: if MAE/MFE telemetry available, different cutoff; else **GATE** long-duration entries in **unknown** regime. |

### D. Entry regime **unknown** (n=41, avg -0.61)

| Level | Answer |
|-------|--------|
| **WHY 1** | Trades with **unknown** entry regime underperform **mixed**. |
| **WHY 2** | Without regime label, strategies cannot **size or gate** for vol/trend state. |
| **WHY 3** | Telemetry or persistence failed to stamp `entry_regime` at open for a subset of paths (reconcile, partial metadata, or timing). |
| **HOW** | **Data gap** — fix `entry_regime` capture at `mark_open` / metadata persist; **GATE** — optionally block or halve size when regime is unknown until fixed. |

---

## Step 4 — Directional decision

**Observation:** SHORT is **not** the dominant drag in this slice (sum **-0.23** over 120 trades; expectancy ≈ flat). LONG carries essentially all **positive** sum PnL.

**Decision:** **KEEP** short sleeve with **monitoring**; **do not FLIP** or **KILL** shorts on this packet alone. Optional **SIZE** — if capital is constrained, priority is **long** quality and **exit tuning**, not short removal.

**Rationale:** Short win rate ≈ long; problem cluster is **exit type and unknown regime**, not directional beta in this cohort.

---

## Step 5 — Exit policy review

| Exit bucket | Assessment | Action |
|-------------|------------|--------|
| signal_decay(0.83), (0.85) | Positive expectancy, n≥20 | **KEEP**; **SIZE** only after ARMED + fragility review |
| signal_decay(0.93), (0.94) | Negative expectancy | **CHANGE** thresholds / add PnL-path condition |
| signal_decay(0.64), (0.65)+flow_reversal | Negative | **CHANGE** flow_reversal confirmation; **GATE** weak flow setups |
| stale_alpha (losers) | Small n but large per-trade pain | **CHANGE** time-exit branching |
| trail_stop (n=2) | Insufficient n | **KEEP** (no decision) |

---

## Step 6 — Regime / telemetry gaps

| Bucket | Classification | Action |
|--------|----------------|--------|
| entry_regime **unknown** | **Data gap** + **gating opportunity** | Fix telemetry; interim **GATE** or **SIZE** down |
| exit_regime only **mixed** | **Structural regime blindness** at exit | Enrich exit regime bucketing in attribution |
| exit_v2 components all n=399 | **Telemetry / analysis gap** | Do not use current component table for signal **KILL** decisions; need sparse or marginal components |

---

## Step 7 — Decision matrix

See companion JSON: `ALPACA_STRICT_QUANT_EDGE_DECISION_MATRIX_20260401_184749Z.json`.

---

## Step 8 — Prerequisites to re-arm (BLOCKED)

1. Resolve **31** incomplete strict-chain trades (backfill + confirm live `exit_intent` / metadata join fixes deployed).  
2. Re-run `export_strict_quant_edge_review_cohort.py` → reconciliation true, **LEARNING_STATUS: ARMED**.  
3. Re-run `run_strict_quant_edge_analysis.py` and **replace** this packet with an ARMED run for any promotion-linked narrative.

---

## Step 9 — Recommended expansions

- **Complete-only** cohort filter for learning-grade tables.  
- Blocked-trade opportunity cost.  
- Bar-based **MFE/MAE** for giveback diagnosis.  
- Signal **agreement** at entry vs exit decay bucket.

---

*This file is generated from a specific droplet run; numbers drift as logs grow. Re-run the tool for fresh cohort stats.*
