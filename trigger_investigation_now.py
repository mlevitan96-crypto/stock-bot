#!/usr/bin/env python3
"""
Trigger investigation immediately via SSH to droplet.
This bypasses waiting for cron jobs.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from droplet_client import DropletClient
except ImportError as e:
    print(f"Error: Could not import droplet_client: {e}")
    print("Make sure droplet_client.py exists and droplet_config.json is configured.")
    sys.exit(1)

def main():
    print("Connecting to droplet...")
    client = DropletClient()
    
    # Test connection by getting status
    try:
        status = client.get_status()
        print("✓ Connected to droplet")
        print(f"   Host: {status.get('host')}")
        print("")
    except Exception as e:
        print(f"❌ Failed to connect to droplet: {e}")
        print("   Make sure droplet_config.json exists with connection details")
        return 1
    
    # Step 1: Pull latest code
    print("Step 1: Pulling latest code...")
    result = client.execute_command("cd ~/stock-bot && git pull origin main --no-rebase")
    if result.get("exit_code", 1) == 0:
        print("✓ Code pulled successfully")
    else:
        print(f"⚠ Git pull had issues: {result.get('stderr', '')[:200]}")
    print("")
    
    # Step 2: Run investigation
    print("Step 2: Running investigation...")
    result = client.execute_command("cd ~/stock-bot && python3 investigate_no_trades.py", timeout=120)
    if result.get("exit_code", 1) == 0:
        print("✓ Investigation completed")
        print("")
        output = result.get("stdout", "") + result.get("stderr", "")
        if output:
            print("Investigation output:")
            print(output[-1000:] if len(output) > 1000 else output)
    else:
        print(f"❌ Investigation failed (exit code: {result.get('exit_code', 'unknown')})")
        print(f"Error: {result.get('stderr', '')[:500]}")
        print("")
        # Still try to get results if file was created
    print("")
    
    # Step 3: Commit and push results
    print("Step 3: Committing and pushing results...")
    result = client.execute_command(
        "cd ~/stock-bot && "
        "git add investigate_no_trades.json .last_investigation_run 2>/dev/null && "
        "git commit -m 'Investigation results - $(date +%Y-%m-%d\\ %H:%M:%S)' 2>/dev/null && "
        "git push origin main 2>/dev/null",
        timeout=60
    )
    if result.get("exit_code", 1) == 0:
        print("✓ Results pushed to Git")
    else:
        print(f"⚠ Git push had issues: {result.get('stderr', '')[:200]}")
    print("")
    
    # Step 4: Pull results locally
    print("Step 4: Pulling results locally...")
    import subprocess
    try:
        subprocess.run(["git", "pull", "origin", "main", "--no-rebase"], 
                      check=True, capture_output=True, timeout=30)
        print("✓ Results pulled locally")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"⚠ Git pull had issues: {e}")
    print("")
    
    # Step 5: Read and display results
    print("Step 5: Reading investigation results...")
    results_file = Path("investigate_no_trades.json")
    if results_file.exists():
        import json
        with open(results_file) as f:
            results = json.load(f)
        
        print("=" * 80)
        print("INVESTIGATION RESULTS SUMMARY")
        print("=" * 80)
        print("")
        
        if "error" in results:
            print(f"❌ Investigation Error: {results.get('error')}")
            if "traceback" in results:
                print("\nTraceback:")
                print(results["traceback"][:500])
        else:
            checks = results.get("checks", {})
            summary = results.get("summary", {})
            
            # Market hours
            market = checks.get("market_hours", {})
            if market.get("is_market_hours"):
                print("✅ Market is open")
            else:
                print(f"⏰ Market is {'closed' if market.get('is_weekend') else 'outside trading hours'}")
            print("")
            
            # Services
            services = checks.get("services", {})
            if services.get("all_running"):
                print("✅ All services are running")
            else:
                print("❌ Some services are not running:")
                for svc, running in services.get("services", {}).items():
                    status = "✅" if running else "❌"
                    print(f"   {status} {svc}")
            print("")
            
            # Execution cycles
            cycles = checks.get("execution_cycles", {})
            if "error" not in cycles:
                mins_ago = cycles.get("minutes_since_last_cycle", 999)
                if mins_ago > 10:
                    print(f"❌ Last execution cycle: {mins_ago} minutes ago")
                else:
                    print(f"✅ Execution cycles running (last: {mins_ago} min ago)")
            print("")
            
            # Issues
            issues = summary.get("issues", [])
            if issues:
                print("🔍 Issues Found:")
                for issue in issues[:10]:
                    print(f"   - {issue}")
            else:
                print("✅ No major issues detected")
            print("")
            
            # Recommendations
            recommendations = summary.get("recommendations", [])
            if recommendations:
                print("💡 Recommendations:")
                for rec in recommendations[:10]:
                    print(f"   - {rec}")
        
        print("")
        print("=" * 80)
    else:
        print("⚠ Investigation results file not found locally")
        print("   Results may still be on droplet - check git status")
    
    client.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())

