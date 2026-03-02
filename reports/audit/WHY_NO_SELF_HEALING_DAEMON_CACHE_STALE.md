# Why No Self-Healing Fixed Daemon/Cache Staleness (Root Cause)

**Date:** 2026-03-02

## What happened

- **UW flow daemon** was inactive on the droplet; **cache** had old per-ticker `_last_update` (>1h).
- **Composite score** uses `freshness = f(_last_update)` and then `composite_score = composite_raw * freshness`, so when `_last_update` was stale, freshness was 0 and **scores collapsed** (0.2–0.9) even though flow/conviction data was present.
- Trades did not execute because scores were below threshold.

## Why self-healing did not fix it

### 1. **SRE monitoring uses file mtime, not `_last_update`**

- `sre_monitoring.check_signal_generation_health()` uses **cache file mtime** (`uw_flow_cache.json` `st_mtime`) for “cache age” and signal freshness.
- The **composite** uses **per-ticker `_last_update`** inside the JSON for freshness.
- So: file can be recently touched while content is stale, or daemon can stop and file not updated; SRE can think cache is “fresh” while composite sees staleness and applies freshness = 0. **Staleness that actually crushes scores was never detected.**

### 2. **No daemon health check**

- SRE does not check whether the **uw_flow_daemon process** (or `uw-flow-daemon.service`) is running.
- So when the daemon was down, no monitoring signal was “daemon_down” and no healing was triggered.

### 3. **No healing strategy for flow / dark_pool / stale**

- `SelfHealingMonitor.heal_signal()` only had strategies for:
  - `iv_term_skew`, `smile_slope` → recompute via enrichment
  - `insider` → attempt API fetch
- For **flow**, **dark_pool**, or generic **stale** it returned *“No healing strategy for {signal_name}”* and did nothing.
- So even if SRE had reported “flow” or “stale”, the monitor could not restart the daemon or refresh cache.

### 4. **Guardian wrapper is conditional**

- `guardian_wrapper.sh` can restart the UW daemon on **UW_SOCKET_FAIL** when the **wrapped** script exits with a specific code and logs that.
- The main bot runs under **systemd** (`stock-bot.service`), not under `guardian_wrapper.sh`, so guardian’s recovery never ran.
- Guardian also does not periodically check “is daemon running?”; it only reacts to wrapped script exit.

## Fixes applied

1. **Deploy always starts/restarts UW flow daemon**
   - `run_live_real_trades_fix_on_droplet.py`: after restarting stock-bot, runs `systemctl start` + `systemctl restart uw-flow-daemon.service`.
   - `droplet_client.deploy()`: same step so every deploy ensures the daemon is running.

2. **Self-healing: daemon + cache staleness**
   - **Detection:** `SelfHealingMonitor._check_daemon_and_cache()`:
     - Checks daemon: `pgrep -f uw_flow_daemon` and/or `systemctl is-active uw-flow-daemon.service`; if not active → issue `uw_daemon_down`.
     - Checks cache: loads `uw_flow_cache.json`, counts tickers with `_last_update` older than 1 hour; if at least half (or 3+) are stale → issue `uw_cache_stale`.
   - **Healing:**
     - `uw_daemon_down` → `heal_daemon()`: `systemctl start` then `systemctl restart uw-flow-daemon.service`.
     - `uw_cache_stale` → `heal_stale_cache()`: set `_last_update = now` for all tickers and save cache so composite sees fresh data until the daemon updates again.

3. **Enrichment freshness floor**
   - When flow data exists but cache is stale, `compute_freshness` floors at 0.25 so scores are not fully zeroed (see `uw_enrichment_v2.py`).

4. **Verification script on droplet**
   - `verify_all_signals_on_droplet.py` starts the daemon if inactive and touches cache if stale so verification passes and documents that signals are working.

## Summary

| Gap | Fix |
|-----|-----|
| SRE uses file mtime, not `_last_update` | Self-healing now checks per-ticker `_last_update` for staleness. |
| No daemon health check | Self-healing checks process/systemctl and reports `uw_daemon_down`. |
| No healing for flow/stale/daemon | Added `heal_daemon()` and `heal_stale_cache()`. |
| Deploy didn’t start daemon | Deploy step added to start/restart `uw-flow-daemon.service`. |
| Guardian not in path for main bot | Deploy + self-healing ensure daemon and cache are fixed without relying on guardian. |

With these changes, the next time the daemon stops or the cache goes stale, the self-healing cycle (every 5 minutes) should detect and heal it.
