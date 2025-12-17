#!/usr/bin/env python3
"""
Zero-Downtime A/B Deployment System
====================================
Production-grade deployment with automatic health checks and rollback.

Features:
- A/B instance switching (zero downtime)
- Automatic health validation before switch
- Instant rollback on failure
- State preservation (cache, positions, logs)
- Single command deployment
- Safe for market hours
"""

import os
import sys
import json
import time
import shutil
import subprocess
import requests
import signal
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

def find_root_directory() -> Path:
    """Auto-detect root directory (git root or script location)."""
    # Try to find git root from current directory
    current = Path.cwd()
    for path in [current] + list(current.parents):
        if (path / ".git").exists():
            return path
    
    # Fallback: use script location
    script_path = Path(__file__).resolve()
    return script_path.parent

# Auto-detect root directory
BASE_DIR = find_root_directory()
INSTANCE_A_DIR = BASE_DIR / "instance_a"
INSTANCE_B_DIR = BASE_DIR / "instance_b"
STATE_FILE = BASE_DIR / "state" / "deployment_state.json"
HEALTH_CHECK_TIMEOUT = 30  # seconds
HEALTH_CHECK_RETRIES = 3
ROLLBACK_ON_FAILURE = True

# Ports for A/B instances
PORT_A = 5001  # Instance A port (internal)
PORT_B = 5002  # Instance B port (internal)
PROXY_PORT = 5000  # Public-facing port (always 5000 - routes to active instance)

print(f"[DEPLOY] Detected root directory: {BASE_DIR}")

class ZeroDowntimeDeployer:
    """Zero-downtime A/B deployment system."""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_state = self._load_state()
        
    def _load_state(self) -> Dict[str, Any]:
        """Load current deployment state."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {
            "active_instance": "A",
            "last_deployment": None,
            "deployment_history": []
        }
    
    def _save_state(self):
        """Save deployment state."""
        self.state_file.write_text(json.dumps(self.current_state, indent=2))
    
    def _get_active_instance(self) -> Tuple[Path, int]:
        """Get active instance directory and port."""
        if self.current_state["active_instance"] == "A":
            return INSTANCE_A_DIR, PORT_A
        else:
            return INSTANCE_B_DIR, PORT_B
    
    def _get_staging_instance(self) -> Tuple[Path, int]:
        """Get staging instance directory and port."""
        if self.current_state["active_instance"] == "A":
            return INSTANCE_B_DIR, PORT_B
        else:
            return INSTANCE_A_DIR, PORT_A
    
    def _ensure_instance_dirs(self):
        """Ensure both instance directories exist and shared resources are linked."""
        for instance_dir in [INSTANCE_A_DIR, INSTANCE_B_DIR]:
            instance_dir.mkdir(parents=True, exist_ok=True)
            # Create symlinks for shared resources (relative paths for portability)
            for shared_dir in ["data", "state", "logs", "config"]:
                shared_path = BASE_DIR / shared_dir
                instance_link = instance_dir / shared_dir
                
                # Remove if it's a broken symlink or wrong type
                if instance_link.exists():
                    if instance_link.is_symlink():
                        try:
                            instance_link.resolve()  # Check if symlink is valid
                        except:
                            instance_link.unlink()  # Remove broken symlink
                    elif instance_link.is_dir() and not instance_link.is_symlink():
                        # If it's a real directory, remove it (should be symlink)
                        shutil.rmtree(instance_link)
                    elif instance_link.is_file():
                        instance_link.unlink()
                
                # Create symlink to shared resource
                if shared_path.exists() and not instance_link.exists():
                    try:
                        # Use relative path for symlink (more portable)
                        rel_path = os.path.relpath(shared_path, instance_dir)
                        instance_link.symlink_to(rel_path)
                        print(f"[DEPLOY] Created symlink: {instance_link} -> {shared_path}")
                    except Exception as e:
                        print(f"[DEPLOY] Warning: Could not create symlink for {shared_dir}: {e}")
    
    def _clone_to_staging(self) -> bool:
        """Clone current codebase to staging instance."""
        staging_dir, staging_port = self._get_staging_instance()
        
        print(f"[DEPLOY] Cloning to staging instance: {staging_dir}")
        
        try:
            # Remove old staging if exists (preserve symlinks)
            if staging_dir.exists():
                for item in staging_dir.iterdir():
                    if item.is_symlink():
                        continue  # Preserve symlinks to shared resources
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        try:
                            item.unlink()
                        except:
                            pass
            
            # Copy all files except instance directories and shared dirs
            exclude_patterns = {".git", "__pycache__", "instance_a", "instance_b", "venv"}
            shared_dirs = {"data", "state", "logs", "config"}  # These are symlinked
            
            for item in BASE_DIR.iterdir():
                if item.name in exclude_patterns or item.name.startswith("instance_"):
                    continue
                if item.is_dir() and item.name in shared_dirs:
                    continue  # These are symlinked, don't copy
                
                dest = staging_dir / item.name
                if dest.exists():
                    continue  # Skip if already exists
                
                try:
                    if item.is_dir():
                        shutil.copytree(
                            item, dest, 
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "*.pyc"),
                            dirs_exist_ok=True
                        )
                    else:
                        shutil.copy2(item, dest)
                except Exception as e:
                    print(f"[DEPLOY] Warning: Could not copy {item.name}: {e}")
                    continue
            
            # Ensure venv is symlinked (don't copy, use shared venv)
            venv_source = BASE_DIR / "venv"
            venv_staging = staging_dir / "venv"
            if venv_source.exists():
                if venv_staging.exists() and not venv_staging.is_symlink():
                    shutil.rmtree(venv_staging)
                if not venv_staging.exists():
                    rel_venv = os.path.relpath(venv_source, staging_dir)
                    venv_staging.symlink_to(rel_venv)
            
            print(f"[DEPLOY] Staging instance prepared at {staging_dir}")
            return True
            
        except Exception as e:
            print(f"[DEPLOY] Error cloning to staging: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _pull_latest_code(self) -> bool:
        """Pull latest code from git in base directory, then sync to staging."""
        print(f"[DEPLOY] Pulling latest code from git")
        
        try:
            # Pull in base directory (where git repo is)
            result = subprocess.run(
                ["git", "pull", "origin", "main", "--no-rebase"],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"[DEPLOY] Git pull failed: {result.stderr}")
                return False
            
            print(f"[DEPLOY] Code updated successfully in base directory")
            return True
            
        except Exception as e:
            print(f"[DEPLOY] Error pulling code: {e}")
            return False
    
    def _check_health(self, port: int, instance_name: str) -> bool:
        """Check health of instance on given port."""
        print(f"[DEPLOY] Checking health of {instance_name} on port {port}")
        
        for attempt in range(HEALTH_CHECK_RETRIES):
            try:
                response = requests.get(
                    f"http://localhost:{port}/health",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") in ["healthy", "ok"]:
                        print(f"[DEPLOY] {instance_name} health check passed")
                        return True
                
                print(f"[DEPLOY] {instance_name} health check failed (attempt {attempt + 1}/{HEALTH_CHECK_RETRIES})")
                
            except Exception as e:
                print(f"[DEPLOY] {instance_name} health check error (attempt {attempt + 1}/{HEALTH_CHECK_RETRIES}): {e}")
            
            if attempt < HEALTH_CHECK_RETRIES - 1:
                time.sleep(2)
        
        return False
    
    def _ensure_proxy_running(self) -> bool:
        """Ensure dashboard proxy is running on port 5000."""
        import socket
        
        # Check if port 5000 is in use
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', PROXY_PORT))
        sock.close()
        
        if result == 0:
            # Port is in use - check if it's our proxy
            try:
                # Check if it's the proxy by hitting its health endpoint
                response = requests.get(f"http://localhost:{PROXY_PORT}/proxy/health", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("proxy"):
                        print(f"[DEPLOY] Proxy already running on port {PROXY_PORT}")
                        return True
            except:
                pass
            
            # If not proxy, try to identify and stop what's running
            try:
                result = subprocess.run(
                    ["lsof", "-ti", f":{PROXY_PORT}"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    pid = result.stdout.strip()
                    # Check if it's dashboard.py (old) - kill it to make room for proxy
                    result2 = subprocess.run(
                        ["ps", "-p", pid, "-o", "args="],
                        capture_output=True,
                        text=True
                    )
                    if result2.returncode == 0:
                        cmd = result2.stdout
                        if "dashboard.py" in cmd and "instance" not in cmd and "dashboard_proxy" not in cmd:
                            # Old dashboard from supervisor - kill it
                            print(f"[DEPLOY] Stopping old dashboard on port {PROXY_PORT} (PID: {pid})")
                            subprocess.run(["kill", "-9", pid], timeout=5)
                            time.sleep(2)
            except:
                pass
        
        # Start proxy
        print(f"[DEPLOY] Starting dashboard proxy on port {PROXY_PORT}")
        proxy_script = BASE_DIR / "dashboard_proxy.py"
        if not proxy_script.exists():
            print(f"[DEPLOY] Warning: dashboard_proxy.py not found, skipping proxy")
            return False
        
        venv_python = BASE_DIR / "venv" / "bin" / "python3"
        if not venv_python.exists():
            venv_python = Path("/usr/bin/python3")
        
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            proxy_process = subprocess.Popen(
                [str(venv_python), str(proxy_script)],
                cwd=str(BASE_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            time.sleep(3)
            if proxy_process.poll() is None:
                print(f"[DEPLOY] Proxy started (PID: {proxy_process.pid})")
                # Verify it's responding
                time.sleep(2)
                try:
                    response = requests.get(f"http://localhost:{PROXY_PORT}/proxy/health", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("proxy"):
                            print(f"[DEPLOY] Proxy verified and responding")
                            return True
                except:
                    print(f"[DEPLOY] Warning: Proxy started but not responding yet")
                return True
            else:
                stdout, stderr = proxy_process.communicate()
                print(f"[DEPLOY] Proxy failed to start")
                print(f"[DEPLOY] stderr: {stderr.decode()[:500]}")
        except Exception as e:
            print(f"[DEPLOY] Warning: Could not start proxy: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def _start_instance(self, instance_dir: Path, port: int, instance_name: str) -> Optional[subprocess.Popen]:
        """Start instance in background."""
        print(f"[DEPLOY] Starting {instance_name} on port {port}")
        
        try:
            # Check if port is already in use
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                print(f"[DEPLOY] Warning: Port {port} is already in use")
                # Try to find and kill existing process
                try:
                    result = subprocess.run(
                        ["lsof", "-ti", f":{port}"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        pid = result.stdout.strip()
                        print(f"[DEPLOY] Killing existing process on port {port} (PID: {pid})")
                        subprocess.run(["kill", "-9", pid], timeout=5)
                        time.sleep(2)
                except:
                    pass
            
            # Activate venv and start dashboard
            venv_python = instance_dir / "venv" / "bin" / "python3"
            if not venv_python.exists() or not venv_python.is_file():
                # Try base directory venv
                base_venv = BASE_DIR / "venv" / "bin" / "python3"
                if base_venv.exists():
                    venv_python = base_venv
                else:
                    venv_python = Path("/usr/bin/python3")
            
            dashboard_script = instance_dir / "dashboard.py"
            if not dashboard_script.exists():
                print(f"[DEPLOY] Dashboard script not found in {instance_dir}")
                return None
            
            # Set environment - ensure we use correct working directory
            env = os.environ.copy()
            env["PORT"] = str(port)
            env["PYTHONUNBUFFERED"] = "1"
            env["INSTANCE"] = instance_name
            # Ensure Python path includes instance directory
            pythonpath = str(instance_dir)
            if "PYTHONPATH" in env:
                pythonpath = f"{instance_dir}:{env['PYTHONPATH']}"
            env["PYTHONPATH"] = pythonpath
            
            # Start process with proper working directory
            process = subprocess.Popen(
                [str(venv_python), str(dashboard_script)],
                cwd=str(instance_dir),  # Critical: run from instance directory
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from parent
            )
            
            # Wait a moment for startup
            time.sleep(5)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"[DEPLOY] {instance_name} started (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"[DEPLOY] {instance_name} failed to start")
                print(f"[DEPLOY] stdout: {stdout.decode()[:500]}")
                print(f"[DEPLOY] stderr: {stderr.decode()[:500]}")
                return None
                
        except Exception as e:
            print(f"[DEPLOY] Error starting {instance_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _stop_instance(self, process: Optional[subprocess.Popen], instance_name: str):
        """Stop instance process."""
        if process:
            print(f"[DEPLOY] Stopping {instance_name} (PID: {process.pid})")
            try:
                process.terminate()
                process.wait(timeout=10)
            except:
                try:
                    process.kill()
                except:
                    pass
    
    def _switch_traffic(self, new_instance: str):
        """Switch traffic to new instance (update nginx/load balancer if needed)."""
        # For now, we'll use port-based switching
        # In production, you might use nginx upstream or load balancer
        print(f"[DEPLOY] Switching traffic to instance {new_instance}")
        
        # Update state
        old_instance = self.current_state["active_instance"]
        self.current_state["active_instance"] = new_instance
        self.current_state["last_deployment"] = {
            "timestamp": time.time(),
            "from": old_instance,
            "to": new_instance
        }
        self._save_state()
        
        print(f"[DEPLOY] Traffic switched from {old_instance} to {new_instance}")
    
    def _rollback(self, reason: str):
        """Rollback to previous instance."""
        print(f"[DEPLOY] ROLLBACK: {reason}")
        
        old_instance = self.current_state["active_instance"]
        new_instance = "B" if old_instance == "A" else "A"
        
        self.current_state["active_instance"] = new_instance
        self.current_state["last_deployment"] = {
            "timestamp": time.time(),
            "from": old_instance,
            "to": new_instance,
            "rollback": True,
            "reason": reason
        }
        self._save_state()
        
        print(f"[DEPLOY] Rolled back to instance {new_instance}")
    
    def deploy(self) -> bool:
        """Main deployment function - zero downtime A/B deployment."""
        print("=" * 60)
        print("ZERO-DOWNTIME DEPLOYMENT")
        print("=" * 60)
        print(f"Active instance: {self.current_state['active_instance']}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Step 0: Ensure proxy is running
        print("\n[STEP 0] Ensuring dashboard proxy is running...")
        self._ensure_proxy_running()
        
        # Step 1: Ensure instance directories exist
        print("\n[STEP 1] Preparing instance directories...")
        self._ensure_instance_dirs()
        
        # Step 2: Clone to staging
        print("\n[STEP 2] Cloning to staging instance...")
        if not self._clone_to_staging():
            print("[DEPLOY] Failed to clone to staging")
            return False
        
        staging_dir, staging_port = self._get_staging_instance()
        active_dir, active_port = self._get_active_instance()
        
        # Step 3: Pull latest code in base directory
        print("\n[STEP 3] Pulling latest code from git...")
        if not self._pull_latest_code():
            print("[DEPLOY] Failed to pull latest code")
            return False
        
        # Step 3b: Re-clone to staging with latest code
        print("\n[STEP 3b] Updating staging instance with latest code...")
        if not self._clone_to_staging():
            print("[DEPLOY] Failed to update staging instance")
            return False
        
        # Step 4: Start staging instance (on internal port, not 5000)
        print("\n[STEP 4] Starting staging instance...")
        # Use internal ports - proxy will route from 5000
        staging_process = self._start_instance(staging_dir, staging_port, "STAGING")
        if not staging_process:
            print("[DEPLOY] Failed to start staging instance")
            return False
        
        # Step 5: Health check staging
        print("\n[STEP 5] Health checking staging instance...")
        if not self._check_health(staging_port, "STAGING"):
            print("[DEPLOY] Staging instance failed health check")
            self._stop_instance(staging_process, "STAGING")
            if ROLLBACK_ON_FAILURE:
                self._rollback("Staging health check failed")
            return False
        
        # Step 6: Switch traffic
        print("\n[STEP 6] Switching traffic to staging...")
        new_instance = "B" if self.current_state["active_instance"] == "A" else "A"
        self._switch_traffic(new_instance)
        
        # Step 7: Verify active instance health via proxy
        print("\n[STEP 7] Verifying active instance health via proxy...")
        time.sleep(5)  # Give it a moment to stabilize
        # Check via proxy (port 5000) which routes to active instance
        if not self._check_health(PROXY_PORT, "ACTIVE (via proxy)"):
            print("[DEPLOY] Active instance failed health check after switch")
            if ROLLBACK_ON_FAILURE:
                self._rollback("Active instance health check failed after switch")
                # Restart old instance
                old_staging_dir, old_staging_port = self._get_staging_instance()
                old_process = self._start_instance(old_staging_dir, old_staging_port, "ROLLBACK")
                if old_process:
                    self._check_health(old_staging_port, "ROLLBACK")
            return False
        
        # Step 8: Stop old instance (optional - can keep running for quick rollback)
        print("\n[STEP 8] Deployment complete!")
        print(f"[DEPLOY] Active instance: {new_instance}")
        print(f"[DEPLOY] Old instance kept running for quick rollback")
        
        # Log deployment
        self.current_state["deployment_history"].append({
            "timestamp": time.time(),
            "from": "A" if new_instance == "B" else "B",
            "to": new_instance,
            "success": True
        })
        if len(self.current_state["deployment_history"]) > 10:
            self.current_state["deployment_history"] = self.current_state["deployment_history"][-10:]
        self._save_state()
        
        return True

def main():
    """Main entry point."""
    deployer = ZeroDowntimeDeployer()
    success = deployer.deploy()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
