#!/usr/bin/env python3
"""
Diagnose droplet SSH connectivity. Run locally to see why SSH fails.
Prints: config used, connection attempt result, and underlying errors if any.
Usage: python scripts/diagnose_droplet_ssh.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient
    
    print("Loading droplet config...")
    try:
        c = DropletClient()
    except Exception as e:
        print(f"Config error: {e}")
        return 1
    
    host = c.config.get("host", "")
    port = c.config.get("port", 22)
    timeout = c.config.get("connect_timeout", 30)
    retries = c.config.get("connect_retries", 5)
    print(f"  host={host} port={port} timeout={timeout}s retries={retries}")
    print(f"  use_ssh_config={c.config.get('use_ssh_config')} key_file={c.config.get('key_file') or '(none)'}")
    print()
    
    print("Attempting SSH connection...")
    try:
        c._connect()
        print("  OK: connected.")
        c.close()
        return 0
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        if hasattr(e, "__cause__") and e.__cause__ is not None:
            cause = e.__cause__
            print(f"  Cause: {type(cause).__name__}: {cause}")
            if hasattr(cause, "errors") and cause.errors:
                print("  Underlying errors:")
                for addr, err in cause.errors.items():
                    print(f"    {addr}: {type(err).__name__}: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
