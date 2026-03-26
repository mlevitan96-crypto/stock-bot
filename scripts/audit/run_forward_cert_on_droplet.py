#!/usr/bin/env python3
"""
Run deploy + capture health + forward cert metrics on Alpaca droplet (SSH).
Read-only after deploy; writes local JSON summary to stdout or path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402


def main() -> int:
    c = DropletClient()
    proj = "/root/stock-bot"
    out: dict = {"project_dir": proj, "steps": {}}

    # 1) Deploy timestamp + git
    r0 = c.execute_command(
        f"cd {proj} && date -u +%s > /tmp/alpaca_deploy_ts_utc.txt && "
        f"git fetch origin main && git reset --hard origin/main && "
        f"echo -n $(cat /tmp/alpaca_deploy_ts_utc.txt) && echo ' DEPLOY_TS' && git rev-parse HEAD",
        timeout=120,
    )
    out["steps"]["deploy_git"] = {
        "stdout": (r0.get("stdout") or "").strip(),
        "stderr": (r0.get("stderr") or "").strip(),
        "exit_code": r0.get("exit_code"),
    }

    # 2) Restart services
    for unit in ("stock-bot.service", "uw-flow-daemon.service", "stock-bot-dashboard.service"):
        rr = c.execute_command(f"systemctl restart {unit} 2>&1", timeout=90)
        out["steps"][f"restart_{unit}"] = {
            "stdout": (rr.get("stdout") or "").strip(),
            "exit_code": rr.get("exit_code"),
        }

    # 3) Status (no-pager)
    rs = c.execute_command(
        "systemctl status stock-bot.service uw-flow-daemon.service stock-bot-dashboard.service --no-pager -l 2>&1 | head -80",
        timeout=30,
    )
    out["steps"]["systemctl_status"] = (rs.get("stdout") or "").strip()

    # 4) Journal last 200 each
    journals = {}
    for unit in ("stock-bot.service", "uw-flow-daemon.service", "stock-bot-dashboard.service"):
        rj = c.execute_command(f"journalctl -u {unit} --no-pager -n 200 2>&1", timeout=45)
        journals[unit] = (rj.get("stdout") or "").strip()
    out["steps"]["journals_last_200"] = journals

    # 5) Read DEPLOY_TS from droplet
    rts = c.execute_command("cat /tmp/alpaca_deploy_ts_utc.txt 2>/dev/null || echo 0", timeout=10)
    deploy_ts = (rts.get("stdout") or "0").strip().split()[0]
    try:
        deploy_epoch = float(deploy_ts)
    except ValueError:
        deploy_epoch = 0.0
    out["DEPLOY_TS_UTC_EPOCH"] = deploy_epoch

    # 6) Strict gate full + forward segment (strict era floor unchanged)
    rg = c.execute_command(
        f"cd {proj} && PYTHONPATH={proj} {proj}/venv/bin/python telemetry/alpaca_strict_completeness_gate.py "
        f"--root . --audit --open-ts-epoch 1774458080 --forward-since-epoch {deploy_epoch} 2>&1",
        timeout=120,
    )
    gout = (rg.get("stdout") or "").strip()
    out["steps"]["strict_gate_forward"] = {"stdout_tail": gout[-15000:], "exit_code": rg.get("exit_code")}
    try:
        # last JSON object in output
        jstart = gout.rfind("{")
        if jstart >= 0:
            out["strict_gate_json"] = json.loads(gout[jstart:])
    except json.JSONDecodeError:
        out["strict_gate_json_parse_error"] = True

    # 7) Parity audit script (upload — may not be in repo until second pull; try both paths)
    local_audit = REPO / "scripts" / "audit" / "forward_parity_audit.py"
    if local_audit.is_file():
        try:
            c.put_file(local_audit, "/tmp/forward_parity_audit.py")
            ra = c.execute_command(
                f"cd {proj} && PYTHONPATH={proj} {proj}/venv/bin/python /tmp/forward_parity_audit.py "
                f"--root {proj} --deploy-epoch {deploy_epoch} 2>&1",
                timeout=120,
            )
            aout = (ra.get("stdout") or "").strip()
            out["steps"]["forward_parity_audit"] = {"stdout": aout[-12000:], "exit_code": ra.get("exit_code")}
            try:
                aj = aout.rfind("{")
                if aj >= 0:
                    out["forward_parity_json"] = json.loads(aout[aj:])
            except json.JSONDecodeError:
                out["forward_parity_json_parse_error"] = True
        except Exception as e:
            out["forward_parity_upload_error"] = str(e)[:500]

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
