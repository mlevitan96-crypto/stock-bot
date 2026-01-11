#!/usr/bin/env python3
"""Check for API failures in critical_api_failure.log"""

from droplet_client import DropletClient
import json

def check_api_failures():
    c = DropletClient()
    
    print("="*80)
    print("CHECKING FOR API FAILURES")
    print("="*80)
    print()
    
    # Check if log file exists
    r = c.execute_command('cd ~/stock-bot && test -f logs/critical_api_failure.log && echo "EXISTS" || echo "NOT_EXISTS"', timeout=15)
    exists = r['stdout'].strip() if r['stdout'] else 'UNKNOWN'
    print(f"Log file exists: {exists}")
    print()
    
    if exists == "EXISTS":
        # Get last 20 lines
        r2 = c.execute_command('cd ~/stock-bot && tail -20 logs/critical_api_failure.log 2>&1', timeout=20)
        if r2['stdout']:
            lines = r2['stdout'].strip().split('\n')
            print(f"Last {len(lines)} entries in critical_api_failure.log:")
            print()
            for line in lines[-10:]:  # Show last 10
                if line.strip():
                    print(f"  {line[:200]}")
            print()
        else:
            print("  Log file is empty")
    else:
        print("  No API failures logged yet (this could mean orders are succeeding, or no orders attempted)")
    print()
    
    # Check recent order logs
    print("Recent order submission logs:")
    r3 = c.execute_command('cd ~/stock-bot && tail -50 logs/order.jsonl 2>&1 | tail -10', timeout=20)
    if r3['stdout']:
        print(r3['stdout'][:1000])
    else:
        print("  No recent order logs")
    print()
    
    c.close()
    print("="*80)

if __name__ == "__main__":
    check_api_failures()
