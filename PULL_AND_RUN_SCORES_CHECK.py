#!/usr/bin/env python3
"""
Pull latest code and run current scores check
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def pull_and_run():
    """Pull latest code and run check."""
    client = DropletClient()
    
    try:
        # Pull latest code
        print("Pulling latest code...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        
        if exit_code == 0:
            print("[OK] Code pulled")
        else:
            print(f"[WARNING] Git pull had issues")
        print()
        
        # Run the check script
        print("Running current scores check...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && (source venv/bin/activate 2>/dev/null && python3 check_open_positions_scores.py || python3 check_open_positions_scores.py)",
            timeout=300
        )
        
        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()
        
        if stdout:
            try:
                print(stdout.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
            except:
                print(stdout.encode('ascii', errors='replace').decode('ascii', errors='replace'))
        if stderr:
            try:
                print("STDERR:", stderr.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
            except:
                print("STDERR:", stderr.encode('ascii', errors='replace').decode('ascii', errors='replace'))
        
        return exit_code == 0
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = pull_and_run()
    sys.exit(0 if success else 1)
