#!/usr/bin/env python3
"""
Deploy and run PATH_TO_PROFITABILITY autopilot on droplet (MEMORY_BANK golden workflow).
Uploads scripts, pulls on droplet, runs autopilot (with STOP_AFTER_APPLY=1 for verify), fetches results.
For full run (wait 50 trades + compare), run on droplet: bash scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh in screen/tmux.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh",
    "scripts/analysis/run_effectiveness_reports.py",
    "scripts/analysis/attribution_loader.py",
    "scripts/analysis/compare_effectiveness_runs.py",
    "scripts/governance/generate_recommendation.py",
    "scripts/ops/apply_paper_overlay.py",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    stop_after_apply = os.environ.get("STOP_AFTER_APPLY", "1")
    start_date = os.environ.get("START_DATE_UTC", "2026-02-01")
    end_date = os.environ.get("END_DATE_UTC", "")

    with DropletClient() as c:
        # Ensure droplet has latest code
        print("--- Git pull on droplet ---")
        out, err, rc = c._execute(
            f"cd {c.project_dir} && git fetch origin && git pull origin main",
            timeout=60,
        )
        if rc != 0:
            print("Warning: git pull non-zero (continuing with upload)", file=sys.stderr)
        print(out[-1500:] if out and len(out) > 1500 else (out or ""))

        # Upload autopilot and deps so they exist even if not on main yet
        print("\n--- Upload autopilot + deps ---")
        for rel in FILES:
            local = REPO / rel
            if not local.is_file():
                print(f"Skip (missing): {rel}", file=sys.stderr)
                continue
            remote = f"{pd}/{rel}".replace("\\", "/")
            remote_dir = "/".join(remote.split("/")[:-1])
            c._execute(f"mkdir -p '{remote_dir}'", timeout=5)
            content = local.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
            c._connect()
            sftp = c.ssh_client.open_sftp()
            sftp.putfo(io.BytesIO(content.encode("utf-8")), remote)
            sftp.close()
            print(f"Uploaded: {rel}")

        c._execute(f"chmod +x {pd}/scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh 2>/dev/null", timeout=5)

        # Run autopilot (stop after apply so we don't block on 50-trade wait)
        env_parts = [
            f"STOP_AFTER_APPLY={stop_after_apply}",
            f"START_DATE_UTC={start_date}",
        ]
        if end_date:
            env_parts.append(f"END_DATE_UTC={end_date}")
        env_str = " ".join(env_parts)

        cmd = f"cd {c.project_dir} && {env_str} bash scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh"
        print("\n--- Running PATH_TO_PROFITABILITY autopilot on droplet ---")
        print(f"   STOP_AFTER_APPLY={stop_after_apply} START_DATE_UTC={start_date}\n")
        out, err, rc = c._execute(cmd, timeout=300)

        print(out[-8000:] if out and len(out) > 8000 else (out or "(no stdout)"))
        if err:
            print("stderr:", err[:2000] if len(err) > 2000 else err)
        print("exit code:", rc)

        # Find latest run dir and fetch
        list_out, _, _ = c._execute(
            f"cd {c.project_dir} && ls -1dt reports/path_to_profitability/path_to_profitability_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_tag = (list_out or "").strip()
        if run_tag:
            name = Path(run_tag).name
            out_dir = REPO / "reports" / "path_to_profitability" / name
            out_dir.mkdir(parents=True, exist_ok=True)
            for fname in [
                "CURSOR_FINAL_SUMMARY.txt",
                "recommendation.json",
                "overlay_config.json",
                "lock_or_revert_decision.json",
            ]:
                content, _, _ = c._execute(
                    f"cd {c.project_dir} && cat {run_tag}/{fname} 2>/dev/null || true",
                    timeout=15,
                )
                if content and len(content) > 5:
                    (out_dir / fname).write_text(content, encoding="utf-8")
                    print(f"Fetched: {fname}")
            print("Run dir:", run_tag)
            print("Local copy:", out_dir)
        else:
            print("No path_to_profitability run dir found.", file=sys.stderr)

        if stop_after_apply == "1":
            print("\n--- Next: full autopilot (wait 50 trades + compare) ---")
            print("On droplet, run in screen/tmux:")
            print("  cd /root/stock-bot && STOP_AFTER_APPLY=0 bash scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh")
            print("Then activate overlay (source state/paper_overlay.env or GOVERNED_TUNING_CONFIG=config/tuning/paper_overlay.json) and restart paper bot so trades accumulate under the overlay.")

    return rc


if __name__ == "__main__":
    sys.exit(main())
