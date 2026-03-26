# Alpaca dashboard — learning status banner

**Timestamp:** 20260326_2200Z  

## Location

- `#learning-notice-banner` with class `learning-notice-banner` in main dashboard template (`dashboard.py`).

## Copy (Phase 3)

- **Headline:** `LEARNING STATUS: NOT CERTIFIED`  
- **Body:** States that strict learning / replay cohorts and telemetry bundles are not CSA-certified; clarifies this **does not** mean live trading is broken; operational panels may still reflect real execution; separation is intentional and under CSA review.  
- **Styling:** Blue informational palette (`.learning-notice-banner`) — **not** red error styling.

## Contract

- Banner is **persistent** (always visible in header).  
- Does **not** imply CSA data certification for any panel below it.  
- Complements per-tab `#tab-state-line-*` banners for OK / STALE / PARTIAL / DISABLED.
