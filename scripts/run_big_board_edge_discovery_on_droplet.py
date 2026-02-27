#!/usr/bin/env python3
"""
Run CURSOR_DROPLET_BIG_BOARD_EDGE_DISCOVERY.sh on the droplet with real data.

- Pushes the big-board script, edge discovery script, multi_model_runner, and learning/analysis deps.
- Runs edge discovery + MIN_TRADES re-aggregate + multi-model adversarial review.
- Fetches the report: BOARD_REVIEW_PACKET.md, board_review/*, CURSOR_FINAL_SUMMARY.txt, key artifacts.

Usage:
  python scripts/run_big_board_edge_discovery_on_droplet.py
  TRUTH=reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json python scripts/run_big_board_edge_discovery_on_droplet.py  # optional override

Override via env: TRUTH, ITERATIONS, PARALLELISM, MIN_TRADES (passed to the shell script).
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Scripts and deps that must be on the droplet for the run to work
FILES = [
    "scripts/CURSOR_DROPLET_BIG_BOARD_EDGE_DISCOVERY.sh",
    "scripts/CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh",
    "scripts/multi_model_runner.py",
    "scripts/analysis/label_large_moves.py",
    "scripts/analysis/replay_entry_signals.py",
    "scripts/learning/generate_candidate_policies.py",
    "scripts/learning/run_policy_simulations.py",
    "scripts/learning/aggregate_profitability_campaign.py",
]

# Artifacts to fetch from the latest big_board_edge_discovery run
FETCH_FILES = [
    "BOARD_REVIEW_PACKET.md",
    "CURSOR_FINAL_SUMMARY.txt",
    "artifacts/aggregate_result.json",
    "artifacts/labeled_moves.json",
    "artifacts/signal_leading_stats.json",
    "artifacts/candidate_policies.json",
    "board_review/prosecutor_output.md",
    "board_review/defender_output.md",
    "board_review/sre_output.md",
    "board_review/board_verdict.md",
    "board_review/board_verdict.json",
    "board_review/stdout.txt",
    "board_review/stderr.txt",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    pd = "/root/stock-bot"
    rc = 1

    truth = os.environ.get("TRUTH", "")
    iterations = os.environ.get("ITERATIONS", "600")
    parallelism = os.environ.get("PARALLELISM", "10")
    min_trades = os.environ.get("MIN_TRADES", "300")

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

        for script in ["CURSOR_DROPLET_BIG_BOARD_EDGE_DISCOVERY.sh", "CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh"]:
            c._execute(f"chmod +x {pd}/scripts/{script} 2>/dev/null", timeout=5)

        env_parts = [
            f"ITERATIONS={iterations}",
            f"PARALLELISM={parallelism}",
            f"MIN_TRADES={min_trades}",
        ]
        if truth:
            env_parts.append(f"TRUTH={truth}")
        env_str = " ".join(env_parts)

        cmd = (
            f"cd {c.project_dir} && "
            f"{env_str} bash scripts/CURSOR_DROPLET_BIG_BOARD_EDGE_DISCOVERY.sh"
        )
        print("\n--- Running BIG BOARD EDGE DISCOVERY on droplet (multi-model adversarial) ---")
        print(f"   ITERATIONS={iterations} PARALLELISM={parallelism} MIN_TRADES={min_trades}")
        if truth:
            print(f"   TRUTH={truth}")
        print("   (long run: edge discovery + re-aggregate + prosecutor/defender/sre/board)\n")
        out, err, rc = c._execute(cmd, timeout=7200)

        print(out[-10000:] if out and len(out) > 10000 else (out or "(no stdout)"))
        if err:
            print("stderr:", err[:2000] if len(err) > 2000 else err)
        print("exit code:", rc)

        list_out, _, _ = c._execute(
            f"cd {c.project_dir} && ls -1dt reports/big_board_edge_discovery/big_board_edge_discovery_* 2>/dev/null | head -1",
            timeout=10,
        )
        run_tag = (list_out or "").strip()
        if run_tag:
            name = Path(run_tag).name
            out_dir = REPO / "reports" / "big_board_edge_discovery" / name
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
            print("No big_board_edge_discovery run dir found; check droplet log.", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
