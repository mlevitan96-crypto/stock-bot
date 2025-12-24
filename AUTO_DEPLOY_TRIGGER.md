# Auto-Deploy Trigger

The droplet has a post-merge hook set up. To trigger automatic deployment:

**On the droplet, run:**
```bash
cd ~/stock-bot && rm -f setup_droplet_git.sh && git pull origin main
```

The post-merge hook will automatically:
1. Run `run_investigation_on_pull.sh`
2. Which runs the investigation
3. Commits and pushes results

**OR use the quick fix script:**
```bash
cd ~/stock-bot && git pull origin main && bash RESOLVE_AND_DEPLOY.sh
```

The `FINAL_DEPLOYMENT_SCRIPT.sh` has been updated to handle conflicts automatically, so once you pull it, future deployments will work smoothly.

