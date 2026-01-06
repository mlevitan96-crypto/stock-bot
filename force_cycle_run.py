#!/usr/bin/env python3
"""Force a cycle to run manually to test"""

import sys
import os
sys.path.insert(0, '/root/stock-bot')

# Set environment  
os.chdir('/root/stock-bot')

# Activate venv
activate_this = '/root/stock-bot/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

print("Forcing cycle run...")

try:
    from main import run_once
    print("Calling run_once()...")
    metrics = run_once()
    print(f"Cycle complete: {metrics}")
    print(f"Clusters: {metrics.get('clusters', 0)}")
    print(f"Orders: {metrics.get('orders', 0)}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
