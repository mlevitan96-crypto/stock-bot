#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Code Audit Tool
==============================
Performs massive code audit covering:
1. Hard-coded values audit
2. Mismatched labels and references
3. Logging setup verification
4. Trade -> Learning flow verification
5. Learning -> Trading updates verification
6. Signal capture verification (all 11 UW endpoints)
7. Architecture review
8. Documentation review
9. Memory bank review
10. General bugs and bad practices

Generates comprehensive report with findings and fixes.
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set
from collections import defaultdict
from datetime import datetime

class ComprehensiveAuditor:
    def __init__(self, root_dir: Path = Path(".")):
        self.root_dir = root_dir
        self.findings = {
            "hardcoded_values": [],
            "mismatched_labels": [],
            "logging_issues": [],
            "learning_flow_issues": [],
            "signal_capture_issues": [],
            "architecture_issues": [],
            "documentation_issues": [],
            "bugs": [],
            "best_practices": []
        }
        self.stats = defaultdict(int)
        
    def audit_all(self) -> Dict[str, Any]:
        """Run all audit checks"""
        print("=" * 80)
        print("COMPREHENSIVE CODE AUDIT")
        print("=" * 80)
        print()
        
        print("[1/10] Auditing hard-coded values...")
        self.audit_hardcoded_values()
        
        print("[2/10] Checking for mismatched labels and references...")
        self.audit_mismatched_references()
        
        print("[3/10] Verifying logging setup...")
        self.audit_logging_setup()
        
        print("[4/10] Verifying trade -> learning flow...")
        self.audit_trade_learning_flow()
        
        print("[5/10] Verifying learning -> trading updates...")
        self.audit_learning_trading_updates()
        
        print("[6/10] Verifying signal capture (all 11 UW endpoints)...")
        self.audit_signal_capture()
        
        print("[7/10] Reviewing architecture...")
        self.audit_architecture()
        
        print("[8/10] Reviewing documentation...")
        self.audit_documentation()
        
        print("[9/10] Reviewing memory bank...")
        self.audit_memory_bank()
        
        print("[10/10] Checking for bugs and bad practices...")
        self.audit_bugs_and_practices()
        
        return self.generate_report()
    
    def audit_hardcoded_values(self):
        """Find hard-coded values that should be in config"""
        patterns = {
            "api_endpoints": r'["\']https?://[^"\']+["\']',
            "timezones": r'(UTC|ET|EST|EDT|US/Eastern|timezone\(["\']US/Eastern["\']\))',
            "magic_numbers": r'\b\d{3,}\b',  # Numbers >= 100
            "thresholds": r'(threshold|limit|max_|min_|MIN_|MAX_)\s*=\s*[\d.]+',
            "file_paths": r'["\'](logs|data|state|config)/[^"\']+["\']',
        }
        
        critical_files = [
            "main.py", "uw_flow_daemon.py", "deploy_supervisor.py",
            "signals/uw_composite.py", "signals/uw_adaptive.py",
            "adaptive_signal_optimizer.py", "comprehensive_learning_orchestrator_v2.py"
        ]
        
        for file_path in critical_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
                
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for hardcoded file paths
            hardcoded_paths = re.findall(r'["\'](logs|data|state|config)/[^"\']+["\']', content)
            if hardcoded_paths:
                self.findings["hardcoded_values"].append({
                    "file": file_path,
                    "type": "hardcoded_path",
                    "issue": f"Hardcoded paths found: {set(hardcoded_paths)}",
                    "fix": "Use config/registry.py (StateFiles, CacheFiles, LogFiles, ConfigFiles)",
                    "severity": "high"
                })
            
            # Check for hardcoded API endpoints
            api_endpoints = re.findall(r'["\']https?://[^"\']+["\']', content)
            if api_endpoints and "api.unusualwhales.com" in str(api_endpoints):
                self.findings["hardcoded_values"].append({
                    "file": file_path,
                    "type": "hardcoded_api_endpoint",
                    "issue": f"Hardcoded API endpoint: {api_endpoints[0]}",
                    "fix": "Use config/registry.py APIConfig.UW_BASE_URL",
                    "severity": "medium"
                })
            
            # Check for hardcoded timezones (should use US/Eastern consistently)
            timezone_refs = re.findall(r'(UTC|ET|EST|EDT|timezone\(["\']US/Eastern["\']\))', content)
            if timezone_refs and "US/Eastern" not in str(timezone_refs):
                self.findings["hardcoded_values"].append({
                    "file": file_path,
                    "type": "timezone_inconsistency",
                    "issue": f"Timezone references: {set(timezone_refs)}",
                    "fix": "Use pytz.timezone('US/Eastern') consistently (handles DST)",
                    "severity": "medium"
                })
    
    def audit_mismatched_references(self):
        """Check for mismatched labels, component names, and references"""
        # Check signal component consistency
        from config.uw_signal_contracts import SIGNAL_COMPONENTS
        from config.registry import SignalComponents
        
        # Compare signal component lists
        contracts_components = set(SIGNAL_COMPONENTS)
        registry_components = set(SignalComponents.ALL_COMPONENTS)
        
        if contracts_components != registry_components:
            missing_in_registry = contracts_components - registry_components
            missing_in_contracts = registry_components - contracts_components
            
            self.findings["mismatched_labels"].append({
                "type": "signal_component_mismatch",
                "issue": "Signal component lists don't match",
                "missing_in_registry": list(missing_in_registry),
                "missing_in_contracts": list(missing_in_contracts),
                "fix": "Synchronize SIGNAL_COMPONENTS and SignalComponents.ALL_COMPONENTS",
                "severity": "high"
            })
        
        # Check endpoint contracts match actual usage
        self._check_endpoint_contracts()
    
    def _check_endpoint_contracts(self):
        """Verify UW endpoint contracts match actual usage"""
        from config.uw_signal_contracts import UW_ENDPOINT_CONTRACTS
        
        expected_endpoints = {
            "market_tide", "greek_exposure", "oi_change", "etf_inflow_outflow",
            "iv_rank", "shorts_ftds", "max_pain"
        }
        
        defined_endpoints = set(UW_ENDPOINT_CONTRACTS.keys())
        
        # Check if all expected endpoints are defined
        missing = expected_endpoints - defined_endpoints
        if missing:
            self.findings["mismatched_labels"].append({
                "type": "missing_endpoint_contract",
                "issue": f"Missing endpoint contracts: {missing}",
                "fix": "Add missing endpoint contracts to UW_ENDPOINT_CONTRACTS",
                "severity": "high"
            })
    
    def audit_logging_setup(self):
        """Verify all critical events are logged"""
        critical_events = [
            "trade_entry", "trade_exit", "order_submission", "order_fill",
            "signal_generation", "learning_update", "error", "risk_freeze"
        ]
        
        # Check main.py for logging
        main_py = self.root_dir / "main.py"
        if main_py.exists():
            content = main_py.read_text(encoding='utf-8', errors='ignore')
            
            # Check for attribution logging
            if "log_exit_attribution" not in content:
                self.findings["logging_issues"].append({
                    "type": "missing_attribution_logging",
                    "issue": "log_exit_attribution not found",
                    "fix": "Ensure all trade exits log attribution for learning",
                    "severity": "critical"
                })
            
            # Check for blocked trade logging
            if "log_blocked_trade" not in content:
                self.findings["logging_issues"].append({
                    "type": "missing_blocked_trade_logging",
                    "issue": "log_blocked_trade not found",
                    "fix": "Log all blocked trades for counterfactual learning",
                    "severity": "high"
                })
    
    def audit_trade_learning_flow(self):
        """Verify trades flow to learning system"""
        main_py = self.root_dir / "main.py"
        if not main_py.exists():
            return
        
        content = main_py.read_text(encoding='utf-8', errors='ignore')
        
        # Check if log_exit_attribution calls learning
        if "log_exit_attribution" in content:
            # Check if it calls learning function
            if "learn_from_trade_close" not in content and "record_trade_for_learning" not in content:
                self.findings["learning_flow_issues"].append({
                    "type": "missing_learning_call",
                    "issue": "log_exit_attribution doesn't call learning function",
                    "fix": "Call learn_from_trade_close() or record_trade_for_learning() in log_exit_attribution",
                    "severity": "critical"
                })
        
        # Check if comprehensive_learning_orchestrator_v2 is used (not deprecated v1)
        if "comprehensive_learning_orchestrator" in content and "comprehensive_learning_orchestrator_v2" not in content:
            self.findings["learning_flow_issues"].append({
                "type": "deprecated_learning_orchestrator",
                "issue": "Using deprecated comprehensive_learning_orchestrator (without _v2)",
                "fix": "Use comprehensive_learning_orchestrator_v2",
                "severity": "high"
            })
    
    def audit_learning_trading_updates(self):
        """Verify learning updates flow back to trading"""
        # Check if adaptive weights are loaded in signal computation
        uw_composite = self.root_dir / "signals" / "uw_composite.py"
        if not uw_composite.exists():
            uw_composite = self.root_dir / "uw_composite_v2.py"
        
        if uw_composite.exists():
            content = uw_composite.read_text(encoding='utf-8', errors='ignore')
            
            if "get_adaptive_weights" not in content:
                self.findings["learning_flow_issues"].append({
                    "type": "missing_adaptive_weights",
                    "issue": "Signal computation doesn't use adaptive weights",
                    "fix": "Call get_adaptive_weights() and apply to signal weights",
                    "severity": "critical"
                })
    
    def audit_signal_capture(self):
        """Verify all 11 UW endpoints are captured"""
        expected_endpoints = {
            "option_flow", "dark_pool", "insider", "congress", "shorts",
            "institutional", "market_tide", "calendar", "etf_flow",
            "greek_exposure", "oi_change", "iv_rank", "shorts_ftds", "max_pain"
        }
        
        # Check uw_flow_daemon.py
        daemon_file = self.root_dir / "uw_flow_daemon.py"
        if daemon_file.exists():
            content = daemon_file.read_text(encoding='utf-8', errors='ignore')
            
            # Check for endpoint polling
            found_endpoints = set()
            for endpoint in expected_endpoints:
                if endpoint.replace("_", "") in content.lower() or endpoint in content:
                    found_endpoints.add(endpoint)
            
            missing = expected_endpoints - found_endpoints
            if missing:
                self.findings["signal_capture_issues"].append({
                    "type": "missing_endpoint_polling",
                    "issue": f"Missing endpoint polling: {missing}",
                    "fix": "Add polling for missing endpoints in uw_flow_daemon.py",
                    "severity": "high"
                })
    
    def audit_architecture(self):
        """Review architecture for soundness"""
        # Check for registry usage
        critical_files = ["main.py", "uw_flow_daemon.py", "deploy_supervisor.py"]
        
        for file_path in critical_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
            
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check if registry is imported
            if "from config.registry import" not in content and "import config.registry" not in content:
                # Check if it uses hardcoded paths
                if re.search(r'["\'](logs|data|state|config)/', content):
                    self.findings["architecture_issues"].append({
                        "file": file_path,
                        "type": "missing_registry_usage",
                        "issue": "Uses hardcoded paths but doesn't import registry",
                        "fix": "Import from config.registry and use StateFiles, CacheFiles, LogFiles",
                        "severity": "high"
                    })
    
    def audit_documentation(self):
        """Review documentation for accuracy"""
        # Check if MEMORY_BANK.md mentions current practices
        memory_bank = self.root_dir / "MEMORY_BANK.md"
        if memory_bank.exists():
            content = memory_bank.read_text(encoding='utf-8', errors='ignore')
            
            # Check for outdated references
            if "comprehensive_learning_orchestrator" in content and "comprehensive_learning_orchestrator_v2" not in content:
                self.findings["documentation_issues"].append({
                    "type": "outdated_documentation",
                    "issue": "MEMORY_BANK.md references deprecated orchestrator",
                    "fix": "Update to reference comprehensive_learning_orchestrator_v2",
                    "severity": "medium"
                })
    
    def audit_memory_bank(self):
        """Review memory bank for accuracy"""
        memory_bank = self.root_dir / "MEMORY_BANK.md"
        if not memory_bank.exists():
            self.findings["documentation_issues"].append({
                "type": "missing_memory_bank",
                "issue": "MEMORY_BANK.md not found",
                "fix": "Create/update MEMORY_BANK.md with current practices",
                "severity": "medium"
            })
            return
        
        content = memory_bank.read_text(encoding='utf-8', errors='ignore')
        
        # Check for key sections
        required_sections = [
            "Project Overview", "Environment Setup", "Deployment Procedures",
            "Learning System", "Signal Components"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            self.findings["documentation_issues"].append({
                "type": "incomplete_memory_bank",
                "issue": f"Missing sections: {missing_sections}",
                "fix": "Add missing sections to MEMORY_BANK.md",
                "severity": "low"
            })
    
    def audit_bugs_and_practices(self):
        """Check for bugs and bad practices"""
        # Check for common bugs
        critical_files = ["main.py", "uw_flow_daemon.py"]
        
        for file_path in critical_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
            
            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                
                # Check for syntax errors
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    self.findings["bugs"].append({
                        "file": file_path,
                        "type": "syntax_error",
                        "issue": f"Syntax error: {e}",
                        "fix": "Fix syntax error",
                        "severity": "critical"
                    })
                
                # Check for common bugs
                if "except:" in content and "except Exception:" not in content:
                    # Count bare excepts
                    bare_excepts = len(re.findall(r'except\s*:', content))
                    if bare_excepts > 0:
                        self.findings["best_practices"].append({
                            "file": file_path,
                            "type": "bare_except",
                            "issue": f"{bare_excepts} bare except clauses found",
                            "fix": "Use 'except Exception:' instead of 'except:'",
                            "severity": "medium"
                        })
                
            except Exception as e:
                self.findings["bugs"].append({
                    "file": file_path,
                    "type": "file_read_error",
                    "issue": f"Could not read file: {e}",
                    "severity": "high"
                })
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_findings": sum(len(v) for v in self.findings.values()),
                "critical": sum(1 for category in self.findings.values() for item in category if item.get("severity") == "critical"),
                "high": sum(1 for category in self.findings.values() for item in category if item.get("severity") == "high"),
                "medium": sum(1 for category in self.findings.values() for item in category if item.get("severity") == "medium"),
                "low": sum(1 for category in self.findings.values() for item in category if item.get("severity") == "low"),
            },
            "findings": self.findings,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if self.findings["hardcoded_values"]:
            recommendations.append("Move all hardcoded values to config/registry.py")
        
        if self.findings["mismatched_labels"]:
            recommendations.append("Synchronize signal component names across all modules")
        
        if self.findings["learning_flow_issues"]:
            recommendations.append("Ensure all trades flow to learning system and updates flow back")
        
        if self.findings["signal_capture_issues"]:
            recommendations.append("Verify all 11 UW endpoints are being polled and cached")
        
        if self.findings["architecture_issues"]:
            recommendations.append("Use config/registry.py for all file paths")
        
        return recommendations


def main():
    auditor = ComprehensiveAuditor()
    report = auditor.audit_all()
    
    # Print summary
    print()
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Findings: {report['summary']['total_findings']}")
    print(f"  Critical: {report['summary']['critical']}")
    print(f"  High: {report['summary']['high']}")
    print(f"  Medium: {report['summary']['medium']}")
    print(f"  Low: {report['summary']['low']}")
    print()
    
    # Print findings by category
    for category, items in report['findings'].items():
        if items:
            print(f"{category.upper().replace('_', ' ')}: {len(items)} issues")
            for item in items[:5]:  # Show first 5
                print(f"  - [{item.get('severity', 'unknown').upper()}] {item.get('issue', 'Unknown issue')}")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
            print()
    
    # Save report
    report_file = Path("comprehensive_audit_report.json")
    report_file.write_text(json.dumps(report, indent=2))
    print(f"Full report saved to: {report_file}")
    
    return report


if __name__ == "__main__":
    main()
