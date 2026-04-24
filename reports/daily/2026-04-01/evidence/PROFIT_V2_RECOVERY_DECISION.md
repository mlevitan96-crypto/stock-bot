# PROFIT_V2_RECOVERY_DECISION

**Choice: hybrid — (A) for UW-equivalent signal rows, (B) for minute bars.**

## (A) RECOVER EXISTING DATA — UW / entry context

**Justification (evidence):**

- `logs/signal_context.jsonl` is **empty**; re-labeling it as “source of truth” would require new emission (Phase 4 optional).
- `logs/score_snapshot.jsonl` has **2000** lines with nested **`signal_group_scores.components`** including **`flow`**, **`dark_pool`**, **`whale`**, **`etf_flow`**, **`greeks_gamma`**, etc. (sample in `_PROFIT_V2_DROPLET_RAW.json`).
- **`state/uw_cache/`** holds **~43 MB** of shard JSON — suitable for deep UW payload recovery if keyed lookups are needed.
- **Joinability:** match exits to snapshots on **`symbol`** + **nearest snapshot timestamp ≤ exit time**; campaign / V2 uplift achieved **63** matched pairs on tail windows (`PROFIT_V2_SIGNAL_UW_UPLIFT.json`).

**Minimal transform:** none beyond the nearest-timestamp join already implemented in `compute_profit_v2_uplift_and_blocked.py`.

## (B) RE-CAPTURE REQUIRED — minute bars

**Justification (evidence):**

- `artifacts/market_data/alpaca_bars.jsonl` was **missing** on droplet (`phase1.bars_stat`).
- No substitute file in `data/bars_cache/` was evidenced in the Phase 1 sample.
- **Re-capture** = **read-only** Alpaca Data API pull into the **canonical path** expected by replay scripts — **no** order or strategy changes.

**Implementation:** `scripts/audit/fetch_alpaca_bars_for_counterfactuals.py` (self-contained HTTP). **Result:** **49** symbols, **49** JSONL lines, **~8.2 MB** on disk.

## Explicit non-choice

- **Full liquidation / engine restart / tuning / gate changes:** **out of scope** per mission constraints.
