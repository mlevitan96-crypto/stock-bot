# AI Board Synthesis — Attribution Mega-Block

**Date:** 2026-02-17  
**Scope:** Granular intelligence attribution, scoring transparency, exit/entry optimization, backtest + lab, dashboards, docs, deploy.

---

## 1. Critique: What’s Overkill, What’s Missing, Fastest Path to Value

### Overkill / Defer

- **Periodic mid-trade snapshots (post_entry)**  
  High storage and complexity for marginal gain at first. Defer until entry/exit attribution is stable and you’re explicitly testing “hold longer” vs “exit now” with in-trade features.

- **Full tree for every component (deep sub_components)**  
  One level of decomposition (e.g. flow → premium, sweep_ratio, conviction) is enough for “which micro-signal helped.” Deeper trees can be added later for specific analyses.

- **Real-time dashboard for every component**  
  Start with “per-trade drill-down” (entry + exit component breakdown + exit quality). Aggregate “top components for winners/losers” can be a batch report or weekly view.

### Missing

- **MFE/MAE at write time**  
  You need max favorable/adverse excursion per trade for exit quality. Today these are not stored; add them at exit (from position_metadata or a small history buffer).

- **Stable trade_id early**  
  `trade_id` is currently set at fill (e.g. `open_SYMBOL_ts`). Define a stable `attribution_id` at entry decision and carry it through to exit so entry and exit snapshots always join.

- **Config-driven exit reason mapping**  
  `build_composite_close_reason` produces long strings; analytics need a single primary code. Add a small mapping table (composite string → primary exit_reason_code) in config so dashboards and reports are consistent.

### Fastest path to value

1. **Schema + contracts (Phase 1)** — Done. Use them as the single contract for all producers.
2. **UW decomposition (Phase 2)** — Done (module + tests + config). Wire UW micro-signals into the scoring pipeline so entry/exit snapshots include them; no need to replace the existing composite score yet—add as an extra tree “uw_micro” under the same snapshot.
3. **Exit quality metrics (Phase 5)** — Add MFE/MAE/profit giveback/time-in-trade to exit attribution and to the same store. Enables “tune exits without degrading entries” immediately.
4. **Persistence (Phase 4)** — One canonical store (e.g. `logs/attribution_v2.jsonl` or extend `attribution.jsonl` with a `schema_version` and component tree). Backfill only recent N days.
5. **Backtest + lab (Phase 6)** — Emit same attribution records from backtest; lab mode injects components deterministically. Enables “config A vs config B” and hypothesis testing.
6. **Dashboards (Phase 7)** — One new panel: “Trade drill-down” (entry tree + exit tree + exit quality). Then add “component effectiveness” as a report or second panel.

---

## 2. Additional Edge Features (Especially Around Exits)

- **Excursion after exit**  
  For N minutes after exit, track whether price went further in our favor. Metric: “would we have been better holding?” Store as optional flag or small summary (e.g. post_exit_benefit_pct).

- **Slippage vs expected**  
  At exit you have decision price vs fill price. Store expected_exit_price (e.g. from midpoint at decision time) and realized; slippage_bps = f(realized, expected). Enables execution quality tuning.

- **Partial exits**  
  If you support scale-outs, each slice should have its own attribution slice (entry snapshot shared, exit snapshot + MFE/MAE/profit giveback per slice).

- **Regime at exit vs at entry**  
  You already have entry_regime and exit_regime in exit_attribution. Add a simple “regime_shift” flag (same/different) and segment exit quality by “held through regime shift” vs “exited in same regime.”

- **Time-of-day and day-of-week at exit**  
  Already in log_exit_attribution (time_of_day, day_of_week). Ensure they’re in the canonical attribution record and in exit quality so you can segment “exits at open vs mid-day vs close.”

- **Volatility bucket at exit**  
  If you have realized_vol_20d or similar at exit, store it (or a bucket). Segment “exit quality in high vol” vs “low vol.”

---

## 3. Prioritized Rollout (Schema Stable)

Keep the schema (v1) and truth contract fixed. Roll out in this order:

| Priority | Phase | Deliverable | Rationale |
|----------|--------|-------------|-----------|
| P0 | 1 | Schema + truth contract | Foundation; no code refactor yet. |
| P1 | 2 | UW micro-signals module + tests + config | Decomposition without breaking existing score. |
| P2 | 5 | Exit quality (MFE, MAE, profit giveback, time-in-trade) | Needed to tune exits. |
| P3 | 4 | Attribution persistence (one store, versioned, backfill script) | Enables query by trade_id and by component_key. |
| P4 | 3 | Scoring pipeline emits full component tree | Replace opaque totals with tree; config-driven weights. |
| P5 | 6 | Backtest + lab emit same attribution; lab injects components | Config A vs B and hypothesis testing. |
| P6 | 7 | Dashboard: trade drill-down + component effectiveness | Auditable, no opaque panels. |
| P7 | 8 | Docs, tests, deployment, proof artifacts | Governance and repeatability. |

---

## 4. Performance and Storage (Without Losing Auditability)

- **Storage**  
  Append-only JSONL is fine. Optional: partition by month or week (e.g. `logs/attribution/2026-02.jsonl`) to keep files small and speed up “recent” queries. Keep a single canonical path in config (e.g. current month) so dashboard and backtest read from the same place.

- **Sampling**  
  Do not sample attribution records—every trade must have entry + exit attribution. You can sample telemetry or high-frequency snapshots if you add post_entry later.

- **Compression**  
  Gzip older JSONL files (e.g. after 30 days) if size becomes an issue. Keep last 30 days uncompressed for fast tail reads.

- **Indexing**  
  For “by trade_id” and “by component_key” queries: either a small SQLite index (trade_id, symbol, timestamp_utc) built from JSONL, or a daily batch that builds a Parquet/JSON index for analytics. Prefer “query helper script + JSONL” first; add index only when query time is a problem.

- **Backfill**  
  Backfill only last N days (e.g. 30) from existing logs (attribution.jsonl, master_trade_log, exit_attribution). New fields (e.g. MFE/MAE) will be null for backfilled rows; document that in the schema.

---

## 5. What Was Delivered (This Session)

- **Phase 0:** Repo map — `docs/ATTRIBUTION_MEGA_BLOCK_PHASE0_REPO_MAP.md` (UW, scoring, entry/exit, lifecycle, telemetry, backtest, lab, dashboards; panel → endpoint → producer → schema → source).
- **Phase 1:** Canonical schema `schema/attribution_v1.py` (ScoreComponent, AttributionSnapshot, TradeAttributionRecord; lifecycle stages; dict constructors). Truth contract `docs/ATTRIBUTION_TRUTH_CONTRACT.md`. JSON Schema `schema/attribution_v1.schema.json`. Contract validation `schema/contract_validation.py`.
- **Phase 2:** UW micro-signals `src/uw/uw_micro_signals.py` (flow, dark_pool, insider decomposition; raw, normalized, contribution, quality). Config `config/uw_micro_signal_weights.yaml`. Unit tests `validation/scenarios/test_uw_micro_signals.py`.
- **Contract tests:** `validation/scenarios/test_attribution_schema_contract.py` (total_score == sum(contributions), exit_reason_code required, entry/exit snapshot validation).

---

## 6. Next Steps (Implementation Order)

1. Wire UW micro-signals into `log_attribution` and `log_exit_attribution` (or into the composite pipeline) so each snapshot includes an `uw_micro` component tree.
2. Add MFE/MAE/profit giveback/time-in-trade to exit attribution and to the canonical record (Phase 5).
3. Add a single persistence path for attribution v1 records (Phase 4) and a small backfill script for recent history.
4. Refactor scoring pipeline to emit full component tree and satisfy contract (Phase 3).
5. Update backtest and lab to emit and validate attribution records (Phase 6).
6. Add dashboard panel “Trade drill-down” and “Component effectiveness” (Phase 7).
7. Document “How to add a new signal component,” “How to run backtests and compare configs,” “How to interpret exit quality” (Phase 8); deploy to droplet and produce proof artifacts.
