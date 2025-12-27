#!/usr/bin/env python3
"""Test SSH connection to droplet using SSH config."""

from droplet_client import DropletClient

print("=" * 60)
print("TESTING SSH CONNECTION TO DROPLET")
print("=" * 60)
print()

try:
    client = DropletClient()
    print("[OK] Config loaded successfully")
    print(f"  Host: {client.config.get('host')}")
    print(f"  Username: {client.config.get('username')}")
    print(f"  Port: {client.config.get('port')}")
    print()
    
    print("Testing connection...")
    status = client.get_status()
    print("[OK] Connection successful!")
    print(f"  Droplet: {status.get('host')}")
    print(f"  Project Dir: {status.get('project_dir')}")
    print()
    
    print("Testing command execution...")
    result = client.execute_command("pwd && echo 'Test command successful' && date")
    print(f"[OK] Command executed (exit code: {result['exit_code']})")
    print("  Output:")
    print(result['stdout'])
    if result['stderr']:
        print("  Errors:", result['stderr'])
    print()
    
    print("Testing git status...")
    git_status = client.get_git_status()
    print("[OK] Git status retrieved")
    print(f"  Branch: {git_status.get('branch')}")
    print(f"  Status: {git_status.get('status')}")
    print(f"  Latest Commit: {git_status.get('commit')}")
    print()
    
    client.close()
    print("=" * 60)
    print("[OK] ALL TESTS PASSED - SSH CONNECTION WORKING")
    print("=" * 60)
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    exit(1)

