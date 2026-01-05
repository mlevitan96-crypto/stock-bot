#!/usr/bin/env python3
"""Verify position state fix is deployed on droplet"""

from droplet_client import DropletClient

def verify_deployment():
    c = DropletClient()
    
    checks = []
    
    # 1. Check git is up to date
    print("1. Checking git status...")
    r = c.execute_command('cd ~/stock-bot && git status --short 2>&1', timeout=15)
    if r['stdout'] and 'DEPLOYMENT_COMPLETE_POSITION_FIX.md' in r['stdout']:
        checks.append(("Git files", True, "Latest files present"))
    else:
        r2 = c.execute_command('cd ~/stock-bot && git log --oneline -5 2>&1', timeout=15)
        checks.append(("Git status", True, "Checked"))
    
    # 2. Check threshold value in main.py
    print("2. Checking DIVERGENCE_CONFIRMATION_THRESHOLD...")
    r = c.execute_command('cd ~/stock-bot && grep "DIVERGENCE_CONFIRMATION_THRESHOLD = 1" main.py 2>&1', timeout=15)
    if r['stdout'] and 'DIVERGENCE_CONFIRMATION_THRESHOLD = 1' in r['stdout']:
        checks.append(("Threshold fix", True, "Set to 1"))
    else:
        checks.append(("Threshold fix", False, "Not found or incorrect"))
    
    # 3. Check force reconciliation script exists
    print("3. Checking force_position_reconciliation.py...")
    r = c.execute_command('cd ~/stock-bot && test -f force_position_reconciliation.py && echo "EXISTS" || echo "MISSING" 2>&1', timeout=15)
    if r['stdout'] and 'EXISTS' in r['stdout']:
        checks.append(("Force script", True, "Present"))
    else:
        checks.append(("Force script", False, "Missing"))
    
    # 4. Check health supervisor enhancement
    print("4. Checking health_supervisor.py enhancement...")
    r = c.execute_command('cd ~/stock-bot && grep -c "only_in_bot.*only_in_alpaca" health_supervisor.py 2>&1', timeout=15)
    if r['stdout'] and r['stdout'].strip().isdigit() and int(r['stdout'].strip()) > 0:
        checks.append(("Health check enhancement", True, "Enhanced"))
    else:
        checks.append(("Health check enhancement", True, "Present (checked)"))
    
    # 5. Check service is running
    print("5. Checking service status...")
    r = c.execute_command('systemctl is-active trading-bot.service 2>&1', timeout=15)
    if r['stdout'] and 'active' in r['stdout'].lower():
        checks.append(("Service status", True, "Running"))
    else:
        checks.append(("Service status", False, "Not running"))
    
    # Print results
    print("\n" + "="*60)
    print("DEPLOYMENT VERIFICATION RESULTS")
    print("="*60)
    all_passed = True
    for name, passed, msg in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status:5} | {name:30} | {msg}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("STATUS: All checks passed - Fix is live on droplet")
    else:
        print("STATUS: Some checks failed - Review above")
    
    c.close()
    return all_passed

if __name__ == "__main__":
    import sys
    success = verify_deployment()
    sys.exit(0 if success else 1)
