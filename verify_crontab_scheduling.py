#!/usr/bin/env python3
"""
Verify Crontab Scheduling
=========================
Verifies that telemetry extraction is properly scheduled in crontab.
"""

import sys
import json
from pathlib import Path

# Inline script to run on droplet
VERIFY_SCRIPT = '''python3 << 'VERIFY_EOF'
import subprocess
import json
from datetime import datetime, timezone

def verify_crontab():
    """Verify crontab scheduling"""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "crontab_entries": [],
        "telemetry_scheduled": False,
        "telemetry_entry": None
    }
    
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    results["crontab_entries"].append(line)
                    if "run_full_telemetry_extract" in line:
                        results["telemetry_scheduled"] = True
                        results["telemetry_entry"] = line
        else:
            results["error"] = "No crontab found or error reading crontab"
    except Exception as e:
        results["error"] = str(e)
    
    return results

results = verify_crontab()
print(json.dumps(results, indent=2))
VERIFY_EOF
'''

def main():
    """Verify crontab scheduling on droplet"""
    print("=" * 80)
    print("VERIFYING CRONTAB SCHEDULING")
    print("=" * 80)
    print()
    
    try:
        from droplet_client import DropletClient
        
        client = DropletClient()
        
        print("Connecting to droplet...")
        print("Checking crontab...")
        print()
        
        stdout, stderr, exit_code = client._execute_with_cd(
            VERIFY_SCRIPT,
            timeout=30
        )
        
        print("=" * 80)
        print("CRONTAB VERIFICATION")
        print("=" * 80)
        print(stdout)
        if stderr:
            print("\nSTDERR:")
            print(stderr)
        
        # Parse results
        if stdout:
            try:
                lines = stdout.split('\n')
                json_start = None
                for i, line in enumerate(lines):
                    if line.strip().startswith('{'):
                        json_start = i
                        break
                
                if json_start is not None:
                    json_text = '\n'.join(lines[json_start:])
                    results = json.loads(json_text)
                    
                    print("\n" + "=" * 80)
                    print("SUMMARY")
                    print("=" * 80)
                    
                    if results.get("telemetry_scheduled"):
                        print("[SUCCESS] Telemetry extraction is scheduled")
                        if results.get("telemetry_entry"):
                            print(f"Entry: {results['telemetry_entry']}")
                    else:
                        print("[WARNING] Telemetry extraction NOT found in crontab")
                        if results.get("error"):
                            print(f"Error: {results['error']}")
                    
                    if results.get("crontab_entries"):
                        print(f"\nTotal crontab entries: {len(results['crontab_entries'])}")
                        for entry in results["crontab_entries"][:5]:
                            print(f"  - {entry}")
                    
            except json.JSONDecodeError as e:
                print(f"\nCould not parse JSON: {e}")
        
        client.close()
        return exit_code
        
    except ImportError:
        print("ERROR: droplet_client not available")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
