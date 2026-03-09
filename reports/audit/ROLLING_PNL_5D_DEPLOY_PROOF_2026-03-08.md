# 5-Day Rolling PnL — Deploy Proof

**Date:** 2026-03-08  
**Mission:** Upgrade Performance Engine line to continuous 5-day rolling window; droplet-native, CSA-auditable.

---

## Proof artifacts

### 1. Rolling state file (sample)

**Path:** `reports/state/rolling_pnl_5d.jsonl`

```
{"ts": "2026-03-08T22:41:23.944408+00:00", "equity": 0.0, "pnl": 0.0, "source": "unified_exits", "window": "5d"}
{"ts": "2026-03-08T22:43:52.452643+00:00", "equity": 0.0, "pnl": 0.0, "source": "unified_exits", "window": "5d"}
```

- Append-only; one point per run.
- Prune removes points older than 5 days.

### 2. Update summary artifact

**Path:** `reports/audit/ROLLING_PNL_5D_UPDATE_<YYYY-MM-DD>_<HHMM>.json`

Example: `reports/audit/ROLLING_PNL_5D_UPDATE_2026-03-08_2243.json` — contains `ts`, `points_after_prune`, `exits_in_window`, `net_pnl`, `equity`, `window_days: 5`.

### 3. Dashboard

- **Executive Summary** → Timeframe dropdown includes **5D (rolling)**.
- When **5D (rolling)** is selected: **5D (rolling) Performance Line** chart is shown (X = time UTC, Y = equity). No smoothing; gaps visible if data missing.
- API: `GET /api/rolling_pnl_5d` returns `{ "points": [...], "window": "5d" }`.

### 4. Cron (droplet)

- **Entry:** `*/10 * * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/performance/update_rolling_pnl_5d.py >> logs/rolling_pnl_5d.log 2>&1`
- **Verify:** `crontab -l | grep update_rolling_pnl_5d`  
- **Log:** `tail logs/rolling_pnl_5d.log`

### 5. Idempotence

- Script run twice manually: two points appended (different timestamps); no failure. Prune and validation run each time.

---

## Exit criteria

| Criterion | Status |
|-----------|--------|
| 5-day rolling line visible on dashboard | Yes (5D (rolling) option + chart) |
| Updates every ~10 minutes | Cron doc and entry provided |
| Window always rolls forward | Prune in script |
| No recomputation drift | Append-only; no full history recompute |
| CSA verification artifact exists | `reports/audit/ROLLING_PNL_5D_VERIFICATION_2026-03-08.md` |

---

## Post-deploy (droplet)

1. Add cron entry (see `docs/ROLLING_PNL_5D_CRON.md`).
2. Run script twice: `python scripts/performance/update_rolling_pnl_5d.py` to confirm idempotence.
3. Open dashboard → Executive Summary → select **5D (rolling)** → confirm chart and/or “No rolling 5d data yet” until cron populates.
