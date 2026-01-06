#!/usr/bin/env python3
"""
Run comprehensive droplet verification and report results
"""

from droplet_client import DropletClient
import sys

def main():
    print("=" * 80)
    print("DROPLET VERIFICATION - TRADING READINESS CHECK")
    print("=" * 80)
    print()
    
    client = DropletClient()
    errors = []
    warnings = []
    
    try:
        # 1. Git Status
        print("1. Checking Git Status...")
        r = client.execute_command('cd /root/stock-bot && git fetch origin main && git log --oneline -1')
        commit = r.get('output', '').strip()
        if commit:
            print(f"   Latest commit: {commit[:70]}")
        else:
            warnings.append("Could not get git commit")
        
        # 2. Service Status
        print("\n2. Checking Service Status...")
        r = client.execute_command('systemctl is-active trading-bot.service')
        status = r.get('output', '').strip()
        if status == 'active':
            print("   OK: trading-bot.service is active")
        else:
            errors.append(f"Service status: {status}")
            print(f"   ERROR: Service status is '{status}'")
        
        # 3. Processes
        print("\n3. Checking Critical Processes...")
        processes = [
            ('main.py', 'main.py'),
            ('uw_flow_daemon.py', 'uw_flow_daemon.py'),
            ('dashboard.py', 'dashboard.py'),
            ('deploy_supervisor.py', 'deploy_supervisor.py')
        ]
        for name, pattern in processes:
            r = client.execute_command(f'pgrep -f "{pattern}" | head -1')
            pid = r.get('output', '').strip()
            if pid:
                print(f"   OK: {name} running (PID: {pid})")
            else:
                errors.append(f"{name} not running")
                print(f"   ERROR: {name} is NOT running")
        
        # 4. Recent Fixes
        print("\n4. Verifying Recent Fixes...")
        r = client.execute_command('cd /root/stock-bot && grep -q "signal_type.*BULLISH_SWEEP" main.py && echo YES || echo NO')
        if r.get('output', '').strip() == 'YES':
            print("   OK: UW parser fix present")
        else:
            warnings.append("UW parser fix not found")
            print("   WARNING: UW parser fix not found")
        
        r = client.execute_command('cd /root/stock-bot && grep -q "gate_type=" main.py && echo YES || echo NO')
        if r.get('output', '').strip() == 'YES':
            print("   OK: Gate logging fix present")
        else:
            warnings.append("Gate logging fix not found")
            print("   WARNING: Gate logging fix not found")
        
        # 5. SRE Sentinel Files
        print("\n5. Checking SRE Sentinel...")
        r = client.execute_command('cd /root/stock-bot && test -f sre_diagnostics.py && echo EXISTS || echo MISSING')
        if 'EXISTS' in r.get('output', ''):
            print("   OK: sre_diagnostics.py exists")
        else:
            warnings.append("sre_diagnostics.py missing")
            print("   WARNING: sre_diagnostics.py missing")
        
        r = client.execute_command('cd /root/stock-bot && test -f mock_signal_injection.py && echo EXISTS || echo MISSING')
        if 'EXISTS' in r.get('output', ''):
            print("   OK: mock_signal_injection.py exists")
        else:
            warnings.append("mock_signal_injection.py missing")
            print("   WARNING: mock_signal_injection.py missing")
        
        # 6. Dashboard
        print("\n6. Checking Dashboard...")
        r = client.execute_command('curl -s http://localhost:5000/health 2>&1 | head -1')
        if r.get('output', '').strip():
            print("   OK: Dashboard responding")
        else:
            errors.append("Dashboard not responding")
            print("   ERROR: Dashboard not responding")
        
        # 7. API Keys
        print("\n7. Checking API Configuration...")
        r = client.execute_command('cd /root/stock-bot && test -f .env && grep -q "UW_API_KEY=" .env && echo YES || echo NO')
        if r.get('output', '').strip() == 'YES':
            print("   OK: UW_API_KEY configured")
        else:
            errors.append("UW_API_KEY not configured")
            print("   ERROR: UW_API_KEY not configured")
        
        r = client.execute_command('cd /root/stock-bot && test -f .env && grep -q "ALPACA_KEY=" .env && echo YES || echo NO')
        if r.get('output', '').strip() == 'YES':
            print("   OK: ALPACA_KEY configured")
        else:
            errors.append("ALPACA_KEY not configured")
            print("   ERROR: ALPACA_KEY not configured")
        
        # Summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Errors: {len(errors)}")
        print(f"Warnings: {len(warnings)}")
        print()
        
        if errors:
            print("ERRORS:")
            for err in errors:
                print(f"  - {err}")
            print()
        
        if warnings:
            print("WARNINGS:")
            for warn in warnings:
                print(f"  - {warn}")
            print()
        
        if not errors:
            if not warnings:
                print("ALL CHECKS PASSED - READY FOR TRADING")
                return 0
            else:
                print("READY WITH WARNINGS - Review warnings above")
                return 0
        else:
            print("ERRORS DETECTED - Fix errors before trading")
            return 1
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        client.close()

if __name__ == "__main__":
    sys.exit(main())
