#!/usr/bin/env python3
"""
Phase 0: Droplet precheck for Truth Run. Run on droplet at /root/stock-bot.
- git status clean, branch
- source .env (required for bars_loader/Alpaca)
- logs/score_snapshot.jsonl and state/blocked_trades.jsonl exist and non-empty
Writes reports/research_dataset/droplet_precheck.md. Exit 1 if any check fails.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "research_dataset"
SNAPSHOT = REPO / "logs" / "score_snapshot.jsonl"
BLOCKED = REPO / "state" / "blocked_trades.jsonl"


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def main() -> int:
    lines = ["# Droplet Precheck (Phase 0)", ""]
    failed = []

    # Git status
    code, out = run_cmd(["git", "status", "--porcelain"], REPO)
    if code != 0:
        lines.append(f"- **git status:** FAIL (exit {code})")
        failed.append("git status")
    else:
        clean = "nothing to commit" in out or out.strip() == ""
        lines.append(f"- **git status:** {'clean' if clean else 'dirty'}")
        if not clean:
            lines.append("  (proceeding; dirty allowed for dev)")
    code, out = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], REPO)
    branch = out.strip() if code == 0 else "?"
    lines.append(f"- **branch:** {branch}")
    lines.append("")

    # .env
    env_path = REPO / ".env"
    if env_path.exists():
        lines.append("- **.env:** exists (source manually before bars: `source .env`)")
    else:
        lines.append("- **.env:** MISSING — required for bars_loader/Alpaca")
        failed.append(".env")
    lines.append("")

    # Snapshot and blocked_trades
    for name, path in [("logs/score_snapshot.jsonl", SNAPSHOT), ("state/blocked_trades.jsonl", BLOCKED)]:
        if not path.exists():
            lines.append(f"- **{name}:** MISSING")
            failed.append(name)
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            n_lines = len([l for l in text.splitlines() if l.strip()])
        except Exception as e:
            lines.append(f"- **{name}:** ERROR reading ({e})")
            failed.append(name)
            continue
        if n_lines == 0:
            lines.append(f"- **{name}:** EMPTY (need non-empty)")
            failed.append(name)
        else:
            lines.append(f"- **{name}:** OK ({n_lines} lines)")

    lines.extend(["", "## Verdict", ""])
    if failed:
        lines.append(f"**STOP — FAIL.** Missing/empty: {', '.join(failed)}")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "droplet_precheck.md").write_text("\n".join(lines), encoding="utf-8")
        return 1
    lines.append("**PASS** — Proceed to Phase 1.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "droplet_precheck.md").write_text("\n".join(lines), encoding="utf-8")
    print("Precheck PASS. See reports/research_dataset/droplet_precheck.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
