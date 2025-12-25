#!/usr/bin/env python3
"""
Complete Droplet Verification - Runs on droplet to verify all implementations
This script is pushed to git, pulled by droplet, runs verification, and pushes results back.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

def run_verification():
    """Run complete verification and return results"""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verification_passed": False,
        "tests": {},
        "errors": []
    }
    
    print("=" * 80)
    print("COMPLETE DROPLET VERIFICATION")
    print("=" * 80)
    print()
    
    # Test 1: Verify all files exist
    print("Test 1: Verifying all implementation files exist...")
    required_files = [
        "tca_data_manager.py",
        "execution_quality_learner.py",
        "signal_pattern_learner.py",
        "parameter_optimizer.py",
        "backtest_all_implementations.py",
        "deploy_and_verify_on_droplet.sh"
    ]
    
    files_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"  [PASS] {file}")
            results["tests"][f"file_{file}"] = "PASS"
        else:
            print(f"  [FAIL] {file} MISSING")
            results["tests"][f"file_{file}"] = "FAIL"
            results["errors"].append(f"Missing file: {file}")
            files_exist = False
    
    if not files_exist:
        results["errors"].append("Some required files are missing")
        return results
    
    # Test 2: Run backtest
    print("\nTest 2: Running comprehensive backtest...")
    try:
        result = subprocess.run(
            ["python3", "backtest_all_implementations.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  [PASS] Backtest passed")
            results["tests"]["backtest"] = "PASS"
        else:
            print(f"  [FAIL] Backtest failed: {result.stderr[:200]}")
            results["tests"]["backtest"] = "FAIL"
            results["errors"].append(f"Backtest failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"  [FAIL] Backtest error: {e}")
        results["tests"]["backtest"] = "FAIL"
        results["errors"].append(f"Backtest error: {e}")
    
    # Test 3: Verify imports
    print("\nTest 3: Verifying Python imports...")
    import_tests = {
        "tca_data_manager": "from tca_data_manager import get_recent_slippage",
        "execution_quality_learner": "from execution_quality_learner import get_execution_learner",
        "signal_pattern_learner": "from signal_pattern_learner import get_signal_pattern_learner",
        "parameter_optimizer": "from parameter_optimizer import get_parameter_optimizer"
    }
    
    for name, import_stmt in import_tests.items():
        try:
            exec(import_stmt)
            print(f"  [PASS] {name}")
            results["tests"][f"import_{name}"] = "PASS"
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            results["tests"][f"import_{name}"] = "FAIL"
            results["errors"].append(f"Import failed {name}: {e}")
    
    # Test 4: Verify main.py integration
    print("\nTest 4: Verifying main.py integration...")
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            checks = {
                "tca_integration": "get_recent_slippage" in content,
                "regime_forecast": "get_regime_forecast_modifier" in content,
                "toxicity": "get_toxicity_sentinel_score" in content,
                "execution_tracking": "track_execution_failure" in content,
                "experiment_params": "promoted_to_prod" in content or "parameters_copied" in content
            }
            for check_name, passed in checks.items():
                if passed:
                    print(f"  [PASS] {check_name}")
                    results["tests"][f"main_{check_name}"] = "PASS"
                else:
                    print(f"  [FAIL] {check_name}")
                    results["tests"][f"main_{check_name}"] = "FAIL"
                    results["errors"].append(f"main.py missing: {check_name}")
    except Exception as e:
        print(f"  [FAIL] Error reading main.py: {e}")
        results["errors"].append(f"Error reading main.py: {e}")
    
    # Test 5: Verify learning orchestrator integration
    print("\nTest 5: Verifying learning orchestrator integration...")
    try:
        with open("comprehensive_learning_orchestrator_v2.py", "r", encoding="utf-8") as f:
            content = f.read()
            checks = {
                "execution_quality": "execution_quality_learner" in content,
                "signal_patterns": "signal_pattern_learner" in content,
                "counterfactual": "compute_counterfactual_pnl" in content
            }
            for check_name, passed in checks.items():
                if passed:
                    print(f"  [PASS] {check_name}")
                    results["tests"][f"orchestrator_{check_name}"] = "PASS"
                else:
                    print(f"  [FAIL] {check_name}")
                    results["tests"][f"orchestrator_{check_name}"] = "FAIL"
                    results["errors"].append(f"orchestrator missing: {check_name}")
    except Exception as e:
        print(f"  [FAIL] Error reading orchestrator: {e}")
        results["errors"].append(f"Error reading orchestrator: {e}")
    
    # Determine overall status
    all_passed = all(
        status == "PASS" 
        for status in results["tests"].values()
    )
    results["verification_passed"] = all_passed
    
    print("\n" + "=" * 80)
    if all_passed:
        print("[SUCCESS] ALL VERIFICATIONS PASSED")
    else:
        print(f"[FAILURE] {len(results['errors'])} VERIFICATION(S) FAILED")
    print("=" * 80)
    
    return results

def main():
    """Main entry point"""
    results = run_verification()
    
    # Save results
    results_file = Path("droplet_verification_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    # Push results to git
    print("\nPushing results to git...")
    try:
        subprocess.run(["git", "add", str(results_file)], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Droplet verification results - {datetime.now(timezone.utc).isoformat()}"],
            check=True
        )
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("  [PASS] Results pushed to git")
    except Exception as e:
        print(f"  [WARNING] Could not push to git: {e}")
        print("  Results saved locally - manual push may be needed")
    
    return 0 if results["verification_passed"] else 1

if __name__ == "__main__":
    sys.exit(main())

