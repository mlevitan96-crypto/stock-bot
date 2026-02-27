#!/usr/bin/env python3
"""
Phase 2: Prove EXPECTANCY_GATE_TRUTH_LOG=1 and SIGNAL_SCORE_BREAKDOWN_LOG=1 are active.
Run ON THE DROPLET. Writes reports/investigation/TRUTH_LOG_ENABLEMENT_PROOF.md.
Includes: systemctl show env, /proc/<pid>/environ check, line counts, file paths.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "investigation"
OUT_MD = OUT_DIR / "TRUTH_LOG_ENABLEMENT_PROOF.md"
GATE_TRUTH_JSONL = REPO / "logs" / "expectancy_gate_truth.jsonl"
BREAKDOWN_JSONL = REPO / "logs" / "signal_score_breakdown.jsonl"

REQUIRED_GATE_LINES = 200
REQUIRED_BREAKDOWN_CANDIDATES = 100


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Current process env (when this script runs, we document what we have)
    env_exp = os.environ.get("EXPECTANCY_GATE_TRUTH_LOG")
    env_break = os.environ.get("SIGNAL_SCORE_BREAKDOWN_LOG")

    # Try to get stock-bot service env (Linux/droplet)
    systemctl_env = ""
    try:
        r = subprocess.run(
            ["systemctl", "show", "stock-bot", "--property=Environment"],
            cwd=str(REPO), capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout:
            systemctl_env = r.stdout.strip()
    except Exception as e:
        systemctl_env = f"(systemctl not available or error: {e})"

    # MainPID for /proc check
    main_pid = ""
    try:
        r = subprocess.run(
            ["systemctl", "show", "stock-bot", "--property=MainPID"],
            cwd=str(REPO), capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout:
            main_pid = r.stdout.strip().replace("MainPID=", "").strip()
    except Exception:
        pass

    proc_environ_note = ""
    if main_pid and main_pid != "0":
        proc_path = Path(f"/proc/{main_pid}/environ")
        if proc_path.exists():
            try:
                raw = proc_path.read_bytes()
                env_str = raw.decode("utf-8", errors="replace").replace("\x00", "\n")
                has_exp = "EXPECTANCY_GATE_TRUTH_LOG=1" in env_str
                has_break = "SIGNAL_SCORE_BREAKDOWN_LOG=1" in env_str
                proc_environ_note = f"Read /proc/{main_pid}/environ: EXPECTANCY_GATE_TRUTH_LOG=1 present={has_exp}, SIGNAL_SCORE_BREAKDOWN_LOG=1 present={has_break}."
            except Exception as e:
                proc_environ_note = f"Could not read /proc/{main_pid}/environ: {e}"
        else:
            proc_environ_note = f"/proc/{main_pid}/environ not found (service may not be running)."
    else:
        proc_environ_note = "MainPID not available (service not running or not systemd)."

    gate_lines = 0
    if GATE_TRUTH_JSONL.exists():
        gate_lines = sum(1 for line in GATE_TRUTH_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines() if line.strip())
    breakdown_lines = 0
    if BREAKDOWN_JSONL.exists():
        breakdown_lines = sum(1 for line in BREAKDOWN_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines() if line.strip())
    # Breakdown: each line = one candidate
    breakdown_candidates = breakdown_lines

    lines = [
        "# Truth log enablement proof (Phase 2)",
        "",
        "## Force runtime signal truth (systemd, NOT shell)",
        "",
        "Env vars MUST be set in the **stock-bot SERVICE** (systemd override or unit env file), not in a shell. Then restart the service. Then prove they are active.",
        "",
        "## Required env vars (for stock-bot service)",
        "",
        "- `EXPECTANCY_GATE_TRUTH_LOG=1`",
        "- `SIGNAL_SCORE_BREAKDOWN_LOG=1`",
        "",
        "## Proof (run on droplet)",
        "",
        "### 1) systemctl show stock-bot --property=Environment",
        "```bash",
        "systemctl show stock-bot --property=Environment",
        "```",
        "",
        "**Result:** Environment must contain EXPECTANCY_GATE_TRUTH_LOG=1 and SIGNAL_SCORE_BREAKDOWN_LOG=1.",
        "",
        f"**Captured:** {systemctl_env[:500] + '...' if len(systemctl_env) > 500 else systemctl_env or '(not captured; run command above on droplet)'}",
        "",
        "### 2) /proc/<MainPID>/environ (grep both vars)",
        "```bash",
        "systemctl show stock-bot --property=MainPID",
        "PID=$(systemctl show stock-bot --property=MainPID --value)",
        "cat /proc/$PID/environ | tr '\\0' '\\n' | grep -E 'EXPECTANCY_GATE_TRUTH_LOG|SIGNAL_SCORE_BREAKDOWN_LOG'",
        "```",
        "",
        f"**Note:** {proc_environ_note}",
        "",
        "### 3) Log file paths and counts",
        "",
        f"- **logs/expectancy_gate_truth.jsonl:** `{GATE_TRUTH_JSONL}` — **{gate_lines} lines** (required >= {REQUIRED_GATE_LINES})",
        f"- **logs/signal_score_breakdown.jsonl:** `{BREAKDOWN_JSONL}` — **{breakdown_candidates} candidates** (required >= {REQUIRED_BREAKDOWN_CANDIDATES})",
        "",
        "## DROPLET COMMANDS (systemd override + restart)",
        "",
        "```bash",
        "cd /root/stock-bot",
        "# Option A: systemd override (recommended)",
        "sudo mkdir -p /etc/systemd/system/stock-bot.service.d",
        "echo '[Service]' | sudo tee /etc/systemd/system/stock-bot.service.d/env.conf",
        "echo 'Environment=\"EXPECTANCY_GATE_TRUTH_LOG=1\"' | sudo tee -a /etc/systemd/system/stock-bot.service.d/env.conf",
        "echo 'Environment=\"SIGNAL_SCORE_BREAKDOWN_LOG=1\"' | sudo tee -a /etc/systemd/system/stock-bot.service.d/env.conf",
        "sudo systemctl daemon-reload",
        "sudo systemctl restart stock-bot",
        "# Prove",
        "systemctl show stock-bot --property=Environment",
        "PID=$(systemctl show stock-bot --property=MainPID --value); cat /proc/$PID/environ | tr '\\0' '\\n' | grep -E 'EXPECTANCY_GATE_TRUTH_LOG|SIGNAL_SCORE_BREAKDOWN_LOG'",
        "python3 scripts/truth_log_enablement_proof_on_droplet.py",
        "```",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD} (gate lines={gate_lines}, breakdown candidates={breakdown_candidates})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
