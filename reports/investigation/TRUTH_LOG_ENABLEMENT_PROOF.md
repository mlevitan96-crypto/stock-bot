# Truth log enablement proof (Phase 2)

## Required env vars (for stock-bot service)

- `EXPECTANCY_GATE_TRUTH_LOG=1`
- `SIGNAL_SCORE_BREAKDOWN_LOG=1`

## Proof (run on droplet)

### 1) systemctl show stock-bot --property=Environment
```bash
systemctl show stock-bot --property=Environment
```

**Result (example):** Environment must contain EXPECTANCY_GATE_TRUTH_LOG=1 and SIGNAL_SCORE_BREAKDOWN_LOG=1.

**Captured:** (systemctl not available or error: [WinError 2] The system cannot find the file specified)

### 2) /proc/<pid>/environ contains both vars
```bash
systemctl show stock-bot --property=MainPID
# Then: cat /proc/<MainPID>/environ | tr '\0' '\n' | grep -E 'EXPECTANCY_GATE_TRUTH_LOG|SIGNAL_SCORE_BREAKDOWN_LOG'
```

**Note:** MainPID not available (service not running or not systemd).

### 3) Log file paths and counts

- **logs/expectancy_gate_truth.jsonl:** C:\Dev\stock-bot\logs\expectancy_gate_truth.jsonl — **0 lines** (required >= 200)
- **logs/signal_score_breakdown.jsonl:** C:\Dev\stock-bot\logs\signal_score_breakdown.jsonl — **0 candidates** (required >= 100)

## DROPLET COMMANDS (enable and restart)

```bash
cd /root/stock-bot
# Add to service environment (e.g. in /etc/systemd/system/stock-bot.service or Environment= line)
sudo systemctl set-environment EXPECTANCY_GATE_TRUTH_LOG=1 SIGNAL_SCORE_BREAKDOWN_LOG=1  # or edit service file
# Better: edit service file to add:
# Environment="EXPECTANCY_GATE_TRUTH_LOG=1"
# Environment="SIGNAL_SCORE_BREAKDOWN_LOG=1"
sudo systemctl daemon-reload
sudo systemctl restart stock-bot
systemctl show stock-bot --property=Environment
python3 scripts/truth_log_enablement_proof_on_droplet.py
```
