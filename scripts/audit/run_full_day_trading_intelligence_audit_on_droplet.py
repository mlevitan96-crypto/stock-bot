#!/usr/bin/env python3
"""
Run Full Day Trading Intelligence Audit ON DROPLET (live data), then fetch artifacts.
Uses droplet logs/state/telemetry. Execute from repo root. Requires: droplet_client, paramiko.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run full day trading intelligence audit on droplet and fetch artifacts")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--require-counter-intel", action="store_true", help="Set REQUIRE_COUNTER_INTEL=true and run CI emit/merge")
    ap.add_argument("--min-ci-events", type=int, default=None, help="Set MIN_CI_EVENTS (e.g. 1 for strict); default leaves script default")
    args = ap.parse_args()

    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1

    client = DropletClient()

    # 0) Pull latest so droplet has audit script and Phase 1 scripts
    out_pull, err_pull, rc_pull = client._execute_with_cd("git pull origin main", timeout=30)
    print("git pull:", out_pull or err_pull or "ok")
    if rc_pull != 0:
        print("Warning: git pull had non-zero exit", rc_pull, file=sys.stderr)

    # 1) Run full audit script (CSA + SRE + multi-persona; optional strict CI gate)
    env_parts = []
    if args.date:
        env_parts.append(f"DATE={args.date}")
    if args.require_counter_intel:
        env_parts.append("REQUIRE_COUNTER_INTEL=true")
    if args.min_ci_events is not None:
        env_parts.append(f"MIN_CI_EVENTS={args.min_ci_events}")
    prefix = " ".join(env_parts) + " " if env_parts else ""
    cmd = f"{prefix}bash scripts/audit/run_full_day_trading_intelligence_audit.sh"
    out, err, rc = client._execute_with_cd(cmd, timeout=600)
    print("=== AUDIT OUTPUT ===")
    print(out or "")
    if err:
        print(err, file=sys.stderr)
    print("=== EXIT CODE ===", rc)

    # 2) Resolve date for artifact paths (script uses DATE env or today)
    if args.date:
        date_str = args.date
    else:
        import datetime
        date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    # 3) Fetch any artifacts that exist (CSA + SRE + signals + ideas + verdict + board)
    artifacts = [
        ("reports/ledger", f"FULL_TRADE_LEDGER_{date_str}.json"),
        ("reports/audit", f"SRE_DAY_HEALTH_{date_str}.json"),
        ("reports/audit", f"CSA_DECISION_QUALITY_{date_str}.json"),
        ("reports/experiments", f"SIGNAL_WEIGHT_SWEEPS_{date_str}.json"),
        ("reports/experiments", f"SIGNAL_PROFITABILITY_{date_str}.json"),
        ("reports/ideas", f"RAW_IDEA_POOL_{date_str}.json"),
        ("reports/ideas", f"CLUSTERED_IDEAS_{date_str}.json"),
        ("reports/experiments", f"PERSONA_REVIEWS_{date_str}.json"),
        ("reports/experiments", f"IDEA_SCORECARD_{date_str}.json"),
        ("reports/audit", f"CSA_DAY_PROMOTION_VERDICT_{date_str}.json"),
        ("reports/board", f"DAY_TRADING_INTELLIGENCE_BOARD_PACKET_{date_str}.md"),
    ]
    fetched = 0
    for remote_sub, name in artifacts:
        remote = f"{remote_sub}/{name}"
        cat_out, _, _ = client._execute_with_cd(f"cat {remote} 2>/dev/null || true", timeout=15)
        if not (cat_out or "").strip():
            print("Missing on droplet:", remote)
            continue
        local_dir = (REPO / remote_sub).resolve()
        local_dir.mkdir(parents=True, exist_ok=True)
        out_path = local_dir / name
        try:
            if name.endswith(".json"):
                json.loads(cat_out)
            out_path.write_text(cat_out, encoding="utf-8")
        except (json.JSONDecodeError, OSError):
            out_path.write_text(cat_out, encoding="utf-8")
        print("Fetched", out_path)
        fetched += 1

    print("Fetched", fetched, "artifact(s). Audit exit code:", rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
