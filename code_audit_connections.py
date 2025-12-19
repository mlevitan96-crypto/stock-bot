#!/usr/bin/env python3
"""
Code Audit: Verify All Connections and File Paths
===================================================
Verifies that all components read/write to consistent file paths
and all endpoints are properly connected.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def check_file_paths() -> List[Tuple[str, bool, str]]:
    """Check that file paths match between readers and writers."""
    results = []
    
    # 1. attribution.jsonl
    # Writer: main.py jsonl_write("attribution", ...) -> logs/attribution.jsonl
    # Reader: executive_summary_generator.py -> should read logs/attribution.jsonl
    # Reader: comprehensive_learning_orchestrator.py -> should read logs/attribution.jsonl
    
    exec_summary_code = Path("executive_summary_generator.py").read_text(encoding='utf-8', errors='ignore')
    learning_orch_code = Path("comprehensive_learning_orchestrator.py").read_text(encoding='utf-8', errors='ignore')
    
    exec_uses_logs = "LOGS_DIR / \"attribution.jsonl\"" in exec_summary_code or "logs/attribution.jsonl" in exec_summary_code
    learning_uses_logs = "LOGS_DIR / \"attribution.jsonl\"" in learning_orch_code or "logs/attribution.jsonl" in learning_orch_code
    
    results.append(("attribution.jsonl (executive_summary_generator)", exec_uses_logs, 
                   "Should read from LOGS_DIR/attribution.jsonl" if not exec_uses_logs else "OK"))
    results.append(("attribution.jsonl (comprehensive_learning_orchestrator)", learning_uses_logs,
                   "Should read from LOGS_DIR/attribution.jsonl" if not learning_uses_logs else "OK"))
    
    # 2. blocked_trades.jsonl
    # Writer: main.py log_blocked_trade() -> state/blocked_trades.jsonl
    # Reader: counterfactual_analyzer.py -> should read state/blocked_trades.jsonl
    
    main_code = Path("main.py").read_text(encoding='utf-8', errors='ignore')
    counterfactual_code = Path("counterfactual_analyzer.py").read_text(encoding='utf-8', errors='ignore')
    
    main_writes_state = "state/blocked_trades.jsonl" in main_code or "STATE_DIR" in main_code
    counterfactual_reads_state = "STATE_DIR / \"blocked_trades.jsonl\"" in counterfactual_code
    
    results.append(("blocked_trades.jsonl (counterfactual_analyzer)", counterfactual_reads_state,
                   "Should read from STATE_DIR/blocked_trades.jsonl" if not counterfactual_reads_state else "OK"))
    
    # 3. comprehensive_learning.jsonl
    # Writer: comprehensive_learning_orchestrator.py -> data/comprehensive_learning.jsonl
    # Reader: executive_summary_generator.py -> should read data/comprehensive_learning.jsonl
    
    learning_writes_data = "DATA_DIR / \"comprehensive_learning.jsonl\"" in learning_orch_code
    exec_reads_learning = "DATA_DIR / \"comprehensive_learning.jsonl\"" in exec_summary_code
    
    results.append(("comprehensive_learning.jsonl (executive_summary_generator)", exec_reads_learning,
                   "Should read from DATA_DIR/comprehensive_learning.jsonl" if not exec_reads_learning else "OK"))
    
    # 4. counterfactual_results.jsonl
    # Writer: counterfactual_analyzer.py -> data/counterfactual_results.jsonl
    # Reader: executive_summary_generator.py -> should read data/counterfactual_results.jsonl
    
    counterfactual_writes_data = "DATA_DIR / \"counterfactual_results.jsonl\"" in counterfactual_code
    exec_reads_counterfactual = "DATA_DIR / \"counterfactual_results.jsonl\"" in exec_summary_code
    
    results.append(("counterfactual_results.jsonl (executive_summary_generator)", exec_reads_counterfactual,
                   "Should read from DATA_DIR/counterfactual_results.jsonl" if not exec_reads_counterfactual else "OK"))
    
    # 5. signal_weights.json
    # Writer: adaptive_signal_optimizer.py -> state/signal_weights.json
    # Reader: executive_summary_generator.py -> should read state/signal_weights.json
    
    exec_reads_weights = "STATE_DIR / \"signal_weights.json\"" in exec_summary_code or "state/signal_weights.json" in exec_summary_code
    
    results.append(("signal_weights.json (executive_summary_generator)", exec_reads_weights,
                   "Should read from STATE_DIR/signal_weights.json" if not exec_reads_weights else "OK"))
    
    return results

def check_endpoint_connections() -> List[Tuple[str, bool, str]]:
    """Check that dashboard endpoints are properly connected."""
    results = []
    
    dashboard_code = Path("dashboard.py").read_text(encoding='utf-8', errors='ignore')
    
    # 1. Executive Summary endpoint
    has_executive_endpoint = "@app.route(\"/api/executive_summary\"" in dashboard_code
    has_executive_import = "from executive_summary_generator import" in dashboard_code
    has_executive_call = "generate_executive_summary()" in dashboard_code
    
    exec_endpoint_ok = has_executive_endpoint and has_executive_import and has_executive_call
    
    results.append(("Executive Summary API endpoint", exec_endpoint_ok,
                   "Missing route/import/call" if not exec_endpoint_ok else "OK"))
    
    # 2. Executive Summary frontend
    has_executive_tab = "executive-tab" in dashboard_code
    has_load_function = "loadExecutiveSummary()" in dashboard_code
    has_render_function = "renderExecutiveSummary(" in dashboard_code
    has_api_fetch = "fetch('/api/executive_summary')" in dashboard_code
    
    exec_frontend_ok = has_executive_tab and has_load_function and has_render_function and has_api_fetch
    
    results.append(("Executive Summary frontend", exec_frontend_ok,
                   "Missing tab/function/fetch" if not exec_frontend_ok else "OK"))
    
    # 3. SRE Health endpoint
    has_sre_endpoint = "@app.route(\"/api/sre/health\"" in dashboard_code
    has_sre_frontend = "fetch('/api/sre/health')" in dashboard_code
    
    sre_ok = has_sre_endpoint and has_sre_frontend
    
    results.append(("SRE Health endpoint", sre_ok,
                   "Missing endpoint or frontend fetch" if not sre_ok else "OK"))
    
    # 4. Positions endpoint
    has_positions_endpoint = "@app.route(\"/api/positions\"" in dashboard_code
    has_positions_fetch = "fetch('/api/positions')" in dashboard_code
    
    positions_ok = has_positions_endpoint and has_positions_fetch
    
    results.append(("Positions endpoint", positions_ok,
                   "Missing endpoint or frontend fetch" if not positions_ok else "OK"))
    
    return results

def check_data_flow() -> List[Tuple[str, bool, str]]:
    """Check that data flows correctly through the system."""
    results = []
    
    # Check if attribution.jsonl file exists
    attribution_file = Path("logs/attribution.jsonl")
    attribution_exists = attribution_file.exists()
    
    results.append(("attribution.jsonl file exists", attribution_exists,
                   f"File not found at {attribution_file.absolute()}" if not attribution_exists else "OK"))
    
    if attribution_exists:
        # Check if file has content
        try:
            with attribution_file.open("r") as f:
                lines = [line for line in f if line.strip()]
                has_content = len(lines) > 0
                results.append(("attribution.jsonl has content", has_content,
                               f"{len(lines)} lines found" if has_content else "File is empty"))
        except Exception as e:
            results.append(("attribution.jsonl readable", False, str(e)))
    
    # Check if comprehensive_learning.jsonl exists
    learning_file = Path("data/comprehensive_learning.jsonl")
    learning_exists = learning_file.exists()
    
    results.append(("comprehensive_learning.jsonl exists", learning_exists,
                   "Will be created after first learning cycle runs" if not learning_exists else "OK"))
    
    # Check if counterfactual_results.jsonl exists
    counterfactual_file = Path("data/counterfactual_results.jsonl")
    counterfactual_exists = counterfactual_file.exists()
    
    results.append(("counterfactual_results.jsonl exists", counterfactual_exists,
                   "Will be created after counterfactual analysis runs" if not counterfactual_exists else "OK"))
    
    # Check if signal_weights.json exists
    weights_file = Path("state/signal_weights.json")
    weights_exists = weights_file.exists()
    
    results.append(("signal_weights.json exists", weights_exists,
                   "Will be created by adaptive signal optimizer" if not weights_exists else "OK"))
    
    return results

def main():
    print(f"{BLUE}{'='*70}")
    print("CODE AUDIT: Connections and File Paths")
    print(f"{'='*70}{RESET}\n")
    
    # File paths
    print(f"{YELLOW}[1] FILE PATH CONSISTENCY{RESET}")
    print("-" * 70)
    file_results = check_file_paths()
    for name, ok, msg in file_results:
        status = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"{status} {name}")
        if not ok:
            print(f"   {RED}→ {msg}{RESET}")
    print()
    
    # Endpoint connections
    print(f"{YELLOW}[2] ENDPOINT CONNECTIONS{RESET}")
    print("-" * 70)
    endpoint_results = check_endpoint_connections()
    for name, ok, msg in endpoint_results:
        status = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"{status} {name}")
        if not ok:
            print(f"   {RED}→ {msg}{RESET}")
    print()
    
    # Data flow
    print(f"{YELLOW}[3] DATA FLOW (File Existence){RESET}")
    print("-" * 70)
    data_results = check_data_flow()
    for name, ok, msg in data_results:
        status = f"{GREEN}✓{RESET}" if ok else f"{YELLOW}⚠{RESET}"
        print(f"{status} {name}")
        if not ok or "Will be created" in msg:
            print(f"   {YELLOW}→ {msg}{RESET}")
    print()
    
    # Summary
    print(f"{BLUE}{'='*70}")
    all_file_ok = all(ok for _, ok, _ in file_results)
    all_endpoint_ok = all(ok for _, ok, _ in endpoint_results)
    
    if all_file_ok and all_endpoint_ok:
        print(f"{GREEN}✓ ALL CONNECTIONS VERIFIED{RESET}")
    else:
        print(f"{RED}✗ SOME ISSUES FOUND{RESET}")
        if not all_file_ok:
            print(f"   {RED}→ File path mismatches detected{RESET}")
        if not all_endpoint_ok:
            print(f"   {RED}→ Endpoint connection issues detected{RESET}")
    print(f"{'='*70}{RESET}")

if __name__ == "__main__":
    main()



