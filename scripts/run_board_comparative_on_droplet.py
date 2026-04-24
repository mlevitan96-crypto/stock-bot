#!/usr/bin/env python3
"""Run comparative synthesis on droplet (reads 30d + last387 reviews there), then fetch outputs."""
from __future__ import annotations
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

def main() -> int:
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    with DropletClient() as c:
        c._execute(f"mkdir -p {proj}/reports/board")
        c.put_file(REPO / "scripts" / "board_comparative_synthesis.py", f"{proj}/scripts/board_comparative_synthesis.py")
        out, err, rc = c._execute(f"cd {proj} && python3 scripts/board_comparative_synthesis.py .", timeout=60)
        print(out)
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            return rc
        for name in ["COMPARATIVE_REVIEW_30D_vs_LAST387.json", "COMPARATIVE_REVIEW_30D_vs_LAST387.md"]:
            src = f"{proj}/reports/board/{name}"
            content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
            if content and content.strip():
                dest = REPO / "reports" / "board" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"Fetched {name}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
