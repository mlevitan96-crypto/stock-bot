# ALPACA GOVERNANCE CONTEXT BLOCK
# (Meta Governance + Alpaca Stock Bot)
# This block is authoritative for Alpaca only.
# It must not reference Kraken or any crypto-bot concepts.

===========================================================
SECTION A — GOVERNANCE RULES (AUTHORITATIVE)
===========================================================

These institutional concepts govern the Alpaca bot.
Cursor's multi-models must enforce, challenge, and evolve them.

-----------------------------------------
A1. TRUTH CONTRACTS (INSTITUTIONAL INVARIANTS)
-----------------------------------------
Every subsystem must prove correctness before deployment.

Truth contracts include:
- Telemetry completeness
- Exit policy correctness
- Directionality fairness
- Shadow learning health
- Attribution integrity
- Capacity allocation correctness
- Dashboard truth parity
- Infra fallback correctness
- Schema integrity
- Score snapshot consistency

Cursor responsibilities:
- Enforce all contracts
- Propose missing contracts
- Challenge weak contracts
- Identify contradictions
- Generate tests
- Generate PRs to fix violations

-----------------------------------------
A2. SYNTHETIC LAB MODE (DETERMINISTIC SANDBOX)
-----------------------------------------
Every idea must be tested deterministically before live deployment.

Lab mode must simulate:
- Scoring
- Entries/exits
- Capacity
- Directionality
- Attribution
- Blocked trades
- Infra failures
- Market regimes

Cursor responsibilities:
- Run lab mode
- Propose new lab tests
- Challenge lab assumptions
- Compare lab vs live behavior
- Generate PRs for discrepancies

-----------------------------------------
A3. ATTRIBUTION DECOMPOSITION (EXPLAINABILITY ENGINE)
-----------------------------------------
Every decision must be decomposed into:
- Signal contributions
- Scoring components
- Exit drivers
- Capacity blockers
- Shadow vs live deltas
- Regime effects
- Volatility effects

Cursor responsibilities:
- Run attribution
- Propose new components
- Challenge attribution logic
- Identify missing or contradictory signals

-----------------------------------------
A4. BLOCKED-WINNER FORENSICS
-----------------------------------------
Every missed opportunity must be analyzed.

Forensics must:
- Rank blocked trades by counterfactual PnL
- Attribute blame to gates
- Propose relaxations
- Propose promotions
- Propose threshold changes

Cursor responsibilities:
- Run forensics
- Challenge ranking logic
- Propose new gating rules

-----------------------------------------
A5. SHADOW LEARNING HEALTH
-----------------------------------------
Shadow must:
- Learn from every blocked trade
- Produce consistent score snapshots
- Maintain telemetry provenance
- Avoid drift and staleness

Cursor responsibilities:
- Audit shadow learning
- Propose relaxations and experiments
- Challenge shadow assumptions

-----------------------------------------
A6. DIRECTIONALITY FAIRNESS
-----------------------------------------
No directional bias unless proven profitable.

Cursor responsibilities:
- Audit long/short symmetry
- Propose corrections
- Propose new fairness metrics

-----------------------------------------
A7. CAPACITY ALLOCATION
-----------------------------------------
Capacity is scarce and must be justified.

Cursor responsibilities:
- Identify capacity blockers
- Propose reallocation
- Propose threshold changes
- Propose symbol promotions/demotions

-----------------------------------------
A8. TELEMETRY PROVENANCE
-----------------------------------------
Every metric must be traceable to its source.

Cursor responsibilities:
- Audit telemetry
- Detect missing fields
- Detect schema drift
- Propose fixes

-----------------------------------------
A9. DEPLOYMENT AUTHORIZATION
-----------------------------------------
No change goes live without explicit human approval.

Cursor responsibilities:
- Generate PRs
- Attach proofs, lab results, contract checks
- Attach attribution deltas and risk assessments

-----------------------------------------
A10. MEMORY BANK
-----------------------------------------
Every run, anomaly, and decision becomes institutional memory.

Cursor responsibilities:
- Update Memory Bank
- Propose new sections
- Challenge outdated knowledge

-----------------------------------------
A11. DAILY "WHAT'S WRONG?" REPORT
-----------------------------------------
Every day begins with adversarial anomaly hunting.

Cursor responsibilities:
- Run all diagnostics
- Rank anomalies
- Propose fixes
- Challenge assumptions
- Generate the daily report

-----------------------------------------
A12. DASHBOARD TRUTH AUDIT
-----------------------------------------
Dashboard must reflect backend truth.

Cursor responsibilities:
- Audit endpoints
- Validate schemas
- Detect drift
- Propose fixes

-----------------------------------------
A13. MULTI-MODEL ADVERSARIAL REVIEW
-----------------------------------------
Cursor must:
- Run multiple models
- Assign critic / prosecutor / defender / synthesizer roles
- Escalate contradictions
- Refine proposals

-----------------------------------------
A14. PLUGIN ORCHESTRATION
-----------------------------------------
Cursor must:
- Use Parallel for concurrent diagnostics
- Use Continual Learning to retain governance preferences
- Use Create Plugin when a behavior should be formalized and reused


===========================================================
SECTION B — CURRENT STATE (FACTUAL, NON-NEGOTIABLE)
===========================================================

Cursor must treat this section as ground truth and update it only when changes are actually implemented and verified.

**Discovered/verified for this repo (Alpaca stock-bot):**

| Concept | Location / value |
|--------|-------------------|
| Venue | Alpaca (stocks) |
| Execution | Alpaca API (orders, positions, account) |
| Market data | Alpaca historical bars + live feed (`data/bars_loader.py`, `scripts/alpaca_ws_collector.py`, `scripts/fetch_alpaca_bars.py`) |
| Strategy | Multi-signal scoring + gating (as implemented in `main.py`) |
| Shadow learning | Per repo config; audit via `reports/_daily_review_tools/generate_shadow_audit.py` (event types: `shadow_candidate`, `shadow_executed`, `shadow_exit`, `shadow_pnl_update`, `score_compare`, `divergence`) |
| Capacity | `MAX_OPEN_POSITIONS` and per-symbol/per-sector caps in `main.py` |
| Governance runner | **No** `scripts/run_governance_full.py`. Canonical processes: **EOD** `board/eod/run_stock_quant_officer_eod.py`; **Molt** `scripts/run_molt_on_droplet.sh`; **comparison** `scripts/governance/compare_backtest_runs.py`; **AI governance chair** `moltbot/agents/governance_chair.py` (`run_governance_chair`) |
| Daily report / governance index | `reports/GOVERNANCE_DISCOVERY_INDEX.md`; governance comparison outputs: `reports/governance_comparison/` |
| Memory Bank | `MEMORY_BANK.md` (root) |
| Attribution truth contract | `docs/ATTRIBUTION_TRUTH_CONTRACT.md`; canonical schema `docs/ATTRIBUTION_SCHEMA_CANONICAL_V1.md`; code: `src/exit/exit_attribution.py` (`ATTRIBUTION_SCHEMA_VERSION`), `schema/attribution_v1.py`, `schema/contract_validation.py` |
| Data feed health contract | `scripts/data_feed_health_contract.py` → `reports/data_integrity/DATA_FEED_HEALTH_CONTRACT.md` and `.json` |
| Lifecycle events schema (gate + shadow) | `docs/ALPACA_LIFECYCLE_EVENTS_SCHEMA.md`; validator: `scripts/validate_lifecycle_events_schema.py` |
| Infra fallback contract | `docs/ALPACA_INFRA_FALLBACK_CONTRACT.md` (market data, order failures, rate limits; code refs only) |
| Shadow starvation policy | `docs/ALPACA_SHADOW_STARVATION_POLICY.md`; optional diagnostic: `scripts/diagnose_shadow_starvation.py` |
| Daily run integrity contract | `docs/ALPACA_DAILY_RUN_INTEGRITY_CONTRACT.md`; validator: `scripts/validate_daily_governance_artifacts.py`; canonical entry: `scripts/run_daily_governance.sh` |

If any of the above paths/files differ in the Alpaca repo, Cursor must discover the correct locations, update this section, and keep all Alpaca governance self-contained.


===========================================================
SECTION C — OPEN ADVERSARIAL ITEMS (REQUIRES ACTION)
===========================================================

Cursor must focus adversarial review here and propose/implement concrete fixes.

---

**C1. Venue isolation**

- **Status:** No Kraken/crypto-only checks, symbols, or data paths found in Alpaca code. Only `venue: "alpaca"` and a comment in `scripts/entry_intelligence_parity_audit.py` that "None are crypto-specific for stock-bot."
- **Action:** Add venue guards only if cross-venue logic is introduced (e.g. `if venue != "alpaca": return` or config-driven branch). No code change required until then.

---

**C2. Schema truth contract**

- **Status:** **Implemented.** Attribution schema and truth contract remain in place; gate-trace and shadow lifecycle events are now specified and validated.
  - **Attribution (unchanged):** `docs/ATTRIBUTION_TRUTH_CONTRACT.md`, `docs/ATTRIBUTION_SCHEMA_CANONICAL_V1.md`; `src/exit/exit_attribution.py`, `schema/attribution_v1.py`, `schema/contract_validation.py`.
  - **Lifecycle events (gate + shadow):** `docs/ALPACA_LIFECYCLE_EVENTS_SCHEMA.md` — required fields for blocked_trades (gate traces) and shadow events; WARN vs FAIL semantics documented (missing required → FAIL in validator; missing optional → WARN).
  - **Validator:** `scripts/validate_lifecycle_events_schema.py` — runs over `state/blocked_trades.jsonl` and `logs/shadow.jsonl`; default WARN-only; `--fail-on-required` for strict. Can be wired into EOD or daily diagnostics.
- **Next steps:** Run validator in governance/EOD flow if desired; add new event_type values to the spec as they appear.

---

**C3. Infra fallback contract**

- **Status:** **Implemented.** Single contract document and code references in place; no new automated tests (per plan).
  - **Doc:** `docs/ALPACA_INFRA_FALLBACK_CONTRACT.md` — expected behavior for: (1) market data outages (bars 1m→5m/15m fallback, UW defer, websocket health); (2) order submission failures (no retry same order on reject; bounded retry on transient); (3) rate limits (Alpaca 429 back off; UW rate limit log and defer). Each scenario references existing code paths (`data/bars_loader.py`, `scripts/data_feed_health_contract.py`, `src/uw/uw_client.py`, `main.py`).
  - **Verification:** Run `python scripts/data_feed_health_contract.py`; inspect `reports/data_integrity/DATA_FEED_HEALTH_CONTRACT.md` and `.json`.
- **Next steps:** Add an automated test only if explicitly justified and approved.

---

**C4. Shadow starvation policy**

- **Status:** **Implemented.** Definition, policy, and optional diagnostic in place; no enforcement without approval.
  - **Definition:** Shadow starvation = at least one blocked_trade in the period and no corresponding shadow_candidate (or shadow_variant_decision) for that opportunity. See `docs/ALPACA_SHADOW_STARVATION_POLICY.md`.
  - **Policy:** **WARN only.** Do not FAIL pipeline or deployment when starvation is detected; prefer observability. Conditional FAIL only if governance later approves and is gated (e.g. shadow-auditable run flag).
  - **Diagnostic:** `scripts/diagnose_shadow_starvation.py` — compares `state/blocked_trades.jsonl` vs `logs/shadow.jsonl` for a date; reports starved symbols; exit 0 by default; `--strict` exits 1 when starvation detected (use only after approval). Not wired as mandatory gate.
- **Next steps:** Run diagnostic in daily/EOD review; consider adding a starvation sentence to `generate_shadow_audit.py` output as informational only.

---

**Daily run integrity (fail-closed)**

- **Status:** **Implemented.** Daily run is explicit and fail-closed; execution integrity FAIL when required artifacts or phases are missing.
  - **Contract:** `docs/ALPACA_DAILY_RUN_INTEGRITY_CONTRACT.md` — required phases (Molt orchestration, governance chair, discovery index, daily board output, attribution summary, diagnostics summaries), required artifacts and locations, run window for timestamp alignment, FAIL conditions (Molt exit != 0, chair no output, missing/empty artifact, timestamp misalignment). Analytical issues remain WARN-only.
  - **Validator:** `scripts/validate_daily_governance_artifacts.py` — verifies required files exist, non-empty, optional timestamp in run window; exit non-zero on any FAIL; `--date`, `--base-dir`, `--skip-timestamps`.
  - **Canonical entry point:** `scripts/run_daily_governance.sh` — runs Molt (`scripts/run_molt_on_droplet.sh`), then artifact validation; single PASS/FAIL verdict; exit 1 if Molt or validation fails.
- **Failure modes now prevented:** Molt exits early (validator sees missing molt_last_run.json or exit_code != 0); governance chair emits no output (validator requires PROMOTION_PROPOSAL or REJECTION_WITH_REASON); missing/empty discovery index or diagnostics; silent board breakage (explicit FAIL instead of silent skip).

---

# END OF ALPACA GOVERNANCE CONTEXT BLOCK
