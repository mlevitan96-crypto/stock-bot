#!/usr/bin/env python3
"""Write minimal DAILY_MARKET_SESSION_REPORT.{md,json} for any session with evidence but no daily (lockdown helper)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_SESSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SUFFIXES = {".md", ".json", ".csv"}


def _has_evidence(ev: Path) -> bool:
    if not ev.is_dir():
        return False
    for p in ev.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUFFIXES:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=REPO)
    ap.add_argument(
        "--note",
        default="Evidence present; stub created during repo-wide report lockdown (imported or session-scoped artifacts).",
    )
    args = ap.parse_args()
    repo = args.repo.resolve()
    daily = repo / "reports" / "daily"
    if not daily.is_dir():
        return 0
    n = 0
    for sess in sorted(daily.iterdir()):
        if not sess.is_dir() or not _SESSION_RE.match(sess.name):
            continue
        ev = sess / "evidence"
        md = sess / "DAILY_MARKET_SESSION_REPORT.md"
        if not _has_evidence(ev):
            continue
        if md.is_file() and md.stat().st_size > 0:
            continue
        date = sess.name
        body = "\n".join(
            [
                f"# Daily market session report — {date}",
                "",
                f"> {args.note}",
                "",
                "## Operator note",
                "",
                "This file satisfies the canonical daily report path for CI. For narrative and tables, open files under `evidence/` for this session.",
                "",
                "## Evidence",
                "",
                f"- `reports/daily/{date}/evidence/`",
                "",
                "**CSA_VERDICT:** STUB_SESSION_ARCHIVE",
                "",
            ]
        )
        md.write_text(body, encoding="utf-8")
        js = sess / "DAILY_MARKET_SESSION_REPORT.json"
        js.write_text(
            json.dumps(
                {
                    "session_date_et": date,
                    "stub": True,
                    "note": args.note,
                    "evidence_dir": str(ev.relative_to(repo)),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        n += 1
    print(json.dumps({"stubs_written": n}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
