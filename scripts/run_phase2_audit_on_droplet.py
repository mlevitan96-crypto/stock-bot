#!/usr/bin/env python3
"""Upload phase2 audit + activation proof to droplet, run (--local), fetch reports + CSVs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-01-26", help="YYYY-MM-DD")
    ap.add_argument("--skip-proof", action="store_true", help="Skip phase2_activation_proof run")
    args = ap.parse_args()
    date = args.date

    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    ssh = sftp = None
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()

        # 1) Upload audit + proof + runtime-identity scripts
        for name in ["phase2_forensic_audit.py", "phase2_activation_proof.py", "phase2_runtime_identity.py"]:
            local_f = REPO / "scripts" / name
            remote_f = f"{REMOTE_ROOT}/scripts/{name}"
            if local_f.exists():
                sftp.put(str(local_f), remote_f)
                print(f"[OK] Uploaded {name}")
            else:
                print(f"[WARN] Missing {local_f}")

        # 2) Run audit on droplet (--local = use droplet's logs/state)
        cmd = f"cd {REMOTE_ROOT} && python3 scripts/phase2_forensic_audit.py --date {date} --local"
        out, err, rc = client._execute(cmd, timeout=120)
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        if rc not in (0, 1):
            print(f"[WARN] Audit exit code {rc}", file=sys.stderr)

        # 2b) Run activation proof (heartbeats, trade_intent, shadow, symbol_risk, EOD)
        if not args.skip_proof:
            cmd2 = f"cd {REMOTE_ROOT} && python3 scripts/phase2_activation_proof.py --date {date}"
            out2, err2, rc2 = client._execute(cmd2, timeout=90)
            print(out2 or "")
            if err2:
                print(err2, file=sys.stderr)

        # 2c) Runtime identity
        cmd3 = f"cd {REMOTE_ROOT} && python3 scripts/phase2_runtime_identity.py"
        client._execute(cmd3, timeout=30)

        # 3) Fetch reports and CSVs
        report_remote = f"{REMOTE_ROOT}/reports/PHASE2_VERIFICATION_SUMMARY_{date}.md"
        report_local = REPO / "reports" / f"PHASE2_VERIFICATION_SUMMARY_{date}.md"
        report_local.parent.mkdir(parents=True, exist_ok=True)
        try:
            sftp.get(report_remote, str(report_local))
            print(f"[OK] Fetched PHASE2_VERIFICATION_SUMMARY -> {report_local}")
        except FileNotFoundError:
            print(f"[FAIL] Report not found: {report_remote}", file=sys.stderr)
        for rname in [f"PHASE2_ACTIVATION_PROOF_{date}.md", "PHASE2_RUNTIME_IDENTITY.md"]:
            try:
                sftp.get(f"{REMOTE_ROOT}/reports/{rname}", str(REPO / "reports" / rname))
                print(f"[OK] Fetched {rname}")
            except FileNotFoundError:
                print(f"[WARN] Missing {rname}")

        exports_local = REPO / "exports"
        exports_local.mkdir(parents=True, exist_ok=True)
        for name in [
            "VERIFY_trade_intent_samples.csv",
            "VERIFY_exit_intent_samples.csv",
            "VERIFY_directional_gate_blocks.csv",
            "VERIFY_displacement_decisions.csv",
            "VERIFY_shadow_variant_activity.csv",
            "VERIFY_high_vol_cohort.csv",
        ]:
            remote = f"{REMOTE_ROOT}/exports/{name}"
            local = exports_local / name
            try:
                sftp.get(remote, str(local))
                print(f"[OK] Fetched {name} -> {local}")
            except FileNotFoundError:
                print(f"[WARN] Missing on droplet: {remote}", file=sys.stderr)

        return 0
    except Exception as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1
    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
