# Snapshot & Blocked Trade Key Verification

**Purpose:** From recent droplet data, sample N records from `score_snapshot.jsonl` and `blocked_trades.jsonl`, list keys present in `group_sums` and `weighted_contributions`, and compare to the canonical list.

**Canonical reference:** `reports/data_integrity/canonical_signal_keys.md`

---

## Expected schema (per record)

**score_snapshot.jsonl (each line):**
- `weighted_contributions`: dict of component_key → float (same keys as canonical components).
- `group_sums`: dict with keys `uw`, `regime_macro`, `other_components`.

**blocked_trades.jsonl (each line):**
- `attribution_snapshot` (optional): dict with:
  - `weighted_contributions`: same as above.
  - `group_sums`: same as above.
  - `composite_pre_norm`, `composite_post_norm`: floats.

---

## Verification procedure (run on droplet or with local data)

1. Sample up to N=20 records from `logs/score_snapshot.jsonl` (e.g. last 20 lines).
2. For each record, collect:
   - Keys in `weighted_contributions` (if present).
   - Keys in `group_sums` (if present).
3. Sample up to N=20 records from `state/blocked_trades.jsonl`.
4. For each record, collect:
   - Keys in `attribution_snapshot.weighted_contributions` (if present).
   - Keys in `attribution_snapshot.group_sums` (if present).
5. Compare:
   - **Missing keys:** Any canonical component or group_sum key never seen.
   - **Renamed keys:** Any key in snapshot/blocked_trades not in canonical list.
   - **Extra keys:** Acceptable if additive (e.g. composite_pre_norm); flag if in weighted_contributions or group_sums and not canonical.

---

## Local / droplet status

**Local:** No `logs/score_snapshot.jsonl` or `state/blocked_trades.jsonl` found in this workspace. Snapshot/blocked_trade key verification must be run where those files exist (e.g. droplet).

**Checklist when data is available:**

| Source | Keys in weighted_contributions | Keys in group_sums | vs canonical |
|--------|-------------------------------|--------------------|--------------|
| score_snapshot.jsonl (sample) | (list keys) | uw, regime_macro, other_components | Match / Mismatch |
| blocked_trades.jsonl (sample) | (list keys) | uw, regime_macro, other_components | Match / Mismatch |

**If all sampled records have:**  
- `weighted_contributions` with the 22 canonical component keys (or subset when composite uses reduced set), and  
- `group_sums` with exactly `uw`, `regime_macro`, `other_components`  

then **snapshot_key_audit: PASS**. Otherwise list exact mismatches (missing/renamed/extra) per file.

---

## Code path guarantee (without droplet sample)

The only code that writes these files is:
- `score_snapshot_writer.append_score_snapshot(..., weighted_contributions=meta.get("components"), group_sums=meta.get("group_sums"), ...)` with `meta` from `composite_meta` (full composite from `_compute_composite_score_core`).
- `log_blocked_trade(..., attribution_snapshot={ "weighted_contributions": meta.get("components"), "group_sums": meta.get("group_sums"), ... })`.

So by code inspection, keys written are identical to canonical **when composite_meta is the full composite**. No renaming or key mapping occurs in the writer or in main. **In-code verdict: PASS** pending runtime check on droplet.
