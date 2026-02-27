#!/usr/bin/env python3
"""Run the phase9 comparison on droplet via base64-exec. Prints comparison JSON to stdout."""
import base64
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

script = (Path(__file__).parent / "_droplet_compare_phase9.py").read_text(encoding="utf-8")
b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")

from droplet_client import DropletClient

with DropletClient() as c:
    # Run on droplet: decode and execute the script
    cmd = "cd /root/stock-bot && python3 -c 'import base64; exec(base64.b64decode(\"%s\").decode())'" % b64
    out, err, code = c._execute_with_cd(cmd, timeout=120000)
    if code != 0:
        print(err or out, file=sys.stderr)
        sys.exit(code)
    print(out)
