#!/usr/bin/env python3
"""
Automatically test UW endpoints on droplet via SSH
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def main():
    config_path = Path("droplet_config.json")
    if not config_path.exists():
        print("ERROR: droplet_config.json not found")
        print("Cannot connect to droplet automatically")
        sys.exit(1)
    
    print("=" * 60)
    print("TESTING UW ENDPOINTS ON DROPLET")
    print("=" * 60)
    print()
    
    try:
        client = DropletClient()
        
        print("Step 1: Connecting to droplet...")
        status = client.get_status()
        print(f"OK: Connected to {status['host']}")
        print()
        
        print("Step 2: Pulling latest code...")
        stdout, stderr, exit_code = client._execute_with_cd("git pull origin main", timeout=60)
        if exit_code == 0:
            print("OK: Code pulled")
        else:
            print(f"WARNING: Pull had issues: {stderr[:200]}")
        print()
        
        print("Step 3: Running UW endpoint test...")
        stdout, stderr, exit_code = client._execute_with_cd("bash TRIGGER_UW_TEST.sh", timeout=120)
        if exit_code == 0:
            print("OK: Test completed")
            # Show summary
            if stdout:
                lines = stdout.strip().split('\n')
                for line in lines[-20:]:
                    if line.strip():
                        print(f"  {line}")
        else:
            print(f"WARNING: Test had issues (exit code: {exit_code})")
            if stderr:
                print(f"  Error: {stderr[:300]}")
        print()
        
        print("Step 4: Pulling test results...")
        # Pull results from Git
        stdout, stderr, exit_code = client._execute_with_cd("git pull origin main", timeout=60)
        if exit_code == 0:
            print("OK: Results pulled")
        print()
        
        print("Step 5: Checking for results file...")
        stdout, stderr, exit_code = client._execute_with_cd("test -f uw_endpoint_test_results.json && cat uw_endpoint_test_results.json | head -50 || echo 'NOT_FOUND'")
        if "NOT_FOUND" not in stdout:
            print("OK: Results file exists")
            print()
            print("Results preview:")
            print(stdout[:500])
        else:
            print("WARNING: Results file not found")
        print()
        
        client.close()
        
        # Now pull locally to get results
        import subprocess
        result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("OK: Results pulled to local repository")
            print("Check uw_endpoint_test_results.json for full results")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

