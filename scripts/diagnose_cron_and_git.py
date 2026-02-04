#!/usr/bin/env python3
"""
Stock-bot — Full Cron + Git + Execution Diagnostic & Repair (Path-Agnostic).

Auto-detects repo path, diagnoses cron, verifies scripts, reports, git push,
repairs issues, rewrites cron if needed, updates Memory Bank, generates report.

Usage:
    # On droplet (or Linux with stock-bot at /root/stock-bot or /root/stock-bot-current):
    python3 scripts/diagnose_cron_and_git.py

    # Local mode (Windows): use current repo, skip cron install
    python scripts/diagnose_cron_and_git.py --local

    # Remote mode: run full diagnostic on droplet via SSH
    python scripts/diagnose_cron_and_git.py --remote

    # Dry-run: detect path and report only, no repairs
    python scripts/diagnose_cron_and_git.py --dry-run

Exit: 0 success, 1 failure
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# -----------------------------------------------------------------------------
# Phase 1 — Auto-detect stock-bot path
# -----------------------------------------------------------------------------

CANDIDATE_ROOTS = ["/root/stock-bot-current", "/root/stock-bot"]
REQUIRED_DIRS = ["scripts", "config"]
OPTIONAL_VENV = "venv"
REQUIRED_SCRIPTS = [
    "board/eod/run_stock_quant_officer_eod.py",
]
OPTIONAL_SCRIPTS = [
    "scripts/run_stock_bot_workflow.py",
    "scripts/run_wheel_strategy.py",
]


def _is_valid_stockbot_root(root: Path) -> bool:
    """Check if path contains valid stock-bot repo structure."""
    if not root.is_dir():
        return False
    for d in REQUIRED_DIRS:
        if not (root / d).is_dir():
            return False
    # venv optional but preferred
    if not (root / OPTIONAL_VENV).exists():
        pass  # still valid, might use system python
    # At least one required script
    found = False
    for rel in REQUIRED_SCRIPTS:
        if (root / rel).exists():
            found = True
            break
    if not found:
        return False
    return True


def detect_stockbot_root() -> Optional[Path]:
    """
    Detect stock-bot root in order: stock-bot-current, stock-bot, script's repo.
    Returns first valid path, or None.
    """
    # 1. Standard droplet paths
    for p in CANDIDATE_ROOTS:
        root = Path(p)
        if _is_valid_stockbot_root(root):
            return root.resolve()

    # 2. Script's repo (e.g. c:\Dev\stock-bot or /root/stock-bot/...)
    script = Path(__file__).resolve()
    maybe_root = script.parents[1]  # parent of scripts/
    if _is_valid_stockbot_root(maybe_root):
        return maybe_root.resolve()

    return None


# -----------------------------------------------------------------------------
# Phase 2 — Discover cron state
# -----------------------------------------------------------------------------

def get_crontab() -> tuple[str, str, int]:
    """Return (stdout, stderr, exit_code) of crontab -l."""
    try:
        r = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (r.stdout or "", r.stderr or "", r.returncode)
    except FileNotFoundError:
        return ("", "crontab not found (Windows?)", 1)
    except Exception as e:
        return ("", str(e), 1)


def get_syslog_cron(tail_n: int = 200) -> tuple[str, str, int]:
    """Return last N lines of syslog mentioning CRON. Linux only."""
    try:
        r = subprocess.run(
            ["sh", "-c", f"grep CRON /var/log/syslog 2>/dev/null | tail -{tail_n}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (r.stdout or "", r.stderr or "", r.returncode)
    except Exception:
        return ("", "syslog not available", 1)


# -----------------------------------------------------------------------------
# Phase 3 — Verify script paths
# -----------------------------------------------------------------------------

def check_script(root: Path, rel: str) -> tuple[bool, str]:
    """Check script exists and is executable. Return (ok, msg)."""
    p = root / rel
    if not p.exists():
        return False, f"missing: {rel}"
    if not p.is_file():
        return False, f"not a file: {rel}"
    # On Unix, check +x
    if platform.system() != "Windows":
        import stat
        mode = p.stat().st_mode
        if not (mode & stat.S_IXUSR):
            return False, f"not executable (chmod +x {rel})"
    return True, f"ok: {rel}"


def get_venv_python(root: Path) -> Optional[Path]:
    """Return venv python path if venv exists."""
    venv_py = root / "venv" / "bin" / "python3"
    if venv_py.exists():
        return venv_py
    venv_py_win = root / "venv" / "Scripts" / "python.exe"
    if venv_py_win.exists():
        return venv_py_win
    return None


# -----------------------------------------------------------------------------
# Phase 4 — Verify report generation
# -----------------------------------------------------------------------------

def run_eod_dry_run(root: Path, venv_python: Optional[Path], python_fallback: str) -> tuple[int, str, str]:
    """Run EOD with --dry-run. Return (exit_code, stdout, stderr)."""
    py = str(venv_python) if venv_python else python_fallback
    script = root / "board" / "eod" / "run_stock_quant_officer_eod.py"
    if not script.exists():
        return 1, "", f"Script not found: {script}"
    env = os.environ.copy()
    env["CLAWDBOT_SESSION_ID"] = "diagnostic_dry_run"
    try:
        r = subprocess.run(
            [py, str(script), "--dry-run"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        return (r.returncode, r.stdout or "", r.stderr or "")
    except subprocess.TimeoutExpired:
        return 1, "", "Timeout (60s)"
    except Exception as e:
        return 1, "", str(e)


# -----------------------------------------------------------------------------
# Phase 5 — Git state
# -----------------------------------------------------------------------------

def git_status(root: Path) -> tuple[str, str, int]:
    """Run git status in root."""
    try:
        r = subprocess.run(
            ["git", "status"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (r.stdout or "", r.stderr or "", r.returncode)
    except Exception as e:
        return ("", str(e), 1)


def git_branch(root: Path) -> tuple[str, str, int]:
    """Run git branch --show-current."""
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        return (r.stdout or "", r.stderr or "", r.returncode)
    except Exception as e:
        return ("", str(e), 1)


def git_remote(root: Path) -> tuple[str, str, int]:
    """Run git remote -v."""
    try:
        r = subprocess.run(
            ["git", "remote", "-v"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        return (r.stdout or "", r.stderr or "", r.returncode)
    except Exception as e:
        return ("", str(e), 1)


# -----------------------------------------------------------------------------
# Phase 6 — GitHub push under cron simulation
# -----------------------------------------------------------------------------

def simulate_cron_push(root: Path, dry_run: bool = False) -> tuple[int, str, str]:
    """
    Simulate cron env: cd to root, git add, commit, push.
    If dry_run, only run git status.
    """
    if dry_run:
        return git_status(root)

    try:
        # Add, commit (allow empty), push
        cmds = [
            "git add .",
            "git commit -m 'Stock-bot cron push test' || true",
            "git push origin main",
        ]
        full = " && ".join(cmds)
        r = subprocess.run(
            ["sh", "-c", f"cd {root!s} && {full}"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return (r.returncode, r.stdout or "", r.stderr or "")
    except Exception as e:
        return (1, "", str(e))


# -----------------------------------------------------------------------------
# Phase 7 — Rewrite cron
# -----------------------------------------------------------------------------

def build_cron_lines(root: Path, venv_python: Optional[Path], use_venv: bool) -> list[str]:
    """
    Build stock-bot cron lines. Uses venv python if available and use_venv.
    Escaped % for cron: date +\\%Y-\\%m-\\%d
    """
    py = str(root / "venv" / "bin" / "python3") if (use_venv and venv_python) else "/usr/bin/python3"
    root_s = str(root)
    logs_dir = Path(root) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # EOD: 21:30 UTC weekdays (Memory Bank §5.5)
    eod_log = root / "logs" / "cron_eod.log"
    eod = (
        f"30 21 * * 1-5 cd {root_s} && "
        f"CLAWDBOT_SESSION_ID=\"stock_quant_eod_$(date -u +\\%Y-\\%m-\\%d)\" "
        f"{py} board/eod/run_stock_quant_officer_eod.py >> {eod_log} 2>&1"
    )

    # Audit + sync after EOD 21:32 UTC (runs audit, writes to reports/droplet_audit/YYYY-MM-DD/, then pushes to GitHub)
    audit_sync_sh = root / "scripts" / "run_droplet_audit_and_sync.sh"
    sync_sh = root / "scripts" / "droplet_sync_to_github.sh"
    lines = [eod]
    if audit_sync_sh.exists():
        sync_log = root / "logs" / "cron_sync.log"
        sync = f"32 21 * * 1-5 cd {root_s} && bash scripts/run_droplet_audit_and_sync.sh >> {sync_log} 2>&1"
        lines.append(sync)
    elif sync_sh.exists():
        sync_log = root / "logs" / "cron_sync.log"
        sync = f"32 21 * * 1-5 cd {root_s} && bash scripts/droplet_sync_to_github.sh >> {sync_log} 2>&1"
        lines.append(sync)

    return lines


def install_crontab(lines: list[str], existing: str) -> tuple[bool, str]:
    """
    Merge new stock-bot lines with existing crontab. Remove old stock-bot entries
    (run_stock_quant_officer_eod, droplet_sync_to_github), add new.
    """
    kept = []
    for ln in existing.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            kept.append(ln)
            continue
        if "run_stock_quant_officer_eod" in ln or "droplet_sync_to_github" in ln or "run_droplet_audit_and_sync" in ln:
            continue
        kept.append(ln)

    new_crontab = "\n".join(kept + [""] + ["# stock-bot (diagnose_cron_and_git)"] + lines) + "\n"
    try:
        r = subprocess.run(
            ["crontab", "-"],
            input=new_crontab,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            return False, r.stderr or "crontab install failed"
        return True, "crontab installed"
    except FileNotFoundError:
        return False, "crontab not found"
    except Exception as e:
        return False, str(e)


# -----------------------------------------------------------------------------
# Phase 8 — Memory Bank update
# -----------------------------------------------------------------------------

def update_memory_bank(root: Path, data: dict) -> tuple[bool, str]:
    """Append/update a diagnostic section in MEMORY_BANK.md."""
    mb = root / "MEMORY_BANK.md"
    if not mb.exists():
        return False, "MEMORY_BANK.md not found"

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    section = f"""
---
## CRON + GIT DIAGNOSTIC ({ts})
- **Detected path:** {data.get("root", "?")}
- **Cron:** {data.get("cron_status", "?")}
- **Git push:** {data.get("git_push_status", "?")}
- **Report generation:** {data.get("report_status", "?")}
- **Repairs applied:** {data.get("repairs", "none")}
---
"""
    try:
        content = mb.read_text(encoding="utf-8")
        # Remove any previous diagnostic section (between --- and ---)
        pattern = r"\n---\n## CRON \+ GIT DIAGNOSTIC.*?---\n"
        content = re.sub(pattern, "", content, flags=re.DOTALL)
        content = content.rstrip() + section + "\n"
        mb.write_text(content, encoding="utf-8")
        return True, "Memory Bank updated"
    except Exception as e:
        return False, str(e)


# -----------------------------------------------------------------------------
# Phase 9 — Diagnostic report
# -----------------------------------------------------------------------------

def write_diagnostic_report(root: Path, report_path: Path, data: dict) -> None:
    """Write STOCKBOT_CRON_AND_GIT_DIAGNOSTIC_<DATE>.md"""
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fname = report_path / f"STOCKBOT_CRON_AND_GIT_DIAGNOSTIC_{date}.md"
    lines = [
        "# Stock-bot Cron + Git + Execution Diagnostic Report",
        "",
        f"**Date:** {date}",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Detected Path",
        f"- `{data.get('root', 'N/A')}`",
        "",
        "## 2. Cron State",
        "```",
        data.get("crontab_out", "(none)"),
        "```",
        "",
        "## 3. Script Verification",
    ]
    for k, v in data.get("scripts", {}).items():
        lines.append(f"- {k}: {v}")
    lines.extend([
        "",
        "## 4. Report Generation (EOD --dry-run)",
        f"- Exit code: {data.get('eod_exit', '?')}",
        f"- Stdout: (see below)",
        "",
        "```",
        data.get("eod_stdout", ""),
        "```",
        "",
        "## 5. Git State",
        f"- Branch: {data.get('git_branch', '?')}",
        "",
        "```",
        data.get("git_status_out", ""),
        "```",
        "",
        "## 6. Fixes Applied",
        "\n".join(str(r) for r in (data.get("repairs") or [])) or "None",
        "",
        "## 7. Next Steps",
        data.get("next_steps", "- Verify cron fires at scheduled times\n- Monitor logs/ directory"),
        "",
    ])
    fname.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------------------------------------------------------
# Main orchestrator
# -----------------------------------------------------------------------------

def run_remote() -> int:
    """Execute full diagnostic on droplet via DropletClient."""
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("Error: droplet_client not found. Run from repo root.", file=sys.stderr)
        return 1

    with DropletClient() as c:
        script_path = Path(__file__).resolve()
        # Push script first if needed
        remote_script = f"{c.project_dir}/scripts/diagnose_cron_and_git.py"
        cmd = f"cd {c.project_dir} && python3 scripts/diagnose_cron_and_git.py"
        out, err, rc = c._execute(cmd, timeout=120)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Stock-bot cron + git diagnostic and repair")
    ap.add_argument("--local", action="store_true", help="Local mode (Windows); skip cron install")
    ap.add_argument("--remote", action="store_true", help="Run on droplet via SSH")
    ap.add_argument("--dry-run", action="store_true", help="Detect and report only, no repairs")
    args = ap.parse_args()

    if args.remote:
        return run_remote()

    on_windows = platform.system() == "Windows"
    local_mode = args.local or on_windows

    # Phase 1
    root = detect_stockbot_root()
    if not root:
        print("FAIL: No valid stock-bot root found. Checked:", CANDIDATE_ROOTS, file=sys.stderr)
        return 1

    print(f"DETECTED_STOCKBOT_ROOT={root}")

    data = {
        "root": str(root),
        "crontab_out": "",
        "scripts": {},
        "eod_exit": -1,
        "eod_stdout": "",
        "git_branch": "",
        "git_status_out": "",
        "repairs": [],
        "cron_status": "unknown",
        "git_push_status": "unknown",
        "report_status": "unknown",
    }

    # Phase 2
    crontab_out, crontab_err, crontab_rc = get_crontab()
    data["crontab_out"] = crontab_out or crontab_err
    if crontab_rc == 0:
        data["cron_status"] = "crontab readable"
        if "run_stock_quant_officer_eod" in crontab_out:
            if str(root) in crontab_out:
                data["cron_status"] = "crontab has EOD entry with correct path"
            else:
                data["repairs"].append("Cron path may be wrong (root mismatch)")
        else:
            data["repairs"].append("Cron missing EOD entry")
    else:
        data["cron_status"] = f"crontab unreadable: {crontab_err}"

    # Phase 3
    venv_py = get_venv_python(root)
    for rel in REQUIRED_SCRIPTS + OPTIONAL_SCRIPTS:
        ok, msg = check_script(root, rel)
        data["scripts"][rel] = msg

    python_fallback = "/usr/bin/python3" if not on_windows else sys.executable

    # Phase 4
    eod_rc, eod_stdout, eod_stderr = run_eod_dry_run(root, venv_py, python_fallback)
    data["eod_exit"] = eod_rc
    data["eod_stdout"] = (eod_stdout or "") + (eod_stderr or "")
    if eod_rc == 0:
        data["report_status"] = "EOD dry-run OK"
    else:
        data["report_status"] = f"EOD dry-run failed (exit {eod_rc})"
        data["repairs"].append("Fix EOD script (check imports, paths)")

    # Phase 5
    gs_out, _, _ = git_status(root)
    gb_out, _, _ = git_branch(root)
    data["git_status_out"] = gs_out
    data["git_branch"] = gb_out.strip()

    # Phase 6
    if not local_mode and not args.dry_run:
        push_rc, _, push_err = simulate_cron_push(root, dry_run=False)
        if push_rc == 0:
            data["git_push_status"] = "push OK"
        else:
            data["git_push_status"] = f"push failed: {push_err[:200]}"
            data["repairs"].append("Fix SSH/key for root; check known_hosts, remote URL")
    else:
        data["git_push_status"] = "skipped (local/dry-run)"

    # Phase 7
    has_crontab = shutil.which("crontab") is not None
    if not local_mode and not args.dry_run and has_crontab and str(root).startswith("/"):
        cron_lines = build_cron_lines(root, venv_py, use_venv=(venv_py is not None))
        if "Cron missing EOD entry" in data["repairs"] or "Cron path may be wrong" in str(data["repairs"]):
            ok, msg = install_crontab(cron_lines, crontab_out)
            if ok:
                data["repairs"].append("Cron rewritten and installed")
                data["cron_status"] = "cron repaired"
            else:
                data["repairs"].append(f"Cron install failed: {msg}")

    # Phase 8
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_diagnostic_report(root, reports_dir, data)

    if not args.dry_run:
        mb_ok, mb_msg = update_memory_bank(root, data)
        if mb_ok:
            data["repairs"].append("Memory Bank updated")

    # Phase 10 (commit/push) — only if not dry-run and we're on the detected repo
    if not args.dry_run and not local_mode:
        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=str(root),
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["git", "commit", "-m", "Stock-bot cron + git + execution diagnostic and repair — automated"],
                cwd=str(root),
                capture_output=True,
                timeout=10,
            )
            r = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.returncode == 0:
                print("Pushed to origin main.")
            else:
                print("Warning: git push failed:", r.stderr, file=sys.stderr)
        except Exception as e:
            print("Warning: commit/push failed:", e, file=sys.stderr)

    # Summary
    print("\n--- DIAGNOSTIC COMPLETE ---")
    print(f"Report: {reports_dir / f'STOCKBOT_CRON_AND_GIT_DIAGNOSTIC_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md'}")
    failed = (
        data["eod_exit"] != 0
        or "push failed" in data.get("git_push_status", "")
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
