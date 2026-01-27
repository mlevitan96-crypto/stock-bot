#!/usr/bin/env python3
"""
Fix Telemetry Extraction - Schedule and Run
===========================================
This script:
1. Runs telemetry extraction immediately
2. Schedules it in crontab for daily execution
3. Verifies artifacts are generated
"""

import sys
import json
from pathlib import Path

# Inline script to run on droplet
FIX_SCRIPT = '''python3 << 'FIX_EOF'
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime, timezone

def run_telemetry_extraction():
    """Run telemetry extraction script"""
    print("Running telemetry extraction...")
    result = subprocess.run(
        ["python3", "scripts/run_full_telemetry_extract.py"],
        capture_output=True,
        text=True,
        timeout=300
    )
    return result.returncode == 0, result.stdout, result.stderr

def check_crontab():
    """Check if telemetry extraction is in crontab"""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "run_full_telemetry_extract" in result.stdout
        return False
    except:
        return None

def add_to_crontab():
    """Add telemetry extraction to crontab"""
    try:
        # Get current crontab
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Check if already exists
        if "run_full_telemetry_extract" in current_cron:
            return True, "Already in crontab"
        
        # Add new line
        new_line = "30 20 * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py >> logs/telemetry_extract.log 2>&1\\n"
        new_cron = current_cron + new_line
        
        # Write to temp file and install
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as f:
            f.write(new_cron)
            temp_path = f.name
        
        result = subprocess.run(
            ["crontab", temp_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        import os
        os.unlink(temp_path)
        
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def verify_artifacts():
    """Verify artifacts were generated"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    telemetry_dir = Path(f"telemetry/{today}/computed")
    
    if not telemetry_dir.exists():
        return False, f"Telemetry directory not found: {telemetry_dir}"
    
    artifacts = [
        "exit_intel_completeness.json",
        "signal_performance.json",
        "signal_weight_recommendations.json",
        "regime_timeline.json",
        "score_distribution_curves.json"
    ]
    
    found = []
    missing = []
    for artifact in artifacts:
        if (telemetry_dir / artifact).exists():
            found.append(artifact)
        else:
            missing.append(artifact)
    
    return len(found) > 0, {"found": found, "missing": missing}

results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "actions": {},
    "issues": []
}

# Step 1: Run telemetry extraction
print("Step 1: Running telemetry extraction...")
success, stdout, stderr = run_telemetry_extraction()
results["actions"]["run_extraction"] = {
    "success": success,
    "stdout": stdout[:500] if stdout else "",
    "stderr": stderr[:500] if stderr else ""
}
if not success:
    results["issues"].append(f"Telemetry extraction failed: {stderr[:200]}")

# Step 2: Check crontab
print("\\nStep 2: Checking crontab...")
in_crontab = check_crontab()
results["actions"]["check_crontab"] = {"scheduled": in_crontab}

# Step 3: Add to crontab if not present
if not in_crontab:
    print("\\nStep 3: Adding to crontab...")
    success, msg = add_to_crontab()
    results["actions"]["add_to_crontab"] = {"success": success, "message": msg}
    if not success:
        results["issues"].append(f"Failed to add to crontab: {msg}")

# Step 4: Verify artifacts
print("\\nStep 4: Verifying artifacts...")
success, artifacts = verify_artifacts()
results["actions"]["verify_artifacts"] = {
    "success": success,
    "artifacts": artifacts
}
if not success or artifacts.get("missing"):
    results["issues"].append(f"Some artifacts missing: {artifacts.get('missing', [])}")

print("\\n=== RESULTS ===")
print(json.dumps(results, indent=2))
FIX_EOF
'''

def main():
    """Fix telemetry extraction on droplet"""
    print("=" * 80)
    print("FIXING TELEMETRY EXTRACTION ON DROPLET")
    print("=" * 80)
    print()
    
    try:
        from droplet_client import DropletClient
        
        client = DropletClient()
        
        print("Connecting to droplet...")
        print("Running fix script...")
        print()
        
        stdout, stderr, exit_code = client._execute_with_cd(
            FIX_SCRIPT,
            timeout=360
        )
        
        print("=" * 80)
        print("FIX OUTPUT")
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
                    print("FIX SUMMARY")
                    print("=" * 80)
                    
                    actions = results.get("actions", {})
                    
                    if actions.get("run_extraction"):
                        ext = actions["run_extraction"]
                        status = "SUCCESS" if ext.get("success") else "FAILED"
                        print(f"Telemetry Extraction: {status}")
                    
                    if actions.get("check_crontab"):
                        scheduled = actions["check_crontab"].get("scheduled")
                        print(f"Crontab Scheduled: {scheduled}")
                    
                    if actions.get("add_to_crontab"):
                        add = actions["add_to_crontab"]
                        status = "SUCCESS" if add.get("success") else "FAILED"
                        print(f"Added to Crontab: {status}")
                        if add.get("message"):
                            print(f"  Message: {add['message']}")
                    
                    if actions.get("verify_artifacts"):
                        verify = actions["verify_artifacts"]
                        status = "SUCCESS" if verify.get("success") else "FAILED"
                        print(f"Artifacts Verified: {status}")
                        artifacts = verify.get("artifacts", {})
                        if artifacts.get("found"):
                            print(f"  Found: {len(artifacts['found'])} artifacts")
                        if artifacts.get("missing"):
                            print(f"  Missing: {artifacts['missing']}")
                    
                    if results.get("issues"):
                        print(f"\nIssues: {len(results['issues'])}")
                        for issue in results["issues"]:
                            print(f"  - {issue}")
                    else:
                        print("\nNo issues - fix completed successfully")
                    
                    # Save results
                    local_path = Path("reports/telemetry_fix_results.json")
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(local_path, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"\nResults saved to: {local_path}")
                    
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
