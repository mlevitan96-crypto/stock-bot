"""
Droplet Client - SSH-based interface for Cursor to interact with the droplet.

This module allows Cursor to:
- Check droplet status (services, processes, health)
- View logs in real-time
- Check git status and changes
- Execute commands remotely
- Deploy changes
- Monitor system health

Usage:
    from droplet_client import DropletClient
    
    client = DropletClient()
    status = client.get_status()
    logs = client.get_recent_logs()
    git_status = client.get_git_status()
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import socket
import paramiko
from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import SSHException, AuthenticationException, NoValidConnectionsError


class DropletClient:
    """SSH client for interacting with the droplet."""
    
    def __init__(self, config_path: str = "droplet_config.json"):
        """
        Initialize droplet client.
        
        Args:
            config_path: Path to configuration file with droplet connection details
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.ssh_client: Optional[SSHClient] = None
        self.project_dir = self.config.get("project_dir", "~/stock-bot")
        
    def _load_config(self) -> Dict:
        """Load configuration from file or environment variables."""
        config = {}
        
        # Try to load from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Override with environment variables if present
        config["host"] = os.getenv("DROPLET_HOST", config.get("host", ""))
        config["port"] = int(os.getenv("DROPLET_PORT", config.get("port", 22)))
        config["username"] = os.getenv("DROPLET_USER", config.get("username", "root"))
        config["password"] = os.getenv("DROPLET_PASSWORD", config.get("password", ""))
        config["key_file"] = os.getenv("DROPLET_KEY_FILE", config.get("key_file", ""))
        config["project_dir"] = os.getenv("DROPLET_PROJECT_DIR", config.get("project_dir", "~/stock-bot"))
        config["use_ssh_config"] = config.get("use_ssh_config", False)
        config["connect_timeout"] = int(os.getenv("DROPLET_CONNECT_TIMEOUT", config.get("connect_timeout", 30)))
        config["connect_retries"] = int(os.getenv("DROPLET_CONNECT_RETRIES", config.get("connect_retries", 5)))
        
        if not config.get("host"):
            raise ValueError(
                "Droplet configuration not found. Please create droplet_config.json or set "
                "DROPLET_HOST environment variable. See droplet_config.example.json for template."
            )
        
        # If using SSH config, parse it to get connection details
        if config.get("use_ssh_config"):
            config = self._parse_ssh_config(config)
        
        return config
    
    def _parse_ssh_config(self, config: Dict) -> Dict:
        """Parse SSH config file to extract connection details for the host."""
        import subprocess
        
        ssh_host = config.get("host", "")
        if not ssh_host:
            return config
        
        try:
            # Use ssh -G to get resolved config for the host
            result = subprocess.run(
                ['ssh', '-G', ssh_host],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse the output
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if ' ' in line:
                        key, value = line.split(' ', 1)
                        if key == 'hostname' and not config.get('hostname'):
                            config['hostname'] = value
                        elif key == 'user' and not config.get('username'):
                            config['username'] = value
                        elif key == 'port' and not config.get('port'):
                            config['port'] = int(value)
                        elif key == 'identityfile' and not config.get('key_file'):
                            # Use first identity file (remove quotes if present)
                            key_path = value.strip().strip('"').strip("'")
                            # Expand ~ to home directory
                            if key_path.startswith('~'):
                                import os
                                key_path = os.path.expanduser(key_path)
                            # Convert Windows path separators if needed
                            if os.sep == '\\' and '/' in key_path:
                                key_path = key_path.replace('/', '\\')
                            elif os.sep == '/' and '\\' in key_path:
                                key_path = key_path.replace('\\', '/')
                            if os.path.exists(key_path):
                                config['key_file'] = key_path
                
                # Use resolved hostname for connection
                if config.get('hostname'):
                    config['host'] = config['hostname']
        except Exception as e:
            print(f"Warning: Could not parse SSH config: {e}")
        
        return config
    
    def _connect(self) -> SSHClient:
        """Establish SSH connection to droplet. Retries with backoff; uses connect_timeout and connect_retries from config."""
        if self.ssh_client and self.ssh_client.get_transport() and self.ssh_client.get_transport().is_active():
            return self.ssh_client
        
        host = self.config["host"]
        port = self.config["port"]
        timeout = self.config.get("connect_timeout", 30)
        retries = self.config.get("connect_retries", 5)
        last_error = None
        
        for attempt in range(1, retries + 1):
            ssh = SSHClient()
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            try:
                if self.config.get("key_file") and os.path.exists(self.config["key_file"]):
                    ssh.connect(
                        hostname=host,
                        port=port,
                        username=self.config["username"],
                        key_filename=self.config["key_file"],
                        timeout=timeout,
                        banner_timeout=timeout,
                        auth_timeout=timeout,
                    )
                elif self.config.get("password"):
                    ssh.connect(
                        hostname=host,
                        port=port,
                        username=self.config["username"],
                        password=self.config["password"],
                        timeout=timeout,
                        banner_timeout=timeout,
                        auth_timeout=timeout,
                    )
                elif self.config.get("use_ssh_config"):
                    if self.config.get("key_file") and os.path.exists(self.config["key_file"]):
                        ssh.connect(
                            hostname=host,
                            port=port,
                            username=self.config["username"],
                            key_filename=self.config["key_file"],
                            timeout=timeout,
                            banner_timeout=timeout,
                            auth_timeout=timeout,
                        )
                    else:
                        ssh.connect(
                            hostname=host,
                            port=port,
                            username=self.config["username"],
                            timeout=timeout,
                            banner_timeout=timeout,
                            auth_timeout=timeout,
                            look_for_keys=True,
                            allow_agent=True,
                        )
                else:
                    raise ValueError("Either key_file, password, or use_ssh_config must be provided in config")
                
                self.ssh_client = ssh
                return ssh
            except AuthenticationException as e:
                raise ValueError(f"Authentication failed for {self.config['username']}@{host}: {e}")
            except NoValidConnectionsError as e:
                last_error = e
                underlying = getattr(e, "errors", {}) or {}
                parts = [str(e)]
                for addr, err in underlying.items():
                    parts.append(f"  {addr}: {type(err).__name__}: {err}")
                msg = "\n".join(parts)
                if attempt < retries:
                    time.sleep(2 * attempt)
                    continue
                raise ConnectionError(
                    f"SSH to {host}:{port} failed after {retries} attempts (timeout={timeout}s).\n"
                    f"{msg}\n"
                    "Possible causes: droplet off/rebooting, firewall blocking port 22, network unreachable, "
                    "or slow network (try increasing connect_timeout or connect_retries in droplet_config.json)."
                ) from e
            except (SSHException, socket.timeout, OSError) as e:
                last_error = e
                if attempt < retries:
                    time.sleep(2 * attempt)
                    continue
                raise ConnectionError(
                    f"SSH to {host}:{port} failed after {retries} attempts: {type(e).__name__}: {e}"
                ) from e
            except Exception as e:
                last_error = e
                if attempt < retries:
                    time.sleep(2 * attempt)
                    continue
                raise ConnectionError(f"Failed to connect to droplet: {e}") from e
        
        raise ConnectionError(
            f"SSH to {host}:{port} failed after {retries} attempts. Last error: {last_error}"
        )
    
    def _execute(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """
        Execute command on droplet with a real timeout.
        Paramiko's exec_command(timeout=) does not reliably limit runtime;
        recv_exit_status() can hang. We poll exit_status_ready() until deadline
        and read stdout/stderr in a thread so the channel does not block.
        On timeout we close the channel and return exit_code 124 (same as timeout(1)).
        """
        ssh = self._connect()
        # Use get_pty=False and short timeout only for opening the channel
        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        channel = stdout.channel
        out_buf: List[str] = []
        err_buf: List[str] = []

        def read_streams() -> None:
            try:
                out_buf.append(stdout.read().decode("utf-8", errors="replace"))
            except Exception:
                pass
            try:
                err_buf.append(stderr.read().decode("utf-8", errors="replace"))
            except Exception:
                pass

        reader = threading.Thread(target=read_streams, daemon=True)
        reader.start()
        deadline = time.monotonic() + timeout
        try:
            while time.monotonic() < deadline:
                if channel.exit_status_ready():
                    break
                time.sleep(1)
            if not channel.exit_status_ready():
                channel.close()
                reader.join(timeout=5)
                return (
                    "".join(out_buf),
                    "".join(err_buf) + f"\n[Command timed out after {timeout}s]\n",
                    124,
                )
            reader.join(timeout=10)
            exit_code = channel.recv_exit_status()
            return "".join(out_buf), "".join(err_buf), exit_code
        finally:
            if not channel.exit_status_ready() and channel.active:
                try:
                    channel.close()
                except Exception:
                    pass
    
    def _execute_with_cd(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute command in project directory."""
        full_command = f"cd {self.project_dir} && {command}"
        return self._execute(full_command, timeout)

    def put_file(self, local_path: str | Path, remote_path: str) -> None:
        """Upload a file to the droplet via SFTP. Uses existing connection or connects."""
        ssh = self._connect()
        local = Path(local_path)
        if not local.is_file():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        sftp = ssh.open_sftp()
        try:
            sftp.put(str(local), remote_path)
        finally:
            sftp.close()

    def close(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # Status and Monitoring Methods
    
    def get_status(self) -> Dict:
        """
        Get comprehensive droplet status.
        
        Returns:
            Dictionary with status information including:
            - services: Running services status
            - processes: Key process status
            - git: Git status
            - disk: Disk usage
            - memory: Memory usage
            - uptime: System uptime
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "host": self.config["host"],
            "project_dir": self.project_dir
        }
        
        # Check services
        stdout, _, _ = self._execute("systemctl is-active stock-bot 2>/dev/null || echo 'not-found'")
        status["service_status"] = stdout.strip()
        
        # Check processes
        stdout, _, _ = self._execute("ps aux | grep -E 'deploy_supervisor|main.py|dashboard.py' | grep -v grep | wc -l")
        status["process_count"] = int(stdout.strip() or 0)
        
        # Check git status
        status["git"] = self.get_git_status()
        
        # Disk usage
        stdout, _, _ = self._execute_with_cd("df -h . | tail -1 | awk '{print $5}'")
        status["disk_usage"] = stdout.strip()
        
        # Memory usage
        stdout, _, _ = self._execute("free -h | grep Mem | awk '{print $3\"/\"$2}'")
        status["memory_usage"] = stdout.strip()
        
        # Uptime
        stdout, _, _ = self._execute("uptime -p")
        status["uptime"] = stdout.strip()
        
        return status
    
    def get_git_status(self) -> Dict:
        """
        Get git status from droplet.
        
        Returns:
            Dictionary with git information:
            - branch: Current branch
            - commit: Latest commit hash
            - message: Latest commit message
            - status: Git status (clean/dirty)
            - ahead: Commits ahead of remote
            - behind: Commits behind remote
            - uncommitted: List of uncommitted files
        """
        git_info = {}
        
        # Current branch
        stdout, _, _ = self._execute_with_cd("git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown'")
        git_info["branch"] = stdout.strip()
        
        # Latest commit
        stdout, _, _ = self._execute_with_cd("git rev-parse HEAD 2>/dev/null || echo 'unknown'")
        git_info["commit"] = stdout.strip()[:8] if stdout.strip() != "unknown" else "unknown"
        
        # Commit message
        stdout, _, _ = self._execute_with_cd("git log -1 --pretty=format:'%s' 2>/dev/null || echo 'unknown'")
        git_info["message"] = stdout.strip()
        
        # Status
        stdout, _, _ = self._execute_with_cd("git status --porcelain 2>/dev/null")
        uncommitted = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
        git_info["status"] = "clean" if not uncommitted else "dirty"
        git_info["uncommitted"] = uncommitted
        
        # Ahead/behind
        stdout, _, _ = self._execute_with_cd("git rev-list --left-right --count origin/$(git rev-parse --abbrev-ref HEAD)...HEAD 2>/dev/null || echo '0 0'")
        parts = stdout.strip().split()
        if len(parts) == 2:
            git_info["behind"] = int(parts[0])
            git_info["ahead"] = int(parts[1])
        else:
            git_info["behind"] = 0
            git_info["ahead"] = 0
        
        return git_info
    
    def get_recent_logs(self, lines: int = 50, log_file: str = "trading.log") -> List[str]:
        """
        Get recent log lines from droplet.
        
        Args:
            lines: Number of lines to retrieve
            log_file: Log file name (relative to logs/ directory)
        
        Returns:
            List of log lines
        """
        log_path = f"{self.project_dir}/logs/{log_file}"
        stdout, stderr, exit_code = self._execute(f"tail -n {lines} {log_path} 2>/dev/null || echo ''")
        
        if exit_code != 0 and stderr:
            return [f"Error reading logs: {stderr}"]
        
        log_lines = [line for line in stdout.strip().split('\n') if line.strip()]
        return log_lines
    
    def get_all_logs_info(self) -> Dict:
        """
        Get information about all log files.
        
        Returns:
            Dictionary with log file information
        """
        stdout, _, _ = self._execute_with_cd("ls -lh logs/*.log 2>/dev/null | awk '{print $9, $5}'")
        
        logs_info = {}
        for line in stdout.strip().split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    filename = parts[0].split('/')[-1]
                    size = parts[1]
                    logs_info[filename] = {"size": size}
        
        return logs_info
    
    def get_health(self) -> Dict:
        """
        Get health check information.
        
        Returns:
            Dictionary with health status
        """
        health = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown"
        }
        
        # Check health endpoint
        stdout, _, exit_code = self._execute("curl -s http://localhost:8080/health 2>/dev/null || curl -s http://localhost:5000/api/sre/health 2>/dev/null || echo 'unavailable'")
        
        if exit_code == 0 and stdout.strip() != "unavailable":
            try:
                health_data = json.loads(stdout)
                health.update(health_data)
                health["status"] = "healthy" if health_data.get("status") == "ok" else "degraded"
            except:
                health["status"] = "unknown"
                health["raw_response"] = stdout.strip()
        else:
            health["status"] = "unavailable"
        
        return health
    
    # Command Execution Methods
    
    def execute_command(self, command: str, timeout: int = 60) -> Dict:
        """
        Execute arbitrary command on droplet.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
        
        Returns:
            Dictionary with command results:
            - stdout: Standard output
            - stderr: Standard error
            - exit_code: Exit code
            - success: Boolean indicating success
        """
        stdout, stderr, exit_code = self._execute_with_cd(command, timeout)
        
        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "success": exit_code == 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def git_pull(self) -> Dict:
        """Pull latest changes from git."""
        return self.execute_command("git pull origin main")
    
    def git_status_full(self) -> str:
        """Get full git status output."""
        stdout, stderr, exit_code = self._execute_with_cd("git status")
        return stdout + (f"\n{stderr}" if stderr else "")
    
    def deploy(self) -> Dict:
        """
        Deploy latest changes to droplet.
        
        Returns:
            Dictionary with deployment results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        # Step 1: Fetch and reset to origin/main (overwrites local changes so deploy always wins)
        fetch_reset = self.execute_command("git fetch --all && git reset --hard origin/main")
        results["steps"].append({"name": "git_fetch_reset", "result": fetch_reset})
        
        if not fetch_reset["success"]:
            results["success"] = False
            results["error"] = "Git fetch/reset failed"
            return results

        # Step 1b: Run minimal pytest spine (exit/attribution/effectiveness). Record result; do not block deploy.
        pytest_cmd = (
            "python3 -m pytest validation/scenarios/test_exit_attribution_phase4.py "
            "validation/scenarios/test_effectiveness_reports.py "
            "validation/scenarios/test_attribution_loader_join.py -v --tb=short 2>&1 | tail -50"
        )
        pytest_out, pytest_err, pytest_rc = self._execute_with_cd(pytest_cmd, timeout=90)
        results["steps"].append({
            "name": "pytest_spine",
            "result": {
                "success": pytest_rc == 0,
                "exit_code": pytest_rc,
                "output_tail": (pytest_out or "")[-1500:],
            },
        })

        # Step 2a: Kill ALL dashboard.py processes so no orphan holds port 5000.
        # (systemctl restart stock-bot kills deploy_supervisor but its child dashboard may survive as orphan.)
        kill_out, kill_err, kill_rc = self._execute_with_cd("pkill -f 'dashboard\\.py' 2>/dev/null; sleep 1; true")
        results["steps"].append({
            "name": "kill_stale_dashboard",
            "result": {"success": True, "note": "pkill dashboard.py so new deploy_supervisor owns port 5000"}
        })

        # Step 2b: Check if deployment script exists and run it
        deploy_script = f"{self.project_dir}/deploy.sh"
        stdout, _, exit_code = self._execute(f"test -f {deploy_script} && echo 'exists' || echo 'not-found'")
        
        if "exists" in stdout:
            step2 = self.execute_command("./deploy.sh", timeout=300)
            results["steps"].append({"name": "deploy_script", "result": step2})
        else:
            # Fallback: restart service (supervisor will start fresh dashboard)
            step2 = self.execute_command("sudo systemctl restart stock-bot", timeout=60)
            results["steps"].append({"name": "restart_service", "result": step2})
        # Ensure UW flow daemon is running so cache stays fresh. Copy unit if present, enable, start.
        step_daemon = self.execute_command(
            "if [ -f deploy/systemd/uw-flow-daemon.service ]; then "
            "sudo cp deploy/systemd/uw-flow-daemon.service /etc/systemd/system/uw-flow-daemon.service && sudo systemctl daemon-reload; fi; "
            "sudo systemctl enable uw-flow-daemon.service 2>/dev/null; "
            "sudo systemctl start uw-flow-daemon.service; "
            "sudo systemctl restart uw-flow-daemon.service; "
            "sudo systemctl is-active uw-flow-daemon.service 2>/dev/null || echo 'uw-flow-daemon-not-active'",
            timeout=30,
        )
        results["steps"].append({"name": "uw_flow_daemon_restart", "result": step_daemon})
        results["success"] = step2["success"]
        return results
    
    def get_process_info(self) -> List[Dict]:
        """
        Get information about running processes.
        
        Returns:
            List of process dictionaries
        """
        stdout, _, _ = self._execute("ps aux | grep -E 'deploy_supervisor|main.py|dashboard.py|python' | grep -v grep")
        
        processes = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        "user": parts[0],
                        "pid": parts[1],
                        "cpu": parts[2],
                        "mem": parts[3],
                        "command": parts[10] if len(parts) > 10 else " ".join(parts[10:])
                    })
        
        return processes


# Convenience functions for easy access

def get_droplet_status() -> Dict:
    """Quick function to get droplet status."""
    with DropletClient() as client:
        return client.get_status()


def get_droplet_logs(lines: int = 50) -> List[str]:
    """Quick function to get recent logs."""
    with DropletClient() as client:
        return client.get_recent_logs(lines)


def get_droplet_git_status() -> Dict:
    """Quick function to get git status."""
    with DropletClient() as client:
        return client.get_git_status()


if __name__ == "__main__":
    # Example usage
    print("Droplet Client - Testing Connection")
    print("=" * 60)
    
    try:
        with DropletClient() as client:
            print(f"Connected to: {client.config['host']}")
            print()
            
            # Get status
            print("Status:")
            status = client.get_status()
            print(json.dumps(status, indent=2))
            print()
            
            # Get git status
            print("Git Status:")
            git_status = client.get_git_status()
            print(json.dumps(git_status, indent=2))
            print()
            
            # Get recent logs
            print("Recent Logs (last 10 lines):")
            logs = client.get_recent_logs(10)
            for line in logs[-10:]:
                print(line)
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have created droplet_config.json with your droplet connection details.")

