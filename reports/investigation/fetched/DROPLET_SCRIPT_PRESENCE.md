# Droplet script presence (Phase 1)

Required scripts after `git pull origin main`:

| Script | Present |
|--------|---------|
| scripts/investigation_baseline_snapshot_on_droplet.py | YES |
| scripts/run_closed_loops_checklist_on_droplet.py | YES |
| scripts/expectancy_gate_truth_report_200_on_droplet.py | YES |
| scripts/signal_score_breakdown_summary_on_droplet.py | YES |
| scripts/full_signal_review_on_droplet.py | YES |

## ls output (key scripts)

```
-rw-r--r-- 1 root root  3760 Feb 20 20:17 /root/stock-bot/scripts/expectancy_gate_truth_report_200_on_droplet.py
-rw-r--r-- 1 root root 35461 Feb 20 20:17 /root/stock-bot/scripts/full_signal_review_on_droplet.py
-rw-r--r-- 1 root root  6006 Feb 20 20:17 /root/stock-bot/scripts/investigation_baseline_snapshot_on_droplet.py
-rw-r--r-- 1 root root  9324 Feb 20 20:17 /root/stock-bot/scripts/run_closed_loops_checklist_on_droplet.py
-rw-r--r-- 1 root root 10777 Feb 20 20:17 /root/stock-bot/scripts/signal_score_breakdown_summary_on_droplet.py
```

## DROPLET COMMANDS

```bash
cd /root/stock-bot   # or /root/stock-bot-current
git fetch origin && git pull origin main
python3 scripts/verify_droplet_script_presence.py
```

If any script is missing: commit and push from local, then re-run git pull on droplet.