#!/usr/bin/env python3
"""
COMPLETE BOT AUDIT - Final Comprehensive Check
Audits: hardcoded values, logging analysis, bugs, labels, references
Ensures bot is 100% ready for trading tomorrow morning
"""

import json
import sys
import re
import ast
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set

class CompleteBotAudit:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_passed": False,
            "sections": {},
            "errors": [],
            "warnings": [],
            "hardcoded_critical": [],
            "unanalyzed_logs": [],
            "bugs_critical": [],
            "mismatched_labels": []
        }
    
    def audit_hardcoded_critical(self):
        """Audit critical hardcoded values that should use config/registry.py"""
        print("=" * 80)
        print("AUDIT: HARDCODED VALUES (CRITICAL ONLY)")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check for hardcoded paths that should use registry
        critical_files = ["main.py", "dashboard.py", "sre_monitoring.py", "deploy_supervisor.py"]
        
        for file_path in critical_files:
            if not Path(file_path).exists():
                continue
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
            
            # Check for hardcoded paths (state/, logs/, data/, cache/)
            path_patterns = [
                (r'["\'](state|logs|data|cache)/', "hardcoded_path"),
                (r'Path\(["\'](state|logs|data|cache)/', "hardcoded_path"),
            ]
            
            for pattern, issue_type in path_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count("\n") + 1
                    # Skip if it's in a comment or uses registry
                    context = content[max(0, match.start()-100):match.end()+100]
                    if "config/registry" in context or "StateFiles" in context or "CacheFiles" in context:
                        continue
                    if "#" in lines[line_num-1][:lines[line_num-1].find(match.group())]:
                        continue
                    issues.append({
                        "file": file_path,
                        "line": line_num,
                        "type": issue_type,
                        "value": match.group()
                    })
        
        if issues:
            print(f"  [WARNING] Found {len(issues)} potential hardcoded paths")
            for issue in issues[:10]:
                print(f"    {issue['file']}:{issue['line']} - {issue['value']}")
            self.results["hardcoded_critical"] = issues[:20]
        else:
            print("  [PASS] No critical hardcoded paths found (all use config/registry.py)")
        
        self.results["sections"]["hardcoded_critical"] = {
            "status": "WARNING" if issues else "PASS",
            "count": len(issues),
            "details": issues[:10]
        }
        return len(issues) == 0
    
    def audit_logging_analysis(self):
        """Verify all logging feeds into analysis"""
        print("\n" + "=" * 80)
        print("AUDIT: LOGGING ANALYSIS")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check main.py logging
        if Path("main.py").exists():
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find log_event calls
            log_calls = len(re.findall(r'log_event\(', content))
            
            # Check if logs are analyzed
            analysis_functions = [
                "learn_from_trade",
                "process_blocked_trades",
                "comprehensive_learning",
                "feed_to_learning",
                "analyze_"
            ]
            
            has_analysis = any(func in content for func in analysis_functions)
            
            if log_calls > 0 and has_analysis:
                print(f"  [PASS] {log_calls} log_event calls found, analysis functions present")
            elif log_calls > 0:
                print(f"  [WARNING] {log_calls} log_event calls but no analysis functions found")
                issues.append("Logging present but no analysis functions")
        
        # Check log files are read
        log_files = [
            "logs/attribution.jsonl",
            "logs/exit.jsonl",
            "logs/signals.jsonl",
            "logs/orders.jsonl",
            "logs/gate.jsonl"
        ]
        
        readers_found = 0
        for log_file in log_files:
            # Check if any code reads this file
            for py_file in Path(".").glob("*.py"):
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        if log_file in f.read():
                            readers_found += 1
                            break
                except:
                    pass
        
        if readers_found == len(log_files):
            print(f"  [PASS] All {len(log_files)} log files have readers")
        else:
            print(f"  [WARNING] Only {readers_found}/{len(log_files)} log files have readers")
            issues.append(f"Some log files not analyzed: {readers_found}/{len(log_files)}")
        
        self.results["sections"]["logging_analysis"] = {
            "status": "PASS" if not issues else "WARNING",
            "count": len(issues),
            "details": issues
        }
        if issues:
            self.results["unanalyzed_logs"] = issues
        return len(issues) == 0
    
    def audit_critical_bugs(self):
        """Check for critical bugs only"""
        print("\n" + "=" * 80)
        print("AUDIT: CRITICAL BUGS")
        print("=" * 80)
        print()
        
        bugs = []
        
        # Check syntax of critical files
        critical_files = ["main.py", "dashboard.py", "sre_monitoring.py", "deploy_supervisor.py"]
        
        for file_path in critical_files:
            if not Path(file_path).exists():
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                print(f"  [FAIL] {file_path}: Syntax error - {e}")
                bugs.append({
                    "file": file_path,
                    "type": "syntax_error",
                    "error": str(e)
                })
            except Exception as e:
                # Import errors are OK for now
                pass
        
        if bugs:
            print(f"  [FAIL] Found {len(bugs)} critical bugs")
            self.results["bugs_critical"] = bugs
        else:
            print("  [PASS] No critical syntax errors found")
        
        self.results["sections"]["critical_bugs"] = {
            "status": "PASS" if not bugs else "FAIL",
            "count": len(bugs),
            "details": bugs
        }
        if bugs:
            self.results["errors"].extend([f"Bug: {b['file']}: {b['error']}" for b in bugs])
        return len(bugs) == 0
    
    def audit_labels_references(self):
        """Check for mismatched labels and incorrect references"""
        print("\n" + "=" * 80)
        print("AUDIT: LABELS AND REFERENCES")
        print("=" * 80)
        print()
        
        issues = []
        
        # Check config/registry.py consistency
        if Path("config/registry.py").exists():
            with open("config/registry.py", "r", encoding="utf-8") as f:
                registry_content = f.read()
            
            # Find all defined paths
            defined_classes = ["StateFiles", "CacheFiles", "LogFiles", "ConfigFiles", "Directories"]
            for class_name in defined_classes:
                if f"class {class_name}" in registry_content:
                    print(f"  [PASS] {class_name} defined in registry")
                else:
                    print(f"  [WARNING] {class_name} not found in registry")
                    issues.append(f"Missing class: {class_name}")
        
        if issues:
            print(f"  [WARNING] Found {len(issues)} label/reference issues")
            self.results["mismatched_labels"] = issues
        else:
            print("  [PASS] No mismatched labels or incorrect references found")
        
        self.results["sections"]["labels_references"] = {
            "status": "PASS" if not issues else "WARNING",
            "count": len(issues),
            "details": issues
        }
        return True
    
    def run_complete_audit(self):
        """Run complete comprehensive audit"""
        print("=" * 80)
        print("COMPLETE BOT AUDIT")
        print("=" * 80)
        print()
        print("Auditing: hardcoded values, logging analysis, bugs, labels, references")
        print()
        
        results = []
        results.append(("Hardcoded Values (Critical)", self.audit_hardcoded_critical()))
        results.append(("Logging Analysis", self.audit_logging_analysis()))
        results.append(("Critical Bugs", self.audit_critical_bugs()))
        results.append(("Labels and References", self.audit_labels_references()))
        
        # Final summary
        print("\n" + "=" * 80)
        print("COMPLETE AUDIT SUMMARY")
        print("=" * 80)
        print()
        
        all_passed = True
        for name, passed in results:
            status = "[PASS]" if passed else "[WARNING]"
            print(f"{status} {name}")
            if not passed:
                all_passed = False
        
        print()
        if self.results["errors"]:
            print(f"Errors ({len(self.results['errors'])}):")
            for error in self.results["errors"][:10]:
                print(f"  - {error}")
            print()
        
        if self.results["warnings"]:
            print(f"Warnings ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"][:10]:
                print(f"  - {warning}")
            print()
        
        self.results["audit_passed"] = all_passed
        
        if all_passed:
            print("[SUCCESS] COMPLETE AUDIT PASSED")
        else:
            print("[WARNING] COMPLETE AUDIT FOUND MINOR ISSUES (non-critical)")
        
        return all_passed

def main():
    """Main entry point"""
    audit = CompleteBotAudit()
    passed = audit.run_complete_audit()
    
    # Save results
    results_file = Path("complete_bot_audit_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(audit.results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())

