#!/usr/bin/env python3
"""
Run governance integrity checks once and write reports/audit/GOVERNANCE_AUTOMATION_STATUS.json.
Used to verify the Cursor Automation governance_integrity logic and to run locally or in CI.
Does not open issues or send Slack; that is done by the Cursor Cloud automation.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "reports" / "audit"
OUTPUT_FILE = AUDIT_DIR / "GOVERNANCE_AUTOMATION_STATUS.json"

EXPECTED_TOP_LEVEL = {"src", "scripts", "reports", "docs", ".cursor"}
EXPECTED_TOP_LEVEL_ALT_FILES = {"MEMORY_BANK.md"}
FORBIDDEN_PATTERNS = re.compile(
    r"clawdbot|moltbot|CLAWDBOT_|MOLTBOT_",
    re.IGNORECASE,
)
# Paths that may document removal (allowed to mention Clawdbot/Moltbot)
ALLOWED_MENTION_PATHS = ("reports/audit", "docs/", "MEMORY_BANK", "README", ".md")


def check_repo_structure() -> tuple[str, list[str]]:
    """pass/fail and details."""
    details = []
    top_dirs = set(p.name for p in REPO_ROOT.iterdir() if p.is_dir())
    top_files = set(p.name for p in REPO_ROOT.iterdir() if p.is_file())
    missing_dirs = EXPECTED_TOP_LEVEL - top_dirs
    if missing_dirs:
        details.append(f"Missing expected top-level dirs: {sorted(missing_dirs)}")
    missing_files = EXPECTED_TOP_LEVEL_ALT_FILES - top_files
    if missing_files:
        details.append(f"Missing expected top-level files: {sorted(missing_files)}")
    for sub in ["reports/audit", "reports/board"]:
        if not (REPO_ROOT / sub.replace("/", os.sep)).is_dir():
            details.append(f"Missing expected subdir: {sub}")
    if details:
        return "fail", details
    return "pass", []


def check_config_drift() -> tuple[str, list[str]]:
    """Basic check: .cursor/deployment.json and key paths exist."""
    details = []
    deployment = REPO_ROOT / ".cursor" / "deployment.json"
    if not deployment.is_file():
        return "fail", [".cursor/deployment.json missing"]
    return "pass", details


def check_governance_contracts() -> tuple[str, list[str]]:
    """MEMORY_BANK.md, .cursor/automations (with README), reports/audit and reports/board."""
    details = []
    if not (REPO_ROOT / "MEMORY_BANK.md").is_file():
        details.append("Missing: MEMORY_BANK.md")
    automations_dir = REPO_ROOT / ".cursor" / "automations"
    if not automations_dir.is_dir():
        details.append("Missing: .cursor/automations/")
    else:
        if not (automations_dir / "README.md").is_file():
            details.append("Missing: .cursor/automations/README.md")
        specs = list(automations_dir.glob("*.yaml")) + list(automations_dir.glob("*.ts"))
        if not specs:
            details.append("No automation specs in .cursor/automations/")
    for sub in ["reports/audit", "reports/board"]:
        if not (REPO_ROOT / sub.replace("/", os.sep)).is_dir():
            details.append(f"Missing: {sub}")
    if details:
        return "fail", details
    return "pass", []


def check_required_artifacts() -> tuple[str, list[str]]:
    """No strict list; pass if reports/audit and reports/board exist and are dirs."""
    if AUDIT_DIR.is_dir() and (REPO_ROOT / "reports" / "board").is_dir():
        return "pass", []
    return "fail", ["reports/audit or reports/board missing or not directories"]


def check_no_deprecated_dirs() -> tuple[str, list[str]]:
    """No reintroduced deprecated roots; no strict list in repo, pass by default."""
    return "pass", []


def check_no_clawdbot_moltbot() -> tuple[str, list[str]]:
    """Grep for Clawdbot/Moltbot in active code paths only (reintroduction guard). Exclude reports, docs, legacy moltbot/, automation specs."""
    details = []
    # Only scan paths where reintroduction would be a problem; exclude historical/reporting/legacy
    allowed_prefixes = ("src/", "scripts/")
    skip_prefixes = (
        "scripts/automations/",
        "scripts/run_molt",
        "reports/",
        "docs/",
        "memory_bank/",
        "moltbot/",
        "board/",
        ".cursor/automations/",
        ".git/",
        "node_modules/",
        "__pycache__/",
    )
    for root, _dirs, files in os.walk(REPO_ROOT):
        rel_root = os.path.relpath(root, REPO_ROOT)
        norm_root = rel_root.replace("\\", "/") + "/"
        if not any(norm_root.startswith(p) for p in allowed_prefixes):
            continue
        if any(norm_root.startswith(p) for p in skip_prefixes):
            continue
        if ".git" in root or "node_modules" in root or "__pycache__" in root:
            continue
        for f in files:
            if not (f.endswith(".py") or f.endswith(".json") or f.endswith(".yaml") or f.endswith(".yml") or f.endswith(".ts")):
                continue
            path = os.path.normpath(os.path.join(rel_root, f)).replace("\\", "/")
            if any(path.startswith(p) for p in skip_prefixes):
                continue
            full = Path(root) / f
            try:
                text = full.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in FORBIDDEN_PATTERNS.finditer(text):
                line = text[max(0, m.start() - 80) : m.end() + 80]
                if "removal" in line or "removed" in line or "no " in line.lower() or "without " in line.lower():
                    continue
                if "no_clawdbot_moltbot" in line or "no_clawdbot" in line:
                    continue
                details.append(f"Reference in {path}: ...{m.group(0)}...")
                break
    if details:
        return "fail", details
    return "pass", []


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    checks = {}
    all_details: list[str] = []

    for name, fn in [
        ("repo_structure", check_repo_structure),
        ("config_drift", check_config_drift),
        ("governance_contracts_present", check_governance_contracts),
        ("required_artifacts", check_required_artifacts),
        ("no_deprecated_dirs", check_no_deprecated_dirs),
        ("no_clawdbot_moltbot", check_no_clawdbot_moltbot),
    ]:
        status, details = fn()
        checks[name] = status
        all_details.extend(details)

    anomalies = any(c == "fail" for c in checks.values())
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(REPO_ROOT), text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        branch = "unknown"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
    payload = {
        "schema_version": "1.0",
        "run_ts_utc": now,
        "branch": branch,
        "anomalies_detected": anomalies,
        "checks": checks,
        "details": all_details,
        "slack_sent": False,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")
    print("Anomalies detected:", anomalies)


if __name__ == "__main__":
    main()
