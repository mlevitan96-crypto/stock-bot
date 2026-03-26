#!/usr/bin/env python3
"""
Orchestrate Alpaca droplet learning-cert mission: git sync, service discovery, replay gate, cert bundle, optional forward poll evidence.

Run from developer machine with droplet_config.json + SSH. Writes under reports/audit/ and reports/.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from json import JSONDecoder
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402

TS_DEFAULT = "20260327_0200Z"
PROJ = "/root/stock-bot"


def _run(c: DropletClient, cmd: str, timeout: int = 180) -> dict:
    return c.execute_command(cmd, timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ts", default=TS_DEFAULT)
    ap.add_argument("--max-poll-seconds", type=int, default=900, help="Forward poll budget (not full 6h)")
    ap.add_argument("--skip-poll", action="store_true")
    args = ap.parse_args()
    ts = args.ts
    c = DropletClient()

    bundle: dict = {"ts": ts, "steps": {}}

    # Git
    rg = _run(
        c,
        f"cd {PROJ} && git fetch origin main && git reset --hard origin/main && git rev-parse HEAD",
        timeout=120,
    )
    bundle["steps"]["git"] = {
        "stdout": (rg.get("stdout") or "").strip(),
        "stderr": (rg.get("stderr") or "").strip()[:2000],
        "exit_code": rg.get("exit_code"),
    }

    # Service discovery
    u1 = _run(c, "systemctl list-units --type=service --all 2>&1 | egrep -i 'alpaca|stock-bot|telemetry|dashboard|sidecar' || true", 60)
    u2 = _run(c, "systemctl list-unit-files 2>&1 | egrep -i 'alpaca|stock-bot|telemetry|dashboard|sidecar' || true", 60)
    bundle["steps"]["list_units_egrep"] = (u1.get("stdout") or "").strip()
    bundle["steps"]["list_unit_files_egrep"] = (u2.get("stdout") or "").strip()

    units = ["stock-bot.service", "uw-flow-daemon.service", "stock-bot-dashboard.service"]
    statuses = {}
    journals = {}
    for unit in units:
        st = _run(c, f"systemctl status {unit} --no-pager -l 2>&1", 45)
        statuses[unit] = (st.get("stdout") or "").strip()[:8000]
        jr = _run(c, f"journalctl -u {unit} --no-pager -n 400 2>&1", 60)
        journals[unit] = (jr.get("stdout") or "").strip()[-80000:]

    bundle["steps"]["systemctl_status"] = statuses
    bundle["steps"]["journals_400"] = journals

    # Upload scripts (ensure dirs exist on droplet)
    for rel in (
        "scripts/audit/forward_parity_audit.py",
        "scripts/audit/alpaca_replay_lab_strict_gate.py",
        "scripts/audit/alpaca_strict_cohort_cert_bundle.py",
        "scripts/audit/alpaca_strict_six_trade_additive_repair.py",
        "scripts/audit/alpaca_strict_repair_forensics.py",
        "telemetry/alpaca_strict_completeness_gate.py",
        "src/telemetry/strict_chain_guard.py",
        "src/exit/exit_attribution.py",
    ):
        rel = rel.replace("\\", "/")
        lp = REPO / rel
        if lp.is_file():
            remote = f"{PROJ}/{rel}"
            parent = rel.rsplit("/", 1)[0]
            c.execute_command(f"mkdir -p {PROJ}/{parent}", 15)
            try:
                c.put_file(lp, remote)
            except Exception as e:
                bundle.setdefault("upload_errors", []).append(f"{rel}: {e}")

    # Replay lab on droplet (full logs, auto era, 72h slice)
    replay_json_path = f"/tmp/ALPACA_REPLAY_GATE_{ts}.json"
    rr = _run(
        c,
        f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python {PROJ}/scripts/audit/alpaca_replay_lab_strict_gate.py "
        f"--workspace /tmp/alpaca_replay_lab_ws --source-root {PROJ} --init-snapshot "
        f"--slice-hours 72 --replay-era-auto --audit --json-out {replay_json_path} --ts {ts} 2>&1",
        timeout=300,
    )
    bundle["steps"]["replay_lab"] = {"stdout": (rr.get("stdout") or "").strip()[-8000:], "exit_code": rr.get("exit_code")}

    rj = _run(c, f"cat {replay_json_path} 2>/dev/null || echo {{}}", 30)
    raw = (rj.get("stdout") or "").strip()
    strict_epoch = None
    try:
        rep = json.loads(raw)
        strict_epoch = rep.get("strict_epoch_start")
        bundle["replay_bundle"] = rep
    except json.JSONDecodeError:
        bundle["replay_parse_error"] = raw[:500]

    # Strict gate + cert bundle on full root with same epoch
    if strict_epoch is not None:
        # Idempotent additive backfill for incomplete strict chains (sidecar logs only).
        rpair = _run(
            c,
            f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python "
            f"{PROJ}/scripts/audit/alpaca_strict_six_trade_additive_repair.py --root {PROJ} --apply "
            f"--repair-all-incomplete-in-era --open-ts-epoch {strict_epoch} 2>&1",
            timeout=300,
        )
        bundle["steps"]["strict_repair_apply"] = {
            "exit_code": rpair.get("exit_code"),
            "stdout_tail": ((rpair.get("stdout") or "").strip())[-4000:],
        }

        sg = _run(
            c,
            f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python {PROJ}/telemetry/alpaca_strict_completeness_gate.py "
            f"--root {PROJ} --audit --open-ts-epoch {strict_epoch} 2>&1",
            timeout=240,
        )
        gout = (sg.get("stdout") or "").strip()
        bundle["steps"]["strict_gate"] = {"exit_code": sg.get("exit_code"), "stdout_tail": gout[-15000:]}
        gi = gout.find("{")
        if gi >= 0:
            try:
                bundle["strict_gate_json"] = JSONDecoder().raw_decode(gout, gi)[0]
            except json.JSONDecodeError:
                bundle["strict_gate_parse_error"] = True

        cb_path = f"/tmp/ALPACA_CERT_BUNDLE_{ts}.json"
        cb = _run(
            c,
            f"cd {PROJ} && PYTHONPATH={PROJ} {PROJ}/venv/bin/python {PROJ}/scripts/audit/alpaca_strict_cohort_cert_bundle.py "
            f"--root {PROJ} --open-ts-epoch {strict_epoch} --trace-sample 15 --json-out {cb_path} 2>&1",
            timeout=240,
        )
        bundle["steps"]["cert_bundle"] = {"stdout": (cb.get("stdout") or "").strip()[-6000:], "exit_code": cb.get("exit_code")}
        cbr = _run(c, f"cat {cb_path} 2>/dev/null || echo {{}}", 30)
        try:
            bundle["cert_bundle_json"] = json.loads((cbr.get("stdout") or "{}").strip())
        except json.JSONDecodeError:
            bundle["cert_bundle_parse_error"] = (cbr.get("stdout") or "")[:400]

    # Forward poll (local script invokes SSH)
    if not args.skip_poll:
        import subprocess

        poll_out = REPO / "reports" / f"ALPACA_FORWARD_POLL_{ts}.json"
        pr = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/audit/alpaca_forward_poll_droplet.py"),
                "--max-wait-seconds",
                str(max(120, args.max_poll_seconds)),
                "--poll-interval-seconds",
                "60",
                "--json-out",
                str(poll_out),
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=max(130, args.max_poll_seconds + 60),
        )
        bundle["steps"]["forward_poll_local"] = {
            "returncode": pr.returncode,
            "stdout_tail": (pr.stdout or "")[-4000:],
            "stderr_tail": (pr.stderr or "")[-2000:],
        }
        if poll_out.is_file():
            try:
                bundle["forward_poll_json"] = json.loads(poll_out.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

    # Write master mission JSON
    out_path = REPO / "reports" / f"ALPACA_DROPLET_CERT_MISSION_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
