#!/usr/bin/env python3
"""
One-time backfill: set entry_score in state/position_metadata.json for symbols that have
missing or zero entry_score, using the most recent open_ record per symbol in logs/attribution.jsonl.

Usage:
  python scripts/backfill_entry_scores_from_attribution.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill entry_score in position_metadata from attribution.jsonl")
    ap.add_argument("--dry-run", action="store_true", help="Only print what would be updated")
    args = ap.parse_args()

    meta_path = REPO_ROOT / "state" / "position_metadata.json"
    attr_path = REPO_ROOT / "logs" / "attribution.jsonl"

    if not meta_path.exists():
        print("state/position_metadata.json not found", file=sys.stderr)
        return 1
    if not attr_path.exists():
        print("logs/attribution.jsonl not found", file=sys.stderr)
        return 1

    # Build symbol -> last entry_score from attribution (open_ records only)
    last_score_by_symbol = {}
    try:
        with open(attr_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("type") != "attribution":
                        continue
                    sym = (rec.get("symbol") or "").upper()
                    if not sym:
                        continue
                    tid = str(rec.get("trade_id", ""))
                    if not tid.startswith("open_"):
                        continue
                    ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
                    s = ctx.get("entry_score")
                    if s is not None:
                        try:
                            last_score_by_symbol[sym] = float(s)
                        except (TypeError, ValueError):
                            pass
                except Exception:
                    continue
    except Exception as e:
        print(f"Failed to read attribution: {e}", file=sys.stderr)
        return 1

    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        print(f"Failed to read position_metadata: {e}", file=sys.stderr)
        return 1

    if not isinstance(metadata, dict):
        print("position_metadata.json is not a dict", file=sys.stderr)
        return 1

    updated = 0
    for symbol, meta in list(metadata.items()):
        if not isinstance(meta, dict):
            continue
        current = meta.get("entry_score")
        try:
            current_f = float(current) if current is not None else 0.0
        except (TypeError, ValueError):
            current_f = 0.0
        if current_f > 0:
            continue
        score = last_score_by_symbol.get(symbol.upper())
        if score is None or score <= 0:
            continue
        if args.dry_run:
            print(f"Would set {symbol} entry_score: 0.0 -> {score}")
        else:
            meta["entry_score"] = score
            if "updated_at" not in meta:
                from datetime import datetime, timezone
                meta["updated_at"] = datetime.now(timezone.utc).isoformat()
            print(f"Set {symbol} entry_score: 0.0 -> {score}")
        updated += 1

    if updated and not args.dry_run:
        try:
            from config.registry import atomic_write_json
            atomic_write_json(meta_path, metadata)
        except Exception as e:
            print(f"Failed to write position_metadata: {e}", file=sys.stderr)
            return 1

    print(f"Done. Updated {updated} symbol(s).")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    sys.exit(main())
