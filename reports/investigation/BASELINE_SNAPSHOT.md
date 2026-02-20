# Baseline snapshot (Phase 0)

**Run on droplet to populate this file.**

## DROPLET COMMANDS

```bash
cd /root/stock-bot   # or your repo path
python3 scripts/investigation_baseline_snapshot_on_droplet.py
```

## Placeholder

After running the script on the droplet, this file will contain:

- Service/process status (systemctl status stock-bot or equivalent)
- Newest timestamps in key logs (ledger, snapshots, UW, adjustments, orders, expectancy_gate_truth)
- Last 24h counts: candidates evaluated, expectancy gate pass/fail, submit_entry lines, SUBMIT_ORDER_CALLED lines

Evidence must come from the droplet.
