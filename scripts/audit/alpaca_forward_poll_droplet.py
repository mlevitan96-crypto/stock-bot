#!/usr/bin/env python3
"""
Poll Alpaca droplet until forward cohort is non-vacuous (SSH) or timeout.

Stop when:
  (forward_economic_closes >= 10 AND forward_trade_intents_with_ct_and_tk >= 10)
  OR (runtime_sec >= 3600 AND forward_economic_closes > 0 AND forward_trade_intents_with_ct_and_tk > 0)

Default: --max-wait-seconds 21600, --poll-interval-seconds 300

Writes per-iteration bundles locally: <json_out_stem>_iter_<n>.json and .md
Final aggregate: --json-out path (JSON).
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


def _write_iter_md(path: Path, iteration: int, parsed: dict | None, exit_code: int | None) -> None:
    lines = [
        f"# Forward poll iteration {iteration}",
        "",
        f"exit_code: {exit_code}",
        "",
        "```json",
        json.dumps(parsed or {}, indent=2)[:12000],
        "```",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy-epoch", type=float, default=None)
    ap.add_argument("--poll-interval-seconds", type=int, default=300)
    ap.add_argument("--max-wait-seconds", type=int, default=21600)
    ap.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Final aggregate JSON (default: reports/ALPACA_FORWARD_POLL_<ts>.json)",
    )
    ap.add_argument(
        "--success-on-non-vacuous-only",
        action="store_true",
        help="Exit 0 when parity audit exit code != 2 (any forward activity)",
    )
    args = ap.parse_args()

    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%MZ")
    json_out = args.json_out or (REPO / "reports" / f"ALPACA_FORWARD_POLL_{ts}.json")
    stem = json_out.with_suffix("")

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

    started = time.monotonic()
    deadline = started + max(60, args.max_wait_seconds)
    iterations: list = []
    last: dict = {}
    n = 0

    while time.monotonic() < deadline:
        n += 1
        ra = c.execute_command(
            f"cd {proj} && PYTHONPATH={proj} {proj}/venv/bin/python /tmp/forward_parity_audit.py "
            f"--root {proj} --deploy-epoch {dep} 2>&1",
            timeout=240,
        )
        aout = (ra.get("stdout") or "").strip()
        exit_code = ra.get("exit_code")
        runtime_sec = int(time.monotonic() - started)
        j = None
        try:
            i = aout.rfind("{")
            if i >= 0:
                j, _ = JSONDecoder().raw_decode(aout, i)
        except json.JSONDecodeError:
            pass

        iter_rec = {
            "iteration": n,
            "runtime_sec": runtime_sec,
            "deploy_epoch": dep,
            "exit_code": exit_code,
            "parsed": j,
            "stdout_tail": aout[-12000:],
        }
        iterations.append(iter_rec)
        last = iter_rec

        json_out.parent.mkdir(parents=True, exist_ok=True)
        p_iter = Path(f"{stem}_iter_{n}.json")
        p_iter.write_text(json.dumps(iter_rec, indent=2), encoding="utf-8")
        _write_iter_md(Path(f"{stem}_iter_{n}.md"), n, j, exit_code)

        econ = (j or {}).get("forward_economic_closes") or 0
        ent = (j or {}).get("forward_trade_intents_with_ct_and_tk") or 0

        if args.success_on_non_vacuous_only and exit_code != 2:
            agg = {"status": "non_vacuous", "iterations": iterations, "final": iter_rec}
            json_out.write_text(json.dumps(agg, indent=2), encoding="utf-8")
            print(json.dumps(agg, indent=2))
            return 0

        if econ >= 10 and ent >= 10:
            agg = {"status": "threshold_met", "iterations": iterations, "final": iter_rec}
            json_out.write_text(json.dumps(agg, indent=2), encoding="utf-8")
            print(json.dumps(agg, indent=2))
            return 0

        if runtime_sec >= 3600 and econ > 0 and ent > 0:
            agg = {"status": "hour_non_vacuous", "iterations": iterations, "final": iter_rec}
            json_out.write_text(json.dumps(agg, indent=2), encoding="utf-8")
            print(json.dumps(agg, indent=2))
            return 0

        sleep_s = max(30, args.poll_interval_seconds)
        if time.monotonic() + sleep_s > deadline:
            break
        time.sleep(sleep_s)

    agg = {"status": "timeout", "iterations": iterations, "final": last}
    json_out.write_text(json.dumps(agg, indent=2), encoding="utf-8")
    print(json.dumps(agg, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
