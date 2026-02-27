#!/usr/bin/env python3
"""
Run snapshot fix proof on droplet: pull, restart paper with SCORE_SNAPSHOT_DEBUG=1, collect evidence.
Market may be closed (0 clusters); we still capture pane, wc -l, path evidence.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    out_dir = REPO / "reports" / "snapshot_fix"
    out_dir.mkdir(parents=True, exist_ok=True)
    proof_path = out_dir / "proof.md"

    with DropletClient() as c:
        # Resolve project dir (droplet may use stock-bot-current or stock-bot)
        root_cmd = "cd /root/stock-bot-current 2>/dev/null || cd /root/trading-bot-current 2>/dev/null || cd /root/stock-bot && pwd"
        out_root, _, _ = c._execute(root_cmd, timeout=10)
        project_dir = (out_root or "").strip() or "/root/stock-bot"
        c.project_dir = project_dir

        def run(cmd: str, timeout: int = 30):
            return c._execute_with_cd(cmd, timeout=timeout)

        print("1) Pull latest main...")
        out, err, rc = run("git fetch origin && git checkout main && git pull --rebase origin main", timeout=60)
        print(out or err)
        rev_out, _, _ = run("git rev-parse HEAD", timeout=5)
        commit = (rev_out or "").strip()[:12]

        print("2) Kill tmux, start paper with SCORE_SNAPSHOT_DEBUG=1...")
        kill = "tmux kill-session -t stock_bot_paper_run 2>/dev/null || true"
        start = f"tmux new-session -d -s stock_bot_paper_run 'cd {project_dir} && SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py'"
        run(f"{kill} && {start}", timeout=15)
        time.sleep(5)

        print("3) Capture pane, wc -l, head -1 (after ~90s one cycle may have run if market open)...")
        time.sleep(90)

        pane_out, _, _ = run("tmux capture-pane -pt stock_bot_paper_run -S -200 2>/dev/null || echo 'no-pane'", timeout=10)
        wc_out, _, _ = run("wc -l logs/score_snapshot.jsonl 2>/dev/null || echo '0 logs/score_snapshot.jsonl'", timeout=5)
        head_out, _, _ = run("head -1 logs/score_snapshot.jsonl 2>/dev/null || echo ''", timeout=5)
        ls_out, _, _ = run("ls -la logs/score_snapshot.jsonl 2>/dev/null || echo 'file missing'", timeout=5)

        # Optional: path from debug (if any line in pane shows path=)
        snapshot_count = "0"
        if wc_out:
            parts = wc_out.strip().split()
            if parts:
                snapshot_count = parts[0]

        lines = [
            "# Snapshot fix — proof (droplet)",
            "",
            "## Deploy",
            f"- Commit: `{commit}`",
            "",
            "## Commands run",
            "- `git pull --rebase origin main`",
            f"- `tmux new-session -d -s stock_bot_paper_run 'cd {project_dir} && SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py'`",
            "- Wait ~90s then capture pane, wc -l, head -1",
            "",
            "## tmux capture-pane (stock_bot_paper_run, last 200 lines)",
            "```",
            (pane_out or "no output").strip(),
            "```",
            "",
            "## logs/score_snapshot.jsonl",
            "```",
            f"# wc -l",
            (wc_out or "0").strip(),
            "",
            "# ls -la",
            (ls_out or "").strip(),
            "",
            "# head -1",
            (head_out or "").strip()[:500],
            "```",
            "",
            "## Result",
            f"- snapshot_count: **{snapshot_count}**",
            "- composite_score in first record: (see head -1 above)",
            "- Hook + write success logs: (see capture-pane for SCORE_SNAPSHOT_DEBUG lines)",
            "- **PASS** if snapshot_count > 0 and composite_score present; **PENDING** if market closed (0 clusters).",
        ]
        proof_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Proof written to {proof_path}")
        # Avoid UnicodeEncodeError on Windows console (pane may contain emoji)
        excerpt = "\n".join(lines[-25:]).encode("ascii", errors="replace").decode("ascii")
        print("\n--- Proof (excerpt) ---")
        print(excerpt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
