# Phase 1 — Minimal vs Full Schema Comparison

**Purpose:** Define the smallest schema that unlocks edge, the additional fields that unlock deeper optimization, and a recommendation for what to implement first.

---

## 1. Smallest Schema That Unlocks Edge (Minimal Viable)

**Goal:** Answer "which signals helped or hurt this trade?" and "did composite_score add up?" without building the full pipeline.

### Minimal required fields

**Per snapshot (ENTRY_DECISION, ENTRY_FILL, EXIT_DECISION, EXIT_FILL):**

| Field | Why minimal |
|-------|-------------|
| **trade_id** | Link to trade. |
| **decision_id** | Link to evaluation cycle (needed for "per decision" even when no fill). |
| **symbol** | Required for any symbol-level analysis. |
| **lifecycle_stage** | Which of the four snapshots this is. |
| **timestamp_utc** | When; needed for ordering and freshness. |
| **composite_score** | The total; must equal sum(contributions). |
| **components** | Array of components, each with at least: **signal_id**, **contribution_to_score** (signed). Without this, no decomposition. |
| **exit_reason_code** | Required when lifecycle_stage is EXIT_*; needed to segment by exit type. |
| **schema_version** | So consumers know how to read. |

**Per component (minimal):**

| Field | Why minimal |
|-------|-------------|
| **signal_id** (or **name**) | Stable key—required to attribute "which signal." |
| **contribution_to_score** | Signed contribution—required for sum check and for "helped vs hurt." |
| **source** | uw | internal | derived—required so UW is not opaque (UW components must be identifiable). |

**Explicit absence (minimal):**  
If a component is missing, either one component entry with **missing_reason** (and contribution 0) or a documented convention that "all absent signals are listed with contribution 0 and missing_reason." No silent omission.

**What this unlocks:**

- Per trade_id: full component tree at entry and exit.
- Sum check: composite_score == sum(contributions).
- Per signal_id: distribution of contributions across winners/losers.
- Per exit_reason_code: which components preceded good/bad exits.
- UW as multiple components (no single UW score).

---

## 2. Additional Fields That Unlock Deeper Optimization (Full Schema)

| Field / area | Benefit |
|--------------|---------|
| **raw_value**, **normalized_value**, **weight** per component | Enables "why this contribution?" and re-weighting in backtest/lab without recomputing raw inputs. Tunable at micro-signal level. |
| **quality_flags** (stale, missing, conflicting, low_liquidity) | Enables filtering "only high-quality components" in analysis; avoids attributing noise to bad data. |
| **confidence** per component | Enables confidence-weighted aggregation or filtering in dashboards. |
| **sub_components** (tree) | Enables "flow → premium, sweep_ratio, conviction" drill-down; better diagnostics and tuning of sub-signals. |
| **entry_reason_codes** | Enables "which gate passed/failed" at entry; improves entry tuning. |
| **attribution_id** | Stable link from dashboard/backtest to one record; simplifies audit and replay. |
| **snapshot_id** | Unique id per snapshot; simplifies dedup and cross-reference. |

**What full schema unlocks:**

- Re-weighting and what-if in backtest/lab (weight + normalized_value).
- Quality-aware analytics (filter by quality_flags).
- Deeper drill-down (sub_components) for edge discovery.
- Clear audit trail (attribution_id, snapshot_id).

---

## 3. Recommendation: What to Implement First

**Recommendation: Implement the minimal schema first, with three extensions.**

1. **Minimal core (mandatory from day one)**  
   - trade_id, decision_id, symbol, lifecycle_stage, timestamp_utc, composite_score, components (signal_id, contribution_to_score, source), exit_reason_code when EXIT_*, schema_version.  
   - Explicit missing: missing_reason (or convention) for absent components.  
   - This is enough to validate "composite_score == sum(contributions)," attribute wins/losses to signals, and never log UW as a single score.

2. **Add immediately (same phase, low cost)**  
   - **weight** and **normalized_value** per component: needed for "why this number?" and for future config-driven re-weighting.  
   - **quality_flags** (at least stale, missing): no silent bad data; required by truth contract.

3. **Add next (Phase 2–4)**  
   - **raw_value** where easily available (especially UW micro-signals).  
   - **sub_components** for flow and other composite signals (enables UW decomposition and internal composite drill-down).  
   - **attribution_id**, **snapshot_id** when persistence and dashboard linking are implemented.

**Why this order:**  
Minimal + weight + normalized_value + quality_flags gives you explainable, auditable, tunable attribution and satisfies the truth contract (sum check, no opaque UW, explicit missing/stale). raw_value and sub_components add depth for optimization once the pipeline is stable. attribution_id/snapshot_id are natural when you add the canonical store and dashboards.

**Summary:**  
- **Smallest schema that unlocks edge:** minimal core above + explicit missing.  
- **Additional fields for deeper optimization:** raw_value, normalized_value, weight, quality_flags, confidence, sub_components, entry_reason_codes, attribution_id, snapshot_id.  
- **Implement first:** minimal core + weight + normalized_value + quality_flags; then raw_value and sub_components; then attribution_id/snapshot_id with persistence.
