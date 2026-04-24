#!/usr/bin/env python3
"""
Run direction replay 30d pipeline ON THE DROPLET with real 30d cohort.
Steps: sync repo, sanity-check logs, run load -> reconstruct -> replay,
enforce synthetic gate (fail if synthetic > 10%), fetch artifacts to local.

Usage: python scripts/replay/run_direction_replay_30d_on_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"
    end_date = "2026-03-02"
    days = 30

    with DropletClient() as c:
        # 1) Sync repo
        out, err, rc = c._execute(f"cd {proj} && git fetch --all && git reset --hard origin/main", timeout=60)
        print(out)
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Git sync failed", file=sys.stderr)
            return rc

        # 2) Sanity check required inputs
        out, err, rc = c._execute(
            f"cd {proj} && ls -lh logs/exit_attribution.jsonl logs/attribution.jsonl logs/master_trade_log.jsonl 2>/dev/null || exit 1",
            timeout=10,
        )
        if rc != 0:
            print("Sanity check failed: required log files missing", file=sys.stderr)
            print(out, file=sys.stderr)
            return 1
        print(out)
        out, err, rc = c._execute(f"cd {proj} && wc -l logs/exit_attribution.jsonl", timeout=5)
        print("Exit attribution line count:", out.strip())

        # Ensure replay scripts and deps exist (upload if missing)
        c._execute(f"mkdir -p {proj}/scripts/replay {proj}/scripts/analysis {proj}/reports/replay {proj}/reports/board")
        for local, remote in [
            (REPO / "scripts/replay/load_30d_backtest_cohort.py", f"{proj}/scripts/replay/load_30d_backtest_cohort.py"),
            (REPO / "scripts/replay/reconstruct_direction_30d.py", f"{proj}/scripts/replay/reconstruct_direction_30d.py"),
            (REPO / "scripts/replay/run_direction_replay_30d.py", f"{proj}/scripts/replay/run_direction_replay_30d.py"),
            (REPO / "scripts/replay/check_reconstruction_source.py", f"{proj}/scripts/replay/check_reconstruction_source.py"),
        ]:
            if local.exists():
                c.put_file(local, remote)
        if (REPO / "scripts/analysis/attribution_loader.py").exists():
            c.put_file(REPO / "scripts/analysis/attribution_loader.py", f"{proj}/scripts/analysis/attribution_loader.py")

        # 3) Get deployed commit for authoritative run
        commit_out, _, _ = c._execute(f"cd {proj} && git rev-parse HEAD", timeout=5)
        deployed_commit = (commit_out or "").strip() or "unknown"

        # 4) Run pipeline (fixed commands); replay step must be authoritative on droplet
        for label, cmd in [
            ("load_30d_backtest_cohort", f"cd {proj} && python3 scripts/replay/load_30d_backtest_cohort.py --base-dir . --end-date {end_date} --days {days}"),
            ("reconstruct_direction_30d", f"cd {proj} && python3 scripts/replay/reconstruct_direction_30d.py --base-dir . --end-date {end_date} --days {days}"),
            ("run_direction_replay_30d", f"cd {proj} && DROPLET_RUN=1 python3 scripts/replay/run_direction_replay_30d.py --base-dir . --end-date {end_date} --days {days} --droplet-run --deployed-commit {deployed_commit}"),
        ]:
            out, err, rc = c._execute(cmd, timeout=300)
            print(f"--- {label} ---")
            print(out)
            if err:
                print(err, file=sys.stderr)
            if rc != 0:
                print(f"{label} failed with exit code {rc}", file=sys.stderr)
                return rc

        # 4) Prove outputs generated
        out, err, rc = c._execute(
            f"cd {proj} && ls -lh reports/board/DIRECTION_REPLAY_30D_RESULTS.md reports/replay/direction_replay_30d_results.json reports/replay/direction_reconstruction_30d.jsonl 2>/dev/null || exit 1",
            timeout=5,
        )
        if rc != 0:
            print("Output files missing after pipeline", file=sys.stderr)
            return 1
        print(out)
        out, _, _ = c._execute(f"cd {proj} && tail -n 5 reports/board/DIRECTION_REPLAY_30D_RESULTS.md", timeout=5)
        print("Tail of DIRECTION_REPLAY_30D_RESULTS.md:")
        print(out)

        # 5) Synthetic gate
        out, err, rc = c._execute(f"cd {proj} && python3 scripts/replay/check_reconstruction_source.py", timeout=30)
        print("Reconstruction source check:", out)
        if err:
            print(err, file=sys.stderr)
        gate_failed = rc != 0
        if gate_failed:
            print("BLOCKED: synthetic > 10%. Replay not actionable.", file=sys.stderr)

        # 6) Fetch artifacts
        for name, remote_path, local_path in [
            ("DIRECTION_REPLAY_30D_RESULTS.md", f"{proj}/reports/board/DIRECTION_REPLAY_30D_RESULTS.md", REPO / "reports/board/DIRECTION_REPLAY_30D_RESULTS.md"),
            ("direction_replay_30d_results.json", f"{proj}/reports/replay/direction_replay_30d_results.json", REPO / "reports/replay/direction_replay_30d_results.json"),
            ("direction_reconstruction_30d.jsonl", f"{proj}/reports/replay/direction_reconstruction_30d.jsonl", REPO / "reports/replay/direction_reconstruction_30d.jsonl"),
        ]:
            try:
                content, _, _ = c._execute(f"cat {remote_path} 2>/dev/null || true", timeout=15)
                if content.strip():
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    local_path.write_text(content, encoding="utf-8")
                    print(f"Fetched {name} -> {local_path}", file=sys.stderr)
            except Exception as e:
                print(f"Could not fetch {name}: {e}", file=sys.stderr)
        if gate_failed:
            try:
                blocked_path = f"{proj}/reports/board/DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md"
                content, _, _ = c._execute(f"cat {blocked_path} 2>/dev/null || true", timeout=5)
                if content.strip():
                    (REPO / "reports/board/DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md").write_text(content, encoding="utf-8")
                    print("Fetched DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md", file=sys.stderr)
            except Exception as e:
                print(f"Could not fetch BLOCKED md: {e}", file=sys.stderr)
            return 1

    print("Direction replay 30d completed on droplet. Artifacts in reports/board/ and reports/replay/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
