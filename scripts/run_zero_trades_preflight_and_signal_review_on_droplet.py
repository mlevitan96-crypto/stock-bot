#!/usr/bin/env python3
"""
Run Phase 0 (zero-trades preflight) on droplet; if ZERO TYPE = B, run Phase 1 (full signal review).
Single entry point. No strategy tuning.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    # Phase 0
    rc0 = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "zero_trades_preflight_on_droplet.py")],
        cwd=str(REPO), capture_output=True, text=True, timeout=120,
    )
    out = (rc0.stdout or "") + (rc0.stderr or "")
    print(out)
    if rc0.returncode != 0:
        return rc0.returncode

    # Parse ZERO TYPE
    zero_type = "A"
    m = re.search(r"ZERO TYPE:\s*([ABC])\s*", out)
    if m:
        zero_type = m.group(1).strip()

    if zero_type == "B":
        print("\n--- Phase 1 (full signal review) ---\n")
        rc1 = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "full_signal_review_on_droplet.py"), "--days", "7"],
            cwd=str(REPO), timeout=180,
        )
        return rc1.returncode
    # A or C: STOP; fix-ready verdict is in zero_trades_preflight.md
    return 0


if __name__ == "__main__":
    sys.exit(main())
