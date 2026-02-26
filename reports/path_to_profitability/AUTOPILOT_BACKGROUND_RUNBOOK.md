# Path-to-profitability autopilot — background run

## Status

The full autopilot is **running in the background** on the droplet (started via nohup so it survives SSH disconnect).

- **Log:** `/tmp/path_to_profitability_autopilot.log`
- **Watch live:** `ssh <droplet> 'tail -f /tmp/path_to_profitability_autopilot.log'`
- **Current phase:** Waiting for ≥50 closed trades in overlay window (since overlay_start_date). It polls effectiveness every 120s.

## How it was started

```bash
python scripts/start_path_to_profitability_autopilot_background_on_droplet.py
```

That script runs on your machine, SSHs to the droplet, and starts:

```bash
nohup bash -c 'STOP_AFTER_APPLY=0 bash scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh' \
  </dev/null >> /tmp/path_to_profitability_autopilot.log 2>&1 &
```

So the autopilot keeps running after you close SSH.

## Overlay (entry lever)

- **Applied:** `state/paper_overlay.env` (MIN_EXEC_SCORE=2.7)
- **To activate:** On the droplet, before or when restarting the paper bot:
  - `source /root/stock-bot/state/paper_overlay.env`
  - Or set `MIN_EXEC_SCORE=2.7` in the environment for the paper process (e.g. systemd `Environment=` or your start script).
- Until the overlay is active, new paper trades won’t be under the new threshold; the autopilot still counts closed trades in the overlay date range. For a clean 50-trade overlay comparison, restart paper with the overlay and let 50 trades close.

## What happens when 50 trades are reached

1. Autopilot runs `compare_effectiveness_runs.py` (baseline vs overlay window).
2. Writes `reports/path_to_profitability/<RUN_TAG>/lock_or_revert_decision.json` (LOCK or REVERT).
3. Writes `CURSOR_FINAL_SUMMARY.txt` in that run dir.
4. Script exits. No automatic restart; run the background starter again for the next cycle if desired.

## Run again (next cycle)

1. From your machine: `python scripts/start_path_to_profitability_autopilot_background_on_droplet.py`
2. Or on the droplet:  
   `nohup bash -c 'STOP_AFTER_APPLY=0 bash scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh' </dev/null >> /tmp/path_to_profitability_autopilot.log 2>&1 &`
