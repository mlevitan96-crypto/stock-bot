#!/usr/bin/env python3
"""Clear freeze flag and reset fail counter"""

import json
from pathlib import Path

# Clear freeze flag
freeze_path = StateFiles.PRE_MARKET_FREEZE
if freeze_path.exists():
    freeze_path.unlink()
    print("Cleared pre_market_freeze.flag")

# Reset fail counter
fail_counter_path = StateFiles.FAIL_COUNTER
if fail_counter_path.exists():
    data = json.loads(fail_counter_path.read_text())
else:
    data = {}
data["fail_count"] = 0
data["last_reset"] = "2025-12-29T15:45:00Z"
fail_counter_path.write_text(json.dumps(data, indent=2))
print("Reset fail counter to 0")

print("Done - trading should resume on next cycle")

