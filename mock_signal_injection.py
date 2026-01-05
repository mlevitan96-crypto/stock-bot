#!/usr/bin/env python3
"""
Mock Signal Injection - SRE Sentinel Diagnostic Loop
=====================================================
Injects a "Perfect Whale Signal" every 15 minutes to verify scoring integrity.

If the mock signal scores < 4.0, triggers RCA and updates sre_metrics.json.
"""

import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

STATE_DIR = Path("state")
DATA_DIR = Path("data")

def inject_perfect_whale_signal():
    """
    Inject a perfect whale signal and test scoring.
    
    Creates a perfect signal:
    - High conviction (0.95)
    - High magnitude (HIGH)
    - BULLISH_SWEEP signal_type
    - Should score > 4.0 if scoring is working correctly
    
    Returns: (score: float, success: bool)
    """
    try:
        # Import scoring functions
        from uw_composite_v2 import compute_composite_score_v3
        
        # Create perfect whale signal data
        perfect_signal = {
            "sentiment": "BULLISH",
            "conviction": 0.95,
            "dark_pool": {
                "sentiment": "BULLISH",
                "total_premium": 5_000_000.0,  # High premium
                "print_count": 10
            },
            "insider": {
                "sentiment": "BULLISH",
                "net_buys": 1000,
                "net_sells": 100,
                "total_usd": 10_000_000.0
            },
            "flow_conv": 0.95,
            "flow_magnitude": "HIGH",
            "signal_type": "BULLISH_SWEEP"
        }
        
        # Score the perfect signal
        result = compute_composite_score_v3(
            symbol="MOCK_SIGNAL_TEST",
            enriched_data=perfect_signal,
            regime="BULLISH",
            use_adaptive_weights=False  # Use base weights for consistency
        )
        
        if result and result.get("score"):
            score = float(result.get("score", 0.0))
            success = score >= 4.0
            return score, success
        else:
            return 0.0, False
            
    except Exception as e:
        print(f"[MOCK-SIGNAL] Error injecting mock signal: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return 0.0, False

def update_sre_metrics_from_mock_signal(score: float, success: bool):
    """Update SRE metrics based on mock signal test result."""
    try:
        from sre_diagnostics import get_sre_metrics, update_sre_metrics
        
        metrics = get_sre_metrics()
        
        # Update mock signal success percentage (rolling average)
        current_success_pct = metrics.get("mock_signal_success_pct", 100.0)
        # Simple moving average (last 10 tests)
        if success:
            new_success_pct = min(100.0, current_success_pct + 1.0)
        else:
            new_success_pct = max(0.0, current_success_pct - 10.0)  # Penalty for failure
        
        # Update parser health index (based on score)
        if score >= 4.0:
            parser_health = 100.0
        elif score >= 3.0:
            parser_health = 75.0
        elif score >= 2.0:
            parser_health = 50.0
        else:
            parser_health = 25.0
        
        # Update logic heartbeat (timestamp)
        logic_heartbeat = time.time()
        
        update_sre_metrics({
            "logic_heartbeat": logic_heartbeat,
            "mock_signal_success_pct": new_success_pct,
            "parser_health_index": parser_health,
            "last_mock_signal_score": score,
            "last_mock_signal_time": datetime.now(timezone.utc).isoformat()
        })
        
        if not success:
            print(f"[MOCK-SIGNAL] ⚠️ Mock signal failed: score={score:.2f} (< 4.0) - triggering RCA", flush=True)
            # Trigger RCA
            try:
                from sre_diagnostics import SREDiagnostics
                diag = SREDiagnostics()
                session = diag.run_rca(trigger="mock_signal_failure")
                
                # Update auto-fix count
                auto_fix_count = metrics.get("auto_fix_count", 0) + len(session.fixes_applied)
                update_sre_metrics({"auto_fix_count": auto_fix_count})
                
                print(f"[MOCK-SIGNAL] RCA completed: {session.overall_status}, fixes={session.fixes_applied}", flush=True)
            except Exception as e:
                print(f"[MOCK-SIGNAL] Error running RCA: {e}", flush=True)
        else:
            print(f"[MOCK-SIGNAL] ✅ Mock signal passed: score={score:.2f} (>= 4.0)", flush=True)
            
    except Exception as e:
        print(f"[MOCK-SIGNAL] Error updating metrics: {e}", flush=True)
        import traceback
        traceback.print_exc()

def run_mock_signal_loop():
    """Background thread loop that injects mock signals every 15 minutes."""
    print("[MOCK-SIGNAL] Mock signal injection loop started (every 15 minutes)", flush=True)
    
    while True:
        try:
            time.sleep(15 * 60)  # Wait 15 minutes
            
            print(f"[MOCK-SIGNAL] Injecting perfect whale signal at {datetime.now(timezone.utc).isoformat()}", flush=True)
            score, success = inject_perfect_whale_signal()
            update_sre_metrics_from_mock_signal(score, success)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[MOCK-SIGNAL] Error in mock signal loop: {e}", flush=True)
            import traceback
            traceback.print_exc()
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    # Test injection
    print("Testing mock signal injection...")
    score, success = inject_perfect_whale_signal()
    print(f"Score: {score:.2f}, Success: {success}")
    update_sre_metrics_from_mock_signal(score, success)
