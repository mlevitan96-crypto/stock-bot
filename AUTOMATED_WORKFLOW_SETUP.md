# Automated Investigation Workflow Setup

## One-Time Setup (Run Once on Droplet)

```bash
cd ~/stock-bot
git pull origin main
chmod +x update_status_script.sh
./update_status_script.sh
```

This updates your existing hourly status script to also check for investigation triggers.

## How It Works

1. **I trigger investigation**: `python trigger_investigation.py` (runs locally in Cursor)
2. **Creates trigger file** in git: `.investigation_trigger`
3. **Droplet detects trigger**: Next hourly status run (or within 1 hour) checks for trigger
4. **Droplet runs investigation**: Automatically runs `investigate_no_trades.py`
5. **Results committed to git**: `investigate_no_trades.json` is committed and pushed
6. **I read results**: `python read_investigation_results.py` (runs locally in Cursor)

## Usage

**From Cursor (me):**
```bash
# Trigger investigation
python trigger_investigation.py

# Wait ~1 minute (for next hourly run) or up to 1 hour

# Read results
python read_investigation_results.py
```

**On Droplet (you - one time only):**
```bash
cd ~/stock-bot && git pull && chmod +x update_status_script.sh && ./update_status_script.sh
```

After that, everything is automatic!

