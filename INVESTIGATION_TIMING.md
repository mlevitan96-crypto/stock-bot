# Investigation Report Timing

## When Will the Report Run?

The investigation report will run **automatically** when the droplet's status reporting script detects the trigger file.

### Current Setup

**Status Report Script:** `report_status_to_git_complete.sh`
- This script checks for investigation triggers
- It needs to be run via cron job

### Timing Options

#### Option 1: Hourly Status Report (If Cron is Set Up)
- **Frequency:** Every hour (at :00 minutes)
- **When it runs:** Next hour boundary after trigger is pushed
- **Example:** If trigger pushed at 2:15 PM, report runs at 3:00 PM

#### Option 2: Manual Execution (Immediate)
If you want the report to run immediately, you can run on the droplet:
```bash
cd ~/stock-bot
git pull origin main
bash report_status_to_git_complete.sh
```

#### Option 3: Direct Investigation (Fastest)
Run the investigation directly on the droplet:
```bash
cd ~/stock-bot
git pull origin main
python3 investigate_no_trades.py
git add investigate_no_trades.json
git commit -m "Investigation results - $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main
```

### Check Current Cron Setup

To see if hourly status reporting is configured, run on droplet:
```bash
crontab -l | grep report_status
```

If you see something like:
```
0 * * * * cd ~/stock-bot && bash report_status_to_git_complete.sh
```
Then it's running hourly.

### Recommended: Set Up Hourly Cron (If Not Already Done)

Run this on the droplet to set up hourly status reports:
```bash
cd ~/stock-bot
(crontab -l 2>/dev/null | grep -v "report_status_to_git"; 
 echo "0 * * * * cd ~/stock-bot && bash report_status_to_git_complete.sh >> /tmp/status_report.log 2>&1") | crontab -
```

### Expected Timeline

- **If cron is set up:** Within 1 hour (next hour boundary)
- **If cron is NOT set up:** Never (until you run it manually or set up cron)
- **Manual execution:** Immediately when you run the script

### Quick Check: Is Cron Running?

To verify the status report script is being called, check on droplet:
```bash
tail -20 /tmp/status_report.log
```

If the file doesn't exist or is empty, the cron job may not be set up.

