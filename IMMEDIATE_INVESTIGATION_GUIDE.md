# Immediate Investigation Guide

## You're Right - We Can Trigger It Anytime!

The investigation can be triggered immediately via Git. Here are the methods:

## Method 1: Git Hook (Automatic on Pull)

If the droplet has a post-merge git hook set up, it will run automatically when you push and the droplet pulls.

**To set up on droplet:**
```bash
cd ~/stock-bot
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
cd ~/stock-bot
if [ -f "run_investigation_on_pull.sh" ]; then
    bash run_investigation_on_pull.sh
fi
EOF
chmod +x .git/hooks/post-merge
```

## Method 2: Manual Execution Script

I've created `trigger_immediate_investigation_via_git.sh` which the droplet can run:

**On droplet:**
```bash
cd ~/stock-bot
git pull origin main
chmod +x trigger_immediate_investigation_via_git.sh
./trigger_immediate_investigation_via_git.sh
```

## Method 3: Direct SSH (If droplet_client.py works)

If `droplet_config.json` is configured, you can run:
```bash
python trigger_investigation_now.py
```

This will:
1. Connect via SSH
2. Pull latest code
3. Run investigation
4. Commit and push results
5. Pull results locally
6. Display summary

## Method 4: Simple Git Push Trigger

Just push the trigger file and the droplet's status script will pick it up on next run:

**From Cursor:**
```bash
echo "trigger" > .investigation_trigger
git add .investigation_trigger
git commit -m "Trigger investigation"
git push origin main
```

**Then on droplet (or wait for cron):**
```bash
cd ~/stock-bot
git pull origin main
bash report_status_to_git_complete.sh  # This checks for triggers
```

## Recommended: Method 2 (Manual Script)

The simplest and most reliable is to have the droplet run:
```bash
cd ~/stock-bot && git pull origin main && chmod +x run_investigation_on_pull.sh && ./run_investigation_on_pull.sh
```

This will:
- Pull latest code (including any fixes)
- Run investigation immediately
- Push results back to git
- Take about 30-60 seconds total

