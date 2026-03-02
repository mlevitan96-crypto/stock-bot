#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from droplet_client import DropletClient

with DropletClient() as c:
    out, _, _ = c._execute_with_cd("git rev-parse HEAD")
    print("Droplet HEAD:", (out or "").strip())
    out2, _, _ = c._execute_with_cd("git log -1 --oneline")
    print("Droplet log:", (out2 or "").strip())
    out3, _, _ = c._execute_with_cd("grep -n preserved_strong_composite board/eod/live_entry_adjustments.py")
    print("Grep preserved_strong:", (out3 or "NOT FOUND")[:200])
