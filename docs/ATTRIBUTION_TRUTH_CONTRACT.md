# Attribution Truth Contract

**Schema version:** 1.0.0  
**Canonical schema:** `docs/ATTRIBUTION_SCHEMA_CANONICAL_V1.md`  
**Phase 0 map:** `docs/ATTRIBUTION_MEGA_BLOCK_PHASE0_REPO_MAP.md` (locked).

This document defines **invariants** that the attribution system MUST satisfy. Any producer (live, backtest, or lab) MUST comply; consumers MAY assume these hold.

---

## 1. Score Invariants

- **composite_score == sum(all component contributions)**  
  For every `AttributionSnapshot`,  
  `composite_score == sum(c.contribution_to_score for c in components)`  
  including recursive sum over `sub_components` where present.  
  Tolerance: configurable (e.g. 1e-6); default 0.0.

- **No opaque totals**  
  Every reported score MUST be accompanied by a full component tree. A "total only" record without components is invalid.

- **Penalties and boosts are explicit**  
  Penalties MUST be logged as components with **negative** `contribution_to_score`. Boosts MUST be positive. No single "adjustment" blob; each penalty/boost is a named component.

---

## 2. Trade Attribution Invariants

- **Every ENTRY has an attribution snapshot**  
  For each trade open (entry), there MUST be at least one attribution snapshot with lifecycle_stage = **ENTRY_DECISION** or **ENTRY_FILL**.

- **Every EXIT has an attribution snapshot + exit_reason_code**  
  For each trade close (exit), there MUST be at least one attribution snapshot with lifecycle_stage = **EXIT_DECISION** or **EXIT_FILL**, and the exit record MUST include a non-empty, stable **exit_reason_code** from the taxonomy.

- **Exit snapshot links to exit**  
  The exit MUST reference an attribution snapshot (same schema) taken at or immediately before the exit.

---

## 3. UW Invariants

- **UW is never logged as a single opaque score**  
  UW MUST be decomposed into first-class micro-signals. Each UW micro-signal is a component with: signal_id (namespaced `uw.*`), raw_value(s), normalized_value(s), weight, signed contribution_to_score, quality_flags. No single "uw_score" or "unusual_whales" aggregate without a full decomposition.

- **UW micro-signals treated like internal signals**  
  Same schema shape, same persistence, same auditability as internal/derived components.

---

## 4. Component Invariants

- **Missing / stale / conflicting are explicit (never silent)**  
  If a component is not available, stale, or conflicting:
  - Represent it as a component entry with **missing_reason** set and/or **quality_flags** (e.g. `stale`, `missing`, `conflicting`), and optionally `contribution_to_score = 0`.
  - Components MUST NOT be silently omitted.

- **Stable signal_id**  
  Component **signal_id** (and **name**) MUST be a stable key from the canonical set or a namespaced experimental key (e.g. `exp_*`).

---

## 5. Lifecycle and Timestamps

- **Snapshot timestamps**  
  Every attribution snapshot MUST have a valid **timestamp_utc** (ISO 8601, UTC). For the same trade, entry snapshot timestamp ≤ exit snapshot timestamp.

- **Snapshot types**  
  Allowed lifecycle_stage values: **ENTRY_DECISION**, **ENTRY_FILL**, **EXIT_DECISION**, **EXIT_FILL**. Minimum for a closed trade: one entry snapshot (ENTRY_DECISION or ENTRY_FILL) and one exit snapshot (EXIT_DECISION or EXIT_FILL).

- **decision_id**  
  Every snapshot MUST have a **decision_id** identifying the evaluation cycle.

---

## 6. Reason Codes

- **Entry reason codes**  
  Optional. When present, MUST reference component keys or documented entry gate names (e.g. `score_gate`, `regime_gate`).

- **Exit reason code**  
  MUST be one of the stable exit reason taxonomy (see canonical schema). Composite reasons MUST map to one primary code for analytics.

---

## 7. Schema Versioning

- **All records carry schema_version**  
  Every attribution snapshot and trade attribution record MUST include **schema_version** (e.g. `1.0.0`). Consumers MUST reject or migrate unknown versions.

- **Backward compatibility**  
  New schema versions MUST add optional fields or new enumerations; breaking changes require a new major version and migration path.

---

## 8. Auditability

- **Append-only or auditable store**  
  Attribution records MUST be written to an append-only log or a store that supports audit (no in-place deletion of attribution rows).

- **attribution_id**  
  When present, **attribution_id** MUST uniquely identify the attribution record and be linkable from dashboard and backtest outputs.

---

## 9. Validation (Contract Tests)

The codebase MUST include contract tests that fail if:

- `composite_score != sum(contributions)` for any snapshot.
- A closed trade is missing entry or exit snapshot.
- An exit record is missing **exit_reason_code**.
- A component is omitted without **missing_reason** or **quality_flags** where the schema requires explicit handling.
- UW is logged as a single opaque score instead of decomposed micro-signals.

---

## Exit Reason Taxonomy (Stable Codes)

| Code | Description |
|------|-------------|
| `time_exit` | Time-based exit (e.g. 240 min) |
| `trail_stop` | Trailing stop hit |
| `signal_decay` | Signal strength decay below threshold |
| `flow_reversal` | Flow reversal detected |
| `profit_target` | Profit target hit |
| `stop_loss` | Stop loss hit |
| `regime_protection` | Regime protection exit |
| `displacement` | Displaced by another position |
| `stale_position` | Stale position exit (age + PnL threshold) |
| `structural_exit` | Structural exit (v2) |
| `intel_deterioration` | Intel deterioration (v2 exit score) |
| `replacement` | Replacement candidate exit |
| `profit` | Profit-taking (v2) |
| `risk` | Generic risk / unknown normalized to risk |

Composite close reasons SHOULD be stored as-is for display and MUST map to one primary code above for aggregation.
