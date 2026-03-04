#!/usr/bin/env python3
"""
Run all parallel board reviews and A3 shadow per scope ON THE DROPLET (DROPLET_RUN=1).
Scopes: 7d, 14d, 30d (time); last100, last387, last750 (exit count).
Outputs: reports/board/<scope>_comprehensive_review.{json,md}, reports/board/scenarios/<scope>_A3_shadow.{json,md}.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ["DROPLET_RUN"] = "1"

SCOPES_TIME = [("7d", 7, 0), ("14d", 14, 0), ("30d", 30, 0)]
SCOPES_EXITS = [("last100", 100), ("last387", 387), ("last750", 750)]
# A3 shadow since_hours per scope (time: hours in scope; exits: use 720 for 30d window)
SCOPE_HOURS = {"7d": 168, "14d": 336, "30d": 720, "last100": 720, "last387": 720, "last750": 720}


def main() -> int:
    base = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    if len(sys.argv) > 1:
        base = Path(sys.argv[1]).resolve()
    board = base / "reports" / "board"
    scenarios_dir = base / "reports" / "board" / "scenarios"
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    state_shadow = base / "state" / "shadow"
    state_shadow.mkdir(parents=True, exist_ok=True)

    def run_cmd(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
        try:
            r = subprocess.run(cmd, cwd=base, capture_output=True, text=True, timeout=timeout)
            return r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            return -1, "timeout"
        except Exception as e:
            return -1, str(e)

    # Time-window reviews
    for scope, days, _ in SCOPES_TIME:
        rc, out = run_cmd([
            sys.executable, str(base / "scripts" / "build_30d_comprehensive_review.py"),
            "--base-dir", str(base), "--out-dir", str(board),
            "--days", str(days), "--output-basename", f"{scope}_comprehensive_review",
        ])
        print(f"[{scope}] build rc={rc}")
        if rc != 0:
            print(out, file=sys.stderr)

    # Exit-count reviews
    for scope, n in SCOPES_EXITS:
        rc, out = run_cmd([
            sys.executable, str(base / "scripts" / "build_30d_comprehensive_review.py"),
            "--base-dir", str(base), "--out-dir", str(board),
            "--last-n-exits", str(n), "--output-basename", f"{scope}_comprehensive_review",
        ])
        print(f"[{scope}] build rc={rc}")
        if rc != 0:
            print(out, file=sys.stderr)

    # A3 shadow per scope (overwrites state/shadow each run; then we copy to scenarios/<scope>_A3_shadow)
    for scope in [s[0] for s in SCOPES_TIME] + [s[0] for s in SCOPES_EXITS]:
        since = SCOPE_HOURS.get(scope, 24)
        rc, _ = run_cmd([
            sys.executable, str(base / "scripts" / "shadow" / "run_a3_expectancy_floor_shadow.py"),
            "--base-dir", str(base), "--since-hours", str(since),
        ])
        print(f"[{scope}] A3 shadow rc={rc}")
        shadow_json = state_shadow / "a3_expectancy_floor_shadow.json"
        shadow_md = base / "reports" / "audit" / "A3_SHADOW_RESULTS.md"
        if shadow_json.exists():
            data = json.loads(shadow_json.read_text(encoding="utf-8"))
            data["scope"] = scope
            data["since_hours"] = since
            out_j = scenarios_dir / f"{scope}_A3_shadow.json"
            out_j.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            out_md = scenarios_dir / f"{scope}_A3_shadow.md"
            out_md.write_text(
                f"# A3 shadow — {scope}\n\n"
                f"since_hours={since}\n\n"
                f"additional_admitted_trades: {data.get('additional_admitted_trades')}\n"
                f"estimated_pnl_delta_usd: {data.get('estimated_pnl_delta_usd')} ({data.get('estimated_pnl_delta_label', 'proxy')})\n",
                encoding="utf-8",
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
