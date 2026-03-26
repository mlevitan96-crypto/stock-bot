# Dashboard banner and review automation – verification

**Date:** 2026-03-03  
**Purpose:** Confirm banner/situation update regularly, reviews run on a schedule, and pipeline is hooked up for automated analysis.

---

## 1. Will the banner update on a regular basis?

**Yes.**

- **Display refresh:** The dashboard JS runs `setInterval(..., 60000)` (every **60 seconds**) for both `loadDirectionBanner` and `loadSituationStrip` (see `dashboard.py` ~line 1156). So the **banner and situation strip re-fetch** from the server every minute.
- **Backend data for the banner:** The direction banner reads from:
  - `state/direction_readiness.json` (telemetry-backed trades X/100, ready flag)
  - `state/direction_replay_status.json` (RUNNING / SUCCESS / BLOCKED / FAILED)
  - `reports/board/DIRECTION_REPLAY_30D_RESULTS.md` (and blocked synthetic)
  Those files are **written by backend jobs**, not by the dashboard. So the banner will **show new data** whenever:
  1. The dashboard’s 60s timer fetches again, and  
  2. The backend has already updated those state/report files.

**Conclusion:** The banner **display** updates every 60s. Whether the **numbers/content** change depends on how often the backend runs the jobs that write `direction_readiness.json` and replay status (see §3).

---

## 2. Will the situation strip update on a regular basis?

**Yes (same 60s fetch).**

- **Display:** Same `setInterval` as the banner: **every 60 seconds** the situation strip calls `/api/situation` and re-renders (trades reviewed, Promotion, Governance, Closed, Open).
- **Backend data:**
  - **Trades reviewed:** `state/direction_readiness.json` (same as banner).
  - **Promotion:** `reports/{today}_stock-bot_combined.json` → `strategy_comparison` (recommendation, score, reasons). That file is produced by `scripts/generate_daily_strategy_reports.py`.
  - **Governance (joined):** `reports/equity_governance/.../lock_or_revert_decision.json`.
  - **Closed (90d):** `_load_stock_closed_trades()` (exit attribution / closed trades).
  - **Open:** `state/internal_positions.json` or Alpaca API.

So the strip **updates on the same 60s cycle**; whether Promotion and other numbers change depends on how often the EOD/report scripts run (see §3).

---

## 3. Will review happen on a regular basis? Will it trigger an update you can see?

**Only if the right crons/jobs are installed and running.**

| Data source | Written by | Intended schedule | How you see it |
|------------|------------|-------------------|----------------|
| **Direction readiness** (banner “X/100”, situation “Trades reviewed”) | `scripts/governance/check_direction_readiness_and_run.py` → `state/direction_readiness.json` | **Cron:** `0,30 9-16 * * 1-5` (every 30 min, 9–16 UTC, Mon–Fri) **if** installed via `scripts/governance/install_direction_readiness_cron_on_droplet.py` | Next dashboard 60s refresh shows new X/100 and message. |
| **Direction replay status** (RUNNING/SUCCESS/BLOCKED) | Same script (when ready) runs `scripts/replay/run_direction_replay_30d_on_droplet.py` → `state/direction_replay_status.json` | When readiness first hits 100 telemetry-backed trades (and 90%+), then once per “ready” flip | Banner switches to “Directional replay running” or “Results available” etc. |
| **Promotion / strategy comparison** (situation “Promotion: WAIT/PROMOTE”) | `scripts/generate_daily_strategy_reports.py` → `reports/{date}_stock-bot_combined.json` | **Not** in the default EOD cron. It **is** in `scripts/run_stock_eod_integrity_on_droplet.sh` (Phase 1b). Default `board/eod/install_eod_cron_on_droplet.py` only installs `run_stock_quant_officer_eod.py` at 21:30. | If combined report is not regenerated daily, Promotion stays stale until something runs `generate_daily_strategy_reports.py`. |
| **Daily EOD / board** | `board/eod/run_stock_quant_officer_eod.py` @ 21:30 UTC (canonical per MEMORY_BANK §5.5) | 21:30 UTC Mon–Fri (when cron installed) | Board outputs and EOD memos update; dashboard can show governance/closed data that depend on EOD artifacts. |

So:

- **Review (direction readiness + optional replay)** happens on a regular basis **only if** the direction-readiness cron is installed on the droplet. Then every 30 min during market hours the counts and “ready” state update, and the next 60s dashboard refresh shows it.
- **Review (daily EOD / board)** happens at 21:30 UTC weekdays **if** the EOD cron is installed. That updates EOD/board artifacts; it does **not** by default run `generate_daily_strategy_reports.py`, so the situation strip’s **Promotion** line may not refresh unless the full EOD integrity script (or another job) runs that script.

**Yes, it will trigger an update you can see:** whenever the backend updates the state/report files, the next 60s dashboard refresh (or a manual reload) will show the new banner and situation strip.

---

## 4. Is everything hooked up for real automated analysis?

**Almost.** Gaps to close:

1. **Direction readiness cron**
   - **What:** `scripts/governance/install_direction_readiness_cron_on_droplet.py` adds:  
     `0,30 9-16 * * 1-5 cd /root/stock-bot && python3 scripts/governance/check_direction_readiness_and_run.py >> logs/direction_readiness_cron.log 2>&1`
   - **Why:** So `state/direction_readiness.json` (and replay status when ready) is updated every 30 min during market hours. Without this, the banner/situation “trades reviewed” and “Directional intelligence accumulating” message stay static.
   - **Check on droplet:**  
     `crontab -l | grep check_direction_readiness`

2. **Promotion / strategy comparison (combined report)**
   - **What:** `scripts/generate_daily_strategy_reports.py` produces `reports/{date}_stock-bot_combined.json` (used by `/api/situation` and strategy comparison).
   - **Current state:** The simple EOD cron (`install_eod_cron_on_droplet.py`) runs only `run_stock_quant_officer_eod.py` at 21:30. It does **not** run `generate_daily_strategy_reports.py`. The full pipeline `scripts/run_stock_eod_integrity_on_droplet.sh` **does** run it (Phase 1b).
   - **Recommendation:** Either:
     - Schedule the full EOD script (`run_stock_eod_integrity_on_droplet.sh`) at 21:30 instead of (or before) `run_stock_quant_officer_eod.py`, or  
     - Add a separate daily cron that runs `generate_daily_strategy_reports.py --date $(date -u +%Y-%m-%d)` after 21:30 so the situation strip’s Promotion and strategy comparison stay current.

3. **EOD cron**
   - **What:** 21:30 UTC Mon–Fri for `run_stock_quant_officer_eod.py` (or `eod_confirmation.py` where used).
   - **Check on droplet:**  
     `crontab -l | grep -E 'run_stock_quant_officer_eod|eod_confirmation'`

**Summary:** The dashboard is wired so the banner and situation strip **update every 60 seconds** from the backend. For **real automated analysis** and up-to-date “trades reviewed” and “Promotion”:

- Install (and keep) the **direction readiness** cron on the droplet.
- Ensure the **combined report** is produced daily (full EOD script or a dedicated cron for `generate_daily_strategy_reports.py`).
- Keep the **EOD** cron at 21:30 so daily board/EOD artifacts and governance data stay current.

Once those are in place, reviews run on a regular basis and each update is visible on the next dashboard refresh (within 60s).
