# Droplet script presence (Phase 1)

**Run on droplet after git pull to regenerate this file.**

## Required scripts

| Script | Present |
|--------|---------|
| scripts/investigation_baseline_snapshot_on_droplet.py | (run verify_droplet_script_presence.py) |
| scripts/run_closed_loops_checklist_on_droplet.py | (run verify_droplet_script_presence.py) |
| scripts/expectancy_gate_truth_report_200_on_droplet.py | (run verify_droplet_script_presence.py) |
| scripts/signal_score_breakdown_summary_on_droplet.py | (run verify_droplet_script_presence.py) |
| scripts/full_signal_review_on_droplet.py | (run verify_droplet_script_presence.py) |

## DROPLET COMMANDS

```bash
cd /root/stock-bot
git fetch origin && git pull origin main
python3 scripts/verify_droplet_script_presence.py
```

If any are missing: commit and push from local, then re-run git pull on droplet.
