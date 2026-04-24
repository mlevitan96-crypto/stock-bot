#!/usr/bin/env python3
"""
Shadow: Stamp shortlist as proxy-only (no promotion until true replay is proven).
Read-only; writes stamped copy to .proxy_only.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Stamp shortlist as proxy-only")
    ap.add_argument("--shortlist", required=True)
    ap.add_argument("--method", default="proxy_pnl_scaling")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.shortlist)
    if not path.exists():
        print(f"Shortlist missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    data["method"] = args.method
    data["promotable"] = False
    data["note"] = "Proxy-only; no promotion until true replay artifacts exist and CSA verdict is TRUE_REPLAY_POSSIBLE."

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print("Stamped proxy-only:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
