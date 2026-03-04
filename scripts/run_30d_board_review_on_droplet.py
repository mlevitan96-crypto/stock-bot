#!/usr/bin/env python3
"""
Run comprehensive board review on droplet (real data), then fetch bundle to reports/board/.
Uses last-N-exits scope by default so learning and board review share the same trade set;
includes counter-intelligence and blocked trades. Builds 30d_comprehensive_review.json and .md.

Usage:
  python scripts/run_30d_board_review_on_droplet.py
  python scripts/run_30d_board_review_on_droplet.py --last-n-exits 387   # same scope as current exits
  python scripts/run_30d_board_review_on_droplet.py --days 30            # 30-day window instead
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run comprehensive board review on droplet")
    ap.add_argument("--last-n-exits", type=int, default=5000, help="Scope by last N exits (default 5000 = all). Use 387 to match current count.")
    ap.add_argument("--days", type=int, default=0, help="If set, use 30-day window instead of last-n-exits")
    args = ap.parse_args()

    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root with droplet_client available", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"
    with DropletClient() as c:
        c._execute(f"mkdir -p {proj}/scripts {proj}/reports/board {proj}/board/eod")
        c.put_file(REPO / "scripts" / "build_30d_comprehensive_review.py", f"{proj}/scripts/build_30d_comprehensive_review.py")
        # Ensure board.eod.rolling_windows is present (optional dependency)
        rw = REPO / "board" / "eod" / "rolling_windows.py"
        if rw.exists():
            c._execute(f"mkdir -p {proj}/board/eod")
            c.put_file(rw, f"{proj}/board/eod/rolling_windows.py")

        basename = "30d_comprehensive_review" if args.days > 0 else f"last{args.last_n_exits}_comprehensive_review"
        if args.days > 0:
            cmd = f"cd {proj} && python3 scripts/build_30d_comprehensive_review.py --base-dir . --out-dir reports/board --days {args.days} --output-basename {basename}"
        else:
            cmd = f"cd {proj} && python3 scripts/build_30d_comprehensive_review.py --base-dir . --out-dir reports/board --last-n-exits {args.last_n_exits} --output-basename {basename}"
        out, err, rc = c._execute(cmd, timeout=120)
        print(out)
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Build script exited with", rc, file=sys.stderr)
            return rc

        for name in [f"{basename}.json", f"{basename}.md"]:
            src = f"{proj}/reports/board/{name}"
            try:
                content, _, _ = c._execute(f"cat {src} 2>/dev/null || true")
                if content.strip():
                    dest = REPO / "reports" / "board" / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    print(f"Fetched {name} -> {dest}", file=sys.stderr)
            except Exception as e:
                print(f"Could not fetch {name}: {e}", file=sys.stderr)

    print(f"Board bundle is in reports/board/{basename}.{{json,md}}")
    print("Run Board Review using reports/board/30d_board_instructions.md with this bundle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
