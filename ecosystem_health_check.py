#!/usr/bin/env python3
"""
Ecosystem Health Check
======================
Verifies the complete feedback loop: Signals → Trading → Learning → Back to Signals

Checks:
1. Signals are computed and stored
2. Signals are used in trade decisions
3. Trades are executed and logged
4. Learning system processes outcomes
5. Adaptive weights are updated
6. Updated weights affect future scoring
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

def check_signals_computed() -> Dict[str, Any]:
    """Check if all required signals are computed and stored."""
    result = {
        "status": "healthy",
        "signals_checked": 0,
        "signals_missing": [],
        "signals_present": []
    }
    
    cache_file = DATA_DIR / "uw_flow_cache.json"
    if not cache_file.exists():
        result["status"] = "error"
        result["error"] = "Cache file not found"
        return result
    
    try:
        cache = json.loads(cache_file.read_text())
        symbols = [k for k in cache.keys() if not k.startswith("_")][:5]
        
        for symbol in symbols:
            data = cache.get(symbol, {})
            if not isinstance(data, dict):
                continue
            
            result["signals_checked"] += 1
            symbol_status = {}
            
            # Check required signals
            for signal in ["iv_term_skew", "smile_slope", "insider"]:
                if signal == "insider":
                    insider_data = data.get("insider")
                    has_insider = isinstance(insider_data, dict) and len(insider_data) > 0
                    symbol_status[signal] = has_insider
                    if has_insider:
                        result["signals_present"].append(f"{symbol}:{signal}")
                    else:
                        result["signals_missing"].append(f"{symbol}:{signal}")
                else:
                    value = data.get(signal)
                    # For numeric signals, 0.0 is valid - only None means missing
                    has_signal = value is not None
                    symbol_status[signal] = has_signal
                    if has_signal:
                        result["signals_present"].append(f"{symbol}:{signal}")
                    else:
                        result["signals_missing"].append(f"{symbol}:{signal}")
        
        if result["signals_missing"]:
            result["status"] = "degraded"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_signals_used_in_scoring() -> Dict[str, Any]:
    """Verify signals are used in composite scoring."""
    result = {
        "status": "healthy",
        "signals_used": []
    }
    
    try:
        # Check if composite scoring imports and uses signals
        import uw_composite_v2 as uw_v2
        
        # Verify weights include our signals
        weights = uw_v2.WEIGHTS_V3
        required_signals = ["insider", "iv_term_skew", "smile_slope"]
        
        for signal in required_signals:
            if signal in weights:
                result["signals_used"].append(signal)
        
        if len(result["signals_used"]) < len(required_signals):
            result["status"] = "degraded"
            result["missing_in_weights"] = [s for s in required_signals if s not in result["signals_used"]]
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_trades_logged() -> Dict[str, Any]:
    """Check if trades are being logged for learning."""
    result = {
        "status": "healthy",
        "attribution_log_exists": False,
        "feature_store_exists": False,
        "recent_trades": 0,
        "last_trade_age_sec": None
    }
    
    # Check attribution log
    attribution_file = DATA_DIR / "attribution.jsonl"
    if attribution_file.exists():
        result["attribution_log_exists"] = True
        try:
            with attribution_file.open("r") as f:
                lines = f.readlines()
                if lines:
                    # Get last trade
                    last_line = lines[-1]
                    last_trade = json.loads(last_line)
                    trade_ts = last_trade.get("ts", "")
                    if isinstance(trade_ts, str) and len(trade_ts) > 10:
                        # Parse timestamp
                        try:
                            trade_dt = datetime.fromisoformat(trade_ts.replace("Z", "+00:00"))
                            result["last_trade_age_sec"] = (datetime.now(trade_dt.tzinfo) - trade_dt).total_seconds()
                        except:
                            pass
                    
                    # Count recent trades (last 24h)
                    cutoff = time.time() - 86400
                    for line in lines[-100:]:  # Check last 100 lines
                        try:
                            trade = json.loads(line)
                            trade_ts_val = trade.get("ts", "")
                            if isinstance(trade_ts_val, str):
                                try:
                                    trade_dt = datetime.fromisoformat(trade_ts_val.replace("Z", "+00:00"))
                                    if (datetime.now(trade_dt.tzinfo) - trade_dt).total_seconds() < 86400:
                                        result["recent_trades"] += 1
                                except:
                                    pass
                        except:
                            pass
        except Exception as e:
            result["error"] = str(e)
    
    # Check feature store
    feature_store = DATA_DIR / "feature_store.jsonl"
    if feature_store.exists():
        result["feature_store_exists"] = True
    
    if not result["attribution_log_exists"] and not result["feature_store_exists"]:
        result["status"] = "degraded"
        result["warning"] = "No trade logs found - learning may not be active"
    
    return result

def check_learning_active() -> Dict[str, Any]:
    """Check if learning system is processing outcomes."""
    result = {
        "status": "healthy",
        "adaptive_optimizer_available": False,
        "weights_file_exists": False,
        "learning_samples": 0,
        "weights_last_updated": None
    }
    
    try:
        from adaptive_signal_optimizer import get_optimizer
        optimizer = get_optimizer()
        
        if optimizer:
            result["adaptive_optimizer_available"] = True
            
            # Get learning report
            try:
                report = optimizer.get_report()
                result["learning_samples"] = report.get("learning_samples", 0)
                
                # Check component performance
                comp_perf = report.get("component_performance", {})
                if comp_perf:
                    result["components_tracked"] = len(comp_perf)
            except:
                pass
    
    except ImportError:
        result["status"] = "degraded"
        result["warning"] = "Adaptive optimizer not available"
    except Exception as e:
        result["error"] = str(e)
    
    # Check weights state file
    weights_file = STATE_DIR / "signal_weights.json"
    if weights_file.exists():
        result["weights_file_exists"] = True
        try:
            weights_data = json.loads(weights_file.read_text())
            last_updated = weights_data.get("last_updated", 0)
            if last_updated:
                result["weights_last_updated"] = time.time() - last_updated
        except:
            pass
    
    return result

def check_adaptive_weights_used() -> Dict[str, Any]:
    """Verify adaptive weights are being used in scoring."""
    result = {
        "status": "healthy",
        "adaptive_weights_active": False,
        "weights_loaded": False,
        "sample_weights": {}
    }
    
    try:
        import uw_composite_v2 as uw_v2
        
        # Try to get adaptive weights
        adaptive_weights = uw_v2.get_adaptive_weights()
        
        if adaptive_weights:
            result["adaptive_weights_active"] = True
            result["weights_loaded"] = True
            result["sample_weights"] = dict(list(adaptive_weights.items())[:5])
        else:
            result["status"] = "degraded"
            result["warning"] = "Adaptive weights not loaded - using static weights"
    
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_feedback_loop_complete() -> Dict[str, Any]:
    """Verify the complete feedback loop is working."""
    result = {
        "status": "healthy",
        "cycle_stages": {
            "signals_computed": False,
            "signals_used": False,
            "trades_logged": False,
            "learning_active": False,
            "weights_updated": False,
            "weights_used": False
        },
        "issues": []
    }
    
    # Check each stage
    signals_check = check_signals_computed()
    result["cycle_stages"]["signals_computed"] = signals_check["status"] == "healthy"
    if signals_check["status"] != "healthy":
        result["issues"].append(f"Signals: {signals_check.get('error', 'missing signals')}")
    
    scoring_check = check_signals_used_in_scoring()
    result["cycle_stages"]["signals_used"] = scoring_check["status"] == "healthy"
    if scoring_check["status"] != "healthy":
        result["issues"].append(f"Scoring: {scoring_check.get('error', 'signals not used')}")
    
    trades_check = check_trades_logged()
    result["cycle_stages"]["trades_logged"] = trades_check.get("recent_trades", 0) > 0 or trades_check.get("attribution_log_exists", False)
    if not result["cycle_stages"]["trades_logged"]:
        result["issues"].append("No recent trades logged")
    
    learning_check = check_learning_active()
    result["cycle_stages"]["learning_active"] = learning_check.get("adaptive_optimizer_available", False)
    if not result["cycle_stages"]["learning_active"]:
        result["issues"].append("Learning system not active")
    
    result["cycle_stages"]["weights_updated"] = learning_check.get("learning_samples", 0) > 0
    if not result["cycle_stages"]["weights_updated"]:
        result["issues"].append("No learning samples - weights may not be updating")
    
    weights_check = check_adaptive_weights_used()
    result["cycle_stages"]["weights_used"] = weights_check.get("adaptive_weights_active", False)
    if not result["cycle_stages"]["weights_used"]:
        result["issues"].append("Adaptive weights not being used in scoring")
    
    # Overall status
    all_stages_healthy = all(result["cycle_stages"].values())
    if not all_stages_healthy:
        result["status"] = "degraded"
        if result["issues"]:
            result["status"] = "critical"
    
    return result

def main():
    """Run complete ecosystem health check."""
    print("=" * 80)
    print("ECOSYSTEM HEALTH CHECK")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")
    
    # Run all checks
    checks = {
        "1. Signals Computed": check_signals_computed(),
        "2. Signals Used in Scoring": check_signals_used_in_scoring(),
        "3. Trades Logged": check_trades_logged(),
        "4. Learning Active": check_learning_active(),
        "5. Adaptive Weights Used": check_adaptive_weights_used(),
        "6. Complete Feedback Loop": check_feedback_loop_complete()
    }
    
    for name, result in checks.items():
        status = result.get("status", "unknown")
        status_icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
        
        print(f"{status_icon} {name}: {status.upper()}")
        
        if result.get("error"):
            print(f"   Error: {result['error']}")
        if result.get("warning"):
            print(f"   Warning: {result['warning']}")
        if result.get("issues"):
            for issue in result["issues"]:
                print(f"   Issue: {issue}")
        
        # Print key metrics
        if "signals_present" in result:
            print(f"   Signals present: {len(result['signals_present'])}")
        if "recent_trades" in result:
            print(f"   Recent trades: {result['recent_trades']}")
        if "learning_samples" in result:
            print(f"   Learning samples: {result['learning_samples']}")
        if "adaptive_weights_active" in result and result["adaptive_weights_active"]:
            print(f"   Adaptive weights: ACTIVE")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    feedback_loop = checks["6. Complete Feedback Loop"]
    stages = feedback_loop.get("cycle_stages", {})
    
    for stage, healthy in stages.items():
        icon = "✅" if healthy else "❌"
        print(f"{icon} {stage.replace('_', ' ').title()}")
    
    overall_status = feedback_loop.get("status", "unknown")
    print(f"\nOverall Ecosystem Status: {overall_status.upper()}")
    
    if feedback_loop.get("issues"):
        print("\nIssues to address:")
        for issue in feedback_loop["issues"]:
            print(f"  - {issue}")

if __name__ == "__main__":
    main()
