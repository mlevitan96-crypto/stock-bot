#!/usr/bin/env python3
"""
CI guard:
- Optional: git-added .md/.json/.csv under reports/ must match allowed layout.
- Optional: working tree has no disallowed report files under reports/ (strict tree).
- Any session folder with non-empty evidence/ must have non-empty DAILY_MARKET_SESSION_REPORT.md.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_SESSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_M_DIR = Path(__file__).resolve().parent
if str(_M_DIR) not in sys.path:
    sys.path.insert(0, str(_M_DIR))
from report_path_rules import git_allowed_report_rel, is_allowed_report_rel


def _git_added_files(repo: Path, base: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "diff", "--name-only", "--diff-filter=A", base, "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        return [x.strip().replace("\\", "/") for x in out.decode().splitlines() if x.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _session_has_evidence_files(evidence_dir: Path) -> bool:
    if not evidence_dir.is_dir():
        return False
    for p in evidence_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".md", ".json", ".csv"):
            return True
    return False


def _sessions_missing_daily(repo: Path) -> list[str]:
    daily = repo / "reports" / "daily"
    bad: list[str] = []
    if not daily.is_dir():
        return bad
    for sess in sorted(daily.iterdir()):
        if not sess.is_dir() or not _SESSION_RE.match(sess.name):
            continue
        ev = sess / "evidence"
        if not _session_has_evidence_files(ev):
            continue
        md = sess / "DAILY_MARKET_SESSION_REPORT.md"
        if not md.is_file() or md.stat().st_size == 0:
            bad.append(
                f"{sess.relative_to(repo)}: evidence present but missing or empty DAILY_MARKET_SESSION_REPORT.md"
            )
    return bad


def _disallowed_on_disk(repo: Path) -> list[str]:
    root = repo / "reports"
    bad: list[str] = []
    if not root.is_dir():
        return bad
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".md", ".json", ".csv"):
            continue
        if not is_allowed_report_rel(repo, p):
            bad.append(p.relative_to(repo).as_posix().replace("\\", "/"))
    return sorted(bad)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=REPO)
    ap.add_argument("--base", default="origin/main", help="Merge base ref for added files (CI)")
    ap.add_argument("--skip-added-path-check", action="store_true")
    ap.add_argument("--skip-daily-evidence-check", action="store_true")
    ap.add_argument(
        "--skip-strict-tree",
        action="store_true",
        help="Do not fail on disallowed report files on disk (not recommended in CI)",
    )
    args = ap.parse_args()
    repo = args.repo.resolve()
    rc = 0

    if not args.skip_strict_tree:
        rogue = _disallowed_on_disk(repo)
        if rogue:
            print("Disallowed report files on disk (must be daily/DAILY_* or daily/.../evidence/ or reports/state/):", file=sys.stderr)
            for r in rogue[:500]:
                print(f"  {r}", file=sys.stderr)
            if len(rogue) > 500:
                print(f"  … and {len(rogue) - 500} more", file=sys.stderr)
            rc = 1

    if not args.skip_added_path_check:
        added = _git_added_files(repo, args.base)
        if not added:
            try:
                subprocess.check_output(["git", "-C", str(repo), "rev-parse", args.base], stderr=subprocess.DEVNULL)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("verify_report_layout: skip added-path check (no git base)", file=sys.stderr)
        else:
            bad = [p for p in added if p.endswith((".md", ".json", ".csv")) and not git_allowed_report_rel(p)]
            if bad:
                print(
                    "Disallowed new report paths (must be reports/daily/<YYYY-MM-DD>/DAILY_* or .../evidence/* or reports/state/*):",
                    file=sys.stderr,
                )
                for b in bad:
                    print(f"  {b}", file=sys.stderr)
                rc = 1

    if not args.skip_daily_evidence_check:
        missing = _sessions_missing_daily(repo)
        if missing:
            print("Sessions with evidence but no canonical daily report:", file=sys.stderr)
            for m in missing:
                print(f"  {m}", file=sys.stderr)
            rc = 1

    if rc == 0:
        print("verify_report_layout: OK")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
