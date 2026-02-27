# Truth log enablement proof (Phase 2)

Enable EXPECTANCY_GATE_TRUTH_LOG and SIGNAL_SCORE_BREAKDOWN_LOG in the **stock-bot systemd service** (not a one-off shell). Prove env vars are active in the running process.

## 1) Set env vars for stock-bot service

**Option A — systemd override (recommended)**

```bash
sudo mkdir -p /etc/systemd/system/stock-bot.service.d
sudo tee /etc/systemd/system/stock-bot.service.d/override.conf << 'EOF'
[Service]
Environment="EXPECTANCY_GATE_TRUTH_LOG=1"
Environment="SIGNAL_SCORE_BREAKDOWN_LOG=1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart stock-bot
```

**Option B — if service uses EnvironmentFile (e.g. .env)**

Add to the env file used by the service (e.g. `/root/stock-bot/.env`):

```
EXPECTANCY_GATE_TRUTH_LOG=1
SIGNAL_SCORE_BREAKDOWN_LOG=1
```

Then:

```bash
sudo systemctl restart stock-bot
```

## 2) Prove env vars are active

**Systemd show:**

```bash
systemctl show stock-bot --property=Environment
systemctl show stock-bot --property=EnvironmentFiles
```

**Process env (replace PID with actual main.py pid):**

```bash
PID=$(pgrep -f "main.py" | head -1)
[ -n "$PID" ] && cat /proc/$PID/environ | tr '\0' '\n' | grep -E 'EXPECTANCY_GATE_TRUTH_LOG|SIGNAL_SCORE_BREAKDOWN_LOG'
```

Expected: lines like `EXPECTANCY_GATE_TRUTH_LOG=1` and `SIGNAL_SCORE_BREAKDOWN_LOG=1`.

## 3) Run until truth logs are populated

- **logs/expectancy_gate_truth.jsonl** ≥ 200 lines  
- **logs/signal_score_breakdown.jsonl** ≥ 100 lines (100 candidates)

Check counts:

```bash
wc -l /root/stock-bot/logs/expectancy_gate_truth.jsonl
wc -l /root/stock-bot/logs/signal_score_breakdown.jsonl
```

## 4) Document proof

Fill in after running:

| Check | Command / path | Result |
|-------|----------------|--------|
| systemd Environment | `systemctl show stock-bot --property=Environment` | (paste output) |
| Process env | `cat /proc/<pid>/environ \| tr '\\0' '\\n' \| grep EXPECTANCY` | (paste output) |
| Gate truth lines | logs/expectancy_gate_truth.jsonl | (count) |
| Breakdown lines | logs/signal_score_breakdown.jsonl | (count) |

## DROPLET COMMANDS (summary)

```bash
# Set env (override)
sudo mkdir -p /etc/systemd/system/stock-bot.service.d
sudo tee /etc/systemd/system/stock-bot.service.d/override.conf << 'EOF'
[Service]
Environment="EXPECTANCY_GATE_TRUTH_LOG=1"
Environment="SIGNAL_SCORE_BREAKDOWN_LOG=1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart stock-bot

# Proof
systemctl show stock-bot --property=Environment
PID=$(pgrep -f "main.py" | head -1); [ -n "$PID" ] && cat /proc/$PID/environ | tr '\0' '\n' | grep -E 'EXPECTANCY|SIGNAL_SCORE'

# Wait until 200 + 100 lines, then check
wc -l /root/stock-bot/logs/expectancy_gate_truth.jsonl /root/stock-bot/logs/signal_score_breakdown.jsonl
```