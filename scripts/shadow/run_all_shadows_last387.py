#!/usr/bin/env python3
"""Run all shadows (A1, A2, A3, B1, B2, C2) for last-387 cohort on droplet. DROPLET_RUN=1. No execution imports."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

os.environ["DROPLET_RUN"] = "1"
REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SHADOWS = [
    ("A1", "scripts/shadow/run_a1_shadow.py"),
    ("A2", "scripts/shadow/run_a2_shadow.py"),
    ("A3", "scripts/shadow/run_a3_expectancy_floor_shadow.py"),
    ("B1", "scripts/shadow/run_b1_shadow.py"),
    ("B2", "scripts/shadow/run_b2_shadow.py"),
    ("C2", "scripts/shadow/run_c2_shadow.py"),
]


def main() -> int:
    base = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    if len(sys.argv) > 1:
        base = Path(sys.argv[1]).resolve()
    for name, script_rel in SHADOWS:
        script = base / script_rel
        if not script.exists():
            print(f"Skip {name}: {script} not found", file=sys.stderr)
            continue
        if "a3_expectancy" in script_rel:
            rc = subprocess.call(
                [sys.executable, str(script), "--base-dir", str(base), "--since-hours", "720"],
                cwd=base,
                timeout=120,
            )
        else:
            rc = subprocess.call(
                [sys.executable, str(script), str(base)],
                cwd=base,
                timeout=120,
            )
        print(f"[{name}] shadow rc={rc}", file=sys.stderr)
        if name == "A3":
            # Normalize A3 output to A3_shadow.json for synthesis
            src = base / "state" / "shadow" / "a3_expectancy_floor_shadow.json"
            dst = base / "state" / "shadow" / "A3_shadow.json"
            if src.exists():
                data = json.loads(src.read_text(encoding="utf-8"))
                data["shadow_id"] = "A3_shadow"
                data["would_admit_count"] = data.get("additional_admitted_trades", 0)
                data["proxy_pnl_delta"] = data.get("estimated_pnl_delta_usd")
                data["proxy_pnl_delta_label"] = data.get("estimated_pnl_delta_label", "proxy")
                data["tail_risk_notes"] = data.get("tail_risk_notes", [])
                dst.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    # CSA: run after shadows (always-on)
    mission_id = "shadows_last387_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    subprocess.call(
        [
            sys.executable,
            str(base / "scripts" / "audit" / "run_chief_strategy_auditor.py"),
            "--mission-id", mission_id,
            "--base-dir", str(base),
        ],
        cwd=base,
        timeout=60,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
