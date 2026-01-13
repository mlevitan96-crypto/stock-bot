#!/usr/bin/env python3
"""
Clear freeze flags that are blocking trading
"""

from droplet_client import DropletClient

client = DropletClient()

print("=" * 80)
print("CLEARING FREEZE FLAGS")
print("=" * 80)
print()

# Check current freeze state
print("=== 1. CURRENT FREEZE STATE ===")
check_result = client.execute_command(
    "cd ~/stock-bot && ls -la state/pre_market_freeze.flag state/governor_freezes.json 2>/dev/null || echo 'Freeze files check'",
    timeout=10
)
print(check_result['stdout'] if check_result['stdout'] else 'No output')
print()

# Check contents of freeze files
print("=== 2. FREEZE FILE CONTENTS ===")
pre_market_result = client.execute_command(
    "cd ~/stock-bot && test -f state/pre_market_freeze.flag && cat state/pre_market_freeze.flag || echo 'pre_market_freeze.flag does not exist'",
    timeout=10
)
print(f"pre_market_freeze.flag: {pre_market_result['stdout'] if pre_market_result['stdout'] else 'No output'}")
print()

governor_result = client.execute_command(
    "cd ~/stock-bot && test -f state/governor_freezes.json && cat state/governor_freezes.json || echo 'governor_freezes.json does not exist'",
    timeout=10
)
print(f"governor_freezes.json: {governor_result['stdout'] if governor_result['stdout'] else 'No output'}")
print()

# Clear pre_market_freeze.flag
print("=== 3. CLEARING pre_market_freeze.flag ===")
clear_result = client.execute_command(
    "cd ~/stock-bot && rm -f state/pre_market_freeze.flag && echo 'pre_market_freeze.flag removed' || echo 'Failed to remove'",
    timeout=10
)
print(clear_result['stdout'] if clear_result['stdout'] else 'No output')
print()

# Clear governor_freezes.json (set all to false)
print("=== 4. CLEARING governor_freezes.json ===")
clear_governor_result = client.execute_command(
    "cd ~/stock-bot && echo '{}' > state/governor_freezes.json && echo 'governor_freezes.json cleared' || echo 'Failed to clear'",
    timeout=10
)
print(clear_governor_result['stdout'] if clear_governor_result['stdout'] else 'No output')
print()

# Verify freeze state is clear
print("=== 5. VERIFYING FREEZE STATE CLEARED ===")
verify_result = client.execute_command(
    "cd ~/stock-bot && test -f state/pre_market_freeze.flag && echo 'ERROR: pre_market_freeze.flag still exists' || echo 'OK: pre_market_freeze.flag removed'",
    timeout=10
)
print(verify_result['stdout'] if verify_result['stdout'] else 'No output')
print()

client.close()

print("=" * 80)
print("FREEZE CLEAR COMPLETE")
print("=" * 80)
print()
print("Next cycle should resume trading if freeze was the only blocker.")
