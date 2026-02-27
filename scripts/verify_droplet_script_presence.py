#!/usr/bin/env python3
"""
Phase 1: Verify all required scripts exist on the droplet after git fetch/reset.
Run ON THE DROPLET. Writes reports/investigation/DROPLET_SCRIPT_PRESENCE.md
Exit non-zero if any required script is missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "investigation"
OUT_MD = OUT_DIR / "DROPLET_SCRIPT_PRESENCE.md"
SCRIPTS_DIR = REPO / "scripts"

# Required scripts for Signals + Entries (droplet-only, multi-model) contract
REQUIRED_SCRIPTS = [
    "verify_droplet_script_presence.py",
    "signal_inventory_on_droplet.py",
    "signal_usage_map_on_droplet.py",
    "truth_log_enablement_proof_on_droplet.py",
    "expectancy_gate_truth_report_200_on_droplet.py",
    "signal_pipeline_deep_dive_on_droplet.py",
    "signal_coverage_and_waste_report_on_droplet.py",
    "order_reconciliation_on_droplet.py",
    "full_signal_review_on_droplet.py",
    "run_closed_loops_checklist_on_droplet.py",
    "signal_score_breakdown_summary_on_droplet.py",
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    present = []
    for name in REQUIRED_SCRIPTS:
        p = SCRIPTS_DIR / name
        if p.exists():
            present.append(name)
        else:
            missing.append(name)

    # ls-style output (pathlib so it works on Windows and Linux)
    ls_lines = []
    for s in REQUIRED_SCRIPTS:
        p = SCRIPTS_DIR / s
        if p.exists():
            try:
                st = p.stat()
                ls_lines.append(f"-rw-r--r-- 1 root root {st.st_size} ... scripts/{s}")
            except Exception:
                ls_lines.append(f"scripts/{s}")
        else:
            ls_lines.append(f"(missing) scripts/{s}")

    lines = [
        "# Droplet script presence (Phase 1)",
        "",
        "Verification after `git fetch && git reset --hard origin/main`. All required scripts must exist.",
        "",
        "## Required scripts",
        "",
    ]
    for s in REQUIRED_SCRIPTS:
        status = "PRESENT" if (SCRIPTS_DIR / s).exists() else "**MISSING**"
        lines.append(f"- `scripts/{s}` — {status}")
    lines.append("")
    lines.append("## ls output (scripts)")
    lines.append("")
    lines.append("```")
    lines.extend(ls_lines)
    lines.append("```")
    lines.append("")
    lines.append("## DROPLET COMMANDS")
    lines.append("")
    lines.append("```bash")
    lines.append("cd /root/stock-bot")
    lines.append("git fetch && git reset --hard origin/main")
    lines.append("python3 scripts/verify_droplet_script_presence.py")
    lines.append("```")
    lines.append("")
    if missing:
        lines.append("**Result: FAIL** — missing: " + ", ".join(missing))
    else:
        lines.append("**Result: PASS** — all required scripts present.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    if missing:
        print("FAIL: missing scripts: " + ", ".join(missing), file=sys.stderr)
        return 1
    print("PASS: all required scripts present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
