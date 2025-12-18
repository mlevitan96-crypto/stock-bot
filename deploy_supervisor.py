#!/usr/bin/env python3
"""
Deployment Supervisor V4 - Production-ready for Reserved VM deployments.
Dashboard starts FIRST with ZERO delay to bind port 5000 immediately.
"""

import os
import sys
import time
import signal
import subprocess
import threading
from datetime import datetime
from pathlib import Path

processes = {}
shutdown_flag = threading.Event()
start_time = time.time()

REQUIRED_DIRS = ["logs", "state", "data", "config", "state/heartbeats"]

SERVICES = [
    {
        "name": "dashboard",
        "cmd": ["python", "-u", "dashboard.py"],
        "delay": 0,
        "critical": False,  # Dashboard failure should NOT kill trading bot
        "port": 5000,
        "requires_secrets": False,  # Dashboard works without API keys
    },
    {
        "name": "uw-daemon",
        "cmd": ["python", "uw_flow_daemon.py"],
        "delay": 0,
        "critical": True,
        "requires_secrets": True,  # Needs UW_API_KEY
    },
    {
        "name": "trading-bot",
        "cmd": ["python", "main.py"],
        "delay": 0,
        "critical": True,
        "requires_secrets": True,  # Needs ALPACA_KEY, ALPACA_SECRET
    },
    {
        "name": "v4-research",
        "cmd": ["python", "v4_orchestrator.py"],
        "delay": 0,
        "critical": False,
        "requires_secrets": True,
        "one_shot": True,  # This script runs once and exits - don't restart
    },
    {
        "name": "heartbeat-keeper",
        "cmd": ["python", "heartbeat_keeper.py"],
        "delay": 0,
        "critical": False,
        "requires_secrets": False,
    },
]

def utc_now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

def log(msg):
    print(f"[SUPERVISOR] [{utc_now()}] {msg}", flush=True)

def log_event(event, **kwargs):
    import json
    entry = {"ts": utc_now(), "event": event, **kwargs}
    try:
        with open("logs/supervisor.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        log(f"Log write error: {e}")

def create_directories():
    log("Creating required directories...")
    for dir_path in REQUIRED_DIRS:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            log(f"  Created/verified: {dir_path}/")
        except Exception as e:
            log(f"  ERROR creating {dir_path}: {e}")

secrets_available = False

def check_secrets():
    global secrets_available
    log("Checking required secrets...")
    required = ["UW_API_KEY", "ALPACA_KEY", "ALPACA_SECRET"]
    optional = ["SESSION_SECRET", "GMAIL_APP_PASSWORD"]
    
    missing_required = [s for s in required if not os.getenv(s)]
    missing_optional = [s for s in optional if not os.getenv(s)]
    
    if missing_required:
        log(f"  WARNING: Missing secrets: {missing_required}")
        log(f"  Dashboard will run, but trading services will be SKIPPED")
        log(f"  Add secrets in Publishing > Configuration > Environment Variables")
        secrets_available = False
        return False
    else:
        log(f"  All required secrets are set")
        secrets_available = True
    
    if missing_optional:
        log(f"  Note: Missing optional secrets: {missing_optional}")
    
    return True

def start_service(service):
    name = service["name"]
    cmd = service["cmd"]
    log(f"Starting service {name} with command: {' '.join(cmd)}")
    
    if name in processes:
        proc = processes[name]
        if proc and proc.poll() is None:
            log(f"Service {name} already running (PID: {proc.pid})")
            return True
    
    script_file = None
    for arg in cmd[1:]:
        if arg.endswith('.py'):
            script_file = arg
            break
    if script_file and not Path(script_file).exists():
        log(f"ERROR: Service file not found: {script_file}")
        return False
    
    log(f"Starting {name}: {' '.join(cmd)}")
    log_event("SERVICE_START", service=name)
    
    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"  # Ensure logs flush immediately for crash debugging
        if name == "trading-bot":
            env["API_PORT"] = "8081"
        elif name == "dashboard":
            # Check if port 5000 is already in use (proxy might be running)
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            port_5000_in_use = sock.connect_ex(('127.0.0.1', 5000)) == 0
            sock.close()
            if port_5000_in_use:
                # Port 5000 is in use - likely proxy is running
                # Dashboard should use 5001 (instance A) or check deployment state
                env["PORT"] = "5001"
                log(f"Port 5000 in use - dashboard will use port 5001")
            # If port 5000 is free, dashboard can use it directly
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        processes[name] = proc
        
        def stream_output(proc, name):
            try:
                for line in proc.stdout:
                    print(f"[{name}] {line.rstrip()}", flush=True)
            except:
                pass
        
        thread = threading.Thread(target=stream_output, args=(proc, name), daemon=True)
        thread.start()
        
        time.sleep(0.5)
        if proc.poll() is not None:
            log(f"ERROR: {name} exited immediately with code {proc.returncode}")
            return False
        
        log(f"Service {name} started successfully (PID: {proc.pid})")
        return True
    except Exception as e:
        log(f"ERROR starting {name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def wait_for_port(port, timeout=15):
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.3)
    return False

def shutdown_handler(signum, frame):
    log("Shutdown signal received")
    shutdown_flag.set()
    
    for name, proc in processes.items():
        if proc and proc.poll() is None:
            log(f"Terminating {name}...")
            try:
                proc.terminate()
            except:
                pass
    
    time.sleep(2)
    
    for name, proc in processes.items():
        if proc and proc.poll() is None:
            log(f"Killing {name}...")
            try:
                proc.kill()
            except:
                pass
    
    log("All services stopped")
    sys.exit(0)

def rotate_logs():
    """Rotate large log files to prevent disk filling."""
    max_size_mb = 5
    max_lines = 2000
    try:
        patterns = [
            "logs/*.jsonl", "logs/*.log", 
            "data/*.jsonl", "state/*.jsonl",
            "feature_store/*.jsonl"
        ]
        for pattern in patterns:
            for filepath in Path(".").glob(pattern):
                try:
                    size_mb = filepath.stat().st_size / (1024 * 1024)
                    if size_mb > max_size_mb:
                        log(f"Rotating {filepath} ({size_mb:.1f}MB)")
                        lines = filepath.read_text().splitlines()
                        filepath.write_text("\n".join(lines[-max_lines:]) + "\n")
                except:
                    pass
    except:
        pass

def startup_cleanup():
    """Aggressive cleanup on startup to prevent disk issues."""
    log("Running startup cleanup...")
    max_size_mb = 10
    max_lines = 3000
    cleaned = 0
    patterns = [
        "logs/*.jsonl", "logs/*.log",
        "data/*.jsonl", "state/*.jsonl",
        "feature_store/*.jsonl"
    ]
    for pattern in patterns:
        for filepath in Path(".").glob(pattern):
            try:
                size_mb = filepath.stat().st_size / (1024 * 1024)
                if size_mb > max_size_mb:
                    log(f"  Truncating {filepath} ({size_mb:.1f}MB)")
                    lines = filepath.read_text().splitlines()
                    filepath.write_text("\n".join(lines[-max_lines:]) + "\n")
                    cleaned += 1
            except:
                pass
    log(f"Startup cleanup complete: {cleaned} files truncated")

def main():
    log("="*60)
    log("DEPLOYMENT SUPERVISOR V4 STARTING")
    log(f"Python: {sys.executable}")
    log(f"Working dir: {os.getcwd()}")
    log(f"Time: {utc_now()}")
    log("="*60)
    
    create_directories()
    startup_cleanup()
    
    if not check_secrets():
        log("WARNING: Continuing despite missing secrets...")
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    dashboard_service = SERVICES[0]
    log("="*60)
    log("STARTING DASHBOARD FIRST (port 5000)")
    log("="*60)
    
    dashboard_ok = start_service(dashboard_service)
    if not dashboard_ok:
        log("WARNING: Dashboard failed to start, proceeding with Trading Bot...")
        log_event("DASHBOARD_START_FAILED")
    else:
        log("Waiting for port 5000 to be ready...")
        if wait_for_port(5000, timeout=90):
            log("Port 5000 is READY - deployment should succeed")
            log_event("PORT_5000_READY")
        else:
            log("WARNING: Port 5000 not detected after 90s, proceeding anyway...")
            log_event("PORT_5000_TIMEOUT")
    
    # Brief pause to let health checks register, then start other services
    log("Waiting 15s for health checks to stabilize...")
    time.sleep(15)
    
    log("Starting remaining services...")
    
    for service in SERVICES[1:]:
        # Skip services that require secrets if secrets aren't available
        if service.get("requires_secrets", False) and not secrets_available:
            log(f"SKIPPING {service['name']} - requires secrets (not configured)")
            continue
        
        delay = service.get("delay", 0)
        if delay > 0:
            log(f"Waiting {delay}s before starting {service['name']}...")
            time.sleep(delay)
        
        success = start_service(service)
        if not success and service.get("critical", False):
            log(f"WARNING: Critical service {service['name']} failed to start")
    
    log("="*60)
    log("ALL SERVICES STARTED - ENTERING MONITORING LOOP")
    log("="*60)
    log_event("SUPERVISOR_READY")
    
    last_rotation = time.time()
    rotation_interval = 1800
    last_status = time.time()
    status_interval = 300
    
    while not shutdown_flag.is_set():
        time.sleep(30)
        
        for service in SERVICES:
            name = service["name"]
            # Skip services that require secrets if not available
            if service.get("requires_secrets", False) and not secrets_available:
                continue
            # Skip one-shot services (they exit intentionally)
            if service.get("one_shot", False):
                continue
            proc = processes.get(name)
            if proc:
                if proc.poll() is not None:
                    exit_code = proc.returncode
                    log(f"Service {name} died (exit code {exit_code}), restarting...")
                    log_event("SERVICE_DIED", service=name, exit_code=exit_code)
                    time.sleep(5)
                    start_service(service)
        
        if time.time() - last_rotation >= rotation_interval:
            rotate_logs()
            last_rotation = time.time()
        
        if time.time() - last_status >= status_interval:
            log("-" * 40)
            log("SERVICE STATUS:")
            for name, proc in processes.items():
                if proc:
                    status = "RUNNING" if proc.poll() is None else f"EXITED({proc.returncode})"
                    log(f"  {name}: {status}")
            log(f"Uptime: {int((time.time() - start_time) / 60)} minutes")
            log("-" * 40)
            last_status = time.time()
    
    log("Supervisor exiting")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
