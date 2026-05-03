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
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "reports" / "audit"
OUTPUT_FILE = AUDIT_DIR / "GOVERNANCE_AUTOMATION_STATUS.json"

EXPECTED_TOP_LEVEL = {"src", "scripts", "reports", "memory_bank", "docs", "validation", ".cursor"}
FORBIDDEN_PATTERNS = re.compile(
    r"clawdbot|moltbot|CLAWDBOT_|MOLTBOT_",
    re.IGNORECASE,
)
# Paths that may document removal (allowed to mention Clawdbot/Moltbot)
ALLOWED_MENTION_PATHS = ("reports/audit", "docs/", "MEMORY_BANK", "README", ".md")


def check_repo_structure() -> tuple[str, list[str]]:
    """pass/fail and details."""
    details = []
    top = set(p.name for p in REPO_ROOT.iterdir() if p.is_dir())
    missing = EXPECTED_TOP_LEVEL - top
    if missing:
        return "fail", [f"Missing expected top-level dirs: {sorted(missing)}"]
    return "pass", details


def check_config_drift() -> tuple[str, list[str]]:
    """Basic check: .cursor/deployment.json and key paths exist."""
    details = []
    deployment = REPO_ROOT / ".cursor" / "deployment.json"
    if not deployment.is_file():
        return "fail", [".cursor/deployment.json missing"]
    return "pass", details


def check_governance_contracts() -> tuple[str, list[str]]:
    """memory_bank, .cursor/automations, reports/audit and reports/board."""
    details = []
    for path in ["memory_bank", ".cursor/automations", "reports/audit", "reports/board"]:
        if not (REPO_ROOT / path.replace("/", os.sep)).exists():
            details.append(f"Missing: {path}")
    if details:
        return "fail", details
    return "pass", details


def check_required_artifacts() -> tuple[str, list[str]]:
    """No strict list; pass if reports/audit and reports/board exist and are dirs."""
    if AUDIT_DIR.is_dir() and (REPO_ROOT / "reports" / "board").is_dir():
        return "pass", []
    return "fail", ["reports/audit or reports/board missing or not directories"]


KNOWN_DEPRECATED_DIRS = {"moltbot"}


def check_no_deprecated_dirs() -> tuple[str, list[str]]:
    """Flag known deprecated top-level directories that should have been removed."""
    details = []
    top = set(p.name for p in REPO_ROOT.iterdir() if p.is_dir())
    present = KNOWN_DEPRECATED_DIRS & top
    if present:
        for d in sorted(present):
            details.append(f"Deprecated directory still present: {d}/")
        return "fail", details
    return "pass", []


def check_no_clawdbot_moltbot() -> tuple[str, list[str]]:
    """Search for Clawdbot/Moltbot references in code and config (reintroduction guard).

    Excludes:
      - reports/audit, reports/daily, docs/, MEMORY_BANK_ALPACA.md (document removal)
      - .cursor/automations/ (governance specs that reference the check itself)
      - scripts/automations/ (this governance script)
      - .git/, node_modules/, __pycache__/

    Includes moltbot/ as active code that should have been removed.
    """
    details = []
    skip_prefixes = (
        "reports/",
        "docs/",
        "memory_bank/",
        "board/eod/out/",
        ".cursor/automations/",
        "scripts/automations/",
        ".git/",
        "node_modules/",
        "__pycache__/",
    )
    skip_files = {"MEMORY_BANK_ALPACA.md", "alpaca_codebase_payload.txt"}
    for root, _dirs, files in os.walk(REPO_ROOT):
        rel_root = os.path.relpath(root, REPO_ROOT)
        norm_root = rel_root.replace("\\", "/")
        if norm_root == ".":
            norm_root = ""
        else:
            norm_root += "/"
        if any(norm_root.startswith(p) for p in skip_prefixes):
            continue
        if ".git" in root or "node_modules" in root or "__pycache__" in root:
            continue
        for f in files:
            if f in skip_files:
                continue
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
                context = text[max(0, m.start() - 80) : m.end() + 80]
                if "removal" in context or "removed" in context:
                    continue
                if "no_clawdbot_moltbot" in context or "no_clawdbot" in context:
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
    payload = {
        "schema_version": "1.0",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00"),
        "run_ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00"),
        "branch": "main",
        "status": "anomalies" if anomalies else "ok",
        "anomalies_detected": anomalies,
        "checks": checks,
        "details": all_details,
        "anomalies": all_details,
        "slack_sent": False,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")
    print("Anomalies detected:", anomalies)


if __name__ == "__main__":
    main()
