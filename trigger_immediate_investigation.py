#!/usr/bin/env python3
"""Trigger immediate investigation by creating a script that runs on next pull"""

import subprocess
from datetime import datetime

# Create a file that will trigger investigation
with open("RUN_INVESTIGATION_NOW.flag", "w") as f:
    f.write(f"Investigation requested at {datetime.now().isoformat()}\n")

# Also update the run script to be executable
with open("run_investigation_on_pull.sh", "w") as f:
    f.write("""#!/bin/bash
cd ~/stock-bot
python3 investigate_no_trades.py
git add investigate_no_trades.json 2>/dev/null
git commit -m "Investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
git push origin main 2>/dev/null || true
""")

# Commit and push
subprocess.run(["git", "add", "RUN_INVESTIGATION_NOW.flag", "run_investigation_on_pull.sh"], check=True)
subprocess.run(["git", "commit", "-m", f"Trigger immediate investigation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
subprocess.run(["git", "push", "origin", "main"], check=True)

print("Investigation trigger pushed. Droplet will run it on next status check or when you run: ./run_investigation_on_pull.sh")

