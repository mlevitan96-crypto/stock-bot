#!/usr/bin/env python3
"""Verify weight fix"""

import uw_composite_v2

weight = uw_composite_v2.get_weight("options_flow", "mixed")
expected = 2.4

print(f"options_flow weight: {weight}")
print(f"Expected: {expected}")
print(f"Match: {'YES' if abs(weight - expected) < 0.1 else 'NO'}")

if weight >= 2.0:
    print("OK: Weight is good")
else:
    print("ERROR: Weight still too low!")
