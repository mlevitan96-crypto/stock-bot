#!/usr/bin/env python3
"""
Poll Alpaca droplet until forward cohort is non-vacuous or timeout (SSH).

Does not redeploy. Expects /tmp/alpaca_deploy_ts_utc.txt on droplet (from prior deploy)
or pass --deploy-epoch explicitly.

Exits 0 when forward_economic_closes >= --min-closes AND forward_trade_intents_with_ct_and_tk >= --min-intents,
or when --success-on-non-vacuous-only and forward cohort is non-vacuous (parity audit exit != 2).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from json import JSONDecoder
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy-epoch", type=float, default=None)
    ap.add_argument("--min-closes", type=int, default=10)
    ap.add_argument("--min-intents", type=int, default=10)
    ap.add_argument("--interval-sec", type=int, default=120)
    ap.add_argument("--max-wait-min", type=int, default=60)
    ap.add_argument(
        "--success-on-non-vacuous-only",
        action="store_true",
        help="Exit 0 as soon as forward_parity_audit exit code is not 2 (any forward activity)",
    )
    args = ap.parse_args()

    c = DropletClient()
    proj = "/root/stock-bot"
    dep = args.deploy_epoch
    if dep is None:
        rts = c.execute_command("cat /tmp/alpaca_deploy_ts_utc.txt 2>/dev/null || echo 0", timeout=10)
        dep = float((rts.get("stdout") or "0").strip().split()[0] or 0)

    local_audit = REPO / "scripts" / "audit" / "forward_parity_audit.py"
    if not local_audit.is_file():
        print("missing forward_parity_audit.py", file=sys.stderr)
        return 2
    c.put_file(local_audit, "/tmp/forward_parity_audit.py")

    deadline = time.monotonic() + max(1, args.max_wait_min) * 60.0
    last: dict = {}
    while time.monotonic() < deadline:
        ra = c.execute_command(
            f"cd {proj} && PYTHONPATH={proj} {proj}/venv/bin/python /tmp/forward_parity_audit.py "
            f"--root {proj} --deploy-epoch {dep} 2>&1",
            timeout=180,
        )
        aout = (ra.get("stdout") or "").strip()
        exit_code = ra.get("exit_code")
        last = {"stdout_tail": aout[-20000:], "exit_code": exit_code, "deploy_epoch": dep}
        j = None
        try:
            i = aout.rfind("{")
            if i >= 0:
                j, _ = JSONDecoder().raw_decode(aout, i)
        except json.JSONDecodeError:
            pass
        if j:
            last["parsed"] = {
                "forward_economic_closes": j.get("forward_economic_closes"),
                "forward_trade_intents_with_ct_and_tk": j.get("forward_trade_intents_with_ct_and_tk"),
                "forward_cohort_vacuous": j.get("forward_cohort_vacuous"),
            }
            if args.success_on_non_vacuous_only and exit_code != 2:
                print(json.dumps({"status": "non_vacuous", **last}, indent=2))
                return 0
            if (
                (j.get("forward_economic_closes") or 0) >= args.min_closes
                and (j.get("forward_trade_intents_with_ct_and_tk") or 0) >= args.min_intents
            ):
                print(json.dumps({"status": "threshold_met", **last}, indent=2))
                return 0
        time.sleep(max(30, args.interval_sec))

    print(json.dumps({"status": "timeout", **last}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
