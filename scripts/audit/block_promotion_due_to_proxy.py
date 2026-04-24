#!/usr/bin/env python3
"""
Audit: Block promotion when shadow shortlist is proxy-only.
Records reason and block flag for CSA/SRE. No promotion unless true replay is proven.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Block promotion due to proxy-only shadow")
    ap.add_argument("--reason", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    out = {
        "blocked": True,
        "reason": args.reason,
        "note": "Promotion from shadow shortlist blocked until true replay artifacts exist and CSA verdict is TRUE_REPLAY_POSSIBLE.",
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Promotion blocked:", args.reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
