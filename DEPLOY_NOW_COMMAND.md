# Deploy Now - Run This on Droplet

The deployment script has been fixed to handle the merge conflict. Run this on the droplet:

```bash
cd ~/stock-bot && rm -f setup_droplet_git.sh && git pull origin main && bash FINAL_DEPLOYMENT_SCRIPT.sh
```

Or use the quick fix script:

```bash
cd ~/stock-bot && git pull origin main && bash FIX_AND_DEPLOY.sh
```

The `FINAL_DEPLOYMENT_SCRIPT.sh` now automatically handles untracked file conflicts, so future pulls should work without issues.

