#!/usr/bin/env python3
"""Trigger deploy to droplet per MEMORY_BANK: git pull on droplet + restart service."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from droplet_client import DropletClient

def main():
    c = DropletClient()
    r = c.deploy()
    ok = r.get("success", False)
    for s in r.get("steps", []):
        name = s.get("name", "")
        res = s.get("result", {})
        step_ok = res.get("success", res.get("exit_code", 1) == 0)
        status = "OK" if step_ok else "FAIL"
        print(f"  {name}: {status}")
    if not ok:
        print("Error:", r.get("error", "deploy failed"))
        return 1
    print("Deploy complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
