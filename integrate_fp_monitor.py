#!/usr/bin/env python3
"""
Integration script to add failure point monitoring to main.py
"""

import re
from pathlib import Path

def integrate_fp_monitor():
    """Add failure point monitoring to main.py"""
    main_file = Path("main.py")
    
    if not main_file.exists():
        print("main.py not found")
        return
    
    content = main_file.read_text()
    
    # Check if already integrated
    if "failure_point_monitor" in content:
        print("Failure point monitor already integrated")
        return
    
    # Find the main() function or if __name__ == "__main__"
    # Add import at top
    import_pattern = r"(from\s+.*import.*\n)"
    imports = re.findall(import_pattern, content)
    
    # Add import after other imports
    if "from failure_point_monitor import" not in content:
        # Find a good place to add the import (after other monitoring imports)
        if "from heartbeat_keeper import" in content:
            content = content.replace(
                "from heartbeat_keeper import",
                "from failure_point_monitor import get_failure_point_monitor\nfrom heartbeat_keeper import"
            )
        elif "import monitoring_guards" in content:
            content = content.replace(
                "import monitoring_guards",
                "import monitoring_guards\nfrom failure_point_monitor import get_failure_point_monitor"
            )
        else:
            # Add near top after standard imports
            content = content.replace(
                "import os\n",
                "import os\nfrom failure_point_monitor import get_failure_point_monitor\n"
            )
    
    # Add monitoring call in run_once() - find the end of run_once
    if "def run_once():" in content:
        # Find the return statement in run_once
        run_once_pattern = r"(def run_once\(\):.*?)(return\s+\{.*?\})"
        match = re.search(run_once_pattern, content, re.DOTALL)
        
        if match:
            run_once_body = match.group(1)
            return_stmt = match.group(2)
            
            # Add monitoring before return
            monitoring_code = """
        # FAILURE POINT MONITORING: Check all failure points
        try:
            fp_monitor = get_failure_point_monitor()
            readiness = fp_monitor.get_trading_readiness()
            if readiness["readiness"] == "BLOCKED":
                critical_fps = readiness.get("critical_fps", [])
                log_event("failure_points", "trading_blocked", 
                         critical_fps=critical_fps,
                         readiness=readiness["readiness"])
                print(f"[WARN] Trading BLOCKED by failure points: {', '.join(critical_fps)}", flush=True)
            elif readiness["readiness"] == "DEGRADED":
                warning_fps = readiness.get("warning_fps", [])
                log_event("failure_points", "trading_degraded",
                         warning_fps=warning_fps,
                         readiness=readiness["readiness"])
                print(f"[WARN] Trading DEGRADED - warnings: {', '.join(warning_fps)}", flush=True)
        except Exception as e:
            log_event("failure_points", "monitor_error", error=str(e))
"""
            
            new_return = monitoring_code + "\n        " + return_stmt
            content = content.replace(match.group(0), run_once_body + new_return)
    
    # Add periodic monitoring in main loop
    if "if __name__ == \"__main__\":" in content:
        # Add monitoring thread
        monitoring_thread_code = """
    # FAILURE POINT MONITORING: Periodic checks
    def run_fp_monitoring_periodic():
        \"\"\"Periodically check failure points and log readiness\"\"\"
        import time
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                fp_monitor = get_failure_point_monitor()
                readiness = fp_monitor.get_trading_readiness()
                
                if readiness["readiness"] != "READY":
                    critical_count = readiness.get("critical_count", 0)
                    warning_count = readiness.get("warning_count", 0)
                    print(f"[FP-MONITOR] Readiness: {readiness['readiness']} (Critical: {critical_count}, Warnings: {warning_count})", flush=True)
                    
                    # Log to file
                    log_file = Path("logs/failure_points.log")
                    log_file.parent.mkdir(exist_ok=True)
                    with log_file.open("a") as f:
                        f.write(f"{datetime.now().isoformat()} | {readiness['readiness']} | Critical: {critical_count}, Warnings: {warning_count}\\n")
            except Exception as e:
                print(f"[FP-MONITOR] Error: {e}", flush=True)
                time.sleep(60)  # Wait before retry
    
    fp_monitoring_thread = threading.Thread(target=run_fp_monitoring_periodic, daemon=True, name="FPMonitor")
    fp_monitoring_thread.start()
"""
        
        # Add after other threads
        if "healing_thread.start()" in content:
            content = content.replace(
                "healing_thread.start()",
                "healing_thread.start()\n    " + monitoring_thread_code
            )
        else:
            # Add before app.run or main loop
            content = content.replace(
                "if __name__ == \"__main__\":",
                "if __name__ == \"__main__\":\n    " + monitoring_thread_code
            )
    
    # Write back
    main_file.write_text(content)
    print("Failure point monitor integrated into main.py")

if __name__ == "__main__":
    integrate_fp_monitor()

