#!/usr/bin/env python3
"""Quick check: UW cache + run scoring audit on droplet, print summary."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    with DropletClient() as c:
        out, err, _ = c._execute(
            "cd /root/stock-bot && ls -la data/uw_flow_cache.json data/uw_expanded_intel.json 2>/dev/null; "
            "wc -l data/uw_flow_cache.json data/uw_expanded_intel.json 2>/dev/null"
        )
        print("--- UW cache and expanded_intel ---")
        print(out or err)

        print("\n--- Running scoring pipeline audit (--days 7) ---")
        out2, err2, rc = c._execute(
            "cd /root/stock-bot && python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days 7 2>&1",
            timeout=120,
        )
        print(out2 or err2)
        print("Exit code:", rc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
