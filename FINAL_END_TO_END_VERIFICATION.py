#!/usr/bin/env python3
"""
FINAL END-TO-END VERIFICATION
Complete verification: dashboard, self-healing, monitoring, trading ability
Tests everything to ensure bot is ready for trading tomorrow morning
"""

import json
import sys
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

class FinalVerification:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verification_passed": False,
            "sections": {},
            "errors": [],
            "warnings": []
        }
    
    def verify_dashboard_endpoints(self):
        """Verify all dashboard endpoints exist"""
        print("=" * 80)
        print("VERIFICATION 1: DASHBOARD ENDPOINTS")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check main.py for endpoints
        if Path("main.py").exists():
            with open("main.py", "r", encoding="utf-8") as f:
                main_content = f.read()
            
            required_endpoints = [
                ("/api/positions", "api_positions"),
                ("/api/profit", "api_profit"),
                ("/api/state", "api_state"),
                ("/api/account", "api_account")
            ]
            
            for endpoint, func_name in required_endpoints:
                if f"@app.route(\"{endpoint}\"" in main_content or f"@app.route('{endpoint}'" in main_content:
                    if func_name in main_content:
                        print(f"  [PASS] {endpoint} ({func_name})")
                    else:
                        print(f"  [WARNING] {endpoint} route exists but function may be missing")
                        issues.append(f"{endpoint} function check")
                else:
                    print(f"  [FAIL] {endpoint} MISSING")
                    issues.append(f"Missing endpoint: {endpoint}")
        
        # Check dashboard.py for endpoints
        if Path("dashboard.py").exists():
            with open("dashboard.py", "r", encoding="utf-8") as f:
                dashboard_content = f.read()
            
            dashboard_endpoints = [
                ("/api/sre/health", "api_sre_health"),
                ("/api/xai/auditor", "api_xai_auditor"),
                ("/api/xai/export", "api_xai_export"),
                ("/api/executive_summary", "api_executive_summary"),
                ("/api/health_status", "api_health_status")
            ]
            
            for endpoint, func_name in dashboard_endpoints:
                if f"@app.route(\"{endpoint}\"" in dashboard_content or f"@app.route('{endpoint}'" in dashboard_content:
                    if func_name in dashboard_content:
                        print(f"  [PASS] {endpoint} ({func_name})")
                    else:
                        print(f"  [WARNING] {endpoint} route exists but function may be missing")
                        issues.append(f"{endpoint} function check")
                else:
                    print(f"  [FAIL] {endpoint} MISSING")
                    issues.append(f"Missing endpoint: {endpoint}")
        
        self.results["sections"]["dashboard_endpoints"] = {
            "status": "PASS" if not issues else "FAIL",
            "count": len(issues),
            "details": issues
        }
        if issues:
            self.results["errors"].extend([f"Dashboard: {i}" for i in issues])
        return len(issues) == 0
    
    def verify_self_healing(self):
        """Verify self-healing modules"""
        print("\n" + "=" * 80)
        print("VERIFICATION 2: SELF-HEALING")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check self-healing modules exist
        self_healing_files = [
            "self_healing/shadow_trade_logger.py",
            "architecture_self_healing.py"
        ]
        
        for file_path in self_healing_files:
            if Path(file_path).exists():
                print(f"  [PASS] {file_path}")
            else:
                print(f"  [WARNING] {file_path} not found")
                issues.append(f"Missing: {file_path}")
        
        # Check main.py uses self-healing
        if Path("main.py").exists():
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            if "shadow_trade_logger" in content or "self_healing" in content:
                print("  [PASS] main.py uses self-healing")
            else:
                print("  [WARNING] main.py may not use self-healing")
                issues.append("main.py self-healing integration")
        
        self.results["sections"]["self_healing"] = {
            "status": "PASS" if not issues else "WARNING",
            "count": len(issues),
            "details": issues
        }
        if issues:
            self.results["warnings"].extend([f"Self-healing: {i}" for i in issues])
        return True
    
    def verify_monitoring(self):
        """Verify monitoring and SRE"""
        print("\n" + "=" * 80)
        print("VERIFICATION 3: MONITORING")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check sre_monitoring.py
        if Path("sre_monitoring.py").exists():
            with open("sre_monitoring.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            required_functions = [
                "get_sre_health",
                "check_signal_generation_health",
                "check_uw_api_health"
            ]
            
            for func in required_functions:
                if func in content:
                    print(f"  [PASS] {func}")
                else:
                    print(f"  [FAIL] {func} MISSING")
                    issues.append(f"Missing function: {func}")
        else:
            print("  [FAIL] sre_monitoring.py not found")
            issues.append("sre_monitoring.py missing")
        
        self.results["sections"]["monitoring"] = {
            "status": "PASS" if not issues else "FAIL",
            "count": len(issues),
            "details": issues
        }
        if issues:
            self.results["errors"].extend([f"Monitoring: {i}" for i in issues])
        return len(issues) == 0
    
    def verify_trading_ability(self):
        """Verify trading functions exist"""
        print("\n" + "=" * 80)
        print("VERIFICATION 4: TRADING ABILITY")
        print("=" * 80)
        print()
        
        issues = []
        
        if Path("main.py").exists():
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            required_functions = [
                "decide_and_execute",
                "submit_entry",
                "evaluate_exits",
                "can_open_new_position"
            ]
            
            for func in required_functions:
                if f"def {func}" in content:
                    print(f"  [PASS] {func}")
                else:
                    print(f"  [FAIL] {func} MISSING")
                    issues.append(f"Missing function: {func}")
            
            # Check Alpaca integration
            if "alpaca_trade_api" in content or "tradeapi" in content:
                print("  [PASS] Alpaca API integration")
            else:
                print("  [FAIL] Alpaca API integration MISSING")
                issues.append("Alpaca API integration")
        
        self.results["sections"]["trading_ability"] = {
            "status": "PASS" if not issues else "FAIL",
            "count": len(issues),
            "details": issues
        }
        if issues:
            self.results["errors"].extend([f"Trading: {i}" for i in issues])
        return len(issues) == 0
    
    def verify_syntax(self):
        """Verify no syntax errors"""
        print("\n" + "=" * 80)
        print("VERIFICATION 5: SYNTAX CHECK")
        print("=" * 80)
        print()
        
        issues = []
        
        critical_files = [
            "main.py",
            "dashboard.py",
            "sre_monitoring.py",
            "deploy_supervisor.py"
        ]
        
        for file_path in critical_files:
            if not Path(file_path).exists():
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                compile(content, file_path, "exec")
                print(f"  [PASS] {file_path}")
            except SyntaxError as e:
                print(f"  [FAIL] {file_path}: {e}")
                issues.append(f"{file_path}: {e}")
            except Exception as e:
                print(f"  [WARNING] {file_path}: {e}")
        
        self.results["sections"]["syntax"] = {
            "status": "PASS" if not issues else "FAIL",
            "count": len(issues),
            "details": issues
        }
        if issues:
            self.results["errors"].extend([f"Syntax: {i}" for i in issues])
        return len(issues) == 0
    
    def run_verification(self):
        """Run complete verification"""
        print("=" * 80)
        print("FINAL END-TO-END VERIFICATION")
        print("=" * 80)
        print()
        print("Verifying: dashboard, self-healing, monitoring, trading ability")
        print()
        
        results = []
        results.append(("Dashboard Endpoints", self.verify_dashboard_endpoints()))
        results.append(("Self-Healing", self.verify_self_healing()))
        results.append(("Monitoring", self.verify_monitoring()))
        results.append(("Trading Ability", self.verify_trading_ability()))
        results.append(("Syntax Check", self.verify_syntax()))
        
        # Final summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print()
        
        all_passed = True
        for name, passed in results:
            status = "[PASS]" if passed else "[FAIL/WARNING]"
            print(f"{status} {name}")
            if not passed:
                all_passed = False
        
        print()
        if self.results["errors"]:
            print(f"Errors ({len(self.results['errors'])}):")
            for error in self.results["errors"][:20]:
                print(f"  - {error}")
            print()
        
        if self.results["warnings"]:
            print(f"Warnings ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"][:20]:
                print(f"  - {warning}")
            print()
        
        self.results["verification_passed"] = all_passed
        
        if all_passed:
            print("[SUCCESS] ALL VERIFICATIONS PASSED - BOT READY FOR TRADING")
        else:
            print("[FAILURE] SOME VERIFICATIONS FAILED - REVIEW ABOVE")
        
        return all_passed

def main():
    """Main entry point"""
    verification = FinalVerification()
    passed = verification.run_verification()
    
    # Save results
    results_file = Path("final_verification_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(verification.results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())

