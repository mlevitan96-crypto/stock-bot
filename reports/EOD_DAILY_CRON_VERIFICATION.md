# EOD Daily Cron Verification

**Purpose:** Confirm the daily EOD report runs when the market is open (weekdays), produces the expected data, and is pushed to GitHub. Last updated: 2026-02-26.

---

## 1. When the EOD report is supposed to fire

| Job | Schedule (UTC) | Days | Meaning |
|-----|----------------|------|---------|
| **EOD report** | **21:30** | Mon–Fri (1-5) | Runs 30 minutes after US market close (4:00 PM ET ≈ 21:00 UTC). |
| **Sync to GitHub** | **21:32** | Mon–Fri (1-5) | Commits EOD outputs + audit/stockbot and pushes to `origin/main`. |

So the EOD report fires **daily on weekdays when the market was open**, after the session has closed. It does **not** run on weekends or US market holidays (cron does not account for holidays; it runs every weekday).

---

## 2. What the workflow provides

1. **21:30 UTC — EOD runner** (`board/eod/run_stock_quant_officer_eod.py`)
   - Loads the canonical 8-file bundle from `logs/` and `state/` (attribution, exit_attribution, master_trade_log, blocked_trades, daily_start_equity, peak_equity, signal_weights, daily_universe_v2).
   - Builds a memo via the Quant Officer contract and Clawdbot (or stub with `--dry-run`).
   - **Outputs:** `board/eod/out/stock_quant_officer_eod_<DATE>.json`, `.md`, and `board/eod/out/<DATE>/` (daily bundle from `bundle_writer`).

2. **21:32 UTC — Sync** (either script)
   - **Preferred:** `scripts/run_droplet_audit_and_sync.sh` — runs `run_stockbot_daily_reports.py` for the date, then `audit_stock_bot_readiness.py`, then commits EOD outputs + `reports/stockbot/<DATE>/` + `reports/droplet_audit/` and pushes.
   - **Fallback:** `scripts/droplet_sync_to_github.sh` — pulls, adds `board/eod/out/` and `reports/stockbot/<DATE>/`, commits and pushes.

So the data provided is: EOD memo (JSON + MD), daily bundle under `board/eod/out/<DATE>/`, and (if audit script runs) the stockbot intelligence pack and droplet audit — all pushed to GitHub.

---

## 3. How to confirm it is happening daily

### On the droplet

1. **Crontab:**  
   `crontab -l` should show:
   - A line containing `run_stock_quant_officer_eod.py` at `30 21 * * 1-5`.
   - A line containing `droplet_sync_to_github.sh` or `run_droplet_audit_and_sync.sh` at `32 21 * * 1-5`.

2. **Logs:**  
   - EOD: `tail -n 200 logs/cron_eod.log`  
   - Sync: `tail -n 200 logs/cron_sync.log`

3. **Recent output:**  
   - `ls -la board/eod/out/` and `ls -la board/eod/out/$(date -u +%Y-%m-%d)/` for today’s files.

### From local (without SSH)

1. **Git history:**  
   After 21:35 UTC on a weekday, `origin/main` should have a commit from the droplet with a message like:
   - `EOD report auto-sync YYYY-MM-DD HH:MM UTC`, or  
   - `Droplet audit + EOD sync YYYY-MM-DD HH:MM UTC`.

2. **Full diagnostic (recommended):**  
   Run the cron + git diagnostic on the droplet and open the generated report:
   - **From local:** `python scripts/run_diagnose_on_droplet_via_ssh.py`  
   - **On droplet:** `python3 scripts/diagnose_cron_and_git.py`  
   Report path: `reports/STOCKBOT_CRON_AND_GIT_DIAGNOSTIC_<DATE>.md` (includes cron state, EOD dry-run, git status, and any repairs).

---

## 4. Issues that can impact the workflow

| Issue | Impact | Fix |
|-------|--------|-----|
| **Only EOD cron installed, no sync** | EOD runs but nothing is pushed to GitHub. | Install both jobs: run `python3 scripts/diagnose_cron_and_git.py` on the droplet, or use `board/eod/install_eod_cron_on_droplet.py` (which now installs EOD + sync). |
| **Wrong repo path in cron** | Jobs run in wrong directory and may fail or push wrong repo. | Re-run diagnostic/installer so cron uses the detected root (e.g. `/root/stock-bot` or `/root/stock-bot-current`). |
| **Missing 8-file bundle** | EOD runner logs missing/empty files and continues with partial data; memo may be thin. | Ensure the trading pipeline has written to `logs/` and `state/` during the day. On droplet, the live/paper run produces these. |
| **Clawdbot not installed / not in PATH** | EOD script can fail when calling the agent. | Use `--dry-run` for testing (writes stub JSON/MD). For production, install clawdbot on the droplet and set `CLAWDBOT_SESSION_ID` (cron sets it automatically). |
| **Git push failures (auth, conflicts)** | Sync cron runs but push fails; no new commits on GitHub. | Check SSH/key and `origin` URL; run `scripts/diagnose_cron_and_git.py` (it can repair SSH/key). Resolve conflicts by aligning droplet with `origin/main` before the next sync. |
| **run_droplet_audit_and_sync.sh missing** | Diagnose/installer falls back to `droplet_sync_to_github.sh` (push only, no audit or daily reports). | Either add `run_droplet_audit_and_sync.sh` to the repo and re-run diagnostic, or accept sync-only behavior. |

---

## 5. Quick checklist

- [ ] Crontab has `30 21 * * 1-5` for `run_stock_quant_officer_eod.py`.
- [ ] Crontab has `32 21 * * 1-5` for `droplet_sync_to_github.sh` or `run_droplet_audit_and_sync.sh`.
- [ ] `logs/cron_eod.log` and `logs/cron_sync.log` exist and are updated on weekdays after 21:30 UTC.
- [ ] `board/eod/out/` contains recent dates and `stock_quant_officer_eod_<DATE>.json|.md`.
- [ ] After 21:35 UTC on a weekday, `origin/main` has a recent EOD/audit sync commit.

---

## 6. References

- **Canonical schedule:** Memory Bank §5.5; `docs/EOD_DATA_PIPELINE.md` §4.
- **Cron + Git diagnostic:** `scripts/diagnose_cron_and_git.py`; remote: `scripts/run_diagnose_on_droplet_via_ssh.py`.
- **EOD installer (EOD + sync):** `board/eod/install_eod_cron_on_droplet.py`.
- **Local pull (after droplet sync):** `scripts/pull_eod_to_local.ps1` (Windows), `scripts/pull_eod_to_local.sh` (Git Bash/Linux).
