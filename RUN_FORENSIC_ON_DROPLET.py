#!/usr/bin/env python3
"""
Run Forensic Signal Interrogation on Droplet
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def run_forensic():
    """Run forensic interrogation on droplet"""
    print("=" * 80)
    print("RUNNING FORENSIC SIGNAL INTERROGATION ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Pull latest code
        print("Step 1: Pulling latest code...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        if exit_code == 0:
            print("[OK] Code pulled")
        print()
        
        # Step 2: Run forensic script
        print("Step 2: Running forensic interrogation...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && source venv/bin/activate && python FORENSIC_SIGNAL_INTERROGATION.py 2>&1",
            timeout=300
        )
        
        # Handle encoding for Windows terminal
        try:
            # Replace Unicode checkmarks and other special chars
            stdout_safe = stdout.replace('✓', '[OK]').replace('✗', '[FAIL]').replace('⚠', '[WARN]')
            stdout_safe = stdout_safe.encode('ascii', errors='replace').decode('ascii', errors='replace')
        except:
            stdout_safe = stdout.replace('✓', '[OK]').replace('✗', '[FAIL]').replace('⚠', '[WARN]')
        
        print(stdout_safe)
        
        if stderr:
            try:
                stderr_safe = stderr.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                print(f"\n[STDERR]\n{stderr_safe}")
            except:
                print(f"\n[STDERR]\n{stderr}")
        
        # Step 3: Retrieve results file
        print("\nStep 3: Retrieving results...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && cat data/forensic_interrogation_results.json 2>&1 | head -100",
            timeout=30
        )
        
        if stdout and "forensic_interrogation_results" in stdout:
            print("\n[RESULTS FILE]\n")
            try:
                stdout_safe = stdout.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                print(stdout_safe)
            except:
                print(stdout)
        
        print("\n" + "=" * 80)
        print("COMPLETE")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = run_forensic()
    sys.exit(0 if success else 1)
