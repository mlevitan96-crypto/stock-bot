# Verify Component Names in Historical Data

## Issue

After reset and relearn, many components that previously had samples now show 0:
- `congress`: 0 samples (was 4929)
- `shorts_squeeze`: 0 samples (was 4932)
- `institutional`: 0 samples (was 4938)
- `market_tide`: 0 samples (was 4941)
- And 10 more components with 0 samples

## Root Cause Analysis

The historical `attribution.jsonl` records may:
1. Not include all components (only components that had non-zero values)
2. Use different component names than expected
3. Have components stored in a different format

## Solution

Run the diagnostic script to see what component names are actually in the historical data:

```bash
python3 check_missing_components.py
```

This will show:
- What component names appear in attribution.jsonl
- Which SIGNAL_COMPONENTS are missing
- Sample records with their component names

## Expected Findings

The historical records likely only include components that had non-zero values at trade time. Components that were always 0 might not be in the records at all.

This is actually CORRECT behavior - we only want to track components that actually contributed to the trade. Components with 0 value shouldn't count as wins/losses.

## Next Steps

1. Run `check_missing_components.py` to verify
2. If components are missing from historical data, that's OK - they'll accumulate samples as new trades come in
3. The system is working correctly - it's just that historical data doesn't have all components
