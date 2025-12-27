#!/usr/bin/env python3
"""
Quick verification script for droplet client setup.
Run this after completing the setup steps to verify everything works.
"""

import sys
import json
from pathlib import Path

def check_config_file():
    """Check if config file exists and is valid."""
    print("Step 1: Checking config file...")
    config_path = Path("droplet_config.json")
    
    if not config_path.exists():
        print("   ❌ droplet_config.json not found!")
        print("   → Create it using the instructions in SETUP_DROPLET_CLIENT.md")
        return False
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        if not config.get("host"):
            print("   ❌ 'host' field is missing or empty")
            return False
        
        if not config.get("username"):
            print("   ❌ 'username' field is missing or empty")
            return False
        
        has_auth = bool(config.get("key_file") or config.get("password"))
        if not has_auth:
            print("   ❌ Need either 'key_file' or 'password' for authentication")
            return False
        
        print(f"   ✅ Config file found")
        print(f"   → Host: {config.get('host')}")
        print(f"   → User: {config.get('username')}")
        print(f"   → Auth: {'SSH Key' if config.get('key_file') else 'Password'}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error reading config: {e}")
        return False


def check_paramiko():
    """Check if paramiko is installed."""
    print("\nStep 2: Checking paramiko installation...")
    try:
        import paramiko
        print(f"   ✅ paramiko installed (version: {paramiko.__version__})")
        return True
    except ImportError:
        print("   ❌ paramiko not installed!")
        print("   → Run: pip install paramiko==3.4.0")
        return False


def check_gitignore():
    """Check if config file is in .gitignore."""
    print("\nStep 3: Checking .gitignore...")
    gitignore_path = Path(".gitignore")
    
    if not gitignore_path.exists():
        print("   ⚠️  .gitignore not found (this is okay if you're not using git)")
        return True
    
    try:
        with open(gitignore_path) as f:
            content = f.read()
        
        if "droplet_config.json" in content:
            print("   ✅ droplet_config.json is in .gitignore")
            return True
        else:
            print("   ⚠️  droplet_config.json not in .gitignore")
            print("   → Add it to prevent committing credentials")
            return True  # Not a blocker, just a warning
    except Exception as e:
        print(f"   ⚠️  Could not check .gitignore: {e}")
        return True


def test_connection():
    """Test connection to droplet."""
    print("\nStep 4: Testing connection to droplet...")
    try:
        from droplet_client import DropletClient
        
        with DropletClient() as client:
            print(f"   ✅ Connected to {client.config['host']}")
            
            # Try a simple command
            status = client.get_status()
            print(f"   ✅ Service status: {status.get('service_status', 'unknown')}")
            print(f"   ✅ Git branch: {status.get('git', {}).get('branch', 'unknown')}")
            
            return True
    except ValueError as e:
        print(f"   ❌ Configuration error: {e}")
        return False
    except ConnectionError as e:
        print(f"   ❌ Connection failed: {e}")
        print("   → Check your droplet IP, SSH key/password, and network connectivity")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Droplet Client Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        check_config_file(),
        check_paramiko(),
        check_gitignore(),
    ]
    
    # Only test connection if basic checks pass
    if all(checks):
        checks.append(test_connection())
    else:
        print("\n⚠️  Skipping connection test due to previous failures")
        checks.append(False)
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed! Droplet client is ready to use.")
        print("\nYou can now ask Cursor to:")
        print("  - Check droplet status")
        print("  - View logs")
        print("  - Check git status")
        print("  - Deploy changes")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nSee SETUP_DROPLET_CLIENT.md for detailed setup instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

