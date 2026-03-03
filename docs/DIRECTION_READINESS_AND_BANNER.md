# Direction Readiness and Dashboard Banner

Trade-count-based readiness for directional intelligence replay, with dashboard banner and optional scheduling.

## Overview

- **Readiness:** 100+ telemetry-backed trades and ≥90% telemetry (from `exit_attribution.jsonl` with `direction_intel_embed.intel_snapshot_entry`).
- **State:** `state/direction_readiness.json` (once `ready` is true, it does not flip back).
- **Replay trigger:** When readiness flips to true, `scripts/governance/check_direction_readiness_and_run.py` runs the 30d direction replay on the droplet and writes `state/direction_replay_status.json`.
- **Banner:** Dashboard shows a persistent top banner (WAITING | RUNNING | RESULTS | BLOCKED) via `/api/direction_banner` and updates every 60s.

## Scheduling

Run the check script regularly so that when 100 telemetry-backed trades are reached, the replay runs once.

**Cron (recommended):** Every 15–30 minutes during market hours.

```cron
# Every 30 minutes, 9–16, Mon–Fri (adjust for your timezone)
0,30 9-16 * * 1-5 cd /root/stock-bot && python3 scripts/governance/check_direction_readiness_and_run.py
```

Or every 15 minutes:

```cron
*/15 9-16 * * 1-5 cd /root/stock-bot && python3 scripts/governance/check_direction_readiness_and_run.py
```

**Optional:** If you have an existing “100 trades” or intelligence gate that runs on a schedule, run this script in the same cron slot so direction readiness and other counters are visible together on the dashboard (counters remain separate; only scheduling is shared).

## No live behavior changes

This flow is governance and observability only. It does not change entry logic, exit logic, or direction logic.
