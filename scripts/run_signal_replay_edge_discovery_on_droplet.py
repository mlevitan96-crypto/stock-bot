#!/usr/bin/env python3
"""Run CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh on droplet. Uses real truth from latest massive_profit_reviews run."""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = [
    "scripts/CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh",
    "scripts/analysis/label_large_moves.py",
    "scripts/analysis/replay_entry_signals.py",
    "scripts/learning/generate_candidate_policies.py",
    "scripts/learning/run_policy_simulations.py",
    "scripts/learning/aggregate_profitability_campaign.py",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    rc = 1

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
                if rel.endswith(".sh"):
                    content = content.replace("\r\n", "\n").replace("\r", "\n")
                    c._connect()
                    sftp = c.ssh_client.open_sftp()
                    sftp.putfo(io.BytesIO(content.encode("utf-8")), remote)
                    sftp.close()
                else:
                    c.put_file(local, remote)
                print(f"Uploaded: {rel}")
            except Exception as e:
                print(f"Upload failed {rel}: {e}", file=sys.stderr)

        c._execute(f"chmod +x {pd}/scripts/CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh 2>/dev/null", timeout=5)

        cmd = (
            f"cd {c.project_dir} && "
            "ITERATIONS=96 PARALLELISM=8 bash scripts/CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh"
        )
        print("\n--- Running MASSIVE SIGNAL REPLAY + EDGE DISCOVERY on droplet (96 iters, 8 parallel) ---\n")
        out, err, rc = c._execute(cmd, timeout=900)

        print(out[-8000:] if out and len(out) > 8000 else (out or "(no stdout)"))
        if err:
            print("stderr:", err[:1500] if len(err) > 1500 else err)
        print("exit code:", rc)

        list_out, _, _ = c._execute(
            f"cd {c.project_dir} && ls -td reports/edge_discovery/signal_replay_edge_discovery_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_tag = (list_out or "").strip()
        if run_tag:
            name = Path(run_tag).name
            out_dir = REPO / "reports" / "edge_discovery" / name
            out_dir.mkdir(parents=True, exist_ok=True)
            for fname in ["CURSOR_FINAL_SUMMARY.txt", "aggregate_result.json", "labeled_moves.json", "signal_leading_stats.json", "candidate_policies.json"]:
                content, _, _ = c._execute(f"cd {c.project_dir} && cat {run_tag}/{fname} 2>/dev/null || true", timeout=15)
                if content and len(content) > 20:
                    (out_dir / fname).write_text(content, encoding="utf-8")
                    print(f"Fetched: {fname}")
            print("Run dir:", run_tag)

    return rc


if __name__ == "__main__":
    sys.exit(main())
