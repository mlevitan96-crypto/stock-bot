#!/usr/bin/env python3
"""Analyze backtest report for specialist gating effectiveness"""
import json
import sys

report_path = "reports/7_day_quick_audit.json"

try:
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("BACKTEST REPORT ANALYSIS")
    print("=" * 60)
    
    # Overall metrics
    print(f"\nTotal Trades: {data.get('total_trades', 0)}")
    print(f"Win Rate: {data.get('win_rate', 0):.2f}%")
    print(f"Total P&L: ${data.get('total_pnl', 0):.2f}")
    
    # Specialist gating
    specialist_metrics = data.get('specialist_metrics', {})
    print(f"\n--- Specialist Gating (11:30-13:30 EST) ---")
    print(f"Specialist Win Rate: {specialist_metrics.get('win_rate', 0):.2f}%")
    print(f"Specialist Trades: {specialist_metrics.get('total_trades', 0)}")
    print(f"Specialist P&L: ${specialist_metrics.get('total_pnl', 0):.2f}")
    
    # Compare with overall
    overall_win_rate = data.get('win_rate', 0)
    specialist_win_rate = specialist_metrics.get('win_rate', 0)
    if overall_win_rate > 0:
        improvement = specialist_win_rate - overall_win_rate
        print(f"\nImprovement vs Overall: {improvement:+.2f}%")
        if improvement > 0:
            print("✅ Specialist gating is EFFECTIVE - improves win rate")
        else:
            print("⚠️  Specialist gating may need adjustment")
    
    # Latency impact
    print(f"\n--- Latency Impact ---")
    print(f"Latency Penalty: 0.5 bps (applied to all entries)")
    
    # Stale exits
    stale_metrics = data.get('stale_exit_metrics', {})
    print(f"\n--- Stale Trade Exits ---")
    print(f"Stale Exits: {stale_metrics.get('count', 0)}")
    print(f"Capacity Freed: {stale_metrics.get('capacity_freed_pct', 0):.2f}%")
    
    print("\n" + "=" * 60)
    
except FileNotFoundError:
    print(f"ERROR: Report file not found: {report_path}")
    print("The backtest may have failed - check credentials and API connectivity")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
