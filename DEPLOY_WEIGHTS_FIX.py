#!/usr/bin/env python3
"""
Deploy Adaptive Weights Fix to Droplet
Pulls code, runs fix, and restarts service
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

try:
    from droplet_client import DropletClient
    
    DEPLOY_TARGET = "104.236.102.57"
    SERVICE_NAME = "stockbot.service"
    
    def main():
        print("=" * 80)
        print("DEPLOYING ADAPTIVE WEIGHTS FIX TO DROPLET")
        print("=" * 80)
        print(f"Target: {DEPLOY_TARGET}")
        print(f"Service: {SERVICE_NAME}")
        print()
        
        client = DropletClient()
        
        try:
            # Step 1: Pull latest code
            print("Step 1: Pulling latest code from GitHub...")
            result = client.execute_command(
                "cd /root/stock-bot && git fetch origin main && git reset --hard origin/main",
                timeout=60
            )
            
            if result.get('success'):
                print("✅ Code pulled successfully")
            else:
                print(f"⚠️  Git pull issues: {result.get('stderr', '')[:200]}")
            print()
            
            # Step 2: Verify fix script exists
            print("Step 2: Verifying fix script exists...")
            result = client.execute_command(
                "cd /root/stock-bot && test -f FIX_ADAPTIVE_WEIGHTS_REDUCTION.py && echo 'EXISTS' || echo 'NOT_FOUND'",
                timeout=10
            )
            
            if 'EXISTS' in result.get('stdout', ''):
                print("✅ Fix script found")
            else:
                print("❌ Fix script not found!")
                print("   Make sure FIX_ADAPTIVE_WEIGHTS_REDUCTION.py is in the repo")
                return 1
            print()
            
            # Step 3: Run the fix script
            print("Step 3: Running adaptive weights fix script...")
            result = client.execute_command(
                "cd /root/stock-bot && python3 FIX_ADAPTIVE_WEIGHTS_REDUCTION.py",
                timeout=60
            )
            
            stdout = result.get('stdout', '')
            stderr = result.get('stderr', '')
            exit_code = result.get('exit_code', -1)
            
            print(stdout)
            if stderr:
                print("STDERR:")
                print(stderr)
            
            if exit_code != 0:
                print(f"❌ Fix script failed with exit code: {exit_code}")
                return 1
            
            if "FIX COMPLETE" not in stdout:
                print("⚠️  Fix script may not have completed successfully")
            else:
                print("✅ Fix script completed successfully")
            print()
            
            # Step 4: Restart service
            print(f"Step 4: Restarting {SERVICE_NAME}...")
            result = client.execute_command(
                f"sudo systemctl restart {SERVICE_NAME}",
                timeout=30
            )
            
            if result.get('success'):
                print(f"✅ Service {SERVICE_NAME} restarted")
            else:
                print(f"⚠️  Service restart issues: {result.get('stderr', '')[:200]}")
            print()
            
            # Step 5: Wait a moment and check service status
            print("Step 5: Checking service status...")
            time.sleep(2)
            result = client.execute_command(
                f"sudo systemctl status {SERVICE_NAME} --no-pager | head -15",
                timeout=10
            )
            
            stdout = result.get('stdout', '')
            print(stdout)
            
            if 'active (running)' in stdout.lower():
                print("✅ Service is running")
            else:
                print("⚠️  Service status unclear - check manually")
            print()
            
            # Step 6: Summary
            print("=" * 80)
            print("DEPLOYMENT COMPLETE")
            print("=" * 80)
            print()
            print("Next steps:")
            print("1. Monitor scores - they should increase significantly")
            print("2. Check for trading activity")
            print("3. Monitor stagnation alerts - they should decrease")
            print()
            
            return 0
            
        except Exception as e:
            print(f"\n❌ Error during deployment: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            client.close()
    
    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"❌ Error: Could not import droplet_client: {e}")
    print("\nPlease run manually on droplet:")
    print("  cd /root/stock-bot")
    print("  git pull origin main")
    print("  python3 FIX_ADAPTIVE_WEIGHTS_REDUCTION.py")
    print(f"  sudo systemctl restart stockbot.service")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
