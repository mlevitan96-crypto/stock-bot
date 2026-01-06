#!/usr/bin/env python3
"""
Run verification on droplet and save results to file
"""

from droplet_client import DropletClient
import json
import sys

def main():
    client = DropletClient()
    results = {
        "git_status": "unknown",
        "service_running": False,
        "processes": {},
        "fixes": {},
        "sre_files": {},
        "dashboard": False,
        "api_keys": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        # 1. Git status
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && git log --oneline -1 2>&1', 30)
        if stdout:
            results["git_status"] = stdout.strip()[:70]
        
        # 2. Service status
        stdout, stderr, code = client._execute_with_cd('systemctl is-active trading-bot.service 2>&1', 30)
        if stdout and 'active' in stdout:
            results["service_running"] = True
        
        # 3. Processes
        for proc in ['main.py', 'uw_flow_daemon.py', 'dashboard.py']:
            stdout, stderr, code = client._execute_with_cd(f'pgrep -f "{proc}" 2>&1 | head -1', 20)
            results["processes"][proc] = bool(stdout and stdout.strip())
        
        # 4. Fixes
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && grep -q "signal_type.*BULLISH_SWEEP" main.py 2>&1 && echo YES || echo NO', 20)
        results["fixes"]["uw_parser"] = stdout and 'YES' in stdout
        
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && grep -q "gate_type=" main.py 2>&1 && echo YES || echo NO', 20)
        results["fixes"]["gate_logging"] = stdout and 'YES' in stdout
        
        # 5. SRE files
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && test -f sre_diagnostics.py && echo YES || echo NO', 20)
        results["sre_files"]["sre_diagnostics"] = stdout and 'YES' in stdout
        
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && test -f mock_signal_injection.py && echo YES || echo NO', 20)
        results["sre_files"]["mock_signal"] = stdout and 'YES' in stdout
        
        # 6. Dashboard
        stdout, stderr, code = client._execute_with_cd('curl -s http://localhost:5000/health 2>&1 | head -1', 10)
        results["dashboard"] = bool(stdout and stdout.strip())
        
        # 7. API Keys (simplified check)
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && test -f .env && echo YES || echo NO', 20)
        results["api_keys"]["env_file_exists"] = stdout and 'YES' in stdout
        
        # Save results to file on droplet
        results_json = json.dumps(results, indent=2)
        cmd = f'cd /root/stock-bot && echo \'{results_json}\' > verification_results_temp.json'
        client._execute_with_cd(cmd, 20)
        
        # Read it back
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && cat verification_results_temp.json 2>&1', 20)
        
        # Print summary
        print("=" * 80)
        print("DROPLET VERIFICATION RESULTS")
        print("=" * 80)
        print(f"\nGit Status: {results['git_status']}")
        print(f"Service Running: {results['service_running']}")
        print(f"\nProcesses:")
        for proc, running in results['processes'].items():
            status = "RUNNING" if running else "NOT RUNNING"
            print(f"  {proc}: {status}")
        print(f"\nFixes:")
        print(f"  UW Parser: {'PRESENT' if results['fixes']['uw_parser'] else 'MISSING'}")
        print(f"  Gate Logging: {'PRESENT' if results['fixes']['gate_logging'] else 'MISSING'}")
        print(f"\nSRE Sentinel:")
        print(f"  sre_diagnostics.py: {'EXISTS' if results['sre_files']['sre_diagnostics'] else 'MISSING'}")
        print(f"  mock_signal_injection.py: {'EXISTS' if results['sre_files']['mock_signal'] else 'MISSING'}")
        print(f"\nDashboard: {'RESPONDING' if results['dashboard'] else 'NOT RESPONDING'}")
        print(f"API Keys (.env file): {'EXISTS' if results['api_keys']['env_file_exists'] else 'MISSING'}")
        
        # Count issues
        errors = []
        warnings = []
        
        if not results['service_running']:
            errors.append("Service not running")
        for proc, running in results['processes'].items():
            if not running:
                errors.append(f"{proc} not running")
        if not results['dashboard']:
            errors.append("Dashboard not responding")
        if not results['api_keys']['env_file_exists']:
            errors.append(".env file missing")
        
        if not results['fixes']['uw_parser']:
            warnings.append("UW parser fix not found")
        if not results['fixes']['gate_logging']:
            warnings.append("Gate logging fix not found")
        if not results['sre_files']['sre_diagnostics']:
            warnings.append("sre_diagnostics.py missing")
        if not results['sre_files']['mock_signal']:
            warnings.append("mock_signal_injection.py missing")
        
        print("\n" + "=" * 80)
        print(f"SUMMARY: {len(errors)} errors, {len(warnings)} warnings")
        print("=" * 80)
        
        if errors:
            print("\nERRORS:")
            for err in errors:
                print(f"  - {err}")
        
        if warnings:
            print("\nWARNINGS:")
            for warn in warnings:
                print(f"  - {warn}")
        
        if not errors:
            print("\nREADY FOR TRADING" if not warnings else "\nREADY WITH WARNINGS")
            return 0
        else:
            print("\nERRORS DETECTED - Fix before trading")
            return 1
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        client.close()

if __name__ == "__main__":
    sys.exit(main())
