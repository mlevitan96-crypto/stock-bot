"""
Operator-visible outputs live only at:
  reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.{md,json}

All other report artifacts: reports/daily/<YYYY-MM-DD>/evidence/
"""
from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

_DAILY_RE = re.compile(r"^reports/daily/([^/]+)/(?:DAILY_MARKET_SESSION_REPORT\.(?:md|json))$")
_SESSION_FOLDER_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def daily_session_dir(repo_root: Path, session_date_et: str) -> Path:
    """session_date_et: YYYY-MM-DD (ET session calendar date)."""
    if not _SESSION_FOLDER_RE.match(session_date_et.strip()):
        raise ValueError(f"session_date_et must be YYYY-MM-DD, got {session_date_et!r}")
    return repo_root / "reports" / "daily" / session_date_et.strip()


def evidence_dir(repo_root: Path, session_date_et: str) -> Path:
    return daily_session_dir(repo_root, session_date_et) / "evidence"


def canonical_md_path(repo_root: Path, session_date_et: str) -> Path:
    return daily_session_dir(repo_root, session_date_et) / "DAILY_MARKET_SESSION_REPORT.md"


def canonical_json_path(repo_root: Path, session_date_et: str) -> Path:
    return daily_session_dir(repo_root, session_date_et) / "DAILY_MARKET_SESSION_REPORT.json"


def parse_session_folder_date(folder_name: str) -> Optional[date]:
    if not _SESSION_FOLDER_RE.match(folder_name.strip()):
        return None
    try:
        return datetime.strptime(folder_name.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def is_canonical_report_path(repo_root: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    s = rel.as_posix()
    return bool(_DAILY_RE.match(s))


def is_evidence_path(repo_root: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    parts = rel.parts
    return (
        len(parts) >= 5
        and parts[0] == "reports"
        and parts[1] == "daily"
        and parts[3] == "evidence"
    )
