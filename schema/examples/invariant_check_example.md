# Phase 1 — Example Invariant Checks (Proof Artifacts)

This document shows **concrete** invariant checks on the example JSON files. Humans can inspect real data, not descriptions.

---

## 1. Example: Sum of contributions == composite_score

**File:** `schema/examples/attribution_snapshot_example.json`

**Invariant (Truth Contract §1):** `composite_score == sum(c.contribution_to_score for c in components)` (including sub_components).

**From the example:**

| signal_id                 | contribution_to_score |
|---------------------------|------------------------|
| uw.flow_premium           | 0.288                  |
| uw.flow_conviction        | 0.39                   |
| uw.dp_notional            | 0.325                  |
| internal.regime_modifier   | 0.045                  |
| derived.toxicity_penalty  | -0.18                  |
| internal.options_flow    | 2.04                   |
| internal.dark_pool        | 0.78                   |
| internal.insider          | 0.125                  |

**Sum:** 0.288 + 0.39 + 0.325 + 0.045 + (-0.18) + 2.04 + 0.78 + 0.125 = **3.823**

**Recorded composite_score:** 3.42

**Note:** This example was constructed for illustration; the numbers above do not sum to 3.42. A **valid** producer MUST ensure sum(contributions) == composite_score (within tolerance). Contract tests MUST fail when they differ. Here we demonstrate the *check*: compute sum(contributions), compare to composite_score, fail if not equal.

**Validated example (corrected):** See **`schema/examples/attribution_snapshot_valid_sum.json`**. There, composite_score = 3.50 and the component contributions sum to 0.32 + 0.40 + 0.30 + 2.00 + 0.52 + 0.06 + (-0.10) = **3.50**. So composite_score == sum(contributions). Contract tests MUST enforce this on every snapshot.

---

## 2. Example: Required fields present (entry and exit snapshots)

**File:** `schema/examples/trade_attribution_record_example.json`

**Invariants (Truth Contract §2):**
- Every ENTRY has an attribution snapshot.
- Every EXIT has an attribution snapshot + exit_reason_code.

**Check:**

| Requirement                    | Present in example |
|--------------------------------|--------------------|
| entry_snapshot                 | Yes                |
| exit_snapshot                  | Yes                |
| exit_reason_code (on record)   | Yes ("signal_decay") |
| exit_snapshot.exit_reason_code | Yes ("signal_decay") |
| entry_snapshot.lifecycle_stage | ENTRY_FILL         |
| exit_snapshot.lifecycle_stage  | EXIT_FILL          |
| trade_id, symbol               | Yes                |
| schema_version on record and snapshots | Yes ("1.0.0") |

**Result:** Required fields for a closed trade are present. Contract tests MUST assert these on every closed-trade record.

---

## 3. Example: UW not a single opaque score

**Invariant (Truth Contract §3):** UW is never logged as a single opaque score; it is decomposed into first-class components.

**From `attribution_snapshot_example.json`, UW-related components:**

| signal_id          | source | contribution_to_score |
|--------------------|--------|------------------------|
| uw.flow_premium    | uw     | 0.288                  |
| uw.flow_conviction | uw     | 0.39                   |
| uw.dp_notional     | uw     | 0.325                  |

There is **no** single field such as `uw_score` or `unusual_whales`. UW appears only as separate components with namespaced signal_id and source "uw". **Check:** No key named "uw_score" or "unusual_whales" in components; at least one component has source "uw" and signal_id starting with "uw.".

---

## 4. Example: Explicit missing / quality flags (never silent)

**Invariant (Truth Contract §4):** Missing or low-quality components have missing_reason or quality_flags set.

**From `attribution_snapshot_example.json`, component internal.insider:**

- `"quality_flags": ["defaulted"]`
- `"missing_reason": "no_recent_insider_data"`

So the component is not silently omitted; it is present with contribution 0.125 and explicit reason/flags. **Check:** For any component that is defaulted or missing data, quality_flags or missing_reason (or both) must be non-empty.

---

## 5. Snapshot types (exactly four)

**Invariant (Canonical Schema §3):** Snapshots use exactly ENTRY_DECISION, ENTRY_FILL, EXIT_DECISION, EXIT_FILL.

**From examples:**
- entry_snapshot.lifecycle_stage = "ENTRY_FILL"
- exit_snapshot.lifecycle_stage = "EXIT_FILL"

**Check:** lifecycle_stage must be one of these four strings. No other values (e.g. "pre_entry", "post_entry") are used in the canonical four-stage model; if used elsewhere, they must map to one of the four for analytics.

---

## Summary

| Invariant                          | Example file(s)                    | Check |
|------------------------------------|------------------------------------|-------|
| composite_score == sum(contributions) | attribution_snapshot_valid_sum.json | Sum = 3.50; composite_score = 3.50 ✓ |
| Every ENTRY has snapshot           | trade_attribution_record_example.json | entry_snapshot present, lifecycle_stage entry | 
| Every EXIT has snapshot + code     | trade_attribution_record_example.json | exit_snapshot + exit_reason_code present |
| UW not single score                | attribution_snapshot_example.json  | UW only as uw.* components |
| Explicit missing/flags             | attribution_snapshot_example.json  | internal.insider has quality_flags + missing_reason |
| Four snapshot types                | both                               | lifecycle_stage in {ENTRY_DECISION, ENTRY_FILL, EXIT_DECISION, EXIT_FILL} |

These examples are committed so humans can inspect REAL DATA and run the same checks in contract tests.
