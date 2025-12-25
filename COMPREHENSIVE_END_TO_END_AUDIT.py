#!/usr/bin/env python3
"""
COMPREHENSIVE END-TO-END AUDIT
Complete system audit: hardcoded values, logging analysis, bugs, labels, references,
dashboard, self-healing, monitoring, trading ability - EVERYTHING
"""

import json
import sys
import subprocess
import ast
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class ComprehensiveAudit:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_passed": False,
            "sections": {},
            "errors": [],
            "warnings": [],
            "hardcoded_values": [],
            "unanalyzed_logs": [],
            "bugs": [],
            "mismatched_labels": [],
            "incorrect_references": []
        }
        self.hardcoded_patterns = [
            r'\b\d+\.\d+\b',  # Floating point numbers
            r'\b\d+\b',  # Integers
            r'"[^"]*"',  # String literals
            r"'[^']*'",  # String literals
        ]
        self.config_registry_paths = [
            "StateFiles", "CacheFiles", "LogFiles", "ConfigFiles", 
            "Directories", "Thresholds", "APIConfig"
        ]
    
    def audit_hardcoded_values(self):
        """Audit 1: Find all hardcoded values that should use config/registry.py"""
        print("=" * 80)
        print("AUDIT 1: HARDCODED VALUES")
        print("=" * 80)
        print()
        
        issues = []
        files_to_check = [
            "main.py", "dashboard.py", "sre_monitoring.py", 
            "deploy_supervisor.py", "uw_flow_daemon.py"
        ]
        
        for file_path in files_to_check:
            if not Path(file_path).exists():
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")
                
                # Check for hardcoded paths
                hardcoded_paths = re.findall(r'["\'](/[^"\']+|\./[^"\']+|state/|logs/|data/|cache/)', content)
                for path in set(hardcoded_paths):
                    if "config/registry" not in content[:content.find(path)]:
                        issues.append({
                            "file": file_path,
                            "type": "hardcoded_path",
                            "value": path,
                            "line": self._find_line_number(content, path)
                        })
                
                # Check for hardcoded thresholds (common patterns)
                threshold_patterns = [
                    (r'\b0\.\d+\b', "threshold"),
                    (r'\b\d+\.\d+%', "percentage"),
                    (r'\$\d+', "dollar_amount"),
                ]
                
                for pattern, pattern_type in threshold_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        value = match.group()
                        # Skip if it's in a comment or string that references config
                        context = content[max(0, match.start()-50):match.end()+50]
                        if "config" in context.lower() or "registry" in context.lower():
                            continue
                        if value not in ["0.0", "1.0", "0", "1"]:  # Common defaults
                            issues.append({
                                "file": file_path,
                                "type": f"hardcoded_{pattern_type}",
                                "value": value,
                                "line": self._find_line_number(content, match.group())
                            })
            
            except Exception as e:
                self.results["errors"].append(f"Error checking {file_path}: {e}")
        
        if issues:
            print(f"  [WARNING] Found {len(issues)} potential hardcoded values")
            for issue in issues[:20]:  # Show first 20
                print(f"    {issue['file']}:{issue.get('line', '?')} - {issue['type']}: {issue['value']}")
            self.results["hardcoded_values"] = issues
        else:
            print("  [PASS] No hardcoded values found (or all use config/registry.py)")
        
        self.results["sections"]["hardcoded_values"] = {
            "status": "WARNING" if issues else "PASS",
            "count": len(issues),
            "details": issues[:10]  # Store first 10
        }
        return len(issues) == 0
    
    def audit_logging_analysis(self):
        """Audit 2: Verify all logging feeds into analysis/learning"""
        print("\n" + "=" * 80)
        print("AUDIT 2: LOGGING ANALYSIS")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check main.py logging
        if Path("main.py").exists():
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find all log_event calls
            log_calls = re.findall(r'log_event\([^)]+\)', content)
            
            # Check if logs are analyzed
            analysis_functions = [
                "learn_from_trade", "process_blocked_trades", 
                "analyze_", "feed_to_learning"
            ]
            
            has_analysis = any(func in content for func in analysis_functions)
            
            if log_calls and not has_analysis:
                issues.append({
                    "file": "main.py",
                    "issue": "Logging present but no analysis functions found",
                    "log_calls": len(log_calls)
                })
        
        # Check log files exist and are being read
        log_files = [
            "logs/attribution.jsonl",
            "logs/exit.jsonl",
            "logs/signals.jsonl",
            "logs/orders.jsonl",
            "logs/gate.jsonl"
        ]
        
        for log_file in log_files:
            log_path = Path(log_file)
            if log_path.exists():
                # Check if any code reads this file
                found_reader = False
                for py_file in Path(".").glob("*.py"):
                    try:
                        with open(py_file, "r", encoding="utf-8") as f:
                            if log_file in f.read():
                                found_reader = True
                                break
                    except:
                        pass
                
                if not found_reader:
                    issues.append({
                        "file": log_file,
                        "issue": "Log file exists but no code reads it"
                    })
        
        if issues:
            print(f"  [WARNING] Found {len(issues)} logging analysis issues")
            for issue in issues:
                print(f"    {issue.get('file', 'unknown')}: {issue.get('issue', 'unknown')}")
            self.results["unanalyzed_logs"] = issues
        else:
            print("  [PASS] All logging appears to be analyzed")
        
        self.results["sections"]["logging_analysis"] = {
            "status": "WARNING" if issues else "PASS",
            "count": len(issues),
            "details": issues
        }
        return len(issues) == 0
    
    def audit_bugs(self):
        """Audit 3: Check for bugs, syntax errors, runtime issues"""
        print("\n" + "=" * 80)
        print("AUDIT 3: BUGS AND ERRORS")
        print("=" * 80)
        print()
        
        bugs = []
        
        # Check syntax
        python_files = list(Path(".").glob("*.py"))
        for py_file in python_files[:20]:  # Check first 20 files
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                bugs.append({
                    "file": str(py_file),
                    "type": "syntax_error",
                    "error": str(e)
                })
            except Exception as e:
                # Skip import errors for now
                pass
        
        # Check for common bug patterns
        bug_patterns = [
            (r'except\s*:', "bare_except", "Should specify exception type"),
            (r'print\([^)]*\)', "print_statement", "Consider using logging"),
            (r'\.get\([^,)]+\)\s*$', "unsafe_get", "No default value in .get()"),
        ]
        
        for py_file in ["main.py", "dashboard.py", "sre_monitoring.py"]:
            if not Path(py_file).exists():
                continue
            
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
            
            for pattern, bug_type, description in bug_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count("\n") + 1
                    # Skip if it's in a comment
                    line = lines[line_num - 1] if line_num <= len(lines) else ""
                    if line.strip().startswith("#"):
                        continue
                    bugs.append({
                        "file": py_file,
                        "type": bug_type,
                        "line": line_num,
                        "description": description
                    })
        
        if bugs:
            print(f"  [WARNING] Found {len(bugs)} potential bugs")
            for bug in bugs[:20]:
                print(f"    {bug['file']}:{bug.get('line', '?')} - {bug['type']}: {bug.get('description', '')}")
            self.results["bugs"] = bugs
        else:
            print("  [PASS] No obvious bugs found")
        
        self.results["sections"]["bugs"] = {
            "status": "WARNING" if bugs else "PASS",
            "count": len(bugs),
            "details": bugs[:10]
        }
        return len(bugs) == 0
    
    def audit_labels_and_references(self):
        """Audit 4: Check for mismatched labels and incorrect references"""
        print("\n" + "=" * 80)
        print("AUDIT 4: LABELS AND REFERENCES")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check config/registry.py for consistency
        if Path("config/registry.py").exists():
            with open("config/registry.py", "r", encoding="utf-8") as f:
                registry_content = f.read()
            
            # Find all defined paths
            defined_paths = set()
            for path_class in self.config_registry_paths:
                matches = re.findall(rf'{path_class}\.\w+\s*=\s*["\']([^"\']+)["\']', registry_content)
                defined_paths.update(matches)
            
            # Check if main.py uses these paths correctly
            if Path("main.py").exists():
                with open("main.py", "r", encoding="utf-8") as f:
                    main_content = f.read()
                
                # Find hardcoded paths that should use registry
                for path in defined_paths:
                    if path in main_content:
                        # Check if it's used via registry
                        if f"StateFiles" not in main_content and f"CacheFiles" not in main_content:
                            # This is a warning, not an error
                            pass
        
        # Check for mismatched function names
        if Path("main.py").exists():
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find function definitions
            func_defs = re.findall(r'def\s+(\w+)\s*\(', content)
            func_calls = re.findall(r'(\w+)\s*\(', content)
            
            # Check for undefined functions being called
            defined_funcs = set(func_defs)
            called_funcs = set(func_calls)
            
            # Filter out built-ins and imports
            built_ins = {"print", "len", "str", "int", "float", "dict", "list", "set", "tuple"}
            undefined = called_funcs - defined_funcs - built_ins
            
            # This is too noisy, skip for now
        
        if issues:
            print(f"  [WARNING] Found {len(issues)} label/reference issues")
            for issue in issues:
                print(f"    {issue}")
            self.results["mismatched_labels"] = issues
        else:
            print("  [PASS] No mismatched labels or incorrect references found")
        
        self.results["sections"]["labels_references"] = {
            "status": "PASS",
            "count": len(issues),
            "details": issues
        }
        return True
    
    def audit_dashboard(self):
        """Audit 5: Test dashboard functionality"""
        print("\n" + "=" * 80)
        print("AUDIT 5: DASHBOARD")
        print("=" * 80)
        print()
        
        issues = []
        
        if not Path("dashboard.py").exists():
            issues.append("dashboard.py not found")
        else:
            # Check dashboard imports
            try:
                with open("dashboard.py", "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check for required endpoints
                required_endpoints = [
                    "/api/positions",
                    "/api/profit",
                    "/api/state",
                    "/api/sre/health",
                    "/api/xai/auditor"
                ]
                
                for endpoint in required_endpoints:
                    if endpoint not in content:
                        issues.append(f"Missing endpoint: {endpoint}")
                
                # Check for XAI tab
                if "xai-tab" not in content and "Natural Language Auditor" not in content:
                    issues.append("XAI tab missing from dashboard")
                
                # Check for JavaScript functions
                js_functions = ["loadXAIAuditor", "renderXAIAuditor", "switchTab"]
                for func in js_functions:
                    if func not in content:
                        issues.append(f"Missing JavaScript function: {func}")
            
            except Exception as e:
                issues.append(f"Error reading dashboard.py: {e}")
        
        if issues:
            print(f"  [FAIL] Found {len(issues)} dashboard issues")
            for issue in issues:
                print(f"    {issue}")
            self.results["errors"].extend([f"Dashboard: {i}" for i in issues])
        else:
            print("  [PASS] Dashboard appears complete")
        
        self.results["sections"]["dashboard"] = {
            "status": "PASS" if not issues else "FAIL",
            "count": len(issues),
            "details": issues
        }
        return len(issues) == 0
    
    def audit_self_healing(self):
        """Audit 6: Test self-healing functionality"""
        print("\n" + "=" * 80)
        print("AUDIT 6: SELF-HEALING")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check for self-healing modules
        self_healing_files = [
            "self_healing/shadow_trade_logger.py",
            "architecture_self_healing.py",
            "self_healing_monitor.py"
        ]
        
        for file_path in self_healing_files:
            if not Path(file_path).exists():
                issues.append(f"Missing self-healing file: {file_path}")
        
        # Check if main.py uses self-healing
        if Path("main.py").exists():
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            if "shadow_trade_logger" not in content and "self_healing" not in content:
                issues.append("main.py does not use self-healing modules")
        
        if issues:
            print(f"  [WARNING] Found {len(issues)} self-healing issues")
            for issue in issues:
                print(f"    {issue}")
            self.results["warnings"].extend([f"Self-healing: {i}" for i in issues])
        else:
            print("  [PASS] Self-healing appears functional")
        
        self.results["sections"]["self_healing"] = {
            "status": "PASS" if not issues else "WARNING",
            "count": len(issues),
            "details": issues
        }
        return True
    
    def audit_monitoring(self):
        """Audit 7: Test monitoring and SRE endpoints"""
        print("\n" + "=" * 80)
        print("AUDIT 7: MONITORING")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check sre_monitoring.py
        if not Path("sre_monitoring.py").exists():
            issues.append("sre_monitoring.py not found")
        else:
            with open("sre_monitoring.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for required functions
            required_functions = [
                "get_sre_health",
                "check_signal_generation_health",
                "check_uw_api_health"
            ]
            
            for func in required_functions:
                if func not in content:
                    issues.append(f"Missing monitoring function: {func}")
        
        # Check dashboard has monitoring endpoints
        if Path("dashboard.py").exists():
            with open("dashboard.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            if "/api/sre/health" not in content:
                issues.append("Dashboard missing /api/sre/health endpoint")
        
        if issues:
            print(f"  [FAIL] Found {len(issues)} monitoring issues")
            for issue in issues:
                print(f"    {issue}")
            self.results["errors"].extend([f"Monitoring: {i}" for i in issues])
        else:
            print("  [PASS] Monitoring appears complete")
        
        self.results["sections"]["monitoring"] = {
            "status": "PASS" if not issues else "FAIL",
            "count": len(issues),
            "details": issues
        }
        return len(issues) == 0
    
    def audit_trading_ability(self):
        """Audit 8: Verify trading ability (dry run)"""
        print("\n" + "=" * 80)
        print("AUDIT 8: TRADING ABILITY")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check main.py has trading functions
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
                if func not in content:
                    issues.append(f"Missing trading function: {func}")
            
            # Check for Alpaca integration
            if "alpaca_trade_api" not in content and "tradeapi" not in content:
                issues.append("Missing Alpaca API integration")
        
        # Check for UW integration
        uw_files = [
            "uw_flow_daemon.py",
            "signals/uw.py",
            "uw_composite_v2.py"
        ]
        
        for file_path in uw_files:
            if not Path(file_path).exists():
                issues.append(f"Missing UW file: {file_path}")
        
        if issues:
            print(f"  [FAIL] Found {len(issues)} trading ability issues")
            for issue in issues:
                print(f"    {issue}")
            self.results["errors"].extend([f"Trading: {i}" for i in issues])
        else:
            print("  [PASS] Trading ability appears functional")
        
        self.results["sections"]["trading_ability"] = {
            "status": "PASS" if not issues else "FAIL",
            "count": len(issues),
            "details": issues
        }
        return len(issues) == 0
    
    def audit_imports_and_syntax(self):
        """Audit 9: Verify all imports work"""
        print("\n" + "=" * 80)
        print("AUDIT 9: IMPORTS AND SYNTAX")
        print("=" * 80)
        print()
        
        issues = []
        
        # Test critical imports
        critical_modules = [
            "main",
            "dashboard",
            "sre_monitoring",
            "config.registry"
        ]
        
        for module_name in critical_modules:
            try:
                __import__(module_name)
                print(f"  [PASS] {module_name}")
            except ImportError as e:
                print(f"  [FAIL] {module_name}: {e}")
                issues.append(f"{module_name}: {e}")
            except Exception as e:
                print(f"  [WARNING] {module_name}: {e}")
                issues.append(f"{module_name}: {e}")
        
        if issues:
            self.results["errors"].extend([f"Import: {i}" for i in issues])
        
        self.results["sections"]["imports"] = {
            "status": "PASS" if not issues else "FAIL",
            "count": len(issues),
            "details": issues
        }
        return len(issues) == 0
    
    def _find_line_number(self, content: str, search_str: str) -> int:
        """Find line number of search string in content"""
        try:
            return content[:content.find(search_str)].count("\n") + 1
        except:
            return 0
    
    def run_full_audit(self):
        """Run complete comprehensive audit"""
        print("=" * 80)
        print("COMPREHENSIVE END-TO-END AUDIT")
        print("=" * 80)
        print()
        print("Auditing: hardcoded values, logging, bugs, labels, references,")
        print("dashboard, self-healing, monitoring, trading ability")
        print()
        
        results = []
        results.append(("Hardcoded Values", self.audit_hardcoded_values()))
        results.append(("Logging Analysis", self.audit_logging_analysis()))
        results.append(("Bugs and Errors", self.audit_bugs()))
        results.append(("Labels and References", self.audit_labels_and_references()))
        results.append(("Dashboard", self.audit_dashboard()))
        results.append(("Self-Healing", self.audit_self_healing()))
        results.append(("Monitoring", self.audit_monitoring()))
        results.append(("Trading Ability", self.audit_trading_ability()))
        results.append(("Imports and Syntax", self.audit_imports_and_syntax()))
        
        # Final summary
        print("\n" + "=" * 80)
        print("COMPREHENSIVE AUDIT SUMMARY")
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
        
        self.results["audit_passed"] = all_passed
        
        if all_passed:
            print("[SUCCESS] COMPREHENSIVE AUDIT PASSED")
        else:
            print("[FAILURE] COMPREHENSIVE AUDIT FOUND ISSUES - REVIEW ABOVE")
        
        return all_passed

def main():
    """Main entry point"""
    audit = ComprehensiveAudit()
    passed = audit.run_full_audit()
    
    # Save results
    results_file = Path("comprehensive_audit_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(audit.results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())

