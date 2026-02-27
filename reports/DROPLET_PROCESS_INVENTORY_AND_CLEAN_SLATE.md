# Droplet Process Inventory and Clean-Slate Runbook

**Generated:** 2026-02-23 (from `scripts/list_droplet_processes.py`)

## Why CPU can show 100% even though processes don’t add up

- **Load average 3.14** means the system had ~3 runnable/waiting threads on average. On a 1‑vCPU droplet that’s heavy; on 4 vCPUs it’s ~78% utilization.
- **Visible process %CPU** (e.g. ~20% total for stock-bot) is a single snapshot. Spikes from **uw_flow_daemon** (e.g. 11% in one run), **cron jobs**, or **short-lived scripts** can push CPU to 100% between snapshots.
- **Full disk (100% full)** causes **I/O wait**. The CPU isn’t busy with user code but the system is waiting on disk; load goes up and the box can feel “maxed out.” Freeing disk often reduces load more than killing a few processes.
- **Duplicates/orphans** (e.g. old **main.py** in tmux, extra **uw_flow_daemon** not under systemd) add unnecessary CPU and can cause contention. Removing them is still recommended.

**Action:** Free disk first, then remove duplicate/orphan processes (see script below), then re-check load with `python scripts/list_droplet_processes.py` (section 0: load average and top by CPU).

---

## CPU usage (stock-bot processes)

Current snapshot (run `python scripts/list_droplet_processes.py` for live data):

| Process | PID | %CPU (current) | %MEM | Cumulative CPU time |
|--------|-----|-----------------|------|----------------------|
| **main.py** (supervisor) | 2872614 | 1.6 | 10.1 | 22m 36s |
| **main.py** (old, tmux) | 2729707 | **4.3** | 7.6 | **4h 10m** |
| **uw_flow_daemon.py** | 2929167 | **4.0** | 1.7 | ~1s (just started) |
| **cache_enrichment_service.py** | 525359 | 0.7 | 2.3 | **10h 43m** |
| heartbeat_keeper.py | 2872627 | 0.5 | 2.2 | 8m 19s |
| deploy_supervisor.py | 2872545 | 0.1 | 3.9 | 1m 42s |
| dashboard.py | 2872604 | 0.1 | 5.9 | 1m 55s |
| systemd_start.sh | 2872544 | 0.0 | 0.0 | 0 |

- **%CPU** = instantaneous load at snapshot; **Cumulative CPU time** = total CPU seconds the process has used since start.
- **Total current CPU** (stock-bot): ~11–12% at snapshot. Heaviest: old **main.py** (4.3%) and **uw_flow_daemon** (4%); **cache_enrichment** has used the most total CPU (10h 43m) but is currently light (0.7%).

---

## Critical: Disk Full

- **`/` (root) is 100% full** (48G used, 0 avail). Git and many writes will fail until you free space.
- Free space first (see “Freeing disk” below) before changing services or re-running remediation.

---

## What Is Running (Stock-Bot Related)

| PID     | Command / Role                    | Started  | Notes |
|--------|------------------------------------|----------|--------|
| 2872544 | `systemd_start.sh`                | Feb 22   | Entrypoint from **stock-bot.service** |
| 2872545 | `deploy_supervisor.py`            | Feb 22   | Supervisor (children below) |
| 2872604 | `dashboard.py`                    | Feb 22   | Dashboard (Flask) |
| 2872614 | **`main.py`** (supervisor)        | Feb 22   | Main trading loop (under systemd) |
| 2872627 | `heartbeat_keeper.py`             | Feb 22   | Heartbeat |
| 2928907 | `uw_flow_daemon.py`               | Today    | UW flow daemon (not started by uw-flow-daemon.service; see below) |
| 525359  | `cache_enrichment_service.py --continuous` | 2025  | **Standalone**, ~643 min CPU total |
| 2729707 | **`main.py`** (pts/0 / tmux)      | **Feb 19** | **Duplicate main** – old session |
| 2928983 | `[python] <defunct>`              | -        | Zombie process |

So you have:

- **Two `main.py`**: one from **stock-bot.service** (Feb 22) and one **old** in a **tmux/pts session** (Feb 19). The tmux one is redundant and can be stopped.
- **One `uw_flow_daemon.py`**: running but **uw-flow-daemon.service** is **inactive**; it was likely started manually or by a script.
- **One `cache_enrichment_service.py`**: long-running, not under stock-bot.service; started separately (e.g. manually or old cron).

---

## Systemd Units (Stock-Bot)

| Unit                          | State              | Meaning |
|------------------------------|--------------------|--------|
| **stock-bot.service**        | **active / running** | Starts `systemd_start.sh` → supervisor → main, dashboard, heartbeat |
| stock-bot-dashboard.service  | enabled, **inactive dead** | Dashboard is actually run by supervisor, not this unit |
| stock-bot-dashboard-audit.service | inactive        | Fired by timer (nightly audit) |
| stock-bot-dashboard-audit.timer | active, waiting  | Daily 02:00 UTC |
| **uw-flow-daemon.service**   | **enabled, inactive dead** | UW daemon we see is *not* from this unit |
| trading-bot-doctor.timer    | enabled            | Doctor checks |

Only **stock-bot.service** is actually running the main stack; the rest are either timers or unused.

---

## Cron (Root)

- **Hourly:** `report_status_to_git.sh`
- **Mon–Fri 20:30 UTC:** `specialist_tier_monitoring_orchestrator.py`
- **Daily 20:30 UTC:** `scripts/run_full_telemetry_extract.py`
- **Mon–Fri 21:31 UTC:** `run_exit_join_and_blocked_attribution_on_droplet.py`
- **Mon–Fri 21:32 UTC:** `droplet_sync_to_github.sh`
- **Mon–Fri 21:20 UTC:** `board/eod/cron_health_check.py`
- **Mon–Fri 21:30 UTC:** `board/eod/eod_confirmation.py`

Cron jobs are fine to keep; they don’t add duplicate long-lived processes.

---

## Other Heavy Processes

- **clawdbot-gateway** – ~352 MB RSS (Jan 29)
- **rsyslogd** – ~96 MB
- **do-agent** – DigitalOcean monitoring

These are system/DO, not stock-bot. Leave them unless you have a reason to stop them.

---

## Recommended “Kill and Start from Scratch” (Minimal Set)

Goal: one clean stack under systemd, no duplicate `main.py`, no stray Python trading processes.

### 1. Free disk (do this first)

On the droplet:

```bash
# Large logs
sudo journalctl --vacuum-size=100M
sudo find /root/stock-bot/logs -type f -name "*.log" -mtime +7 -delete
sudo find /var/log -type f -name "*.log" -mtime +14 -size +10M -delete

# Optional: clear old backtest/reports if you don’t need them
# du -sh /root/stock-bot/reports/backtests
# rm -rf /root/stock-bot/reports/backtests/alpaca_backtest_*
# du -sh /root/stock-bot/backtests
```

Then re-check: `df -h /`

### 2. Stop everything stock-bot (and optional extras)

Run on droplet (e.g. SSH):

```bash
# Stop systemd-managed stack (supervisor + main, dashboard, heartbeat)
sudo systemctl stop stock-bot.service

# Kill old main.py in tmux (duplicate)
kill 2729707

# Optional: stop standalone cache enrichment (only if you’re sure you don’t need it running 24/7 here)
# kill 525359

# Optional: stop uw_flow_daemon if you want systemd to own it later
# kill 2928907

# Zombie will go away when its parent is gone; or reboot later
```

If you use tmux and want to close the session that had the old main:

```bash
tmux list-sessions
tmux kill-session -t trading   # only if that’s the session with the old main
```

### 3. Start only what you need (minimal)

- **Option A – Only systemd (recommended)**  
  Start the main stack and optionally the UW daemon under systemd:

  ```bash
  sudo systemctl start stock-bot.service
  sudo systemctl start uw-flow-daemon.service   # if you want UW daemon managed by systemd
  ```

- **Option B – Systemd + cache enrichment**  
  If `cache_enrichment_service.py` must run continuously, start it via systemd (if you have a unit) or a single dedicated tmux/screen session so you don’t accumulate duplicates.

After starting, verify:

```bash
ps aux | grep -E 'main.py|dashboard|heartbeat|uw_flow|deploy_supervisor' | grep -v grep
# Expect one main.py, one dashboard, one heartbeat, one deploy_supervisor; optionally one uw_flow_daemon.
```

### 4. Optional: disable duplicate/unused units

To avoid accidentally starting a second dashboard or overlapping UW daemon:

```bash
sudo systemctl disable stock-bot-dashboard.service   # dashboard already under stock-bot
# Leave uw-flow-daemon.service enabled if you start it in step 3.
```

---

## Script: Kill duplicate/orphan processes on droplet

From your machine (with `droplet_config.json`):

```bash
# Dry run: only list what would be killed
python scripts/kill_droplet_duplicates.py

# Actually kill duplicate main.py and extra uw_flow_daemon (keeps one of each)
python scripts/kill_droplet_duplicates.py --kill
```

The script discovers **orphan `main.py`** (e.g. the one in tmux/pts, not under deploy_supervisor) and **extra `uw_flow_daemon`** if more than one is running, then optionally sends `SIGTERM`. It does **not** stop `stock-bot.service` or the supervised main/dashboard/heartbeat. After `--kill`, re-check with `python scripts/list_droplet_processes.py`.

---

## Script: List Processes Again

From your machine (with `droplet_config.json` and `DROPLET_*` if needed):

```bash
python scripts/list_droplet_processes.py
```

Use this after cleanup to confirm only the desired processes are running.

---

## Summary

- **Running:** stock-bot.service (supervisor → main, dashboard, heartbeat), one standalone cache_enrichment_service, one uw_flow_daemon, and an **old duplicate main.py** in tmux.
- **Kill:** old `main.py` (2729707); optionally cache_enrichment (525359) and/or uw_flow_daemon (2928907) if you want to own them only via systemd.
- **Free disk first** (root 100% full), then stop stock-bot.service, kill the duplicate main, then start `stock-bot.service` (and optionally `uw-flow-daemon.service`) for a clean slate.
