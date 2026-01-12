# Droplet Score Stagnation Investigation Instructions

Since there are Python execution issues on the local machine, here are instructions to run the investigation directly on the droplet.

## Option 1: SSH into droplet and run manually

1. SSH into your droplet:
   ```bash
   ssh alpaca
   # or
   ssh root@104.236.102.57
   ```

2. Navigate to the project directory:
   ```bash
   cd /root/stock-bot
   ```

3. Pull the latest code (to get the investigation script):
   ```bash
   git pull origin main
   ```

4. Run the investigation:
   ```bash
   python3 investigate_score_stagnation_on_droplet.py > investigation_results.txt 2>&1
   ```

5. View the results:
   ```bash
   cat investigation_results.txt
   ```

6. Copy results back to local machine (in a new terminal):
   ```bash
   scp root@104.236.102.57:/root/stock-bot/investigation_results.txt .
   ```

## Option 2: Run commands directly via SSH (one-liner)

From your local machine:
```bash
ssh root@104.236.102.57 "cd /root/stock-bot && git pull origin main && python3 investigate_score_stagnation_on_droplet.py"
```

## Option 3: Use the diagnostic script already on droplet

If `comprehensive_score_diagnostic.py` exists on the droplet, you can run:
```bash
ssh root@104.236.102.57 "cd /root/stock-bot && python3 comprehensive_score_diagnostic.py"
```

## What to Check After Running

The investigation will check:

1. **Adaptive Weights State** - Which components have reduced weights
2. **Stagnation Detector State** - Current stagnation metrics
3. **Recent Scores** - Actual score distribution from cache
4. **Signal Funnel** - Conversion rates and stagnation status
5. **Component Contributions** - Which components are contributing/not contributing

## Key Files to Review

After running, check these files on the droplet:
- `state/signal_weights.json` - Adaptive weight state
- `state/logic_stagnation_state.json` - Stagnation detector state
- `state/signal_funnel_state.json` - Funnel metrics
- `data/uw_flow_cache.json` - Recent signal data
- `logs/logic_stagnation.jsonl` - Stagnation event log
