# Phase 8 / Phase 9 — Cursor multi-model review

**Date:** 2026-02-17 (Phase 8); 2026-02-18 (Phase 9 update)

---

## 1. Adversarial auditor

**Focus:** What can silently break? Where are joins/IDs fragile? What invariants are missing?

### Findings

1. **Join fragility — entry index only "open_*" trade_ids**  
   `attribution_loader.load_joined_closed_trades` builds `entry_by_trade_id` only for records whose `trade_id` starts with `"open_"`. If live logs ever write a different trade_id format (e.g. UUID after fill, or `decision_id` only), those entries will not join on trade_id; we fall back to (symbol, entry_ts_bucket). That fallback is correctly flagged with `quality_flags=["join_fallback"]`, but the **contract** (trade_id as primary when present) is only honored when entry trade_id is `open_*`. Document this contract or extend indexing to any non-empty trade_id.

2. **Exits without entry_timestamp are dropped**  
   If an exit record has no `entry_timestamp` / `entry_ts`, `exit_key(ex)` returns None and that exit is skipped entirely. We do not append a row with `quality_flags=["missing_entry_ts"]`. So we silently drop exits that lack entry_ts — no count, no flag. **Recommendation:** Either add a "dropped_exits_count" (and optional list of reasons) to the loader output, or emit a row with minimal fields + quality_flags so every exit is accounted for.

3. **Guards do not validate persisted snapshots**  
   Regression guards check **code-level** invariants (uw_composite_v2, exit_score_v2): sum(components) == score. They do **not** validate that existing logs (attribution.jsonl, exit_attribution.jsonl) satisfy the same. A writer bug could persist wrong data and guards would still pass. **Recommendation:** Optional "log validator" mode: sample N records from logs, recompute score from components, assert equality (or document as "do later").

4. **Dashboard trade lookup — last 5000/3000 lines only**  
   `/api/attribution/trade/<trade_id>` reads the last 5000 lines of attribution and 3000 of exit_attribution. Old trades beyond that window will not be found. Not silent wrong data, but **truth gap**: dashboard may say "No joined record" for a valid old trade_id. **Recommendation:** Document the window in the API doc or UI (e.g. "Lookup limited to last N trades").

5. **Backtest join always gets join_fallback**  
   `load_from_backtest_dir` does not have trade_id in backtest outputs today, so every row gets `quality_flags=["join_fallback"]`. Correct and explicit. No change needed.

### Concrete recommendations (adversarial)

| Item | Do now | Do later |
|------|--------|-----------|
| Document "open_*" trade_id contract for entry index | ✓ Add one line in attribution_loader docstring | — |
| Exits missing entry_ts: drop vs flag | — | Add dropped_exits_count or emit minimal row with quality_flags |
| Log invariant validator (sample logs) | — | Add optional guard or script |
| Document dashboard trade lookup line window | ✓ One line in DASHBOARD_ENDPOINT_MAP or panel inventory | — |

### Missing tests (adversarial)

- **Join logic:** Test that when entry has trade_id and exit has same trade_id, joined row has no quality_flags (or no "join_fallback"); when join is by (symbol, entry_ts) only, row has quality_flags including "join_fallback".  
- **Backtest loader:** Test that load_from_backtest_dir returns rows with quality_flags=["join_fallback"] when backtest_exits have no trade_id.

---

## 2. Quant reviewer

**Focus:** What’s the highest ROI first tuning lever given Phase 5/7/8 reports?

### Findings

1. **Recommendation script already prioritizes**  
   `generate_recommendation.py` uses blame mix: if `exit_timing_pct >= weak_entry_pct` it suggests exit-weight lever (e.g. flow_deterioration +0.02); if `weak_entry_pct > exit_timing_pct` it suggests entry lever (down-weight worst signal or raise threshold). So the **highest ROI first lever** is the one suggested by the generated recommendation, backed by entry_vs_exit_blame + signal_effectiveness + exit_effectiveness.

2. **Smallest delta is +0.01–0.03**  
   Existing overlay `exit_flow_plus_0_02.json` uses +0.02. This is in the safe band. First cycle should pick **one** such lever from the recommendation (or from manual read of baseline JSONs).

3. **Falsification criteria are in the proposal template**  
   Win rate drop >2%, giveback increase >0.05, guards fail. Quant risk: overfitting to one backtest window. Mitigation: paper/canary after LOCK, and explicit "suggestion only — no auto-apply" in recommendation.

### Concrete recommendations (quant)

| Item | Do now | Do later |
|------|--------|----------|
| Use profitability_recommendation.md (or baseline blame/signal/exit JSONs) to pick one hypothesis | ✓ Required for first cycle | — |
| One lever only (one weight or one threshold), delta +0.01–0.03 | ✓ Enforced in proposal | — |
| Document baseline metrics in change proposal (exact numbers + paths) | ✓ Required | — |

### Missing tests (quant)

- None required for config-only overlay. Comparison script and guards are the tests.

---

## 3. Product reviewer

**Focus:** Is the dashboard telling the truth? Any UX gaps that hide edge?

### Findings

1. **Source vs latest_backtest_dir**  
   Dashboard shows "Data freshness", source path, and "From latest backtest" vs "From reports fallback". Truth: `_get_effectiveness_dir()` uses state/latest_backtest_dir.json first, then reports/effectiveness_*. So if latest_backtest_dir.json is not updated after a run, dashboard can show **stale** effectiveness (old backtest). **Recommendation:** Ensure droplet pipeline writes latest_backtest_dir.json (already in run_30d_backtest_on_droplet.sh). No UX change; operational discipline.

2. **Trade ID search**  
   Works when trade_id exists in logs and within the last 5000/3000 lines. Shows entry/exit attribution tables, exit quality, blame hint. **Gap:** If user pastes a trade_id from backtest (e.g. from backtest_exits.jsonl), backtest data is **not** in logs/attribution.jsonl — it's in backtest dir. So trade lookup is **live-logs only**. Dashboard does not search backtest dir. **Recommendation:** Document: "Trade ID lookup uses live logs (attribution.jsonl, exit_attribution.jsonl). For backtest trades, use effectiveness tables or export from backtest dir." Optionally (do later): add a "Backtest dir" selector and search within that dir's joined data.

3. **Download JSON**  
   Uses fetch-with-credentials; works with Basic Auth. Truth: same data as the effectiveness APIs. No gap.

4. **Blame hint**  
   Heuristic (low entry_score → weak entry; high giveback / had MFE → exit timing). Matches report logic. OK for single-trade UX.

### Concrete recommendations (product)

| Item | Do now | Do later |
|------|--------|----------|
| Document "Trade lookup = live logs only" in panel inventory or UI hint | ✓ One line in README or panel inventory | — |
| Verify latest_backtest_dir.json is written after every droplet backtest | ✓ Operational check | — |

### Missing tests (product)

- None required for dashboard logic. Manual verification (Step G) covers "dashboard truth".

---

## Summary

- **Invariants:** Code-level guards pass. Join uses trade_id when present (for open_* entries), fallback flagged. No validation of persisted logs yet (do later).
- **Dashboard:** Tells truth for effectiveness source and freshness; trade lookup is live-logs-only (document).
- **Quant:** First lever = recommendation or baseline-driven; one overlay, small delta; falsification in proposal.

---

## Do now (Phase 9)

1. Add one-line doc: entry index requires trade_id starting with "open_*" for trade_id join (attribution_loader).
2. Document dashboard trade lookup window / live-logs-only (DASHBOARD_PANEL_INVENTORY or phase7_proof README).
3. Add test: join logic (trade_id primary vs fallback quality_flags).

## Do later

1. Exits missing entry_ts: report dropped count or emit minimal row with quality_flags.
2. Optional log invariant validator (sample logs, assert sum(components)==score).
3. Optional: dashboard "Backtest dir" selector for trade lookup in a chosen backtest.
