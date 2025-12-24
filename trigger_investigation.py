#!/usr/bin/env python3
"""
Trigger investigation on droplet by creating a trigger file in git.
This allows Cursor to initiate investigations without manual intervention.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def trigger_investigation():
    """Create trigger file and push to git"""
    trigger_file = Path(".investigation_trigger")
    
    # Create/update trigger file with timestamp
    with open(trigger_file, 'w') as f:
        f.write(f"Investigation triggered at {datetime.now().isoformat()}\n")
    
    # Add, commit, and push
    try:
        subprocess.run(["git", "add", str(trigger_file)], check=True)
        subprocess.run(["git", "commit", "-m", f"Trigger investigation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Investigation triggered - droplet will run it automatically")
        print("   Waiting for results... (check back in ~30 seconds)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error triggering investigation: {e}")
        return False

if __name__ == "__main__":
    trigger_investigation()

