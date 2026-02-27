#!/usr/bin/env python3
"""
Run CURSOR_DROPLET_CONTEXTUAL_EDGE_DISCOVERY.sh on the droplet.
Uses percent-move intelligence to constrain policy generation; simulate and aggregate.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_DROPLET_CONTEXTUAL_EDGE_DISCOVERY.sh",
    "scripts/learning/generate_contextual_policies.py",
    "scripts/learning/run_policy_simulations.py",
    "scripts/learning/aggregate_profitability_campaign.py",
]

FETCH_FILES = [
    "BOARD_REVIEW_PACKET.md",
    "CURSOR_FINAL_SUMMARY.txt",
    "candidate_policies.json",
    "entry_exit_intelligence.json",
    "aggregate_result.json",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    rc = 1

    truth = os.environ.get("TRUTH_30D_PATH", "")
    intel = os.environ.get("INTEL_PATH", "")
    iterations = os.environ.get("ITERATIONS", "400")
    min_trades = os.environ.get("MIN_TRADES", "200")

    with DropletClient() as c:
        for rel in FILES:
            local = REPO / rel
            if not local.is_file():
                print(f"Skip (missing): {rel}", file=sys.stderr)
                continue
            remote = f"{pd}/{rel}".replace("\\", "/")
            remote_dir = "/".join(remote.split("/")[:-1])
            c._execute(f"mkdir -p '{remote_dir}'", timeout=5)
            try:
                content = local.read_text(encoding="utf-8")
                content = content.replace("\r\n", "\n").replace("\r", "\n")
                if rel.endswith(".sh") or rel.endswith(".py"):
                    c._connect()
                    sftp = c.ssh_client.open_sftp()
                    sftp.putfo(io.BytesIO(content.encode("utf-8")), remote)
                    sftp.close()
                else:
                    c.put_file(local, remote)
                print(f"Uploaded: {rel}")
            except Exception as e:
                print(f"Upload failed {rel}: {e}", file=sys.stderr)

        c._execute(f"chmod +x {pd}/scripts/CURSOR_DROPLET_CONTEXTUAL_EDGE_DISCOVERY.sh 2>/dev/null", timeout=5)

        env_parts = [f"ITERATIONS={iterations}", f"MIN_TRADES={min_trades}"]
        if truth:
            env_parts.append(f"TRUTH_30D_PATH={truth}")
        if intel:
            env_parts.append(f"INTEL_PATH={intel}")
        env_str = " ".join(env_parts)

        cmd = f"cd {c.project_dir} && {env_str} bash scripts/CURSOR_DROPLET_CONTEXTUAL_EDGE_DISCOVERY.sh"
        print("\n--- Running CONTEXTUAL EDGE DISCOVERY on droplet ---")
        if truth:
            print(f"   TRUTH_30D_PATH={truth}")
        if intel:
            print(f"   INTEL_PATH={intel}")
        print(f"   ITERATIONS={iterations} MIN_TRADES={min_trades}\n")
        out, err, rc = c._execute(cmd, timeout=3600)

        print(out[-10000:] if out and len(out) > 10000 else (out or "(no stdout)"))
        if err:
            print("stderr:", err[:2000] if len(err) > 2000 else err)
        print("exit code:", rc)

        list_out, _, _ = c._execute(
            f"cd {c.project_dir} && ls -1dt reports/contextual_edge_discovery/contextual_edge_discovery_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_tag = (list_out or "").strip()
        if run_tag:
            name = Path(run_tag).name
            out_dir = REPO / "reports" / "contextual_edge_discovery" / name
            out_dir.mkdir(parents=True, exist_ok=True)
            for fname in FETCH_FILES:
                content, _, _ = c._execute(
                    f"cd {c.project_dir} && cat {run_tag}/{fname} 2>/dev/null || true",
                    timeout=15,
                )
                if content and len(content) > 10:
                    dest = out_dir / fname
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    print(f"Fetched: {fname}")
            print("Run dir:", run_tag)
            print("Local copy:", out_dir)
        else:
            print("No contextual_edge_discovery run dir found.", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
