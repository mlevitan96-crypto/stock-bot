# Phase 1 — Critique and Expansion

**Scope:** Critique of the attribution approach; additional signal dimensions to capture; performance/storage risks and mitigations.  
**Constraint:** Instrumentation-first, optimization-second. No weight/threshold/exit logic/dashboard changes until attribution exists and is validated.

---

## 1. Critique: What Is Overkill, What Is Missing, What to Simplify or Stage

### Overkill (defer or simplify)

- **Periodic mid-trade snapshots (e.g. every N minutes)**  
  Full POST_ENTRY snapshots on a timer add storage and complexity. Defer until ENTRY_DECISION, ENTRY_FILL, EXIT_DECISION, EXIT_FILL are stable and you explicitly need "state at T during hold" for experiments.

- **Deep component trees (many levels)**  
  One level of decomposition (e.g. flow → premium, sweep_ratio, conviction) is enough for "which micro-signal helped." Deeper trees can be added later for specific analyses.

- **Real-time dashboard for every component**  
  Start with "per-trade drill-down" (entry + exit trees + exit_reason_code). Aggregate "top components for winners/losers" can be a batch report or weekly view.

- **Mandatory sub_components for every composite**  
  Stage: require flat components first; allow optional sub_components where the pipeline naturally has a tree (e.g. UW flow micro-signals).

### Missing

- **MFE/MAE at write time**  
  Max favorable/adverse excursion is not in the schema yet. Needed for exit quality (profit giveback, "did we exit too early?"). Add as optional fields on exit snapshot or on a separate exit_quality payload when Phase 4/5 implement persistence.

- **decision_id on every snapshot**  
  Already in canonical schema; ensure producers emit it so "per evaluation cycle" attribution works even when no trade results (blocked entries, skipped cycles).

- **Mapping from composite close reason string → primary exit_reason_code**  
  Schema defines the taxonomy; a small config or mapping table (composite string → primary code) is needed so all producers and analytics use the same code. Add in Phase 2–4 when exit attribution is wired.

- **Execution quality at fill**  
  Entry/exit fill snapshots could carry expected_price vs fill_price (or slippage_bps) so "execution quality" is a first-class dimension later. Optional in schema v1; add when persistence is in place.

### Simplify or stage

- **Simplify:** Require only the four snapshot types (ENTRY_DECISION, ENTRY_FILL, EXIT_DECISION, EXIT_FILL). Do not add more stages until there is a clear use case.
- **Stage:** Implement minimal + weight + normalized_value + quality_flags first; add raw_value and sub_components where natural (e.g. UW decomposition in Phase 2).
- **Simplify:** One canonical store (e.g. one JSONL or one table) with schema_version on every row; avoid multiple competing attribution logs until one is clearly the source of truth.

---

## 2. Additional Signal Dimensions Not Currently Logged

Focus: exits, execution quality, regime interaction, correlation.

- **Exits**  
  - **MFE / MAE** — Max favorable and max adverse excursion (from entry to exit). Enables profit giveback and "exit too early" analysis.  
  - **Time in trade** — Already often logged; ensure it is in the canonical exit payload and in exit_quality.  
  - **Excursion after exit** — For N minutes after exit, did price move further in our favor? Optional flag or metric for "would we have been better holding?"  
  - **Exit component tree** — Full component tree at EXIT_DECISION/EXIT_FILL (same schema as entry) so "which exit signals fired" is auditable.

- **Execution quality**  
  - **Expected vs fill price** — At entry and exit: expected (e.g. midpoint at decision time) vs fill price; derive slippage_bps.  
  - **Spread/depth at decision** — Optional: bid/ask spread or depth at decision time for liquidity context.

- **Regime interaction**  
  - **Regime at entry vs regime at exit** — Already in some exit attribution; ensure entry_regime and exit_regime (or regime_shift flag) are in the canonical record for "held through regime change" vs "exited in same regime."  
  - **Regime at decision** — Store regime (or regime_label) on each snapshot so component contributions can be segmented by regime.

- **Correlation**  
  - **Theme/sector at entry and exit** — For theme risk and concentration: which theme/sector the symbol belonged to at entry and exit.  
  - **Time-of-day / day-of-week** — Already in some logs; ensure they are in the canonical attribution or exit_quality for segmentation (e.g. "exits at open vs close").

These can be added as optional fields or a separate exit_quality / execution_quality payload so schema v1 stays stable while you add dimensions.

---

## 3. Performance and Storage Risks and Mitigations

**Without losing auditability or replay fidelity.**

- **Storage volume**  
  - **Risk:** One snapshot per decision × many components × four stages per trade can grow quickly.  
  - **Mitigation:** Append-only JSONL; optional partition by month/week (e.g. `logs/attribution/2026-02.jsonl`) to keep single-file size bounded. Keep a single canonical path in config for "current" period.  
  - **Retention:** Keep full fidelity for last N days (e.g. 90); beyond that, allow tiered retention (e.g. compress or aggregate) but never delete attribution rows in-place; archive with same schema so replay is possible.

- **Sampling**  
  - **Do not sample attribution records.** Every trade MUST have entry and exit snapshots. Sampling would break "every ENTRY has a snapshot" and "every EXIT has a snapshot."  
  - Optional: If you add high-frequency POST_ENTRY snapshots later, you could sample those (e.g. every 10th) for storage, but the four required snapshots (ENTRY_DECISION, ENTRY_FILL, EXIT_DECISION, EXIT_FILL) must not be sampled.

- **Compression**  
  - **Mitigation:** Gzip or similar for older files (e.g. after 30 days) to save space. Keep recent files uncompressed for fast tail reads and simple tooling (e.g. `tail`, jq).  
  - **Auditability:** Compressed files must remain readable and schema-versioned; replay scripts must support reading compressed logs.

- **Indexing**  
  - **Risk:** Querying "by trade_id" or "by component_key" over large JSONL is slow.  
  - **Mitigation:** Start with "query helper script + JSONL" (e.g. filter by trade_id or date range). If query time becomes a problem, add a small index (e.g. SQLite or daily Parquet) keyed by trade_id, symbol, timestamp_utc, built from the same JSONL. Index is derived; JSONL remains source of truth for audit and replay.

- **Backfill**  
  - **Mitigation:** Backfill only last N days from existing logs; new fields (e.g. MFE/MAE, execution quality) may be null for backfilled rows. Document "backfilled" or "reconstructed" in schema or a separate flag so analysts know.

Summary: append-only, optionally partitioned and compressed for older data; no sampling of required snapshots; add indexing only when needed; backfill with explicit handling of missing fields.
