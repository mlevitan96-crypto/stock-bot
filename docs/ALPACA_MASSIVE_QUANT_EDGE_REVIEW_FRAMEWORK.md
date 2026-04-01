# Alpaca massive quant edge review — root-cause and action framework

**Purpose:** Explain *why* we win or lose and *how* we improve. This is a **decision engine**, not a narrative report. Every finding ends in a **concrete lever** or an explicit **no action** classification.

**Scope boundary (non-negotiable):**

| In scope | Out of scope (until noted) |
|----------|----------------------------|
| **Strict-scope live trades** — same cohort as `telemetry.alpaca_strict_completeness_gate.evaluate_completeness` for a declared `open_ts_epoch` (typically `STRICT_EPOCH_START` or session policy). | **Warehouse-weighted truth**, execution-join certification, and **DATA_READY** gates — do **not** block this review, but **must not** be cited as authoritative for warehouse-only metrics. |
| Logs under `logs/` + strict backfill mirrors (`strict_backfill_*`). | Promotion decisions that require **DATA_READY: YES** remain separate. |

**Authoritative join rule:** See `AUTHORITATIVE_JOIN_KEY_RULE` in gate output and `MEMORY_BANK.md` strict era notes. Build all per-trade tables on **`canonical_trade_id` / `trade_key` alias sets**, not “latest fill per symbol.”

---

## Review law — WHY ×3 + HOW

For every loss cluster, drawdown slice, or underperforming bucket:

1. **WHAT** happened (observable fact on strict cohort).  
2. **WHY** (mechanism linking fact to PnL).  
3. **WHY** that mechanism exists (policy, threshold, data, market microstructure).  
4. **HOW** we **kill, gate, flip, size, delay entry, or change exit** — or classify **unexploitable noise** / **telemetry gap**.

**No metric without HOW.** Slides must list: root cause, proposed action, confidence (low/med/high), owner.

---

## Workstream map — repo tooling

| Workstream | Focus | Primary inputs | Existing / planned automation |
|------------|-------|----------------|------------------------------|
| **A — Canonical trade_facts** | One row per strict cohort trade; reconcile counts | `exit_attribution.jsonl`, unified exit terminals, `orders.jsonl`, `run.jsonl`, `alpaca_unified_events.jsonl` + `strict_backfill_*` | **`scripts/audit/export_strict_quant_edge_review_cohort.py`** (cohort IDs + reconciliation). Join implementation: extend or pair with `scripts/audit/alpaca_pnl_massive_final_review.py` / session truth JSON. |
| **B — PnL decomposition** | Alpha vs execution vs giveback vs opportunity cost | Exit context, fees from orders/activities where available, blocked ledger | `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` (**excluded** for certification until DATA_READY YES); use **log-native** fees/slippage proxies for strict review. |
| **C — Directional truth** | Long vs short | `exit_attribution` `side` / `direction`, PnL fields | Custom slice on trade_facts; counterfactual “flip direction” = **synthetic** — label as model-only. |
| **D — Entry quality** | Good/bad entry × exit quadrants | `entry_decision_made`, `entry_score`, components, time-to-MFE | `telemetry/alpaca_entry_decision_made_emit` audit helpers; entry timestamps from `trade_id` / orders. |
| **E — Exit attribution** | Normalize exit reasons | `exit_attribution.jsonl`, `close_reason`, V2 exit fields | `src/exit/exit_attribution.py`, `src/exit/exit_score_v2.py`, `scripts/analysis/*exit_edge*`. |
| **F — Blocked / missed** | Opportunity cost | `logs/blocked_trades.jsonl`, shadow/starvation diagnostics, CI on intents | `scripts/diagnose_shadow_starvation.py`, blocked-bucket coverage (warehouse-adjacent — treat as **hypothesis** until DATA_READY). |
| **G — CSA signal edge map** | Per-signal expectancy | Normalized `signals` on exit rows, entry snapshots | `src/analysis/alpaca_signal_path_intelligence.py`, `scripts/audit/alpaca_pnl_massive_final_review.py` (SPI sections). |
| **H — Regime sensitivity** | Vol / trend / time slices | `market_regime`, `direction`, timestamps | Exit row enrichment (`exit_attribution_enrich`); dashboard regime caches. |
| **I — Ten required axes** | Cross-cutting views | Derived from trade_facts + signal history | Checklist below — each needs a named query or script output. |
| **J — Decision matrix** | KEEP / KILL / GATE / SIZE | Synthesis of A–I | `docs/ALPACA_QUANT_EDGE_REVIEW_DECISION_MATRIX_TEMPLATE.md` (template). |

---

## Workstream A — trade_facts (acceptance)

**Required columns (minimum):**

`canonical_trade_id` (or resolved join key), `symbol`, `side`, `quantity`, intent timestamp, fill timestamp, close timestamp, fill price, close price, fees, realized PnL, holding time, MFE, MAE, exit type/reason, signals present, signal strengths, intent→fill latency, slippage estimate, `blocked` + reason.

**Acceptance:**  
`COUNT(*)` **=** `trades_seen` from `evaluate_completeness(root, open_ts_epoch=…)` for the **same** root and epoch.  
Optional stricter mode: restrict to `complete_trade_ids` only when the question is **chain-certified** attribution (then count = `trades_complete`).

**Command:**

```bash
PYTHONPATH=. python3 scripts/audit/export_strict_quant_edge_review_cohort.py \
  --root /root/stock-bot --open-ts-epoch 1774458080 \
  --out-json reports/ALPACA_STRICT_QUANT_EDGE_COHORT.json
```

Exit code **1** if cohort list length ≠ `trades_seen` or complete list ≠ `trades_complete`.

---

## Workstream I — Ten required views (each must produce a HOW)

1. Signal **agreement count** vs PnL.  
2. Signal **disagreement penalty** (conditional expectancy).  
3. **Latency** sensitivity (intent→fill, signal staleness buckets).  
4. **Exit optionality** loss (MFE vs capture).  
5. **False positive cost** per signal (entries that lose).  
6. **Win/loss asymmetry** ratio and tail contribution.  
7. **Loss clustering** in time (serial correlation / regime).  
8. **Regime transition** trades (first/last hour, vol spike days).  
9. **Signal persistence** during hold (drift vs entry snapshot).  
10. **Anti-signal** performance when feature absent (baseline vs conditional).

---

## Loss review template (copy per cluster)

| Field | Content |
|-------|---------|
| **Loss cluster name** | |
| **Scope** | Strict cohort, date range, filters |
| **Net PnL impact** | $ and % of cohort |
| **Frequency** | n trades, % of losers |
| **WHY L1** | Symptom |
| **WHY L2** | Mechanism |
| **WHY L3** | Root cause (policy / threshold / data / structure) |
| **HOW** | Kill / gate / flip / size / delay / exit change |
| **Confidence** | Low / med / high |
| **Owner** | |

---

## Success review template

- **Why does this work?**  
- **Fragility?** (single regime, thin sample, correlated outliers)  
- **Regime-dependent?**  
- **Scalable safely?** (liquidity, capacity, correlation)  
*Profit without understanding is future loss.*

---

## Definition of done

- [ ] Root causes for **all major loss clusters** (cover ≥80% of negative PnL or tail risk).  
- [ ] **Concrete action** or **explicit DO_NOTHING** per finding.  
- [ ] **Top five profit levers** named (with mechanism).  
- [ ] **Top five loss leaks** named (with mechanism).  
- [ ] **Board alignment** on kill / gate / flip / scale for each matrix row.  
- [ ] **Strict cohort reconciliation** passed (Workstream A acceptance).  

---

## Deliverables (file layout)

| Deliverable | Location |
|-------------|----------|
| Framework (this doc) | `docs/ALPACA_MASSIVE_QUANT_EDGE_REVIEW_FRAMEWORK.md` |
| Board summary skeleton | `docs/ALPACA_QUANT_EDGE_REVIEW_BOARD_SUMMARY_TEMPLATE.md` |
| Quant appendix / table spec | `docs/ALPACA_QUANT_EDGE_REVIEW_APPENDIX_TABLES_SPEC.md` |
| Decision matrix template | `docs/ALPACA_QUANT_EDGE_REVIEW_DECISION_MATRIX_TEMPLATE.md` |
| Cohort export | `reports/ALPACA_STRICT_QUANT_EDGE_COHORT.json` (generated) |

---

## Related scripts (non-exhaustive)

- `scripts/audit/alpaca_pnl_massive_final_review.py` — PnL bundle + SPI-style sections.  
- `scripts/audit/alpaca_forward_truth_contract_runner.py` — session truth JSON for gates.  
- `telemetry/alpaca_strict_completeness_gate.py` — strict cohort definition.  
- `src/analysis/signal_edge_analysis.py` — signal-level edge metrics patterns.  

---

## Governance note

This review **does not** relax strict completeness or warehouse gates. It **consumes** strict cohort truth for **causal** and **operational** levers. When **DATA_READY** becomes YES, re-run decomposition workstreams (B, F warehouse slices) for **reconciliation** with board packets — second pass, not a substitute for strict-log forensics.
