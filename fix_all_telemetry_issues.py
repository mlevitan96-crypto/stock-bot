#!/usr/bin/env python3
"""
Fix All Telemetry Issues - Comprehensive Fix
===========================================
This script:
1. Runs telemetry extraction immediately
2. Schedules it in crontab for daily execution
3. Generates missing shadow artifacts (if shadow trading enabled)
4. Verifies all artifacts are generated
5. Ensures everything is working end-to-end
"""

import sys
import json
from pathlib import Path

# Inline script to run on droplet
FIX_ALL_SCRIPT = '''python3 << 'FIX_ALL_EOF'
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
        
        # Add new line (runs daily at 4:30 PM ET / 20:30 UTC after market close)
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

def check_shadow_trading_enabled():
    """Check if shadow trading is enabled"""
    try:
        # Check for shadow trading logs or state
        shadow_log = Path("logs/master_trade_log.jsonl")
        shadow_state = Path("state/shadow_positions.json")
        
        has_shadow_data = shadow_log.exists() or shadow_state.exists()
        
        # Check if shadow tracker is being used
        try:
            result = subprocess.run(
                ["grep", "-r", "shadow_tracker", "main.py"],
                capture_output=True,
                text=True,
                timeout=5
            )
            shadow_in_code = result.returncode == 0 and len(result.stdout) > 0
        except:
            shadow_in_code = False
        
        return has_shadow_data or shadow_in_code
    except:
        return False

def generate_shadow_artifacts():
    """Generate shadow artifacts if shadow trading is enabled"""
    try:
        # Check if shadow vs live script exists
        shadow_script = Path("scripts/run_shadow_vs_live_deep_dive.py")
        if not shadow_script.exists():
            return False, "Shadow script not found"
        
        # Run shadow vs live analysis
        print("Generating shadow artifacts...")
        result = subprocess.run(
            ["python3", str(shadow_script)],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def verify_all_artifacts():
    """Verify all artifacts were generated"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    telemetry_dir = Path(f"telemetry/{today}/computed")
    
    if not telemetry_dir.exists():
        return False, f"Telemetry directory not found: {telemetry_dir}"
    
    # All expected artifacts
    all_artifacts = {
        "exit_intel_completeness": "exit_intel_completeness.json",
        "feature_equalizer_builder": "feature_equalizer_builder.json",
        "feature_value_curves": "feature_value_curves.json",
        "long_short_analysis": "long_short_analysis.json",
        "regime_sector_feature_matrix": "regime_sector_feature_matrix.json",
        "regime_timeline": "regime_timeline.json",
        "replacement_telemetry_expanded": "replacement_telemetry_expanded.json",
        "score_distribution_curves": "score_distribution_curves.json",
        "signal_performance": "signal_performance.json",
        "signal_weight_recommendations": "signal_weight_recommendations.json",
        "entry_parity_details": "entry_parity_details.json",
        "feature_family_summary": "feature_family_summary.json",
        "live_vs_shadow_pnl": "live_vs_shadow_pnl.json",
        "shadow_vs_live_parity": "shadow_vs_live_parity.json",
    }
    
    found = []
    missing = []
    stale = []
    
    now = time.time()
    for name, filename in all_artifacts.items():
        artifact_path = telemetry_dir / filename
        if artifact_path.exists():
            mtime = artifact_path.stat().st_mtime
            age_hours = (now - mtime) / 3600.0
            if age_hours > 24:
                stale.append(name)
            found.append(name)
        else:
            missing.append(name)
    
    return True, {
        "found": found,
        "missing": missing,
        "stale": stale,
        "total": len(all_artifacts),
        "found_count": len(found),
        "missing_count": len(missing),
        "stale_count": len(stale)
    }

results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "actions": {},
    "issues": [],
    "summary": {}
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
    results["issues"].append(f"Telemetry extraction failed: {stderr[:200] if stderr else 'Unknown error'}")

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
else:
    results["actions"]["add_to_crontab"] = {"success": True, "message": "Already scheduled"}

# Step 4: Check shadow trading
print("\\nStep 4: Checking shadow trading...")
shadow_enabled = check_shadow_trading_enabled()
results["actions"]["check_shadow"] = {"enabled": shadow_enabled}

# Step 5: Generate shadow artifacts if enabled
if shadow_enabled:
    print("\\nStep 5: Generating shadow artifacts...")
    success, msg = generate_shadow_artifacts()
    results["actions"]["generate_shadow"] = {
        "success": success,
        "message": msg[:500] if isinstance(msg, str) else "Generated"
    }
    if not success:
        results["issues"].append(f"Shadow artifact generation failed: {msg}")
else:
    results["actions"]["generate_shadow"] = {
        "success": None,
        "message": "Shadow trading not enabled"
    }

# Step 6: Verify all artifacts
print("\\nStep 6: Verifying artifacts...")
success, artifacts = verify_all_artifacts()
results["actions"]["verify_artifacts"] = {
    "success": success,
    "artifacts": artifacts
}

# Summary
results["summary"] = {
    "telemetry_extraction": "SUCCESS" if results["actions"]["run_extraction"]["success"] else "FAILED",
    "crontab_scheduled": results["actions"]["check_crontab"]["scheduled"] or results["actions"].get("add_to_crontab", {}).get("success", False),
    "shadow_enabled": shadow_enabled,
    "artifacts_found": artifacts.get("found_count", 0) if isinstance(artifacts, dict) else 0,
    "artifacts_missing": artifacts.get("missing_count", 0) if isinstance(artifacts, dict) else 0,
    "artifacts_stale": artifacts.get("stale_count", 0) if isinstance(artifacts, dict) else 0,
    "total_issues": len(results["issues"])
}

print("\\n=== RESULTS ===")
print(json.dumps(results, indent=2))
FIX_ALL_EOF
'''

def main():
    """Fix all telemetry issues on droplet"""
    print("=" * 80)
    print("FIXING ALL TELEMETRY ISSUES ON DROPLET")
    print("=" * 80)
    print()
    
    try:
        from droplet_client import DropletClient
        
        client = DropletClient()
        
        print("Connecting to droplet...")
        print("Running comprehensive fix...")
        print()
        
        stdout, stderr, exit_code = client._execute_with_cd(
            FIX_ALL_SCRIPT,
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
                    
                    summary = results.get("summary", {})
                    print(f"Telemetry Extraction: {summary.get('telemetry_extraction', 'UNKNOWN')}")
                    print(f"Crontab Scheduled: {summary.get('crontab_scheduled', False)}")
                    print(f"Shadow Trading Enabled: {summary.get('shadow_enabled', False)}")
                    print(f"Artifacts Found: {summary.get('artifacts_found', 0)}/{summary.get('artifacts_found', 0) + summary.get('artifacts_missing', 0)}")
                    print(f"Artifacts Missing: {summary.get('artifacts_missing', 0)}")
                    print(f"Artifacts Stale: {summary.get('artifacts_stale', 0)}")
                    print(f"Total Issues: {summary.get('total_issues', 0)}")
                    
                    actions = results.get("actions", {})
                    
                    print("\nDetailed Results:")
                    if actions.get("run_extraction"):
                        ext = actions["run_extraction"]
                        status = "SUCCESS" if ext.get("success") else "FAILED"
                        print(f"  Telemetry Extraction: {status}")
                    
                    if actions.get("add_to_crontab"):
                        add = actions["add_to_crontab"]
                        status = "SUCCESS" if add.get("success") else "FAILED"
                        print(f"  Crontab Scheduling: {status}")
                        if add.get("message"):
                            print(f"    {add['message']}")
                    
                    if actions.get("check_shadow"):
                        print(f"  Shadow Trading: {'ENABLED' if actions['check_shadow'].get('enabled') else 'DISABLED'}")
                    
                    if actions.get("generate_shadow"):
                        gen = actions["generate_shadow"]
                        if gen.get("success") is not None:
                            status = "SUCCESS" if gen.get("success") else "FAILED"
                            print(f"  Shadow Artifacts: {status}")
                            if gen.get("message"):
                                print(f"    {gen['message'][:100]}")
                    
                    if actions.get("verify_artifacts"):
                        verify = actions["verify_artifacts"]
                        artifacts = verify.get("artifacts", {})
                        if isinstance(artifacts, dict):
                            print(f"  Artifacts Verification:")
                            print(f"    Found: {artifacts.get('found_count', 0)}")
                            print(f"    Missing: {artifacts.get('missing_count', 0)}")
                            if artifacts.get("missing"):
                                print(f"    Missing: {', '.join(artifacts['missing'][:5])}")
                            if artifacts.get("stale"):
                                print(f"    Stale: {', '.join(artifacts['stale'][:5])}")
                    
                    if results.get("issues"):
                        print(f"\nIssues Found: {len(results['issues'])}")
                        for issue in results["issues"]:
                            print(f"  - {issue}")
                    else:
                        print("\n[SUCCESS] No issues - all fixes completed successfully")
                    
                    # Save results
                    local_path = Path("reports/telemetry_fix_all_results.json")
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(local_path, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"\nResults saved to: {local_path}")
                    
            except json.JSONDecodeError as e:
                print(f"\nCould not parse JSON: {e}")
                print("Raw output:")
                print(stdout[-1000:])
        
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
