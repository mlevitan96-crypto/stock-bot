#!/usr/bin/env python3
"""
Load promotion record and assert it is currently active (now within active_from..active_until).
Output: ACTIVE_PROMOTION_<date>.json for downstream runtime steps.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Load promotion and assert active")
    ap.add_argument("--promotion", required=True)
    ap.add_argument("--assert-active", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.promotion)
    if not path.exists():
        print(f"Promotion missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    active_from = data.get("active_from")
    active_until = data.get("active_until")
    if not active_from or not active_until:
        print("Promotion missing active_from or active_until", file=sys.stderr)
        return 2

    try:
        from_dt = datetime.fromisoformat(active_from.replace("Z", "+00:00"))
        until_dt = datetime.fromisoformat(active_until.replace("Z", "+00:00"))
    except Exception as e:
        print("Invalid active_from/active_until:", e, file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    if from_dt.tzinfo is None:
        from_dt = from_dt.replace(tzinfo=timezone.utc)
    if until_dt.tzinfo is None:
        until_dt = until_dt.replace(tzinfo=timezone.utc)

    # Active = within window; or not yet expired (so we can arm before window starts)
    within_window = from_dt <= now <= until_dt
    not_expired = now <= until_dt
    if args.assert_active and not not_expired:
        print(f"Promotion expired: now={now.isoformat()} > until={until_dt.isoformat()}", file=sys.stderr)
        return 3

    out = dict(data)
    out["loaded_at"] = now.isoformat()
    out["active"] = within_window
    out["not_expired"] = not_expired

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Loaded active promotion:", data.get("selected_parameter"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
