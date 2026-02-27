#!/usr/bin/env python3
"""
Create a deterministic Alpaca bars snapshot (tar of data/bars or manifest).
Droplet-only; used by run_alpaca_backtest_orchestration_on_droplet.sh.
Usage: python scripts/prep_alpaca_bars_snapshot.py --out data/snapshots/alpaca_1m_snapshot_<ts>.tar.gz
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA_BARS = REPO / "data" / "bars"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output tar path (e.g. data/snapshots/alpaca_1m_snapshot_<ts>.tar.gz)")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not DATA_BARS.exists():
        # Write manifest-only so orchestration can continue (bars may be fetched elsewhere)
        manifest = {
            "data_snapshot": str(out),
            "source": "manifest_only",
            "reason": "data/bars not present; use live bars or fetch first",
            "bars_path": str(DATA_BARS),
        }
        out_suffix = out.suffix
        manifest_path = out.with_suffix(".manifest.json")
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Wrote manifest (no bars): {manifest_path}")
        return 0

    # Tar data/bars into snapshot
    try:
        subprocess.run(
            ["tar", "-czf", str(out), "-C", str(REPO), "data/bars"],
            check=True,
            capture_output=True,
            timeout=300,
        )
        print(f"Snapshot: {out}")
        return 0
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # No tar or failed: write manifest so pipeline can proceed
        manifest = {
            "data_snapshot": str(out),
            "source": "manifest_only",
            "reason": str(e),
            "bars_path": str(DATA_BARS),
        }
        manifest_path = out.with_suffix(".manifest.json")
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Wrote manifest (tar failed): {manifest_path}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
