# Comprehensive Fix Plan for UW Daemon Loop Entry Issue

## Problem Statement
The daemon receives SIGTERM before entering the main loop, causing immediate shutdown. Even with signal ignore logic, the daemon is not entering the main loop.

## Root Cause Analysis

### Hypothesis 1: Signal arrives between flag set and loop entry
- **Status**: LIKELY
- **Evidence**: Log shows "Received signal 15" but no loop entry
- **Fix**: Set `_loop_entered` flag INSIDE the loop on first iteration, not before

### Hypothesis 2: Exception before loop entry
- **Status**: POSSIBLE
- **Evidence**: No exception in logs, but could be silent
- **Fix**: Add try/except around entire initialization

### Hypothesis 3: Running flag becomes False before loop
- **Status**: POSSIBLE
- **Evidence**: Multiple checks show running=True, but something sets it False
- **Fix**: Add atomic flag checking

## Implementation Plan

### Step 1: Fix Loop Entry Flag Timing
- Move `_loop_entered = True` to INSIDE the while loop on first iteration
- This prevents race condition where signal arrives between flag set and loop entry

### Step 2: Add Comprehensive Logging
- Log every step from initialization to loop entry
- Log signal handler calls with full context
- Log any exceptions that occur

### Step 3: Add Exception Handling
- Wrap entire run() method in try/except
- Ensure exceptions don't silently prevent loop entry

### Step 4: Test in Isolation
- Run daemon for 2 minutes in complete isolation
- Verify loop entry occurs
- Verify signals are properly handled

### Step 5: Test with Supervisor
- Run daemon via deploy_supervisor.py
- Verify it starts and enters loop
- Verify cache is populated

## Files to Modify
1. `uw_flow_daemon.py` - Fix loop entry flag timing
2. Add comprehensive logging throughout

## Success Criteria
- ✅ Daemon enters main loop within 5 seconds of startup
- ✅ Cache file is created and populated
- ✅ Signals are properly ignored until loop entry
- ✅ Daemon runs continuously under supervisor
