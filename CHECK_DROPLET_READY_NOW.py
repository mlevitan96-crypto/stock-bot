#!/usr/bin/env python3
"""
Quick Droplet Verification - Trading Readiness Check
Runs verification script on droplet and displays results
"""

import sys
from pathlib import Path

def main():
    try:
        from droplet_client import DropletClient
        
        print("=" * 80)
        print("DROPLET TRADING READINESS VERIFICATION")
        print("=" * 80)
        print()
        
        client = DropletClient()
        
        # Step 1: Pull latest code (to get verification script)
        print("Step 1: Pulling latest code on droplet...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd /root/stock-bot && git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        
        if exit_code == 0:
            print("✅ Code pulled successfully")
            if "HEAD is now at" in stdout:
                commit_line = [l for l in stdout.split('\n') if 'HEAD is now at' in l]
                if commit_line:
                    print(f"   {commit_line[0].strip()}")
        else:
            print(f"⚠️  Git pull had issues: {stderr[:200] if stderr else 'Unknown'}")
        print()
        
        # Step 2: Make script executable and run verification
        print("Step 2: Running verification script...")
        print("-" * 80)
        
        cmd = "cd /root/stock-bot && chmod +x VERIFY_DROPLET_READY_FOR_TRADING.sh 2>/dev/null; bash VERIFY_DROPLET_READY_FOR_TRADING.sh"
        stdout, stderr, exit_code = client._execute_with_cd(cmd, timeout=300)
        
        # Print output
        if stdout:
            print(stdout)
        if stderr and stderr.strip():
            print("STDERR:", stderr[:500])
        
        print("-" * 80)
        print()
        
        if exit_code == 0:
            print("✅ VERIFICATION COMPLETE - System appears ready")
        else:
            print(f"⚠️  VERIFICATION COMPLETED WITH EXIT CODE {exit_code}")
            print("   Review output above for any errors or warnings")
        
        client.close()
        return exit_code == 0
        
    except ImportError:
        print("❌ ERROR: droplet_client not available")
        print("\nManual verification required:")
        print("  SSH into droplet and run:")
        print("    cd /root/stock-bot")
        print("    git pull origin main")
        print("    bash VERIFY_DROPLET_READY_FOR_TRADING.sh")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
