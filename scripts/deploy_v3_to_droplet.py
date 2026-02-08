#!/usr/bin/env python3
"""Deploy Board Upgrade V3 to droplet and run today's analysis."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from droplet_client import DropletClient
from datetime import datetime, timezone

def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Deploying Board Upgrade V3 to droplet and running analysis for {today}")
    
    client = DropletClient()
    try:
        # Step 1: Pull latest code
        print("\n[1/5] Pulling latest code from GitHub...")
        stdout, stderr, rc = client._execute_with_cd("git pull origin main", timeout=60)
        if rc == 0:
            print("[OK] Code pulled successfully")
            if stdout:
                print(f"  {stdout.strip()[:300]}")
        else:
            print(f"⚠ Git pull had issues: {stderr[:200] if stderr else 'Unknown'}")
        
        # Step 2: Run multi-day analysis
        print(f"\n[2/5] Running multi-day analysis for {today}...")
        cmd = f"python3 scripts/run_multi_day_analysis.py --date {today}"
        stdout, stderr, rc = client._execute_with_cd(cmd, timeout=120)
        if rc == 0:
            print("[OK] Multi-day analysis completed")
            if stdout:
                print(f"  {stdout.strip()[:300]}")
        else:
            print(f"⚠ Multi-day analysis had issues: {stderr[:200] if stderr else 'Unknown'}")
            print(f"  stdout: {stdout[:200] if stdout else 'None'}")
        
        # Step 3: Run board packager
        print(f"\n[3/5] Running board daily packager for {today}...")
        cmd = f"python3 scripts/board_daily_packager.py --date {today}"
        stdout, stderr, rc = client._execute_with_cd(cmd, timeout=60)
        if rc == 0:
            print("[OK] Board packager completed")
            if stdout:
                print(f"  {stdout.strip()[:300]}")
        else:
            print(f"⚠ Board packager had issues: {stderr[:200] if stderr else 'Unknown'}")
        
        # Step 4: Check outputs
        print(f"\n[4/5] Checking outputs...")
        check_cmd = f"ls -la board/eod/out/{today}/ 2>/dev/null | head -20 || echo 'Directory not found'"
        stdout, stderr, rc = client._execute_with_cd(check_cmd, timeout=30)
        if stdout:
            print("Files in output directory:")
            print(stdout.strip())
        
        # Step 5: Commit and push results
        print(f"\n[5/5] Committing and pushing results...")
        commit_cmd = (
            f"git add board/eod/out/{today}/* 2>/dev/null || true && "
            f"git commit -m 'V3 Board Review {today}' 2>&1 || echo 'Nothing to commit' && "
            f"git push origin main 2>&1 || echo 'Push skipped'"
        )
        stdout, stderr, rc = client._execute_with_cd(commit_cmd, timeout=60)
        if stdout:
            print(stdout.strip()[:500])
        
        print("\n[OK] Deployment complete!")
        print(f"\nNext: Pull results locally and review board/eod/out/{today}/daily_board_review.md")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1
    finally:
        client.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
