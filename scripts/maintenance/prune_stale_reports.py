#!/usr/bin/env python3
"""
Delete disposable reports per retention policy. Logs/telemetry untouched.

- Never delete: reports/daily/*/DAILY_MARKET_SESSION_REPORT.md|.json
- Session evidence: delete files in reports/daily/<DATE>/evidence/ when (today - DATE) > retention_days
- Stray session files: delete non-DAILY *.md|json|csv directly under reports/daily/<DATE>/ when session expired
- Legacy: delete reports/**/*.{md,json,csv} not under allowed daily layout when mtime age > retention_days
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Tuple

REPO = Path(__file__).resolve().parents[2]


def _parse_session_dir(name: str):
    try:
        return datetime.strptime(name, "%Y-%m-%d").date()
    except ValueError:
        return None


def _is_canonical(repo: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo.resolve())
    except ValueError:
        return False
    parts = rel.parts
    return (
        len(parts) == 4
        and parts[0] == "reports"
        and parts[1] == "daily"
        and parts[3] in ("DAILY_MARKET_SESSION_REPORT.md", "DAILY_MARKET_SESSION_REPORT.json")
    )


def _is_daily_evidence(repo: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo.resolve())
    except ValueError:
        return False
    parts = rel.parts
    return len(parts) >= 5 and parts[0] == "reports" and parts[1] == "daily" and parts[3] == "evidence"


def _collect(repo: Path, retention_days: int, now: datetime) -> Tuple[List[Path], List[Path]]:
    today = now.date()
    deleted: List[Path] = []
    retained: List[Path] = []
    cutoff_age_sec = max(1, retention_days) * 86400
    reports = repo / "reports"
    if not reports.is_dir():
        return deleted, retained

    daily = reports / "daily"
    if daily.is_dir():
        for sess_dir in daily.iterdir():
            if not sess_dir.is_dir():
                continue
            sd = _parse_session_dir(sess_dir.name)
            ev = sess_dir / "evidence"
            if ev.is_dir():
                expire_session = sd is not None and (today - sd).days > retention_days
                for p in ev.rglob("*"):
                    if not p.is_file():
                        continue
                    if expire_session:
                        deleted.append(p)
                    else:
                        retained.append(p)
            for p in sess_dir.iterdir():
                if p.is_file() and p.name.startswith("DAILY_MARKET_SESSION_REPORT"):
                    retained.append(p)
                elif (
                    expire_session
                    and p.is_file()
                    and p.suffix.lower() in (".md", ".json", ".csv")
                    and not p.name.startswith("DAILY_MARKET_SESSION_REPORT")
                ):
                    deleted.append(p)

    for p in reports.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".md", ".json", ".csv"):
            continue
        if _is_canonical(repo, p):
            retained.append(p)
            continue
        if _is_daily_evidence(repo, p):
            continue
        try:
            rel = p.resolve().relative_to(reports.resolve())
        except ValueError:
            continue
        if rel.parts and rel.parts[0] == "daily":
            continue
        age = now.timestamp() - p.stat().st_mtime
        if age > cutoff_age_sec:
            deleted.append(p)
        else:
            retained.append(p)

    return deleted, retained


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=REPO)
    ap.add_argument("--retention-days", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log-md", type=Path, default=None, help="Write execution summary markdown")
    args = ap.parse_args()
    repo = args.repo.resolve()
    now = datetime.now(timezone.utc)
    deleted, retained = _collect(repo, args.retention_days, now)

    for p in deleted:
        if args.dry_run:
            continue
        try:
            p.unlink()
        except OSError:
            pass

    lines = [
        f"# Report pruning execution",
        "",
        f"- **UTC:** {now.isoformat()}",
        f"- **retention_days:** {args.retention_days}",
        f"- **dry_run:** {args.dry_run}",
        "",
        f"## Deleted ({len(deleted)})",
        "",
    ]
    for p in sorted(deleted, key=lambda x: str(x))[:2000]:
        lines.append(f"- `{p.relative_to(repo)}`")
    if len(deleted) > 2000:
        lines.append(f"- … and {len(deleted) - 2000} more")
    lines.extend(
        [
            "",
            "## Retained sample (first 80)",
            "",
        ]
    )
    for p in sorted(set(retained), key=lambda x: str(x))[:80]:
        lines.append(f"- `{p.relative_to(repo)}`")

    text = "\n".join(lines)
    print(text)
    if args.log_md:
        args.log_md.parent.mkdir(parents=True, exist_ok=True)
        args.log_md.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
