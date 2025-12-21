#!/usr/bin/env python3
"""
Learning Pipeline Verification Script

This script verifies that:
1. Trade logs are being created
2. Logs are being read by the learning system
3. Learning system is processing the data
4. Weights are being updated
5. Updated weights are being applied to trading decisions

Run this script to diagnose learning pipeline issues.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Paths
LOG_DIR = Path("logs")
DATA_DIR = Path("data")
STATE_DIR = Path("state")

ATTRIBUTION_LOG = LOG_DIR / "attribution.jsonl"
UW_ATTRIBUTION_LOG = DATA_DIR / "uw_attribution.jsonl"
WEIGHTS_STATE = STATE_DIR / "signal_weights.json"
LEARNING_LOG = DATA_DIR / "weight_learning.jsonl"
OPTIMIZER_ERRORS = DATA_DIR / "optimizer_errors.jsonl"
PROFILES_FILE = Path("profiles.json")

def load_jsonl(path: Path) -> List[Dict]:
    """Load JSONL file, return list of records"""
    if not path.exists():
        return []
    records = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"ERROR: Failed to read {path}: {e}")
    return records

def check_logs_exist() -> Dict[str, Any]:
    """Check if log files exist and have data"""
    results = {
        "attribution_log": {
            "exists": ATTRIBUTION_LOG.exists(),
            "records": 0,
            "recent_records": 0,
            "last_record_ts": None
        },
        "uw_attribution_log": {
            "exists": UW_ATTRIBUTION_LOG.exists(),
            "records": 0,
            "recent_records": 0,
            "last_record_ts": None
        }
    }
    
    # Check attribution.jsonl
    if ATTRIBUTION_LOG.exists():
        records = load_jsonl(ATTRIBUTION_LOG)
        results["attribution_log"]["records"] = len(records)
        
        # Count recent records (last 7 days)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        recent = 0
        last_ts = None
        
        for rec in records:
            ts_str = rec.get("ts", "")
            if ts_str:
                try:
                    if "T" in ts_str:
                        rec_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    else:
                        rec_dt = datetime.fromtimestamp(int(ts_str))
                    
                    if rec_dt >= week_ago:
                        recent += 1
                    if last_ts is None or rec_dt > last_ts:
                        last_ts = rec_dt
                except:
                    pass
        
        results["attribution_log"]["recent_records"] = recent
        results["attribution_log"]["last_record_ts"] = last_ts.isoformat() if last_ts else None
    
    # Check uw_attribution.jsonl
    if UW_ATTRIBUTION_LOG.exists():
        records = load_jsonl(UW_ATTRIBUTION_LOG)
        results["uw_attribution_log"]["records"] = len(records)
        
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        recent = 0
        last_ts = None
        
        for rec in records:
            ts = rec.get("_ts", rec.get("ts", 0))
            if ts:
                try:
                    if isinstance(ts, str):
                        rec_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    else:
                        rec_dt = datetime.fromtimestamp(int(ts))
                    
                    if rec_dt >= week_ago:
                        recent += 1
                    if last_ts is None or rec_dt > last_ts:
                        last_ts = rec_dt
                except:
                    pass
        
        results["uw_attribution_log"]["recent_records"] = recent
        results["uw_attribution_log"]["last_record_ts"] = last_ts.isoformat() if last_ts else None
    
    return results

def check_learning_state() -> Dict[str, Any]:
    """Check learning system state"""
    results = {
        "weights_state_exists": WEIGHTS_STATE.exists(),
        "weights_loaded": False,
        "learning_log_exists": LEARNING_LOG.exists(),
        "learning_updates": 0,
        "last_update_ts": None,
        "component_samples": {},
        "multipliers": {},
        "errors": []
    }
    
    # Check weights state
    if WEIGHTS_STATE.exists():
        try:
            with open(WEIGHTS_STATE, 'r') as f:
                state = json.load(f)
            
            results["weights_loaded"] = True
            results["last_update_ts"] = state.get("saved_dt", state.get("saved_at"))
            
            # Extract component data
            entry_weights = state.get("entry_weights", {})
            weight_bands = entry_weights.get("weight_bands", {})
            
            for component, band_data in weight_bands.items():
                if isinstance(band_data, dict):
                    results["component_samples"][component] = {
                        "samples": band_data.get("sample_count", 0),
                        "wins": band_data.get("wins", 0),
                        "losses": band_data.get("losses", 0),
                        "multiplier": band_data.get("current", 1.0),
                        "ewma_win_rate": band_data.get("ewma_performance", 0.5)
                    }
                    results["multipliers"][component] = band_data.get("current", 1.0)
        except Exception as e:
            results["errors"].append(f"Failed to load weights state: {e}")
    
    # Check learning log
    if LEARNING_LOG.exists():
        records = load_jsonl(LEARNING_LOG)
        results["learning_updates"] = len(records)
        
        if records:
            last_update = records[-1]
            results["last_update_ts"] = last_update.get("ts")
            if isinstance(results["last_update_ts"], int):
                results["last_update_ts"] = datetime.fromtimestamp(results["last_update_ts"]).isoformat()
    
    # Check optimizer errors
    if OPTIMIZER_ERRORS.exists():
        errors = load_jsonl(OPTIMIZER_ERRORS)
        results["errors"].extend([e.get("error", "Unknown error") for e in errors[-10:]])  # Last 10 errors
    
    return results

def check_data_flow() -> Dict[str, Any]:
    """Check if data flows from logs to learning system"""
    results = {
        "trades_logged": 0,
        "trades_with_components": 0,
        "trades_fed_to_learning": 0,
        "missing_components": 0,
        "sample_breakdown": {}
    }
    
    # Load attribution logs
    attribution_records = load_jsonl(ATTRIBUTION_LOG)
    results["trades_logged"] = len([r for r in attribution_records if r.get("type") == "attribution"])
    
    # Check if trades have components
    for rec in attribution_records:
        if rec.get("type") != "attribution":
            continue
        
        context = rec.get("context", {})
        components = context.get("components", {})
        
        if components:
            results["trades_with_components"] += 1
        else:
            results["missing_components"] += 1
        
        # Check if this trade would be processed by learn_from_outcomes
        # (only processes today's trades)
        ts_str = rec.get("ts", "")
        if ts_str:
            try:
                if "T" in ts_str:
                    rec_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    rec_dt = datetime.fromtimestamp(int(ts_str))
                
                today = datetime.utcnow().date()
                if rec_dt.date() == today:
                    results["trades_fed_to_learning"] += 1
            except:
                pass
    
    # Check learning history size
    if WEIGHTS_STATE.exists():
        try:
            with open(WEIGHTS_STATE, 'r') as f:
                state = json.load(f)
            learner_data = state.get("learner", {})
            learning_history_count = learner_data.get("learning_history_count", 0)
            results["learning_history_size"] = learning_history_count
        except:
            results["learning_history_size"] = 0
    
    return results

def check_weight_updates() -> Dict[str, Any]:
    """Check if weights are actually being updated"""
    results = {
        "has_learned_weights": False,
        "components_with_samples": 0,
        "components_updated": 0,
        "update_frequency": "unknown",
        "recommendations": []
    }
    
    if not WEIGHTS_STATE.exists():
        results["recommendations"].append("No weights state file found - learning system may not be initialized")
        return results
    
    try:
        with open(WEIGHTS_STATE, 'r') as f:
            state = json.load(f)
        
        entry_weights = state.get("entry_weights", {})
        weight_bands = entry_weights.get("weight_bands", {})
        
        components_with_samples = 0
        components_updated = 0
        
        for component, band_data in weight_bands.items():
            if isinstance(band_data, dict):
                samples = band_data.get("sample_count", 0)
                multiplier = band_data.get("current", 1.0)
                
                if samples > 0:
                    components_with_samples += 1
                
                if multiplier != 1.0:
                    components_updated += 1
                    results["has_learned_weights"] = True
        
        results["components_with_samples"] = components_with_samples
        results["components_updated"] = components_updated
        
        # Check update frequency
        saved_at = state.get("saved_at", 0)
        if saved_at:
            try:
                if isinstance(saved_at, str):
                    saved_dt = datetime.fromisoformat(saved_at.replace("Z", "+00:00"))
                else:
                    saved_dt = datetime.fromtimestamp(int(saved_at))
                
                age = datetime.utcnow() - saved_dt
                if age.days == 0:
                    results["update_frequency"] = "today"
                elif age.days == 1:
                    results["update_frequency"] = "yesterday"
                elif age.days < 7:
                    results["update_frequency"] = f"{age.days} days ago"
                else:
                    results["update_frequency"] = f"{age.days} days ago (STALE)"
                    results["recommendations"].append(f"Weights haven't been updated in {age.days} days - learning may be broken")
            except:
                pass
        
        # Check if enough samples for updates
        if components_with_samples == 0:
            results["recommendations"].append("No components have samples - learning system is not processing trades")
        elif components_with_samples < 5:
            results["recommendations"].append(f"Only {components_with_samples} components have samples - may need more trades for learning")
        
        if components_updated == 0 and components_with_samples > 0:
            results["recommendations"].append("Components have samples but multipliers haven't changed - weight update logic may not be running")
        
    except Exception as e:
        results["recommendations"].append(f"Error checking weights: {e}")
    
    return results

def check_application() -> Dict[str, Any]:
    """Check if learned weights are being applied"""
    results = {
        "adaptive_optimizer_available": False,
        "weights_exported": False,
        "composite_using_adaptive": False,
        "recommendations": []
    }
    
    # Check if optimizer can be imported
    try:
        from adaptive_signal_optimizer import get_optimizer
        optimizer = get_optimizer()
        if optimizer:
            results["adaptive_optimizer_available"] = True
            
            # Check if weights are exported
            weights = optimizer.get_weights_for_composite()
            if weights:
                results["weights_exported"] = True
                results["exported_weights_count"] = len(weights)
            
            # Check if any multipliers are non-default
            multipliers = optimizer.get_multipliers_only()
            non_default = [k for k, v in multipliers.items() if v != 1.0]
            if non_default:
                results["non_default_multipliers"] = len(non_default)
            else:
                results["recommendations"].append("All multipliers are at default (1.0) - learning hasn't adjusted weights yet")
    except ImportError as e:
        results["recommendations"].append(f"Adaptive optimizer not available: {e}")
    except Exception as e:
        results["recommendations"].append(f"Error checking optimizer: {e}")
    
    # Check if composite scoring uses adaptive weights
    try:
        from uw_composite_v2 import get_adaptive_weights
        adaptive = get_adaptive_weights()
        if adaptive:
            results["composite_using_adaptive"] = True
        else:
            results["recommendations"].append("Composite scoring is not using adaptive weights")
    except:
        results["recommendations"].append("Cannot verify if composite scoring uses adaptive weights")
    
    return results

def generate_report() -> Dict[str, Any]:
    """Generate comprehensive learning pipeline report"""
    print("=" * 80)
    print("LEARNING PIPELINE VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "logs": check_logs_exist(),
        "learning_state": check_learning_state(),
        "data_flow": check_data_flow(),
        "weight_updates": check_weight_updates(),
        "application": check_application()
    }
    
    # Print summary
    print("1. LOG FILES")
    print("-" * 80)
    logs = report["logs"]
    print(f"  Attribution log exists: {logs['attribution_log']['exists']}")
    print(f"  Attribution records: {logs['attribution_log']['records']}")
    print(f"  Recent records (7 days): {logs['attribution_log']['recent_records']}")
    print(f"  Last record: {logs['attribution_log']['last_record_ts'] or 'N/A'}")
    print()
    print(f"  UW Attribution log exists: {logs['uw_attribution_log']['exists']}")
    print(f"  UW Attribution records: {logs['uw_attribution_log']['records']}")
    print(f"  Recent records (7 days): {logs['uw_attribution_log']['recent_records']}")
    print(f"  Last record: {logs['uw_attribution_log']['last_record_ts'] or 'N/A'}")
    print()
    
    print("2. LEARNING SYSTEM STATE")
    print("-" * 80)
    state = report["learning_state"]
    print(f"  Weights state exists: {state['weights_state_exists']}")
    print(f"  Weights loaded: {state['weights_loaded']}")
    print(f"  Learning log exists: {state['learning_log_exists']}")
    print(f"  Learning updates: {state['learning_updates']}")
    print(f"  Last update: {state['last_update_ts'] or 'N/A'}")
    print(f"  Components with data: {len(state['component_samples'])}")
    
    if state['component_samples']:
        print("\n  Component Samples:")
        for comp, data in sorted(state['component_samples'].items(), key=lambda x: x[1]['samples'], reverse=True)[:10]:
            print(f"    {comp:20s} samples={data['samples']:4d} wins={data['wins']:3d} losses={data['losses']:3d} "
                  f"mult={data['multiplier']:.2f} wr={data['ewma_win_rate']:.3f}")
    
    if state['errors']:
        print(f"\n  Errors ({len(state['errors'])}):")
        for err in state['errors'][:5]:
            print(f"    - {err}")
    print()
    
    print("3. DATA FLOW")
    print("-" * 80)
    flow = report["data_flow"]
    print(f"  Trades logged: {flow['trades_logged']}")
    print(f"  Trades with components: {flow['trades_with_components']}")
    print(f"  Trades missing components: {flow['missing_components']}")
    print(f"  Trades fed to learning (today): {flow['trades_fed_to_learning']}")
    print(f"  Learning history size: {flow.get('learning_history_size', 0)}")
    print()
    
    print("4. WEIGHT UPDATES")
    print("-" * 80)
    updates = report["weight_updates"]
    print(f"  Has learned weights: {updates['has_learned_weights']}")
    print(f"  Components with samples: {updates['components_with_samples']}")
    print(f"  Components updated: {updates['components_updated']}")
    print(f"  Update frequency: {updates['update_frequency']}")
    
    if updates['recommendations']:
        print("\n  Recommendations:")
        for rec in updates['recommendations']:
            print(f"    [WARNING] {rec}")
    print()
    
    print("5. WEIGHT APPLICATION")
    print("-" * 80)
    app = report["application"]
    print(f"  Adaptive optimizer available: {app['adaptive_optimizer_available']}")
    print(f"  Weights exported: {app['weights_exported']}")
    if app.get('exported_weights_count'):
        print(f"  Exported weights count: {app['exported_weights_count']}")
    if app.get('non_default_multipliers'):
        print(f"  Non-default multipliers: {app['non_default_multipliers']}")
    print(f"  Composite using adaptive: {app['composite_using_adaptive']}")
    
    if app['recommendations']:
        print("\n  Recommendations:")
        for rec in app['recommendations']:
            print(f"    [WARNING] {rec}")
    print()
    
    # Overall health
    print("6. OVERALL HEALTH")
    print("-" * 80)
    issues = []
    
    if not logs['attribution_log']['exists'] or logs['attribution_log']['records'] == 0:
        issues.append("No attribution logs found - trades may not be closing")
    
    if flow['missing_components'] > flow['trades_with_components']:
        issues.append(f"Most trades missing components ({flow['missing_components']} vs {flow['trades_with_components']})")
    
    if not state['weights_loaded']:
        issues.append("Learning system state not loaded")
    
    if updates['components_with_samples'] == 0:
        issues.append("No components have samples - learning not processing trades")
    
    if not app['adaptive_optimizer_available']:
        issues.append("Adaptive optimizer not available")
    
    if not app['composite_using_adaptive']:
        issues.append("Composite scoring not using adaptive weights")
    
    if issues:
        print("  [ISSUES FOUND]:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  [OK] Learning pipeline appears healthy")
    print()
    
    return report

if __name__ == "__main__":
    report = generate_report()
    
    # Save report
    report_file = Path("learning_pipeline_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Full report saved to: {report_file}")
    print()
    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. If logs are missing: Check that trades are closing and log_exit_attribution is called")
    print("2. If components missing: Verify components are stored in position metadata")
    print("3. If learning not running: Check that learn_from_outcomes() is called daily")
    print("4. If weights not updating: Verify update_weights() is called with enough samples (30+)")
    print("5. If weights not applied: Check that uw_composite_v2 uses get_adaptive_weights()")
    print()
