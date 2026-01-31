#!/usr/bin/env python3
"""
Generate SHADOW snapshots from master_trade_log (or harness snapshots).
NO-APPLY. Writes to logs/signal_snapshots_shadow_<DATE>.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--source", default="master_trade_log", choices=["master_trade_log", "harness"])
    ap.add_argument("--max-records", type=int, default=50)
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()

    base = Path(args.base_dir) if args.base_dir else REPO
    target_date = args.date

    from telemetry.snapshot_builder import write_shadow_snapshots, _load_shadow_profiles

    profiles = list(_load_shadow_profiles().keys())

    if args.source == "harness":
        path = base / "logs" / f"signal_snapshots_harness_{target_date}.jsonl"
    else:
        path = base / "logs" / "master_trade_log.jsonl"

    records = []
    if path.exists():
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if args.source == "harness":
                    records.append(rec)
                else:
                    ts = rec.get("entry_ts") or rec.get("exit_ts") or rec.get("timestamp", "")
                    if target_date and not str(ts).startswith(target_date):
                        continue
                    records.append(rec)
                if len(records) >= args.max_records:
                    break

    if args.source == "harness":
        for r in records:
            comps = r.get("components") or {}
            contribs = {k: v.get("contrib") for k, v in comps.items() if isinstance(v, dict) and "contrib" in v}
            r["feature_snapshot"] = contribs
            r["composite_meta"] = {"components": comps, "component_contributions": contribs}

    if not records:
        sys.stderr.write(f"WARN: No records for {target_date} from {args.source}\n")
        return 0

    written = write_shadow_snapshots(base, target_date, records, profiles)
    print(f"Wrote {written} shadow snapshots to logs/signal_snapshots_shadow_{target_date}.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
