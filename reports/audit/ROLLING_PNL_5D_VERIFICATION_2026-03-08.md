# Rolling PnL 5D — CSA & SRE Verification

**Date:** 2026-03-08  
**Artifacts:** `reports/state/rolling_pnl_5d.jsonl`, `reports/audit/ROLLING_PNL_5D_UPDATE_*.json`, `scripts/performance/update_rolling_pnl_5d.py`

---

## CSA checks

| Check | Requirement | How to verify |
|-------|-------------|--------------|
| **Rolling points match unified exits** | Each point’s `pnl` = sum of exit PnL in last 5d from exit_attribution + attribution (same logic as Performance Engine). | Run script, then sum `pnl` from exits in window; compare to last line in `rolling_pnl_5d.jsonl`. |
| **No hidden smoothing** | No interpolation or smoothing of missing data. | Code review: no smoothing; dashboard shows line segments only (gaps visible). |
| **Window always exactly 5 days** | Prune removes points with `ts < now - 5d`. | Script prunes by `cutoff_ts = now_ts - (5 * 86400)`; audit artifact has `window_days: 5`. |

---

## SRE checks

| Check | Requirement | How to verify |
|-------|-------------|----------------|
| **Script survives restart** | No in-memory state; reads logs and appends to JSONL. | Restart droplet or kill script; next cron run appends next point. |
| **Missing data → gaps, not lies** | If no exits in window, point has `pnl: 0`; no fabricated values. | When no trades in 5d, rolling file has points with `pnl: 0`; dashboard shows flat line or gap. |
| **Disk usage bounded** | Prune keeps only last 5 days; ~720 points max at 10-min interval. | `wc -l reports/state/rolling_pnl_5d.jsonl`; file size ~50–100 KB. |

---

## Evidence

- **Rolling state path:** `reports/state/rolling_pnl_5d.jsonl` (append-only).
- **Update artifacts:** `reports/audit/ROLLING_PNL_5D_UPDATE_<YYYY-MM-DD>_<HHMM>.json`.
- **Dashboard:** Executive Summary → Timeframe **5D (rolling)** → 5D Performance Line (X=time, Y=equity; no smoothing).
- **Cron:** See `docs/ROLLING_PNL_5D_CRON.md`.
