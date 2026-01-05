# Scoring Engine Fix - Summary

## Date: 2026-01-05

## Problem

ALL signals showed `score=0.00` and `source=unknown` because unscored `flow_clusters` were being merged with scored `filtered_clusters`.

## Root Cause

Line 6264 in `main.py` was merging:
- `flow_clusters` (from `cluster_signals()`) - NO composite_score
- `filtered_clusters` (from composite scoring) - HAS composite_score

Result: Unscored clusters appeared in signals.jsonl with score=0.00

## Fix

**Changed:** Use ONLY `filtered_clusters` when composite scoring is active
- All clusters now have `composite_score > 0.0`
- All clusters have `source="composite_v3"`
- Signals will show correct scores

## Status: ✅ FIXED AND DEPLOYED
