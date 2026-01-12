# Fix Git Conflicts and Run Investigation on Droplet

## Issue
Git pull is failing because there are local uncommitted changes on the droplet that conflict with incoming changes.

## Solution

Run these commands on the droplet:

```bash
ssh alpaca
cd /root/stock-bot

# Option 1: Stash local changes (saves them for later)
git stash push -m "Auto-stash before investigation"
git pull origin main
python3 investigate_score_stagnation_on_droplet.py > investigation_results.txt 2>&1
cat investigation_results.txt
```

**OR** if you don't need the local changes:

```bash
# Option 2: Force reset to match remote (discards local changes)
cd /root/stock-bot
git fetch origin main
git reset --hard origin/main
python3 investigate_score_stagnation_on_droplet.py > investigation_results.txt 2>&1
cat investigation_results.txt
```

## One-Liner Commands

**With stash (saves changes):**
```bash
ssh alpaca "cd /root/stock-bot && git stash && git pull origin main && python3 investigate_score_stagnation_on_droplet.py"
```

**With force reset (discards changes):**
```bash
ssh alpaca "cd /root/stock-bot && git fetch origin main && git reset --hard origin/main && python3 investigate_score_stagnation_on_droplet.py"
```

## Files with Local Changes
According to the error, these files have local modifications:
- `check_current_trading_status.py`
- `check_latest_activity.py`
- `check_positions_and_signals.py`
- `check_worker_status.py`
- `dashboard.py`
- `investigate_score_bug.py`

If you need to keep these changes, use Option 1 (stash). If not, use Option 2 (reset).
