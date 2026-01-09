#!/usr/bin/env python3
"""
Run Current Scores Check on Droplet
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def run_current_scores_check():
    """Run the current scores check script on the droplet."""
    print("=" * 80)
    print("CHECKING CURRENT SCORES FOR OPEN POSITIONS")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Run the check script
        print("Running current scores check...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && (source venv/bin/activate 2>/dev/null && python3 check_open_positions_scores.py || python3 check_open_positions_scores.py)",
            timeout=300  # 5 minutes
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
        
        print()
        print("=" * 80)
        
        return exit_code == 0
        
    except Exception as e:
        print(f"[ERROR] Failed to run check: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = run_current_scores_check()
    sys.exit(0 if success else 1)
