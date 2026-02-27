# Phase 1 — Canonical Attribution Schema (v1.0.0)

**Status:** LOCKED as canonical. All producers and consumers MUST conform.  
**Phase 0 reference:** `docs/ATTRIBUTION_MEGA_BLOCK_PHASE0_REPO_MAP.md` (single source of truth for repo map).

---

## 1. Design Principles

- Every decision is **explainable, auditable, and tunable at the micro-signal level**.
- **No opaque totals:** every score is the sum of named component contributions.
- **No silent absence:** missing, stale, or conflicting data is explicit (flags or `missing_reason`).
- **UW is never a single number:** UW is decomposed into first-class micro-signals with the same shape as internal signals.
- **Penalties and boosts** are explicit signed components (negative/positive contributions).

---

## 2. Identifiers

| Field | Required | Description |
|-------|----------|-------------|
| **trade_id** | Yes (for trade-scoped records) | Uniquely identifies a trade (e.g. `live:AAPL:2026-02-17T14:30:00Z` or `open_AAPL_<ts>`). |
| **decision_id** | Yes (for every snapshot) | Uniquely identifies one evaluation cycle (e.g. `dec_<symbol>_<timestamp_utc>`). Enables "per decision" attribution even when no trade results. |
| **attribution_id** | Optional (recommended for closed trades) | Stable id for the full attribution record (entry + exit). Links dashboards and backtest outputs. |
| **snapshot_id** | Optional | Unique id for a single snapshot (e.g. `snap_<decision_id>_<stage>`). |

---

## 3. Snapshot Types (Lifecycle Stages)

Exactly four snapshot types are used for the full trade lifecycle:

| Snapshot type | When emitted | Purpose |
|---------------|--------------|---------|
| **ENTRY_DECISION** | At signal evaluation / gate pass; before order submit | Score and component tree at "we decided to enter." |
| **ENTRY_FILL** | After entry order fill | Score and component tree at fill; may match ENTRY_DECISION or reflect fill-time data. |
| **EXIT_DECISION** | When exit is decided; before exit order submit | Score and component tree at "we decided to exit." |
| **EXIT_FILL** | After exit order fill | Final snapshot; must include exit_reason_code. |

**Invariant:** Every ENTRY (trade open) has at least one of ENTRY_DECISION or ENTRY_FILL. Every EXIT (trade close) has at least one of EXIT_DECISION or EXIT_FILL, and the exit record MUST include a non-empty **exit_reason_code**.

---

## 4. Score Component (Per Signal / Sub-Signal)

Every component (signal or sub-signal) has the same shape. UW micro-signals are first-class components; they use a **namespaced signal_id** (e.g. `uw.flow_premium`, `uw.flow_sweep_ratio`, `uw.dp_notional`, `uw.insider_activity`) and the same fields as internal signals.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **signal_id** | string | Yes | Stable, namespaced id (e.g. `uw.flow_premium`, `internal.regime_modifier`, `derived.toxicity_penalty`). UW MUST use `uw.*` namespace. |
| **name** | string | Yes (legacy alias) | Same as signal_id or human-readable label. For compatibility. |
| **source** | string | Yes | One of: `uw` \| `internal` \| `derived`. |
| **raw_value** | any | No | Raw value(s) from source (number, string, object, or array). |
| **normalized_value** | number | No | Normalized value used in score (e.g. 0–1 or signed). |
| **weight** | number | No | Weight applied (from config). |
| **contribution_to_score** | number | Yes | **Signed** contribution to total score. Penalties are negative. |
| **confidence** | number [0,1] | No | Confidence or quality score. |
| **quality_flags** | string[] | No | Explicit flags: `stale`, `missing`, `conflicting`, `low_liquidity`, `defaulted`, etc. Never silent—if data is bad, a flag MUST be set. |
| **missing_reason** | string | No | If component is absent or defaulted: reason (e.g. `no_flow_trades`, `cache_miss`). |
| **timestamp_utc** | string (ISO 8601) | No | When this component was computed. |
| **lifecycle_stage** | string | No | One of: ENTRY_DECISION, ENTRY_FILL, EXIT_DECISION, EXIT_FILL. |
| **sub_components** | component[] | No | Child components (tree). Same schema recursively. |

**Invariant:** `composite_score == sum(contribution_to_score)` over all components (including recursive sum over sub_components). No opaque "UW score"—only UW micro-signals as separate components.

---

## 5. Attribution Snapshot (One Point in Time)

One snapshot = one decision point with full component tree.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **snapshot_id** | string | No | Unique id for this snapshot. |
| **trade_id** | string | Yes | Trade this snapshot belongs to (or placeholder before fill, e.g. `pending_<symbol>_<ts>`). |
| **decision_id** | string | Yes | Evaluation cycle id (e.g. `dec_AAPL_2026-02-17T14:30:00Z`). |
| **symbol** | string | Yes | Symbol. |
| **lifecycle_stage** | string | Yes | One of: **ENTRY_DECISION**, **ENTRY_FILL**, **EXIT_DECISION**, **EXIT_FILL**. |
| **timestamp_utc** | string (ISO 8601) | Yes | When snapshot was taken (UTC). |
| **composite_score** | number | Yes | Total score. MUST equal sum of all component contributions (see Truth Contract). |
| **total_score** | number | No (alias) | Alias for composite_score; for backward compatibility. |
| **components** | component[] | Yes | Full component tree (signals and sub-signals). May not be empty for valid snapshot. |
| **entry_reason_codes** | string[] | No | If entry: reason codes or gate names (e.g. `score_gate`, `regime_gate`). |
| **exit_reason_code** | string | Yes iff lifecycle_stage is EXIT_* | Stable exit reason code from taxonomy (see Truth Contract). |
| **schema_version** | string | Yes | e.g. `1.0.0`. |

---

## 6. Trade Attribution Record (Full Lifecycle)

One record per trade (or per attribution_id) tying entry and exit snapshots together.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **attribution_id** | string | Recommended | Stable id for this record (linkable from dashboard/backtest). |
| **trade_id** | string | Yes | Trade id. |
| **symbol** | string | Yes | Symbol. |
| **entry_snapshot** | AttributionSnapshot | Yes (for closed trades) | Snapshot at ENTRY_FILL (or ENTRY_DECISION if fill not yet recorded). |
| **exit_snapshot** | AttributionSnapshot | Yes (for closed trades) | Snapshot at EXIT_DECISION or EXIT_FILL. |
| **exit_reason_code** | string | Yes (for closed trades) | Stable exit reason code. |
| **schema_version** | string | Yes | e.g. `1.0.0`. |

---

## 7. UW Micro-Signals (First-Class Components)

UW MUST NOT be logged as a single opaque score. Each UW micro-signal is a component with:

- **signal_id:** namespaced, e.g. `uw.flow_premium`, `uw.flow_sweep_ratio`, `uw.flow_conviction`, `uw.dp_notional`, `uw.insider_activity`, `uw.insider_sentiment`.
- **source:** `uw`.
- **raw_value**, **normalized_value**, **weight**, **contribution_to_score** (signed).
- **quality_flags:** e.g. `stale`, `low_liquidity`, `conflicting`, `missing` (never silent).

Treat UW micro-signals exactly the same as internal signals in the schema and in persistence.

---

## 8. Quality Flags (Explicit, Never Silent)

Allowed flags (non-exhaustive):

| Flag | Meaning |
|------|---------|
| **stale** | Data older than policy TTL. |
| **missing** | Data not available (prefer also setting missing_reason). |
| **conflicting** | Multiple sources disagree. |
| **low_liquidity** | Liquidity or depth below threshold. |
| **defaulted** | Value was defaulted due to missing/stale. |

If a component is absent, stale, or conflicting, either **quality_flags** or **missing_reason** (or both) MUST be set. Silent omission is invalid.

---

## 9. Exit Reason Code (Stable Taxonomy)

Every exit MUST have a non-empty **exit_reason_code** from this set (or a documented extension):

- `time_exit` — Time-based exit (e.g. 240 min).
- `trail_stop` — Trailing stop hit.
- `signal_decay` — Signal strength decay below threshold.
- `flow_reversal` — Flow reversal detected.
- `profit_target` — Profit target hit.
- `stop_loss` — Stop loss hit.
- `regime_protection` — Regime protection exit.
- `displacement` — Displaced by another position.
- `stale_position` — Stale position (age + PnL threshold).
- `structural_exit` — Structural exit (v2).
- `intel_deterioration` — Intel deterioration (v2).
- `replacement` — Replacement candidate.
- `profit` — Profit-taking (v2).
- `risk` — Generic risk / unknown normalized to risk.

Composite close reasons (e.g. from `build_composite_close_reason`) SHOULD be stored for display and MUST map to one primary code above for analytics.

---

## 10. Schema Version

- **schema_version:** `1.0.0` for this canonical spec.
- All snapshots and trade attribution records MUST include **schema_version**.
- Consumers MUST reject or migrate records with unknown versions.
