#!/usr/bin/env python3
"""
Run UW missing-input penalty experiment on droplet: set UW_MISSING_INPUT_MODE=penalize,
run one evaluation cycle (or print instructions for one-day run), then fetch reports and
produce experiment_summary.md. Run from repo root (local).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    with DropletClient() as c:
        root_cmd = "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot"
        root_out, _, _ = c._execute(root_cmd, timeout=10)
        root = (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()
        cd = f"cd {root}"

        # Upload changed files
        sftp = c._connect().open_sftp()
        try:
            for local, remote in [
                (REPO / "board" / "eod" / "live_entry_adjustments.py", f"{root}/board/eod/live_entry_adjustments.py"),
                (REPO / "scripts" / "uw_experiment_summary.py", f"{root}/scripts/uw_experiment_summary.py"),
            ]:
                if local.exists():
                    sftp.put(str(local), remote)
                    print(f"Uploaded {local.relative_to(REPO)}")
        finally:
            sftp.close()

        # Ensure main.py has ts passed to apply_uw_to_score (upload if we have it)
        main_py = REPO / "main.py"
        if main_py.exists():
            sftp = c._connect().open_sftp()
            try:
                sftp.put(str(main_py), f"{root}/main.py")
                print("Uploaded main.py")
            finally:
                sftp.close()

        # Create experiment dir on droplet
        c._execute(f"{cd} && mkdir -p reports/uw_experiment", timeout=5)

        # Run one evaluation cycle with UW_MISSING_INPUT_MODE=penalize
        # (Full one-day: run with systemd override or: UW_MISSING_INPUT_MODE=penalize python3 main.py ... for session)
        cmd = f"{cd} && UW_MISSING_INPUT_MODE=penalize python3 -c \"
from board.eod.live_entry_adjustments import UW_MISSING_INPUT_MODE, apply_uw_to_score
print('UW_MISSING_INPUT_MODE=', UW_MISSING_INPUT_MODE)
# Quick smoke: call apply_uw with no uw data (missing) to see penalize path
s, d = apply_uw_to_score('__TEST__', 3.5, ts=0)
print('Test apply_uw (missing): score_after=', s, 'details keys=', list(d.keys()))
\" 2>&1"
        out, err, rc = c._execute(cmd, timeout=30)
        print(out or "")
        if err:
            print(err, file=sys.stderr)

        # Run experiment summary (from penalty events so far)
        c._execute(f"{cd} && python3 scripts/uw_experiment_summary.py 2>&1", timeout=30)
        summary_out, _, _ = c._execute(f"cat {root}/reports/uw_experiment/experiment_summary.md 2>/dev/null || true", timeout=10)
        if summary_out:
            (REPO / "reports" / "uw_experiment" / "experiment_summary.md").parent.mkdir(parents=True, exist_ok=True)
            (REPO / "reports" / "uw_experiment" / "experiment_summary.md").write_text(summary_out, encoding="utf-8")
            print("Fetched experiment_summary.md")
        events_content, _, _ = c._execute(f"cat {root}/reports/uw_experiment/uw_penalty_events.jsonl 2>/dev/null || true", timeout=10)
        if events_content:
            (REPO / "reports" / "uw_experiment" / "uw_penalty_events.jsonl").parent.mkdir(parents=True, exist_ok=True)
            (REPO / "reports" / "uw_experiment" / "uw_penalty_events.jsonl").write_text(events_content, encoding="utf-8")
            print("Fetched uw_penalty_events.jsonl")

    print("")
    print("For a full one-day paper run on droplet, run the main loop with:")
    print("  export UW_MISSING_INPUT_MODE=penalize")
    print("  export UW_MISSING_INPUT_PENALTY=0.75")
    print("  # then start your paper trading process (e.g. systemd service or python main.py)")
    print("After the run, on droplet: python3 scripts/uw_experiment_summary.py")
    print("Then fetch reports/uw_experiment/experiment_summary.md and uw_penalty_events.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
