# EOD Cron and Local Pull Status

**Checked:** Local git and `board/eod/out/` state.

## 1. Did the EOD cron fire (on the droplet)?

**Yes.** Evidence from git history on `origin/main`:

- **9f90424** — `EOD report auto-sync 2026-01-30 00:06 UTC` (touched `board/eod/out/*.json`, `*.md`)
- **2695cf1** — `EOD report auto-sync 2026-01-30 00:33 UTC`
- **a354555** — `EOD report auto-sync 2026-01-30 02:32 UTC`

So the droplet ran the EOD pipeline and the sync script (`scripts/droplet_sync_to_github.sh`) at least three times on 2026-01-30 and pushed those commits to GitHub. The canonical schedule is EOD at 21:30 UTC and sync at 21:32 UTC; the commit timestamps indicate runs around/after midnight UTC on 2026-01-30.

## 2. Did the report get pulled onto your local machine?

**(Update: pulled and repeatable process added.)** Previously local `main` was behind `origin/main`;

- **Local HEAD:** `399b93e` — *EOD: canonical paths, defensive checks...*
- **origin/main:** `a354555` (and two more EOD sync commits between 399b93e and a354555)

Local has since been updated via `git pull origin main` and scripts `pull_eod_to_local.ps1` / `pull_eod_to_local.sh` were added so future runs are repeatable without conflicts.

## 3. How to get the latest EOD reports locally (repeatable)

**Recommended (weekdays after 21:35 UTC):**

- **Windows (PowerShell):** `.\scripts\pull_eod_to_local.ps1`
- **Git Bash / Linux:** `bash scripts/pull_eod_to_local.sh`

These scripts fetch, align `board/eod/out/` with `origin/main` (droplet source of truth), and pull so you always get the latest EOD without conflicts. Optionally schedule (e.g. Windows Task Scheduler) for the same time each weekday.

**Direct from droplet (optional):** `bash scripts/local_sync_from_droplet.sh` — requires `DROPLET_IP` or `droplet_config.json` and SSH.

## 4. Pipeline summary

| Step | Where | Schedule / Trigger | Status |
|------|--------|---------------------|--------|
| EOD run | Droplet | 21:30 UTC weekdays (cron) | Fired; produced reports |
| Sync to GitHub | Droplet | 21:32 UTC weekdays (cron) | Fired; pushed to origin/main |
| Pull to local | Your machine | Run `pull_eod_to_local.ps1` or `pull_eod_to_local.sh` weekdays after 21:35 UTC | Repeatable; scripts added |
