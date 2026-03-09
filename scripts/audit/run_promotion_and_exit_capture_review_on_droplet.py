#!/usr/bin/env python3
"""
Run Promotion & Exit Capture Review on droplet, then fetch artifacts to local.
Execute from repo root. Writes to local reports/audit and reports/board.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"
DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

ARTIFACTS = [
    (AUDIT, f"PROMOTION_TRIGGER_STATUS_{DATE}.json"),
    (AUDIT, f"EXIT_CAPTURE_AUDIT_{DATE}.md"),
    (AUDIT, f"TRADE_SHAPE_TABLE_{DATE}.json"),
    (AUDIT, f"CSA_PROMOTION_VERDICT_{DATE}.json"),
    (BOARD, f"WEEKLY_ECONOMIC_TRUTH_PACKET_{DATE}.md"),
]


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1
    client = DropletClient()

    cmd = f"DROPLET_RUN=1 python3 scripts/audit/run_promotion_and_exit_capture_review.py"
    out, err, rc = client._execute_with_cd(cmd, timeout=180)
    print(out or "")
    if err:
        print(err, file=sys.stderr)
    if rc != 0:
        print("Audit script exited", rc, file=sys.stderr)

    for dir_path, name in ARTIFACTS:
        remote = f"reports/audit/{name}" if dir_path == AUDIT else f"reports/board/{name}"
        cat_out, _, _ = client._execute_with_cd(f"cat {remote} 2>/dev/null || true", timeout=10)
        if not (cat_out or "").strip():
            continue
        dir_path.mkdir(parents=True, exist_ok=True)
        out_path = dir_path / name
        if name.endswith(".json"):
            try:
                json.loads(cat_out)
            except json.JSONDecodeError:
                cat_out = cat_out.strip()
            out_path.write_text(cat_out, encoding="utf-8")
        else:
            out_path.write_text(cat_out, encoding="utf-8")
        print("Fetched", out_path)

    return rc


if __name__ == "__main__":
    sys.exit(main())
