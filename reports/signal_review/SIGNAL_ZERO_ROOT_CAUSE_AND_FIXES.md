# Root Cause: Multiple Signals at 0 and Fixes

**Goal:** Get signals providing real scores (no lowering MIN_EXEC_SCORE). Find why congress, shorts_squeeze, institutional, calendar, whale, motif_bonus (and FTD) were 0 and fix the pipeline.

---

## 1. Data flow (who writes what)

| Signal | Written by | Cache key | Consumed by |
|--------|------------|-----------|-------------|
| congress | uw_flow_daemon | `cache[symbol]["congress"]` | enricher passes through → composite |
| institutional | uw_flow_daemon | `cache[symbol]["institutional"]` | enricher passes through → composite |
| calendar | uw_flow_daemon | `cache[symbol]["calendar"]` | enricher passes through → composite |
| shorts_squeeze / ftd_pressure | uw_flow_daemon | `ftd_pressure`, `shorts_ftds` | enricher → `enriched["shorts"]` → composite |
| whale / motif_bonus | uw_enrichment_v2 | motif_detector (state/uw_motifs.json) | composite reads enriched motif_* |

---

## 2. Root causes identified

### 2.1 FTD / shorts_squeeze

- **Cause:** Composite expected `shorts_data` with `ftd_count`, `squeeze_risk`, `interest_pct`, `days_to_cover`. The daemon stored the **raw API response** (often a list of records or different keys). Composite also **returned 0.0** when `interest_pct == 0`, so FTD-only data never contributed.
- **Fix (daemon):** `_normalize_ftd_for_composite(raw)` normalizes any API shape to `{ftd_count, squeeze_risk, interest_pct, days_to_cover}` (supports list of records, or dict with alternate keys). Daemon now writes this normalized shape to `ftd_pressure` and `shorts_ftds`.
- **Fix (composite):** Removed the early `if interest_pct == 0: return 0.0`. Component now contributes from **ftd_count** and **squeeze_risk** even when `interest_pct` is missing, so FTD-only data produces a score.

### 2.2 Calendar

- **Cause:** Composite expected `has_earnings`, `days_to_earnings`, `has_fda`, `fda_catalyst`, `economic_events`. The daemon stored the **raw calendar API response**, which often uses different keys (`next_earnings`, `events`, etc.), so the component saw “no data.”
- **Fix (daemon):** `_normalize_calendar_for_composite(raw)` maps common API keys into the shape above (earnings date → `has_earnings` / `days_to_earnings`, events list → `economic_events`, etc.). Daemon now writes this normalized calendar for each ticker.

### 2.3 Congress / institutional

- **Cause:** Daemon already summarizes to the right shape (`_summarize_congress`, `_summarize_institutional`). Zeros are likely from **API returning empty** (404, rate limit, or no data for ticker). No schema bug; data just not present.
- **Fix:** No code change. Ensure daemon runs and polls congress (global) and institutional (per-ticker). If UW API returns data, it will flow through. If API continues to return empty, that’s an API/plan/rate-limit issue.

### 2.4 Whale / motif_bonus

- **Cause:** These come from **TemporalMotifDetector** in the enricher, which needs **history** of cache updates (conviction, dark_pool over time). If the cache is sparse or just started, no motifs are detected → 0.
- **Fix:** No change to logic. As the daemon runs and the cache fills, motif_detector.update() gets more data and will start producing staircase/sweep/burst/whale when patterns appear.

---

## 3. Code changes made

1. **uw_flow_daemon.py**
   - `_normalize_ftd_for_composite(raw)`: normalizes FTD/shorts API response to `ftd_count`, `squeeze_risk`, `interest_pct`, `days_to_cover`. Used when writing `ftd_pressure` and `shorts_ftds`.
   - `_normalize_calendar_for_composite(raw)`: normalizes calendar API response to `has_earnings`, `days_to_earnings`, `has_fda`, `fda_catalyst`, `economic_events`. Used when writing `calendar`.
   - Poll shorts/FTDs: store **normalized** FTD dict instead of raw.
   - Poll calendar: store **normalized** calendar dict instead of raw.

2. **uw_composite_v2.py**
   - `compute_shorts_component`: no longer returns 0.0 when `interest_pct == 0`. Still contributes from `ftd_count` and `squeeze_risk` so FTD-only data produces a score. Coerces `ftd_count` to int.

---

## 4. What to expect after deploy

- **shorts_squeeze / ftd_pressure:** Should contribute when the UW shorts/FTD API returns any data (list or dict); normalized shape is written and composite uses it.
- **calendar:** Should contribute when the calendar API returns earnings/FDA/events under any of the common key names we normalize.
- **congress / institutional:** Unchanged; will contribute when the UW API returns non-empty data.
- **whale / motif_bonus:** Will contribute as more history accumulates in the cache and motifs are detected.

Re-run the scoring pipeline audit on the droplet after deploy and confirm score distribution (e.g. median and % above MIN_EXEC_SCORE) improve.
