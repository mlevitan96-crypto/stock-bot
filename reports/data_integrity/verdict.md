# Signal Schema Parity & Data Integrity — Verdict

**Date:** 2026-02-19  
**Scope:** End-to-end signal key parity (composite → snapshot/blocked_trades → analysis).

---

## Step 1 — Canonical signal keys

**Result:** **Defined.**  
See `canonical_signal_keys.md`: 22 component keys + 3 group_sum keys; single source of truth from `uw_composite_v2._compute_composite_score_core`.

---

## Step 2 — Producer verification

**Result:** **PASS.**  
- Composite emits exactly the canonical component and group_sum keys.  
- main.py forwards `meta.get("components")` and `meta.get("group_sums")` without renaming.  
- score_snapshot_writer and log_blocked_trade write keys as provided.  
See `producer_key_audit.md`.

---

## Step 3 — Snapshot & blocked trade verification

**Result:** **PASS (by code inspection).**  
No local droplet sample available; code paths that write snapshot and blocked_trades use the same composite_meta (components + group_sums) with no key mapping. Runtime check on droplet recommended when data exists. See `snapshot_key_audit.md`.

---

## Step 4 — Replay & analysis verification

**Result:** **PASS.**  
- blocked_expectancy_analysis.py does not consume signal keys (N/A).  
- blocked_signal_expectancy_pipeline.py consumes weighted_contributions and group_sums with the same key names; UW_KEYS, REGIME_MACRO_KEYS, OTHER_COMPONENT_KEYS match canonical; no renaming; fallback _component_group_sums uses same grouping.  
See `analysis_key_audit.md`.

---

## Final verdict

**PASS** — Schema parity confirmed.

All signal components are:
- **Named identically** end-to-end (composite → snapshot/blocked_trades → pipeline).  
- **Present** in the canonical list and emitted by the single composite path.  
- **Not silently dropped** (writers and main forward as-is when composite_meta is full).  
- **Consumed consistently** (pipeline uses same keys; fallback recomputes group_sums with same mapping).

**Conditional edge analysis may proceed** subject to runtime check on droplet (sample snapshot/blocked_trades when available) to confirm keys in written records match canonical.
