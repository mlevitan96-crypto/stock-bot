# Signal Dashboard Fix Summary
**Date:** 2026-01-13  
**Status:** ✅ **FIX DEPLOYED**

---

## Problem

Signals were being calculated (composite scores: NIO: 4.22, F: 4.02, HD: 4.24, etc.) but **not showing in the dashboard Signal Review tab**.

---

## Root Cause

Signals were only logged to `signal_history.jsonl` when they reached `decide_and_execute()` and were processed. However:
1. If clusters didn't reach `decide_and_execute()` (e.g., `clusters=0`), signals weren't logged
2. If signals were accepted in composite scoring but blocked before logging, they didn't appear
3. Only "Blocked" signals from `decide_and_execute()` were appearing in the dashboard

---

## Fix

**Added immediate signal logging in composite scoring:**
- When a composite signal is **ACCEPTED** (passes `should_enter_v2()` gate), log it immediately with decision="Accepted: composite_gate"
- When a composite signal is **REJECTED** (fails gate), log it immediately with decision="Rejected: reason"
- This ensures ALL signals appear in the dashboard, even if they're blocked later

**Code Location:** `main.py` lines ~7760-7776 (accepted) and ~7788-7830 (rejected)

---

## Expected Results

After fix:
1. ✅ All composite signals (accepted AND rejected) are logged immediately
2. ✅ Dashboard Signal Review shows all signals with scores
3. ✅ Signals show decision: "Accepted: composite_gate", "Rejected: reason", "Ordered", or "Blocked: reason"
4. ✅ Dashboard displays signals even if they don't reach execution

---

## Verification

Wait for next `run_once()` cycle and check:
1. `state/signal_history.jsonl` should have new entries with "Accepted: composite_gate"
2. Dashboard `/api/signal_history` should return these signals
3. Signal Review tab should show all signals with their scores and decisions

---

**Status:** Fix deployed. Monitoring for signals to appear in dashboard.
