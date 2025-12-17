# Resolve Merge Conflicts on Droplet

## Quick Fix - Accept Incoming Changes (Recommended)

Since you want the latest SRE monitoring code, accept the incoming changes:

```bash
cd /root/stock-bot
git checkout --theirs dashboard.py main.py
git add dashboard.py main.py
git commit -m "Resolve merge conflicts - accept incoming SRE monitoring changes"
git pull origin main --no-rebase
```

## Or Use Git Merge Tool

```bash
cd /root/stock-bot
git mergetool
# Accept all incoming changes
git add dashboard.py main.py
git commit -m "Resolve merge conflicts"
```

## Or Reset and Pull Fresh

If you don't need local changes:

```bash
cd /root/stock-bot
git reset --hard origin/main
git pull origin main
```

## After Resolving

Test the SRE monitoring:

```bash
source venv/bin/activate
python3 -c "from sre_monitoring import get_sre_health; import json; print(json.dumps(get_sre_health(), indent=2, default=str))"
```
