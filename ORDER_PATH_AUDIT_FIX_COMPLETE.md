# Order Log Path Audit Fix - Complete

## Date: 2026-01-05

## Issue Identified
User reported: "There are way more orders than 38 all time. You must check memory bank for correct mapping. We just did a mapping audit and correct path review over the weekend."

## Root Cause
- Audit script was using **INCORRECT PATH**: `logs/order.jsonl` (singular)
- **CORRECT PATH**: `logs/orders.jsonl` (plural) per `config/registry.py` `LogFiles.ORDERS`
- This caused incorrect order counts (showing only 38 when there are many more)

## Fixes Applied

### 1. Updated `check_workflow_audit.py`
- Changed from `logs/order.jsonl` to `logs/orders.jsonl`
- Added total trades count from `logs/attribution.jsonl` (authoritative source)
- Updated reporting to show both:
  - Total trades (all time) from `attribution.jsonl`
  - Recent order events from `orders.jsonl`

### 2. Updated `check_signals_and_orders.py`
- Changed from `logs/order.jsonl` to `logs/orders.jsonl`

### 3. Updated `MEMORY_BANK.md`
- Added warning note: Use plural "orders.jsonl", NOT "order.jsonl"
- Added note that `attribution.jsonl` is authoritative source for total trade counts

### 4. Created Documentation
- `ORDER_LOG_PATH_CORRECTION.md` - Documents the correction

## Correct Paths (Per Memory Bank & Mapping Audit)

### Order Events
- **CORRECT**: `logs/orders.jsonl` (plural)
- **INCORRECT**: `logs/order.jsonl` (singular) - **DO NOT USE**

### Total Trades Count
- **AUTHORITATIVE SOURCE**: `logs/attribution.jsonl`
- Count all records with `type == "attribution"` to get total trades

## Status: ✅ FIXED

All scripts now use the correct paths as confirmed by the mapping audit over the weekend.

## Reference
- Memory Bank: Line 985-987
- config/registry.py: `LogFiles.ORDERS = Directories.LOGS / "orders.jsonl"`
- Mapping audit completed over weekend confirmed correct paths
