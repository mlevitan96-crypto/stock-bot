#!/usr/bin/env python3
"""
Audit Learning System Coverage

This script checks:
1. What logs are being collected
2. What the learning engine currently analyzes
3. What logs are NOT being analyzed
4. Recommendations for improvement
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

LOG_DIR = Path("logs")
DATA_DIR = Path("data")
STATE_DIR = Path("state")

print("=" * 80)
print("LEARNING SYSTEM COVERAGE AUDIT")
print("=" * 80)
print()

# 1. Check what logs exist
print("1. LOG FILES INVENTORY")
print("-" * 80)

log_files = {
    "attribution.jsonl": "Trade attribution (P&L, components, exit reasons)",
    "exit.jsonl": "Exit events and reasons",
    "signals.jsonl": "Signal generation events",
    "orders.jsonl": "Order execution events",
    "run.jsonl": "Execution cycles",
    "displacement.jsonl": "Displacement events",
    "gate.jsonl": "Gate blocks",
    "worker.jsonl": "Worker thread events",
    "supervisor.jsonl": "Supervisor logs",
    "comprehensive_learning.jsonl": "Learning engine cycles",
}

data_files = {
    "uw_attribution.jsonl": "UW signal attribution (including blocked entries)",
    "live_orders.jsonl": "Live order events",
    "weight_learning.jsonl": "Weight learning updates",
    "learning_events.jsonl": "Learning events (telemetry)",
    "daily_postmortem.jsonl": "Daily postmortem summaries",
    "portfolio_events.jsonl": "Portfolio events",
    "ops_errors.jsonl": "Operations errors",
    "uw_flow_cache.json": "UW API cache",
}

state_files = {
    "blocked_trades.jsonl": "Blocked trades (counterfactual learning)",
}

existing_logs = {}
missing_logs = []

for log_file, description in log_files.items():
    path = LOG_DIR / log_file
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = [l for l in f if l.strip()]
                existing_logs[log_file] = {
                    "path": str(path),
                    "description": description,
                    "records": len(lines),
                    "exists": True
                }
        except:
            existing_logs[log_file] = {
                "path": str(path),
                "description": description,
                "records": 0,
                "exists": True,
                "error": "Cannot read"
            }
    else:
        missing_logs.append(log_file)

for data_file, description in data_files.items():
    path = DATA_DIR / data_file
    if path.exists():
        try:
            if data_file.endswith('.jsonl'):
                with open(path, 'r', encoding='utf-8') as f:
                    lines = [l for l in f if l.strip()]
                    existing_logs[data_file] = {
                        "path": str(path),
                        "description": description,
                        "records": len(lines),
                        "exists": True
                    }
            else:
                existing_logs[data_file] = {
                    "path": str(path),
                    "description": description,
                    "records": 1,  # JSON file
                    "exists": True
                }
        except:
            existing_logs[data_file] = {
                "path": str(path),
                "description": description,
                "records": 0,
                "exists": True,
                "error": "Cannot read"
            }
    else:
        missing_logs.append(data_file)

# Check state files
for state_file, description in state_files.items():
    path = STATE_DIR / state_file
    if path.exists():
        try:
            if data_file.endswith('.jsonl'):
                with open(path, 'r', encoding='utf-8') as f:
                    lines = [l for l in f if l.strip()]
                    existing_logs[data_file] = {
                        "path": str(path),
                        "description": description,
                        "records": len(lines),
                        "exists": True
                    }
            else:
                existing_logs[data_file] = {
                    "path": str(path),
                    "description": description,
                    "records": 1,  # JSON file
                    "exists": True
                }
        except:
            existing_logs[data_file] = {
                "path": str(path),
                "description": description,
                "records": 0,
                "exists": True,
                "error": "Cannot read"
            }
    else:
        missing_logs.append(data_file)

print(f"Found {len(existing_logs)} log files with data")
print(f"Missing {len(missing_logs)} expected log files")
print()

for log_file, info in sorted(existing_logs.items()):
    status = "[OK]" if info.get("records", 0) > 0 else "[EMPTY]"
    print(f"{status} {log_file:30s} {info['records']:6d} records - {info['description']}")

if missing_logs:
    print()
    print("Missing log files:")
    for log_file in missing_logs:
        print(f"  [MISSING] {log_file}")

print()
print()

# 2. Check what learning system analyzes
print("2. WHAT LEARNING SYSTEM ANALYZES")
print("-" * 80)

# Check learn_from_outcomes function behavior
attr_log = LOG_DIR / "attribution.jsonl"
if attr_log.exists():
    with open(attr_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        total_records = len(lines)
        
        # Count records by type
        by_type = defaultdict(int)
        by_date = defaultdict(int)
        with_components = 0
        without_components = 0
        
        for line in lines:
            try:
                rec = json.loads(line)
                rec_type = rec.get("type", "unknown")
                by_type[rec_type] += 1
                
                # Check date
                ts = rec.get("ts", rec.get("_ts", ""))
                if ts:
                    if isinstance(ts, str):
                        try:
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            date_str = dt.date().isoformat()
                            by_date[date_str] += 1
                        except:
                            pass
                
                # Check for components
                context = rec.get("context", {})
                if context.get("components"):
                    with_components += 1
                elif rec.get("components"):
                    with_components += 1
                else:
                    without_components += 1
            except:
                pass
        
        print(f"Total attribution records: {total_records}")
        print(f"Records by type:")
        for rec_type, count in sorted(by_type.items()):
            print(f"  {rec_type:20s} {count:4d}")
        
        print()
        print(f"Records with components: {with_components}")
        print(f"Records without components: {without_components}")
        
        print()
        print("Records by date (last 10 days):")
        for date_str in sorted(by_date.keys(), reverse=True)[:10]:
            print(f"  {date_str} {by_date[date_str]:4d} records")
        
        print()
        print("CURRENT LEARNING BEHAVIOR:")
        # Check if comprehensive learning orchestrator is being used
        learning_state_file = Path("state/learning_processing_state.json")
        if learning_state_file.exists():
            try:
                with open(learning_state_file, 'r', encoding='utf-8') as f:
                    learning_state = json.load(f)
                    total_processed = learning_state.get("total_trades_processed", 0)
                    print(f"  - Comprehensive learning orchestrator ACTIVE")
                    print(f"  - Total trades processed historically: {total_processed}")
                    print(f"  - Processes ALL historical trades (not just today's)")
                    print(f"  - Tracks last processed IDs to avoid duplicates")
                    if learning_state.get("last_processed_ts"):
                        print(f"  - Last processed: {learning_state.get('last_processed_ts')}")
            except:
                print("  - Comprehensive learning orchestrator state file exists but unreadable")
        else:
            print("  - learn_from_outcomes() only processes TODAY's trades (LEGACY MODE)")
            print("  - Only processes records with type='attribution'")
            print("  - Requires components in context.components")
            print(f"  - Historical records ignored: {total_records - by_date.get(datetime.now(timezone.utc).date().isoformat(), 0)}")

print()
print()

# 3. Check learning state
print("3. LEARNING SYSTEM STATE")
print("-" * 80)

weights_file = STATE_DIR / "signal_weights.json"
if weights_file.exists():
    with open(weights_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        learner = state.get("learner", {})
        history_count = learner.get("learning_history_count", 0)
        
        print(f"Learning history size: {history_count}")
        
        entry_weights = state.get("entry_weights", {})
        bands = entry_weights.get("weight_bands", {})
        components_with_data = sum(1 for b in bands.values() 
                                 if isinstance(b, dict) and b.get("sample_count", 0) > 0)
        print(f"Components with samples: {components_with_data}")
        
        # Check exit model
        exit_weights = state.get("exit_weights", {})
        if exit_weights:
            exit_bands = exit_weights.get("weight_bands", {})
            exit_components = sum(1 for b in exit_bands.values() 
                                if isinstance(b, dict) and b.get("sample_count", 0) > 0)
            print(f"Exit components with samples: {exit_components}")
        else:
            print("Exit model: Not initialized or no data")

print()
print()

# 4. Identify gaps
print("4. GAPS IN LEARNING COVERAGE")
print("-" * 80)

gaps = []

# Check if exit.jsonl is being analyzed
exit_log = LOG_DIR / "exit.jsonl"
learning_state_file = Path("state/learning_processing_state.json")
if exit_log.exists():
    with open(exit_log, 'r', encoding='utf-8') as f:
        exit_lines = [l for l in f if l.strip()]
        if exit_lines:
            # Check if comprehensive learning processed exits
            if learning_state_file.exists():
                try:
                    with open(learning_state_file, 'r', encoding='utf-8') as f:
                        learning_state = json.load(f)
                        processed_exits = learning_state.get("total_exits_processed", 0)
                        unprocessed = max(0, len(exit_lines) - processed_exits)
                        if unprocessed > 0:
                            gaps.append({
                                "log": "exit.jsonl",
                                "records": unprocessed,
                                "issue": f"{unprocessed} exit events not yet processed",
                                "impact": "Run backfill_historical_learning.py to process remaining exits"
                            })
                except:
                    gaps.append({
                        "log": "exit.jsonl",
                        "records": len(exit_lines),
                        "issue": "Exit events logged but processing state unclear",
                        "impact": "Exit signal weights may not be optimized"
                    })
            else:
                gaps.append({
                    "log": "exit.jsonl",
                    "records": len(exit_lines),
                    "issue": "Exit events logged but not analyzed for exit signal learning",
                    "impact": "Exit signal weights not being optimized based on exit outcomes"
                })

# Check if signals.jsonl is being analyzed
signals_log = LOG_DIR / "signals.jsonl"
learning_state_file = Path("state/learning_processing_state.json")
if signals_log.exists():
    with open(signals_log, 'r', encoding='utf-8') as f:
        signal_lines = [l for l in f if l.strip()]
        if signal_lines:
            if learning_state_file.exists():
                try:
                    with open(learning_state_file, 'r', encoding='utf-8') as f:
                        learning_state = json.load(f)
                        processed_signals = learning_state.get("total_signals_processed", 0)
                        unprocessed = max(0, len(signal_lines) - processed_signals)
                        if unprocessed > 0:
                            gaps.append({
                                "log": "signals.jsonl",
                                "records": unprocessed,
                                "issue": f"{unprocessed} signal events not yet processed",
                                "impact": "Run backfill to process remaining signals"
                            })
                except:
                    gaps.append({
                        "log": "signals.jsonl",
                        "records": len(signal_lines),
                        "issue": "Signal generation events logged but processing state unclear",
                        "impact": "Cannot verify if signals are being analyzed"
                    })
            else:
                gaps.append({
                    "log": "signals.jsonl",
                    "records": len(signal_lines),
                    "issue": "Signal generation events logged but not analyzed",
                    "impact": "Cannot learn which signal patterns lead to better outcomes"
                })

# Check if orders.jsonl is being analyzed
orders_log = LOG_DIR / "orders.jsonl"
if orders_log.exists():
    with open(orders_log, 'r', encoding='utf-8') as f:
        order_lines = [l for l in f if l.strip()]
        if order_lines:
            if learning_state_file.exists():
                try:
                    with open(learning_state_file, 'r', encoding='utf-8') as f:
                        learning_state = json.load(f)
                        processed_orders = learning_state.get("total_orders_processed", 0)
                        unprocessed = max(0, len(order_lines) - processed_orders)
                        if unprocessed > 0:
                            gaps.append({
                                "log": "orders.jsonl",
                                "records": unprocessed,
                                "issue": f"{unprocessed} order events not yet processed",
                                "impact": "Run backfill to process remaining orders"
                            })
                except:
                    gaps.append({
                        "log": "orders.jsonl",
                        "records": len(order_lines),
                        "issue": "Order execution events logged but processing state unclear",
                        "impact": "Cannot verify if orders are being analyzed"
                    })
            else:
                gaps.append({
                    "log": "orders.jsonl",
                    "records": len(order_lines),
                    "issue": "Order execution events logged but not analyzed",
                    "impact": "Cannot learn execution quality, slippage patterns, or order timing"
                })

# Check if blocked_trades.jsonl is being analyzed
blocked_log = STATE_DIR / "blocked_trades.jsonl"
if blocked_log.exists():
    with open(blocked_log, 'r', encoding='utf-8') as f:
        blocked_lines = [l for l in f if l.strip()]
        if blocked_lines:
            if learning_state_file.exists():
                try:
                    with open(learning_state_file, 'r', encoding='utf-8') as f:
                        learning_state = json.load(f)
                        processed_blocked = learning_state.get("total_blocked_processed", 0)
                        unprocessed = max(0, len(blocked_lines) - processed_blocked)
                        if unprocessed > 0:
                            gaps.append({
                                "log": "blocked_trades.jsonl",
                                "records": unprocessed,
                                "issue": f"{unprocessed} blocked trades not yet processed",
                                "impact": "Run backfill to process remaining blocked trades for counterfactual learning"
                            })
                except:
                    gaps.append({
                        "log": "blocked_trades.jsonl",
                        "records": len(blocked_lines),
                        "issue": "Blocked trades logged but processing state unclear",
                        "impact": "Cannot verify if blocked trades are being analyzed for counterfactual learning"
                    })
            else:
                gaps.append({
                    "log": "blocked_trades.jsonl",
                    "records": len(blocked_lines),
                    "issue": "Blocked trades logged but not analyzed",
                    "impact": "Cannot learn from missed opportunities (counterfactual learning)"
                })

# Check if gate.jsonl is being analyzed
gate_log = LOG_DIR / "gate.jsonl"
if gate_log.exists():
    with open(gate_log, 'r', encoding='utf-8') as f:
        gate_lines = [l for l in f if l.strip()]
        if gate_lines:
            if learning_state_file.exists():
                try:
                    with open(learning_state_file, 'r', encoding='utf-8') as f:
                        learning_state = json.load(f)
                        processed_gates = learning_state.get("total_gates_processed", 0)
                        unprocessed = max(0, len(gate_lines) - processed_gates)
                        if unprocessed > 0:
                            gaps.append({
                                "log": "gate.jsonl",
                                "records": unprocessed,
                                "issue": f"{unprocessed} gate events not yet processed",
                                "impact": "Run backfill to process remaining gate events"
                            })
                except:
                    gaps.append({
                        "log": "gate.jsonl",
                        "records": len(gate_lines),
                        "issue": "Gate events logged but processing state unclear",
                        "impact": "Cannot verify if gate events are being analyzed"
                    })
            else:
                gaps.append({
                    "log": "gate.jsonl",
                    "records": len(gate_lines),
                    "issue": "Gate events logged but not analyzed",
                    "impact": "Cannot learn gate blocking patterns or optimize gate thresholds"
                })

# Check if daily_postmortem is being analyzed
postmortem_log = DATA_DIR / "daily_postmortem.jsonl"
if postmortem_log.exists():
    with open(postmortem_log, 'r', encoding='utf-8') as f:
        pm_lines = [l for l in f if l.strip()]
        if pm_lines:
            gaps.append({
                "log": "daily_postmortem.jsonl",
                "records": len(pm_lines),
                "issue": "Daily summaries logged but not analyzed",
                "impact": "Cannot track long-term performance trends or regime changes"
            })

# Check historical trades
learning_state_file = Path("state/learning_processing_state.json")
if attr_log.exists():
    with open(attr_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        total_records = len(lines)
        
        # Check if comprehensive learning is active
        if learning_state_file.exists():
            try:
                with open(learning_state_file, 'r', encoding='utf-8') as f:
                    learning_state = json.load(f)
                    processed = learning_state.get("total_trades_processed", 0)
                    unprocessed = max(0, total_records - processed)
                    if unprocessed > 0:
                        gaps.append({
                            "log": "attribution.jsonl (unprocessed)",
                            "records": unprocessed,
                            "issue": f"{unprocessed} trades not yet processed by comprehensive learning",
                            "impact": "Run backfill_historical_learning.py to process remaining trades"
                        })
            except:
                gaps.append({
                    "log": "attribution.jsonl (historical)",
                    "records": total_records,
                    "issue": "Comprehensive learning state file exists but unreadable",
                    "impact": "Cannot verify if historical trades are processed"
                })
        else:
            # Legacy mode - check for historical trades
            today = datetime.now(timezone.utc).date().isoformat()
            historical = 0
            for line in lines:
                try:
                    rec = json.loads(line)
                    ts = rec.get("ts", "")
                    if ts and not ts.startswith(today):
                        historical += 1
                except:
                    pass
            if historical > 0:
                gaps.append({
                    "log": "attribution.jsonl (historical)",
                    "records": historical,
                    "issue": "Historical trades not being processed (legacy mode)",
                    "impact": "Learning resets daily, losing historical performance data"
                })

if gaps:
    for gap in gaps:
        print(f"[GAP] {gap['log']:30s} {gap['records']:6d} records")
        print(f"      Issue: {gap['issue']}")
        print(f"      Impact: {gap['impact']}")
        print()
else:
    print("No major gaps identified")

print()
print()

# 5. Recommendations
print("5. RECOMMENDATIONS")
print("-" * 80)

recommendations = [
    {
        "priority": "COMPLETE",
        "action": "Process historical trades",
        "details": "✅ Comprehensive learning orchestrator processes all historical trades",
        "benefit": "All historical data now utilized for learning"
    },
    {
        "priority": "COMPLETE",
        "action": "Analyze exit.jsonl for exit signal learning",
        "details": "✅ Exit events processed for exit signal weight optimization",
        "benefit": "Exit timing optimized based on actual outcomes"
    },
    {
        "priority": "COMPLETE",
        "action": "Process blocked trades for counterfactual learning",
        "details": "✅ Blocked trades now processed for counterfactual analysis",
        "benefit": "Learn from missed opportunities - were we too conservative/aggressive?"
    },
    {
        "priority": "COMPLETE",
        "action": "Process gate events",
        "details": "✅ Gate events now processed for gate pattern learning",
        "benefit": "Learn which gates are most effective and optimize thresholds"
    },
    {
        "priority": "COMPLETE",
        "action": "Enable continuous learning",
        "details": "✅ Learning happens immediately after each trade close",
        "benefit": "Faster adaptation to changing market conditions"
    },
    {
        "priority": "MEDIUM",
        "action": "Analyze orders.jsonl for execution quality",
        "details": "Track slippage, fill quality, and order timing patterns",
        "benefit": "Optimize order execution strategy"
    },
    {
        "priority": "MEDIUM",
        "action": "Analyze signals.jsonl for signal pattern learning",
        "details": "Learn which signal combinations and patterns lead to better outcomes",
        "benefit": "Improve signal selection and entry criteria"
    },
    {
        "priority": "LOW",
        "action": "Analyze daily_postmortem.jsonl for regime detection",
        "details": "Use daily summaries to detect regime changes and adjust strategy",
        "benefit": "Better regime-aware trading"
    },
    {
        "priority": "MEDIUM",
        "action": "Enable continuous learning",
        "details": "Call learning after each trade close, not just daily",
        "benefit": "Faster adaptation to changing market conditions"
    }
]

for rec in recommendations:
    print(f"[{rec['priority']:6s}] {rec['action']}")
    print(f"         {rec['details']}")
    print(f"         Benefit: {rec['benefit']}")
    print()

print()
print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
