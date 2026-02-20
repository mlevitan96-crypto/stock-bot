#!/usr/bin/env python3
"""
Phase 1: Verify required scripts exist on droplet after git pull.
Run ON THE DROPLET. Writes reports/investigation/DROPLET_SCRIPT_PRESENCE.md
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "investigation"
OUT_MD = OUT_DIR / "DROPLET_SCRIPT_PRESENCE.md"

REQUIRED = [
    "scripts/investigation_baseline_snapshot_on_droplet.py",
    "scripts/run_closed_loops_checklist_on_droplet.py",
    "scripts/expectancy_gate_truth_report_200_on_droplet.py",
    "scripts/signal_score_breakdown_summary_on_droplet.py",
    "scripts/full_signal_review_on_droplet.py",
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    present = []
    missing = []
    for rel in REQUIRED:
        p = REPO / rel
        if p.exists():
            present.append(rel)
        else:
            missing.append(rel)

    # ls output for scripts
    try:
        ls_out = subprocess.run(
            ["ls", "-la"] + [str(REPO / "scripts" / "investigation_baseline_snapshot_on_droplet.py"),
                            str(REPO / "scripts" / "run_closed_loops_checklist_on_droplet.py"),
                            str(REPO / "scripts" / "expectancy_gate_truth_report_200_on_droplet.py"),
                            str(REPO / "scripts" / "signal_score_breakdown_summary_on_droplet.py"),
                            str(REPO / "scripts" / "full_signal_review_on_droplet.py")],
            cwd=str(REPO), capture_output=True, text=True, timeout=5,
        )
        ls_text = (ls_out.stdout or "") + (ls_out.stderr or "")
    except Exception as e:
        ls_text = str(e)

    lines = [
        "# Droplet script presence (Phase 1)",
        "",
        "Required scripts after `git pull origin main`:",
        "",
        "| Script | Present |",
        "|--------|---------|",
    ]
    for rel in REQUIRED:
        lines.append(f"| {rel} | {'YES' if rel in present else 'NO'} |")
    lines.extend([
        "",
        "## ls output (key scripts)",
        "",
        "```",
        ls_text.strip() or "N/A",
        "```",
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot   # or /root/stock-bot-current",
        "git fetch origin && git pull origin main",
        "python3 scripts/verify_droplet_script_presence.py",
        "```",
        "",
        "If any script is missing: commit and push from local, then re-run git pull on droplet.",
        "",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}; present={len(present)}, missing={len(missing)}")
    if missing:
        print("Missing:", missing, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
