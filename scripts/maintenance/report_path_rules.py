"""Shared rules: which paths under reports/ are allowed after lockdown."""
from __future__ import annotations

import re
from pathlib import Path

SESSION_FOLDER_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_allowed_report_rel(repo_root: Path, path: Path) -> bool:
    """True if path is canonical DAILY*, session evidence, or permanent reports/state telemetry."""
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    s = rel.as_posix()
    if not s.startswith("reports/"):
        return False
    parts = s.split("/")
    # Operational state / traces (not disposable audit reports)
    if len(parts) >= 2 and parts[1] == "state":
        return True
    if len(parts) < 4 or parts[1] != "daily":
        return False
    if not SESSION_FOLDER_RE.match(parts[2]):
        return False
    if parts[3] == "evidence":
        return len(parts) >= 5
    if parts[3].startswith("DAILY_MARKET_SESSION_REPORT") and parts[3].endswith((".md", ".json")):
        return len(parts) == 4
    return False


def git_allowed_report_rel(rel_posix: str) -> bool:
    """Same contract for git-added path strings (posix)."""
    if not rel_posix.startswith("reports/"):
        return True
    parts = rel_posix.split("/")
    if len(parts) >= 2 and parts[1] == "state":
        return True
    if len(parts) < 4 or parts[1] != "daily":
        return False
    if parts[3] == "evidence":
        return len(parts) >= 5
    if parts[3].startswith("DAILY_MARKET_SESSION_REPORT"):
        return len(parts) == 4
    return False
