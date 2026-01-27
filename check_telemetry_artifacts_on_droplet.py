#!/usr/bin/env python3
"""
Check Telemetry Artifacts Status on Droplet
===========================================
Checks what telemetry artifacts exist, their age, and what generates them.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import json

# Inline script to run on droplet
CHECK_SCRIPT = '''python3 << 'TELEMETRY_EOF'
import json
import time
from pathlib import Path
from datetime import datetime, timezone

def check_telemetry_artifacts():
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "telemetry_dirs": {},
        "computed_artifacts": {},
        "generation_scripts": {},
        "issues": []
    }
    
    # Check telemetry directories
    telemetry_base = Path("telemetry")
    if not telemetry_base.exists():
        results["issues"].append("telemetry/ directory missing")
        return results
    
    # Find latest telemetry directory
    telemetry_dirs = sorted([d for d in telemetry_base.iterdir() if d.is_dir() and d.name.startswith("2026")], reverse=True)
    
    if not telemetry_dirs:
        results["issues"].append("No telemetry directories found")
        return results
    
    latest_dir = telemetry_dirs[0]
    results["latest_telemetry_dir"] = str(latest_dir)
    
    # Check computed artifacts in latest directory
    computed_dir = latest_dir / "computed"
    if computed_dir.exists():
        artifacts = {
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
        
        now = time.time()
        for name, filename in artifacts.items():
            artifact_path = computed_dir / filename
            if artifact_path.exists():
                mtime = artifact_path.stat().st_mtime
                age_hours = (now - mtime) / 3600.0
                size = artifact_path.stat().st_size
                results["computed_artifacts"][name] = {
                    "exists": True,
                    "age_hours": round(age_hours, 1),
                    "size": size,
                    "stale": age_hours > 24
                }
                if age_hours > 24:
                    results["issues"].append(f"Artifact stale: {name} ({age_hours:.1f} hours old)")
            else:
                results["computed_artifacts"][name] = {"exists": False}
                results["issues"].append(f"Artifact missing: {name}")
    
    # Check if telemetry extraction script exists
    telemetry_script = Path("scripts/run_full_telemetry_extract.py")
    results["generation_scripts"]["run_full_telemetry_extract"] = {
        "exists": telemetry_script.exists()
    }
    
    # Check when telemetry script last ran (check for recent output)
    if telemetry_script.exists():
        # Check if there are recent telemetry directories
        if telemetry_dirs:
            latest_mtime = latest_dir.stat().st_mtime
            age_hours = (time.time() - latest_mtime) / 3600.0
            results["latest_telemetry_age_hours"] = round(age_hours, 1)
            if age_hours > 24:
                results["issues"].append(f"Telemetry extraction hasn't run in {age_hours:.1f} hours")
    
    # Check for cron jobs or scheduled tasks
    import subprocess
    try:
        stdout, _, _ = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if "telemetry" in stdout.lower() or "run_full_telemetry" in stdout.lower():
            results["generation_scripts"]["scheduled"] = True
        else:
            results["generation_scripts"]["scheduled"] = False
            results["issues"].append("No telemetry extraction scheduled in crontab")
    except:
        results["generation_scripts"]["scheduled"] = None
    
    return results

results = check_telemetry_artifacts()
print(json.dumps(results, indent=2))
TELEMETRY_EOF
'''

def main():
    """Check telemetry artifacts on droplet"""
    print("=" * 80)
    print("CHECKING TELEMETRY ARTIFACTS ON DROPLET")
    print("=" * 80)
    print()
    
    try:
        from droplet_client import DropletClient
        
        client = DropletClient()
        
        print("Connecting to droplet...")
        print("Checking telemetry artifacts...")
        print()
        
        stdout, stderr, exit_code = client._execute_with_cd(
            CHECK_SCRIPT,
            timeout=60
        )
        
        print("=" * 80)
        print("TELEMETRY ARTIFACTS STATUS")
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
                    print(f"Latest Telemetry Dir: {results.get('latest_telemetry_dir', 'N/A')}")
                    print(f"Latest Age: {results.get('latest_telemetry_age_hours', 'N/A')} hours")
                    
                    print("\nComputed Artifacts:")
                    for name, status in results.get("computed_artifacts", {}).items():
                        if status.get("exists"):
                            age = status.get("age_hours", 0)
                            stale = "STALE" if age > 24 else "RECENT"
                            print(f"  {name}: {stale} ({age:.1f}h old, {status.get('size', 0)} bytes)")
                        else:
                            print(f"  {name}: MISSING")
                    
                    print("\nGeneration Scripts:")
                    for name, status in results.get("generation_scripts", {}).items():
                        if isinstance(status, dict):
                            exists = status.get("exists", False)
                            print(f"  {name}: {'EXISTS' if exists else 'MISSING'}")
                        else:
                            print(f"  {name}: {status}")
                    
                    if results.get("issues"):
                        print(f"\nIssues Found: {len(results['issues'])}")
                        for issue in results["issues"]:
                            print(f"  - {issue}")
                    else:
                        print("\nNo issues found")
                    
                    # Save results
                    local_path = Path("reports/telemetry_artifacts_status.json")
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
