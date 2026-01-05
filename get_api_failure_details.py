#!/usr/bin/env python3
"""Get full API failure details"""

from droplet_client import DropletClient
import json

def get_failure_details():
    c = DropletClient()
    
    # Get full last entry
    r = c.execute_command('cd ~/stock-bot && tail -1 logs/critical_api_failure.log 2>&1', timeout=20)
    if r['stdout']:
        line = r['stdout'].strip()
        print("="*80)
        print("LATEST API FAILURE")
        print("="*80)
        print()
        print(line)
        print()
        
        # Try to parse JSON
        try:
            parts = line.split(" | ", 2)
            if len(parts) >= 3:
                timestamp = parts[0]
                event_type = parts[1]
                json_part = parts[2]
                data = json.loads(json_part)
                print("Parsed error details:")
                print(json.dumps(data, indent=2))
        except:
            pass
    else:
        print("No failures in log")
    
    c.close()

if __name__ == "__main__":
    get_failure_details()
