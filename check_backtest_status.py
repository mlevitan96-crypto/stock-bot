#!/usr/bin/env python3
"""Check backtest status and results"""
import json
import sys
from pathlib import Path

report_path = Path("reports/7_day_quick_audit.json")

if report_path.exists():
    with open(report_path, 'r') as f:
        data = json.load(f)
    print(f"Report exists: {report_path}")
    print(f"Total Trades: {data.get('total_trades', 0)}")
    print(f"Win Rate: {data.get('win_rate', 0):.2f}%")
    if data.get('total_trades', 0) > 0:
        specialist = data.get('specialist_metrics', {})
        print(f"\nSpecialist Win Rate: {specialist.get('win_rate', 0):.2f}%")
        print(f"Specialist Trades: {specialist.get('total_trades', 0)}")
else:
    print(f"Report not found: {report_path}")
    print("Backtest may still be running or failed")
    sys.exit(1)
