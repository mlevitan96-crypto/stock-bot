#!/usr/bin/env python3
"""Simple script to get workflow status - run on droplet"""

from droplet_client import DropletClient
import json

def main():
    c = DropletClient()
    
    # Get workflow audit results
    r = c.execute_command('cd ~/stock-bot && source venv/bin/activate && python3 check_workflow_audit.py 2>&1', timeout=40)
    output = r.get('stdout', '')
    
    # Write to file to avoid encoding issues
    with open('workflow_audit_results.txt', 'w', encoding='utf-8', errors='replace') as f:
        f.write(output)
    
    print("Audit complete. Results saved to workflow_audit_results.txt")
    print("\nFirst 2000 chars:")
    print(output[:2000])
    
    c.close()

if __name__ == "__main__":
    main()
