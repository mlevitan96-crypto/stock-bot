#!/usr/bin/env python3
"""
Run Droplet Verification Now - Attempts SSH connection and runs verification
"""

import subprocess
import sys
import os
from pathlib import Path

def try_ssh_connection():
    """Try to connect to droplet via SSH using common methods"""
    
    # Try using environment variables first
    droplet_host = os.getenv("DROPLET_HOST", "")
    droplet_user = os.getenv("DROPLET_USER", "root")
    droplet_key = os.getenv("DROPLET_KEY_FILE", "")
    
    if not droplet_host:
        # Try to find from git remote or other sources
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Can't extract IP from git remote, need user to provide
            print("ERROR: DROPLET_HOST not set")
            print("Please set environment variable: DROPLET_HOST=your-droplet-ip")
            return False
        except:
            pass
    
    # Try SSH connection
    ssh_cmd = ["ssh", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=no"]
    
    if droplet_key and Path(droplet_key).exists():
        ssh_cmd.extend(["-i", droplet_key])
    
    ssh_cmd.append(f"{droplet_user}@{droplet_host}")
    ssh_cmd.append("cd ~/stock-bot && git fetch origin main && git reset --hard origin/main && bash FINAL_DROPLET_VERIFICATION.sh")
    
    try:
        print(f"Attempting SSH connection to {droplet_user}@{droplet_host}...")
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )
        
        print("SSH Output:")
        print(result.stdout)
        if result.stderr:
            print("SSH Errors:")
            print(result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("ERROR: SSH connection timed out")
        return False
    except FileNotFoundError:
        print("ERROR: SSH command not found")
        return False
    except Exception as e:
        print(f"ERROR: SSH connection failed: {e}")
        return False

if __name__ == "__main__":
    # Check if we can use droplet_client
    try:
        from droplet_client import DropletClient
        print("Using droplet_client.py...")
        client = DropletClient()
        
        print("Connecting to droplet...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main && bash FINAL_DROPLET_VERIFICATION.sh",
            timeout=600
        )
        
        print("Output:")
        print(stdout)
        if stderr:
            print("Errors:")
            print(stderr)
        
        if exit_code == 0:
            print("\n[SUCCESS] Droplet verification completed")
            sys.exit(0)
        else:
            print(f"\n[WARNING] Droplet verification had issues (exit code: {exit_code})")
            sys.exit(1)
            
    except (ImportError, ValueError) as e:
        print(f"Droplet client not available: {e}")
        print("Attempting direct SSH...")
        if try_ssh_connection():
            print("\n[SUCCESS] Droplet verification completed")
            sys.exit(0)
        else:
            print("\n[ERROR] Could not connect to droplet")
            print("\nPlease run on droplet console:")
            print("  cd ~/stock-bot && git fetch origin main && git reset --hard origin/main && bash FINAL_DROPLET_VERIFICATION.sh")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

