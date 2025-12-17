# Quick Commands for Droplet (No Merge Editor)

## One-Liner That Avoids Git Merge Editor:

```bash
cd /root/stock-bot && git -c core.editor=true pull origin main --no-rebase && source venv/bin/activate && python3 check_system_health.py
```

## Or Configure Git Once (Permanent Fix):

```bash
cd /root/stock-bot
git config pull.rebase false
git config core.editor true
```

Then you can use the simple command:
```bash
cd /root/stock-bot && git pull origin main && source venv/bin/activate && python3 check_system_health.py
```

## Or Use This (Auto-accepts merge):

```bash
cd /root/stock-bot && GIT_EDITOR=true git pull origin main --no-rebase && source venv/bin/activate && python3 check_system_health.py
```

## Recommended: Set Git Config Once

Run this once to configure git properly:
```bash
cd /root/stock-bot
git config pull.rebase false
git config core.editor true
git config merge.commit no-edit
```

After that, simple commands will work without opening editors.
