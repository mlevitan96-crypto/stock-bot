#!/usr/bin/env python3
"""
Deployment Supervisor V4 - Production-ready for Reserved VM deployments.
Dashboard starts FIRST with ZERO delay to bind port 5000 immediately.

IMPORTANT: For project context, common issues, and solutions, see MEMORY_BANK.md
"""

from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles, Directories
import os
import sys
import time
import signal
import subprocess
import threading
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

# Load .env file if it exists
# CRITICAL: This file contains live trading credentials. DO NOT overwrite.
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Explicitly load from /root/stock-bot/.env to ensure correct path
    # This matches the systemd EnvironmentFile path
    env_path = Path("/root/stock-bot/.env")
    if env_path.exists():
        # Check if .env was recently modified (possible overwrite warning)
        env_mtime = env_path.stat().st_mtime
        script_mtime = Path(__file__).stat().st_mtime
        if env_mtime > script_mtime:
            print(f"[SUPERVISOR] WARNING: .env file ({env_path}) was modified after deploy_supervisor.py")
            print(f"[SUPERVISOR] This may indicate an accidental overwrite. Verify credentials are correct.")
        
        load_dotenv(env_path, override=True)
        
        # CRITICAL: Validate required credentials are present and non-empty
        required_keys = ["ALPACA_KEY", "ALPACA_SECRET", "UW_API_KEY"]
        missing_or_empty = []
        for key in required_keys:
            value = os.getenv(key)
            if not value or value.strip() == "":
                missing_or_empty.append(key)
        
        if missing_or_empty:
            print(f"[SUPERVISOR] CRITICAL ERROR: Required credentials missing or empty: {missing_or_empty}")
            print(f"[SUPERVISOR] The .env file at {env_path} must contain valid credentials.")
            print(f"[SUPERVISOR] DO NOT overwrite this file with templates or empty values.")
            sys.exit(1)
    else:
        print(f"[SUPERVISOR] CRITICAL ERROR: .env file not found at {env_path}")
        print(f"[SUPERVISOR] The .env file is required for trading operations.")
        sys.exit(1)
except ImportError:
    print("[SUPERVISOR] CRITICAL ERROR: python-dotenv not available. Cannot load credentials.")
    sys.exit(1)

processes = {}
shutdown_flag = threading.Event()
start_time = time.time()

REQUIRED_DIRS = ["logs", "state", "data", "config", "state/heartbeats"]

# Health registry
health_registry = {}
health_lock = threading.Lock()
HEALTH_FILE = Directories.STATE / "health.json"

# Chaos mode (for testing)
CHAOS_MODE = os.getenv("CHAOS_MODE", "off").lower()

# Droplet identity verification
def verify_droplet_identity():
    """Verify this is running on the correct droplet."""
    try:
        import requests
        expected_ip = "104.236.102.57"
        actual_ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
        if actual_ip != expected_ip:
            raise RuntimeError(
                f"WRONG DROPLET: Expected {expected_ip} (ubuntu-s-1vcpu-2gb-nyc3-01-alpaca), "
                f"got {actual_ip}. Deployment aborted for safety."
            )
        print(f"[SUPERVISOR] Droplet identity verified: {actual_ip}")
    except Exception as e:
        # Don't fail if network check fails, but log warning
        print(f"[SUPERVISOR] WARNING: Could not verify droplet identity: {e}")

# Verify droplet identity on startup
verify_droplet_identity()

# Use sys.executable to ensure we use the same Python interpreter
PYTHON_EXEC = sys.executable

SERVICES = [
    {
        "name": "dashboard",
        "cmd": [PYTHON_EXEC, "-u", "dashboard.py"],
        "delay": 0,
        "critical": False,  # Dashboard failure should NOT kill trading bot
        "port": 5000,
        "requires_secrets": False,  # Dashboard works without API keys
    },
    {
        "name": "uw-daemon",
        "cmd": [PYTHON_EXEC, "uw_flow_daemon.py"],
        "delay": 0,
        "critical": True,
        "requires_secrets": True,  # Needs UW_API_KEY
    },
    {
        "name": "trading-bot",
        # CRITICAL: main.py no longer starts the engine on import; it must be executed as a script.
        # Use -u for unbuffered logs to make restarts/debugging visible immediately.
        "cmd": [PYTHON_EXEC, "-u", "main.py"],
        "delay": 0,
        "critical": True,
        "requires_secrets": True,  # Needs ALPACA_KEY, ALPACA_SECRET
    },
    {
        "name": "v4-research",
        "cmd": [PYTHON_EXEC, "v4_orchestrator.py"],
        "delay": 0,
        "critical": False,
        "requires_secrets": True,
        "one_shot": True,  # This script runs once and exits - don't restart
    },
    {
        "name": "heartbeat-keeper",
        "cmd": [PYTHON_EXEC, "heartbeat_keeper.py"],
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

# =========================
# HEALTH REGISTRY & AGGREGATION
# =========================

def update_service_health(service_name: str, status: str, error_message: Optional[str] = None):
    """
    Update health status for a service.
    
    Args:
        service_name: Service name
        status: "OK", "DEGRADED", or "FAILED"
        error_message: Optional error message
    """
    with health_lock:
        if service_name not in health_registry:
            health_registry[service_name] = {
                "name": service_name,
                "pid": None,
                "last_heartbeat_time": None,
                "status": "UNKNOWN",
                "last_error_message": None,
                "last_updated": None
            }
        
        health_registry[service_name]["status"] = status
        health_registry[service_name]["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        if error_message:
            health_registry[service_name]["last_error_message"] = error_message
        
        # Update PID if process exists
        if service_name in processes and processes[service_name]:
            health_registry[service_name]["pid"] = processes[service_name].pid
        
        # Update heartbeat time
        health_registry[service_name]["last_heartbeat_time"] = datetime.now(timezone.utc).isoformat()
        
        # Don't persist health during initialization - it's called too frequently and can block
        # Health will be persisted later in the monitoring loop

def compute_overall_health() -> Dict[str, any]:
    """
    Compute overall system health from service health registry.
    
    Returns:
        Dict with overall_status and per-service details
    """
    with health_lock:
        critical_services = ["trading-bot", "uw-daemon", "heartbeat-keeper"]
        supportive_services = ["dashboard"]
        
        overall_status = "OK"
        service_statuses = {}
        
        # Check critical services
        for service_name in critical_services:
            service_health = health_registry.get(service_name, {})
            status = service_health.get("status", "UNKNOWN")
            service_statuses[service_name] = status
            
            if status == "FAILED":
                overall_status = "FAILED"
            elif status == "DEGRADED" and overall_status == "OK":
                overall_status = "DEGRADED"
        
        # Check supportive services
        for service_name in supportive_services:
            service_health = health_registry.get(service_name, {})
            status = service_health.get("status", "UNKNOWN")
            service_statuses[service_name] = status
            
            if status == "FAILED" and overall_status == "OK":
                overall_status = "DEGRADED"
        
        return {
            "overall_status": overall_status,
            "services": service_statuses,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": health_registry.copy()
        }

def persist_health():
    """Persist health registry to health.json."""
    try:
        health_data = compute_overall_health()
        Directories.STATE.mkdir(parents=True, exist_ok=True)
        
        # Atomic write with timeout protection
        tmp_file = HEALTH_FILE.with_suffix(".tmp")
        try:
            with open(tmp_file, 'w') as f:
                json.dump(health_data, f, indent=2)
            tmp_file.replace(HEALTH_FILE)
        except (IOError, OSError) as e:
            # File write error - log but don't fail
            log(f"Failed to write health file (non-critical): {e}")
    except Exception as e:
        log(f"Failed to persist health: {e}")

def check_api_compatibility():
    """
    Check API compatibility on startup.
    
    Returns:
        Tuple of (all_ok: bool, errors: List[str])
    """
    errors = []
    
    # Check Alpaca API
    try:
        from alpaca_client import check_alpaca_compat
        alpaca_key = os.getenv("ALPACA_KEY")
        alpaca_secret = os.getenv("ALPACA_SECRET")
        alpaca_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if alpaca_key and alpaca_secret:
            is_ok, error = check_alpaca_compat(alpaca_key, alpaca_secret, alpaca_url)
            if not is_ok:
                errors.append(f"Alpaca API: {error}")
                update_service_health("trading-bot", "FAILED", f"API compatibility check failed: {error}")
            else:
                log("Alpaca API compatibility check passed")
        else:
            log("Skipping Alpaca API check (credentials not available)")
    except Exception as e:
        errors.append(f"Alpaca API check error: {e}")
        log(f"Alpaca API compatibility check failed: {e}")
    
    # Check UW API
    try:
        from uw_client import check_uw_compat
        uw_key = os.getenv("UW_API_KEY")
        uw_url = os.getenv("UW_BASE_URL", "https://api.unusualwhales.com")
        
        if uw_key:
            is_ok, error = check_uw_compat(uw_key, uw_url)
            if not is_ok:
                errors.append(f"UW API: {error}")
                update_service_health("uw-daemon", "FAILED", f"API compatibility check failed: {error}")
            else:
                log("UW API compatibility check passed")
        else:
            log("Skipping UW API check (credentials not available)")
    except Exception as e:
        errors.append(f"UW API check error: {e}")
        log(f"UW API compatibility check failed: {e}")
    
    return len(errors) == 0, errors

# =========================
# CHAOS TESTING HOOKS
# =========================

def apply_chaos_mode():
    """Apply chaos mode if enabled."""
    if CHAOS_MODE == "off":
        return
    
    log(f"CHAOS MODE ENABLED: {CHAOS_MODE}")
    
    if CHAOS_MODE == "supervisor_crash":
        log("CHAOS: Simulating supervisor crash in 10 seconds...")
        import threading
        def crash():
            time.sleep(10)
            log("CHAOS: Supervisor crashing now!")
            os._exit(1)
        threading.Thread(target=crash, daemon=True).start()
    
    elif CHAOS_MODE == "alpaca_down":
        log("CHAOS: Alpaca API will fail (simulated)")
        # This will be handled by alpaca_client.py if it detects CHAOS_MODE
    
    elif CHAOS_MODE == "invalid_creds":
        log("CHAOS: Invalid credentials mode (simulated)")
        # Override credentials in process only (not in .env)
        os.environ["ALPACA_KEY"] = "INVALID_KEY"
        os.environ["ALPACA_SECRET"] = "INVALID_SECRET"
    
    elif CHAOS_MODE == "state_corrupt":
        log("CHAOS: Corrupting state file...")
        state_file = Directories.STATE / "trading_state.json"
        if state_file.exists():
            # Write invalid JSON
            state_file.write_text("{ invalid json }")
            log("CHAOS: State file corrupted")

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
    cmd = service["cmd"].copy()  # Make a copy to avoid modifying the original
    
    # Replace "python" with sys.executable for systemd compatibility
    if cmd[0] == "python":
        cmd[0] = sys.executable
    
    log(f"Starting service {name} with command: {' '.join(cmd)}")
    
    # Initialize health registry entry
    update_service_health(name, "OK")
    
    if name in processes:
        proc = processes[name]
        if proc and proc.poll() is None:
            log(f"Service {name} already running (PID: {proc.pid})")
            update_service_health(name, "OK")
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
    if name == "trading-bot":
        # Explicit trading engine start visibility.
        log_event("TRADING_ENGINE_STARTING", service=name, entrypoint="main.py", cmd=" ".join(cmd), python=cmd[0])
    
    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"  # Ensure logs flush immediately for crash debugging
        if name == "trading-bot":
            env["API_PORT"] = "8081"
        elif name == "dashboard":
            # Check if ports are in use and find an available one
            import socket
            for port in [5000, 5001, 5002, 5003]:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                if result != 0:  # Port is free
                    env["PORT"] = str(port)
                    log(f"Dashboard will use port {port}")
                    break
            else:
                # All ports in use - kill processes on 5000-5003
                log(f"WARNING: All ports 5000-5003 in use, attempting to free port 5002")
                try:
                    subprocess.run(["fuser", "-k", "5002/tcp"], stderr=subprocess.DEVNULL, timeout=2)
                    time.sleep(1)
                except:
                    pass
                env["PORT"] = "5002"
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,  # Prevent child from reading from terminal
            bufsize=1,
            universal_newlines=True,
            env=env,
            start_new_session=False  # Keep in same process group (don't detach from terminal)
        )
        processes[name] = proc
        log_event("SERVICE_STARTED", service=name, pid=proc.pid, cmd=" ".join(cmd))
        if name == "trading-bot":
            log_event("TRADING_ENGINE_STARTED", pid=proc.pid, cmd=" ".join(cmd), api_port=env.get("API_PORT"))
        
        def stream_output(proc, name):
            try:
                for line in proc.stdout:
                    print(f"[{name}] {line.rstrip()}", flush=True)
            except:
                pass
        
        thread = threading.Thread(target=stream_output, args=(proc, name), daemon=True)
        thread.start()
        
        # Wait longer and check multiple times to catch immediate crashes
        time.sleep(2)  # Increased from 0.5 to 2 seconds
        if proc.poll() is not None:
            exit_code = proc.returncode
            log(f"ERROR: {name} exited immediately with code {exit_code}")
            # Try to capture stderr for debugging
            try:
                if proc.stderr:
                    stderr_output = proc.stderr.read()
                    if stderr_output:
                        log(f"STDERR from {name}: {stderr_output[:500]}")
            except:
                pass
            log_event("SERVICE_EXITED_IMMEDIATELY", service=name, exit_code=exit_code)
            return False
        
        # Check again after another second to catch delayed crashes
        time.sleep(1)
        if proc.poll() is not None:
            exit_code = proc.returncode
            log(f"ERROR: {name} exited after 3 seconds with code {exit_code}")
            log_event("SERVICE_EXITED_EARLY", service=name, exit_code=exit_code)
            return False
        
        log(f"Service {name} started successfully (PID: {proc.pid})")
        update_service_health(name, "OK")
        return True
    except Exception as e:
        log(f"ERROR starting {name}: {e}")
        update_service_health(name, "FAILED", str(e))
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
        def _tail_text(path: Path, n: int) -> str:
            """Read last N lines without loading whole file into memory."""
            try:
                res = subprocess.run(
                    ["tail", "-n", str(n), str(path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if res.returncode == 0:
                    return res.stdout
                return ""
            except Exception:
                return ""

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
                        tail_txt = _tail_text(filepath, max_lines)
                        if tail_txt:
                            # Ensure newline terminator
                            if not tail_txt.endswith("\n"):
                                tail_txt += "\n"
                            filepath.write_text(tail_txt)
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
    def _tail_text(path: Path, n: int) -> str:
        """Read last N lines without loading whole file into memory."""
        try:
            res = subprocess.run(
                ["tail", "-n", str(n), str(path)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if res.returncode == 0:
                return res.stdout
            return ""
        except Exception:
            return ""

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
                    tail_txt = _tail_text(filepath, max_lines)
                    if tail_txt:
                        if not tail_txt.endswith("\n"):
                            tail_txt += "\n"
                        filepath.write_text(tail_txt)
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
    
    # Apply chaos mode if enabled
    apply_chaos_mode()
    
    create_directories()
    startup_cleanup()
    
    log("Initializing health registry...")
    # Initialize health registry
    try:
        for service in SERVICES:
            log(f"  Initializing {service['name']}...")
            update_service_health(service["name"], "UNKNOWN")
            log(f"  {service['name']} initialized")
        log("Health registry initialized")
    except Exception as e:
        log(f"ERROR initializing health registry: {e}")
        import traceback
        traceback.print_exc()
        # Continue anyway
    
    # Check API compatibility (with timeout to prevent hanging)
    log("Checking API compatibility...")
    try:
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("API compatibility check timed out")
        
        # Set 30 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            api_ok, api_errors = check_api_compatibility()
            signal.alarm(0)  # Cancel timeout
            if not api_ok:
                log(f"WARNING: API compatibility checks failed: {api_errors}")
                log("System will continue but trading may be disabled")
        except TimeoutError:
            signal.alarm(0)  # Cancel timeout
            log("WARNING: API compatibility check timed out after 30s, continuing anyway...")
            log("System will continue but trading may be disabled")
            api_ok, api_errors = False, ["Timeout"]
    except (AttributeError, OSError):
        # signal.SIGALRM not available on Windows or some systems, use threading timeout instead
        import threading
        
        api_check_result = [None, None]
        api_check_exception = [None]
        
        def run_api_check():
            try:
                api_check_result[0], api_check_result[1] = check_api_compatibility()
            except Exception as e:
                api_check_exception[0] = e
        
        thread = threading.Thread(target=run_api_check, daemon=True)
        thread.start()
        thread.join(timeout=30)
        
        if thread.is_alive():
            log("WARNING: API compatibility check timed out after 30s, continuing anyway...")
            log("System will continue but trading may be disabled")
            api_ok, api_errors = False, ["Timeout"]
        elif api_check_exception[0]:
            log(f"WARNING: API compatibility check failed: {api_check_exception[0]}")
            log("System will continue but trading may be disabled")
            api_ok, api_errors = False, [str(api_check_exception[0])]
        else:
            api_ok, api_errors = api_check_result[0], api_check_result[1]
            if not api_ok:
                log(f"WARNING: API compatibility checks failed: {api_errors}")
                log("System will continue but trading may be disabled")
    
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
    
    # Track service failure counts for self-healing
    service_failure_counts = {}
    service_failure_window_start = {}
    MAX_FAILURES_IN_WINDOW = 5
    FAILURE_WINDOW_MINUTES = 10
    
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
                    log(f"Service {name} died (exit code {exit_code})")
                    if name == "trading-bot":
                        log_event("TRADING_ENGINE_EXITED", service=name, exit_code=exit_code, pid=getattr(proc, "pid", None))
                    
                    # Track failures
                    now = time.time()
                    if name not in service_failure_counts:
                        service_failure_counts[name] = 0
                        service_failure_window_start[name] = now
                    
                    # Reset window if expired
                    if now - service_failure_window_start[name] > FAILURE_WINDOW_MINUTES * 60:
                        service_failure_counts[name] = 0
                        service_failure_window_start[name] = now
                    
                    service_failure_counts[name] += 1
                    
                    # Check if service should be marked as FAILED
                    if service_failure_counts[name] >= MAX_FAILURES_IN_WINDOW:
                        log(f"CRITICAL: Service {name} failed {service_failure_counts[name]} times in {FAILURE_WINDOW_MINUTES} minutes")
                        log(f"Marking {name} as FAILED and stopping restart attempts")
                        update_service_health(name, "FAILED", f"Repeated failures: {service_failure_counts[name]} in {FAILURE_WINDOW_MINUTES}min")
                        log_event("SERVICE_FAILED_REPEATEDLY", service=name, failure_count=service_failure_counts[name])
                        # Don't restart - wait for manual intervention or cooldown
                    else:
                        log(f"Restarting {name} (failure {service_failure_counts[name]}/{MAX_FAILURES_IN_WINDOW})...")
                        log_event("SERVICE_DIED", service=name, exit_code=exit_code, failure_count=service_failure_counts[name])
                        if name == "trading-bot":
                            log_event("TRADING_ENGINE_RESTARTING", service=name, failure_count=service_failure_counts[name], exit_code=exit_code)
                        update_service_health(name, "DEGRADED", f"Restarting after failure (count: {service_failure_counts[name]})")
                        time.sleep(5)
                        start_service(service)
                else:
                    # Service is running - update health
                    update_service_health(name, "OK")
                    # Reset failure count on success
                    if name in service_failure_counts:
                        service_failure_counts[name] = 0
        
        if time.time() - last_rotation >= rotation_interval:
            rotate_logs()
            last_rotation = time.time()
        
        if time.time() - last_status >= status_interval:
            log("-" * 40)
            log("SERVICE STATUS:")
            for name, proc in processes.items():
                if proc:
                    status = "RUNNING" if proc.poll() is None else f"EXITED({proc.returncode})"
                    health_status = health_registry.get(name, {}).get("status", "UNKNOWN")
                    log(f"  {name}: {status} (health: {health_status})")
            
            # Log overall health
            overall_health = compute_overall_health()
            log(f"OVERALL SYSTEM HEALTH: {overall_health['overall_status']}")
            log(f"Uptime: {int((time.time() - start_time) / 60)} minutes")
            log("-" * 40)
            
            # Persist health
            persist_health()
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
