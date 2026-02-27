# Droplet Upsize Recommendation

**Context:** 48G disk 100% full, load average ~3.14, multiple stock-bot processes + cron jobs and “massive data sets” going forward.

---

## Recommendation: **Upsize Disk + CPU + RAM** (not CPU+RAM only)

Choose the option that includes **Disk, CPU, and RAM**. Disk is your immediate bottleneck; CPU and RAM will support heavier backtests and signal pipelines without constant pruning.

---

## Why include disk

- Root is **100% full** today. Git, logs, and many writes are already failing.
- Your workload is **data-heavy**: logs (attribution, telemetry, signal_context, master_trade_log), state and data (uw_flow_cache, expanded_intel), **reports/backtests** (many `alpaca_backtest_*` and similar dirs), EOD bundles, and bars/cache.
- “Massive data sets going forward” means this will grow. Even with good housekeeping (log rotation, pruning old backtests), 48G is too small for comfort.
- **Upsizing CPU+RAM only** leaves you on 48G; you’ll keep fighting space and I/O wait.

---

## Suggested minimum targets (after resize)

| Resource | Current (inferred) | Suggested minimum | Rationale |
|----------|--------------------|--------------------|------------|
| **Disk** | 48G (full)         | **80–100 GB**      | Headroom for logs, backtests, reports, cache, and future runs without constant cleanup. |
| **CPU**  | ~1 vCPU (load 3+)   | **2–4 vCPUs**      | Load ~3 on 1 vCPU is saturated; bursty jobs (uw_flow_daemon, full_signal_review, cron) need headroom so the main loop isn’t starved. |
| **RAM**  | ~2–4 GB (from %MEM)| **4–8 GB**         | main + dashboard + supervisor + cache_enrichment + clawdbot-gateway already use a large share; backtests and signal reviews use more. More RAM reduces swap and OOM risk. |

- If the resize options are fixed tiers (e.g. “2 vCPU / 4 GB / 80 GB” vs “4 vCPU / 8 GB / 160 GB”), prefer at least **80 GB disk** and **2 vCPU / 4 GB RAM** as a minimum; **4 vCPU / 8 GB / 100+ GB** is better for “massive data sets” and concurrent cron/backtests.
- If you can choose disk separately: **80–100 GB** is a good target; **128 GB** is safer long term.

---

## Why not CPU+RAM only?

- Frees no disk. You stay at 48G and 100% full.
- I/O wait will continue to drive high load and slow everything down.
- You’d still need to aggressively prune logs and backtests, which conflicts with “massive data sets” and keeping history.

---

## After you resize

1. **Free space first** (even on a bigger disk, clean once):  
   `journalctl --vacuum-size=100M`, prune old logs under `logs/` and `reports/backtests/` (e.g. keep last N runs).
2. **Kill duplicate/orphan processes** so one clean stack runs:  
   `python scripts/kill_droplet_duplicates.py --kill`
3. **Keep housekeeping**: log rotation, periodic prune of old backtest/report dirs, and monitoring of `df -h` so disk doesn’t fill again.

---

## Summary

- **Yes, upsize** — current disk is full and load is high; more resources match your direction (massive datasets, backtests, signal pipeline).
- **Prefer the “Disk + CPU + RAM” option** and aim for at least **80–100 GB disk**, **2–4 vCPUs**, **4–8 GB RAM** so you have headroom for growth and fewer outages from disk and CPU.

---

## CPU type: Premium Intel vs AMD vs regular

- **Regular** – Shared vCPUs, variable performance; fine if cost-sensitive.
- **Premium AMD** – Usually best performance per dollar; NVMe storage; good for data-heavy and bursty workloads.
- **Premium Intel** – Slightly more expensive than Premium AMD; also NVMe and consistent CPU. Either Premium option is better than Regular for a trading bot; choose Premium AMD unless you have a reason to prefer Intel.

---

## After you power the droplet back on (post-upgrade)

1. **Turn the droplet off** in the DO console, change plan (resize), then **power it back on**.
2. Once it’s back up, tell me **“Droplet is back on”** or similar and I can run the restart for you from here.

I’ll run (via SSH):

- `sudo systemctl start stock-bot.service` — main loop, supervisor, dashboard, heartbeat  
- `sudo systemctl start uw-flow-daemon.service` — UW flow daemon  

Then verify with `scripts/list_droplet_processes.py`.

You can also run it yourself from the repo:

```bash
python scripts/start_droplet_services.py
```

That script starts both services and prints status. No need to SSH in unless you want to.
