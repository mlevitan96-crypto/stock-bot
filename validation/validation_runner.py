#!/usr/bin/env python3
"""
Validation Runner - Resilience Test Suite
==========================================
Adversarially tests the self-healing architecture under controlled failure conditions.

Usage:
    python3 validation/validation_runner.py --scenario all
    python3 validation/validation_runner.py --scenario state_persistence
    python3 validation/validation_runner.py --scenario partial_failure,api_drift

Safety:
- NEVER runs automatically
- NEVER modifies .env or secrets
- NEVER modifies production logic
- All tests are opt-in and isolated
"""

import os
import sys
import json
import time
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

VALIDATION_DIR = Path(__file__).parent
REPORT_DIR = VALIDATION_DIR / "report"
SCENARIOS_DIR = VALIDATION_DIR / "scenarios"
STATE_DIR = Path("/root/stock-bot/state")
LOG_DIR = Path("/root/stock-bot/logs")

# Ensure directories exist
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class ValidationRunner:
    """Orchestrates resilience tests and generates reports."""
    
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.results: Dict[str, Dict] = {}
        self.snapshots: List[Dict] = []
        self.log_excerpts: List[Dict] = []
        
    def capture_snapshot(self, label: str) -> Dict:
        """Capture current system state snapshot."""
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "label": label,
            "health": self.read_health(),
            "trading_state": self.read_trading_state(),
            "processes": self._get_process_status()
        }
        self.snapshots.append(snapshot)
        return snapshot
    
    def read_health(self) -> Optional[Dict]:
        """Read health.json if it exists."""
        health_file = STATE_DIR / "health.json"
        if health_file.exists():
            try:
                with open(health_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return {"error": str(e)}
        return None
    
    def read_trading_state(self) -> Optional[Dict]:
        """Read trading_state.json if it exists."""
        state_file = STATE_DIR / "trading_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return {"error": str(e)}
        return None
    
    def _get_process_status(self) -> Dict:
        """Get status of key processes."""
        processes = {}
        for proc_name in ["trading-bot", "uw-daemon", "dashboard", "heartbeat-keeper"]:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", f"python.*{proc_name.replace('-', '_')}"],
                    capture_output=True,
                    timeout=2
                )
                processes[proc_name] = {
                    "running": result.returncode == 0,
                    "pid": result.stdout.decode().strip() if result.returncode == 0 else None
                }
            except Exception:
                processes[proc_name] = {"running": False, "error": "check_failed"}
        return processes
    
    def capture_logs(self, label: str, lines: int = 50) -> str:
        """Capture recent supervisor logs."""
        try:
            result = subprocess.run(
                ["journalctl", "-u", "stockbot", "-n", str(lines), "--no-pager"],
                capture_output=True,
                timeout=5
            )
            log_content = result.stdout.decode()
            self.log_excerpts.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "label": label,
                "lines": lines,
                "content": log_content
            })
            return log_content
        except Exception as e:
            return f"Error capturing logs: {e}"
    
    def run_scenario(self, scenario_name: str) -> Dict:
        """Run a single test scenario."""
        print(f"\n{'='*60}")
        print(f"Running scenario: {scenario_name}")
        print(f"{'='*60}\n")
        
        scenario_file = SCENARIOS_DIR / f"test_{scenario_name}.py"
        if not scenario_file.exists():
            return {
                "scenario": scenario_name,
                "status": "ERROR",
                "error": f"Scenario file not found: {scenario_file}",
                "tests": []
            }
        
        # Capture initial state
        self.capture_snapshot(f"{scenario_name}_before")
        
        try:
            # Import and run scenario
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"test_{scenario_name}", scenario_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run scenario
            if hasattr(module, 'run_scenario'):
                result = module.run_scenario(self)
            else:
                result = {
                    "scenario": scenario_name,
                    "status": "ERROR",
                    "error": "Scenario module missing run_scenario() function",
                    "tests": []
                }
            
            # Capture final state
            self.capture_snapshot(f"{scenario_name}_after")
            
            self.results[scenario_name] = result
            return result
            
        except Exception as e:
            import traceback
            error_msg = f"Scenario execution failed: {e}\n{traceback.format_exc()}"
            result = {
                "scenario": scenario_name,
                "status": "ERROR",
                "error": error_msg,
                "tests": []
            }
            self.results[scenario_name] = result
            return result
    
    def generate_report(self) -> Path:
        """Generate final validation report."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_file = REPORT_DIR / f"validation_report_{timestamp}.md"
        
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        # Count pass/fail
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_scenarios = 0
        
        for scenario_name, result in self.results.items():
            if result.get("status") == "ERROR":
                error_scenarios += 1
            else:
                tests = result.get("tests", [])
                total_tests += len(tests)
                for test in tests:
                    if test.get("status") == "PASS":
                        passed_tests += 1
                    elif test.get("status") == "FAIL":
                        failed_tests += 1
        
        # Generate markdown report
        report_lines = [
            "# Resilience Test Report",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"**Duration:** {duration:.1f} seconds",
            f"**Total Tests:** {total_tests}",
            f"**Passed:** {passed_tests}",
            f"**Failed:** {failed_tests}",
            f"**Error Scenarios:** {error_scenarios}",
            "",
            "## Summary",
            "",
            f"- **Total Scenarios:** {len(self.results)}",
            f"- **Total Tests:** {total_tests}",
            f"- **Pass Rate:** {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%",
            "",
            "## Scenario Results",
            ""
        ]
        
        # Per-scenario results
        for scenario_name, result in self.results.items():
            status = result.get("status", "UNKNOWN")
            status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            
            report_lines.append(f"### {status_emoji} {scenario_name}")
            report_lines.append("")
            report_lines.append(f"**Status:** {status}")
            
            if result.get("error"):
                report_lines.append(f"**Error:** {result.get('error')}")
            
            tests = result.get("tests", [])
            if tests:
                report_lines.append("")
                report_lines.append("**Test Results:**")
                report_lines.append("")
                for test in tests:
                    test_status = test.get("status", "UNKNOWN")
                    test_emoji = "✅" if test_status == "PASS" else "❌"
                    report_lines.append(f"- {test_emoji} **{test.get('name', 'Unknown')}**: {test_status}")
                    if test.get("message"):
                        report_lines.append(f"  - {test.get('message')}")
                    if test.get("details"):
                        report_lines.append(f"  - Details: {test.get('details')}")
            
            report_lines.append("")
        
        # Add snapshots
        if self.snapshots:
            report_lines.append("## State Snapshots")
            report_lines.append("")
            for snapshot in self.snapshots:
                report_lines.append(f"### {snapshot['label']}")
                report_lines.append(f"**Timestamp:** {snapshot['timestamp']}")
                report_lines.append("")
                if snapshot.get('health'):
                    report_lines.append("**Health Status:**")
                    report_lines.append("```json")
                    report_lines.append(json.dumps(snapshot['health'], indent=2))
                    report_lines.append("```")
                    report_lines.append("")
        
        # Add log excerpts
        if self.log_excerpts:
            report_lines.append("## Log Excerpts")
            report_lines.append("")
            for log_excerpt in self.log_excerpts[-5:]:  # Last 5 excerpts
                report_lines.append(f"### {log_excerpt['label']}")
                report_lines.append(f"**Timestamp:** {log_excerpt['timestamp']}")
                report_lines.append("")
                report_lines.append("```")
                report_lines.append(log_excerpt['content'][:2000])  # Limit length
                report_lines.append("```")
                report_lines.append("")
        
        # Recommendations
        report_lines.append("## Recommendations")
        report_lines.append("")
        if failed_tests > 0:
            report_lines.append("### Failed Tests Require Attention")
            report_lines.append("")
            for scenario_name, result in self.results.items():
                if result.get("status") == "FAIL":
                    tests = result.get("tests", [])
                    for test in tests:
                        if test.get("status") == "FAIL":
                            report_lines.append(f"- **{scenario_name}/{test.get('name')}**: {test.get('message', 'Test failed')}")
        else:
            report_lines.append("All tests passed! ✅")
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append(f"*Report generated by validation_runner.py*")
        
        # Write report
        with open(report_file, 'w') as f:
            f.write("\n".join(report_lines))
        
        print(f"\n{'='*60}")
        print(f"Report generated: {report_file}")
        print(f"{'='*60}\n")
        
        return report_file


def main():
    parser = argparse.ArgumentParser(description="Run resilience validation tests")
    parser.add_argument(
        "--scenario",
        type=str,
        default="all",
        help="Comma-separated list of scenarios to run, or 'all' for all scenarios"
    )
    
    args = parser.parse_args()
    
    # Available scenarios
    available_scenarios = [
        "state_persistence",
        "partial_failure",
        "api_drift",
        "chaos_modes",
        "trade_guard"
    ]
    
    # Determine which scenarios to run
    if args.scenario.lower() == "all":
        scenarios_to_run = available_scenarios
    else:
        scenarios_to_run = [s.strip() for s in args.scenario.split(",")]
        # Validate
        invalid = [s for s in scenarios_to_run if s not in available_scenarios]
        if invalid:
            print(f"ERROR: Invalid scenarios: {invalid}")
            print(f"Available scenarios: {', '.join(available_scenarios)}")
            sys.exit(1)
    
    print("="*60)
    print("RESILIENCE VALIDATION SUITE")
    print("="*60)
    print(f"Scenarios to run: {', '.join(scenarios_to_run)}")
    print(f"Start time: {datetime.now(timezone.utc).isoformat()}")
    print("="*60)
    
    runner = ValidationRunner()
    
    # Run scenarios
    for scenario in scenarios_to_run:
        runner.run_scenario(scenario)
        time.sleep(2)  # Brief pause between scenarios
    
    # Generate report
    report_file = runner.generate_report()
    
    print(f"\nValidation complete. Report: {report_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
