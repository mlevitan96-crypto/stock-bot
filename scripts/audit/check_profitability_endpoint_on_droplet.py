#!/usr/bin/env python3
"""Quick check: curl /api/profitability_learning on droplet (no auth)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from droplet_client import DropletClient

def main():
    c = DropletClient()
    out, err, code = c._execute(
        "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/profitability_learning 2>/dev/null"
    )
    status = (out or "").strip()
    print("HTTP code (no auth):", status)
    if status == "200":
        out2, _, _ = c._execute("curl -s http://127.0.0.1:5000/api/profitability_learning 2>/dev/null | head -c 300")
        print("Body sample:", (out2 or "")[:300])
    return 0 if status == "200" else 1

if __name__ == "__main__":
    sys.exit(main())
