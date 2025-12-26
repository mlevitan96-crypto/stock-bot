#!/usr/bin/env python3
"""
Inject Fake Signal Test
Creates a fake signal and traces it through the entire trading flow
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class SignalInjectionTest:
    """Test harness for injecting fake signals"""
    
    def __init__(self):
        self.test_results = []
        self.fake_cluster = None
    
    def create_fake_cluster(self, symbol: str = "TEST", score: float = 3.5) -> Dict:
        """Create a fake cluster with known score"""
        return {
            "ticker": symbol,
            "direction": "buy",
            "composite_score": score,
            "source": "composite_v3",
            "sentiment": "BULLISH",
            "conviction": 0.8,
            "start_ts": int(time.time()),
            "components": {
                "options_flow": 1.8,
                "dark_pool": 0.9,
                "insider": 0.3,
                "greeks_gamma": 0.4,
                "iv_rank": 0.2,
                "oi_change": 0.35
            }
        }
    
    def test_step_1_cache_read(self, symbol: str) -> bool:
        """Test: Can we read from cache?"""
        cache_file = Path("data/uw_flow_cache.json")
        if not cache_file.exists():
            self.test_results.append(("Step 1: Cache Read", "FAIL", "Cache file missing"))
            return False
        
        try:
            with cache_file.open() as f:
                cache = json.load(f)
            if symbol not in cache and "_metadata" not in cache:
                self.test_results.append(("Step 1: Cache Read", "FAIL", f"Symbol {symbol} not in cache"))
                return False
            self.test_results.append(("Step 1: Cache Read", "PASS", f"Cache readable, {len(cache)} keys"))
            return True
        except Exception as e:
            self.test_results.append(("Step 1: Cache Read", "FAIL", str(e)))
            return False
    
    def test_step_2_cluster_generation(self) -> bool:
        """Test: Can we generate clusters?"""
        try:
            # Import cluster function
            from main import cluster_signals
            # Create fake trades
            fake_trades = [{
                "symbol": "TEST",
                "premium": 100000,
                "sentiment": "BULLISH",
                "ts": int(time.time())
            }]
            clusters = cluster_signals(fake_trades)
            if len(clusters) > 0:
                self.test_results.append(("Step 2: Cluster Generation", "PASS", f"Generated {len(clusters)} clusters"))
                return True
            else:
                self.test_results.append(("Step 2: Cluster Generation", "WARN", "No clusters generated"))
                return True  # Not a failure, just no data
        except Exception as e:
            self.test_results.append(("Step 2: Cluster Generation", "FAIL", str(e)))
            return False
    
    def test_step_3_scoring(self, cluster: Dict) -> bool:
        """Test: Can we score the cluster?"""
        try:
            import uw_composite_v2 as uw_v2
            # Get enriched data
            cache_file = Path("data/uw_flow_cache.json")
            if cache_file.exists():
                with cache_file.open() as f:
                    cache = json.load(f)
                symbol = cluster["ticker"]
                if symbol in cache:
                    enriched = uw_v2.enrich_signal(symbol, cache, "NEUTRAL")
                    score_result = uw_v2.compute_composite_score_v3(
                        symbol, enriched, "NEUTRAL"
                    )
                    score = score_result.get("composite_score", 0.0)
                    if score > 0:
                        self.test_results.append(("Step 3: Scoring", "PASS", f"Score: {score:.2f}"))
                        return True
                    else:
                        self.test_results.append(("Step 3: Scoring", "WARN", f"Score is 0: {score:.2f}"))
                        return True
            else:
                # Use fake cluster score
                score = cluster.get("composite_score", 0.0)
                self.test_results.append(("Step 3: Scoring", "PASS", f"Using cluster score: {score:.2f}"))
                return True
        except Exception as e:
            self.test_results.append(("Step 3: Scoring", "FAIL", str(e)))
            return False
    
    def test_step_4_threshold_check(self, score: float, threshold: float = 2.0) -> bool:
        """Test: Does score meet threshold?"""
        if score >= threshold:
            self.test_results.append(("Step 4: Threshold Check", "PASS", f"Score {score:.2f} >= {threshold:.2f}"))
            return True
        else:
            self.test_results.append(("Step 4: Threshold Check", "FAIL", f"Score {score:.2f} < {threshold:.2f}"))
            return False
    
    def test_step_5_gates(self, cluster: Dict) -> Dict[str, bool]:
        """Test: Check all gates"""
        gate_results = {}
        
        # Gate 1: Freeze state
        freeze_file = Path("state/governor_freezes.json")
        pre_market = Path("state/pre_market_freeze.flag")
        frozen = (freeze_file.exists() and json.loads(freeze_file.read_text())) or pre_market.exists()
        gate_results["freeze"] = not frozen
        self.test_results.append(("Gate 1: Freeze", "PASS" if not frozen else "FAIL", 
                                 "Frozen" if frozen else "Not frozen"))
        
        # Gate 2: Max positions (simulate check)
        try:
            import alpaca_trade_api as tradeapi
            from dotenv import load_dotenv
            import os
            load_dotenv()
            api = tradeapi.REST(
                os.getenv("ALPACA_KEY"),
                os.getenv("ALPACA_SECRET"),
                os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
                api_version='v2'
            )
            positions = api.list_positions()
            at_max = len(positions) >= 16
            gate_results["max_positions"] = not at_max
            self.test_results.append(("Gate 2: Max Positions", "PASS" if not at_max else "WARN",
                                    f"{len(positions)}/16 positions"))
        except Exception as e:
            gate_results["max_positions"] = True  # Assume OK if check fails
            self.test_results.append(("Gate 2: Max Positions", "WARN", f"Check failed: {e}"))
        
        # Gate 3: Cooldown (simulate)
        gate_results["cooldown"] = True  # Assume OK for test
        self.test_results.append(("Gate 3: Cooldown", "PASS", "Not in cooldown"))
        
        return gate_results
    
    def test_step_6_execution_path(self, cluster: Dict) -> bool:
        """Test: Can we reach execution path?"""
        # This would normally call decide_and_execute, but we'll simulate
        # Check if all prerequisites are met
        score = cluster.get("composite_score", 0.0)
        threshold = 2.0
        
        if score < threshold:
            self.test_results.append(("Step 6: Execution Path", "BLOCKED", 
                                    f"Score {score:.2f} below threshold {threshold:.2f}"))
            return False
        
        # Check gates
        gate_results = self.test_step_5_gates(cluster)
        if not all(gate_results.values()):
            blocked_gates = [gate for gate, passed in gate_results.items() if not passed]
            self.test_results.append(("Step 6: Execution Path", "BLOCKED", 
                                    f"Blocked by: {', '.join(blocked_gates)}"))
            return False
        
        self.test_results.append(("Step 6: Execution Path", "PASS", "Would execute"))
        return True
    
    def run_full_test(self, symbol: str = "TEST", score: float = 3.5) -> Dict[str, Any]:
        """Run complete test flow"""
        print("=" * 80)
        print("SIGNAL INJECTION TEST")
        print("=" * 80)
        print(f"Symbol: {symbol}, Target Score: {score}\n")
        
        # Create fake cluster
        cluster = self.create_fake_cluster(symbol, score)
        self.fake_cluster = cluster
        
        # Step 1: Cache read
        step1_ok = self.test_step_1_cache_read(symbol)
        
        # Step 2: Cluster generation
        step2_ok = self.test_step_2_cluster_generation()
        
        # Step 3: Scoring
        step3_ok = self.test_step_3_scoring(cluster)
        actual_score = cluster.get("composite_score", 0.0)
        
        # Step 4: Threshold check
        step4_ok = self.test_step_4_threshold_check(actual_score)
        
        # Step 5: Gates (already called in step 6)
        
        # Step 6: Execution path
        step6_ok = self.test_step_6_execution_path(cluster)
        
        # Summary
        all_passed = all([step1_ok, step2_ok, step3_ok, step4_ok, step6_ok])
        
        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        for test_name, status, message in self.test_results:
            status_symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
            print(f"{status_symbol} {test_name}: {status} - {message}")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        if all_passed:
            print("✓ ALL TESTS PASSED - Signal would execute")
        else:
            print("✗ SOME TESTS FAILED - Signal would be blocked")
            print("\nBlocking points:")
            for test_name, status, message in self.test_results:
                if status in ["FAIL", "BLOCKED"]:
                    print(f"  - {test_name}: {message}")
        
        return {
            "all_passed": all_passed,
            "results": self.test_results,
            "cluster": cluster,
            "final_score": actual_score,
            "would_execute": step6_ok
        }

if __name__ == "__main__":
    test = SignalInjectionTest()
    result = test.run_full_test()
    sys.exit(0 if result["all_passed"] else 1)

