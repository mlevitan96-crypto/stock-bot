#!/usr/bin/env python3
"""
Repo-wide reports/ cleanup: classify, move recent orphans into session evidence, delete stale.
Rules only — no prompts. See docs/CANONICAL_DAILY_REPORT_CONTRACT.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

_M_DIR = Path(__file__).resolve().parent
if str(_M_DIR) not in sys.path:
    sys.path.insert(0, str(_M_DIR))

from report_path_rules import SESSION_FOLDER_RE, is_allowed_report_rel

REPO = Path(__file__).resolve().parents[2]
REPORT_SUFFIXES = {".md", ".json", ".csv"}
_YMD_COMPACT = re.compile(r"(20\d{2})(\d{2})(\d{2})")
_YMD_DASH = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _infer_session_date(path: Path, repo: Path, default_et_date: str) -> str:
    blob = f"{path.name} {path.parent.name}"
    m = _YMD_DASH.search(blob)
    if m:
        return m.group(1)
    for m in _YMD_COMPACT.finditer(blob):
        y, mo, d = m.group(1), m.group(2), m.group(3)
        try:
            datetime(int(y), int(mo), int(d))
            return f"{y}-{mo}-{d}"
        except ValueError:
            continue
    return default_et_date


def _daily_reference_blob(repo: Path) -> str:
    parts: List[str] = []
    daily = repo / "reports" / "daily"
    if not daily.is_dir():
        return ""
    for sess in daily.iterdir():
        if not sess.is_dir():
            continue
        for name in ("DAILY_MARKET_SESSION_REPORT.md", "DAILY_MARKET_SESSION_REPORT.json"):
            p = sess / name
            if p.is_file():
                try:
                    parts.append(p.read_text(encoding="utf-8", errors="replace")[:500_000])
                except OSError:
                    pass
    return "\n".join(parts)


def _referenced_in_daily(rel_posix: str, name: str, blob: str) -> bool:
    if rel_posix.replace("\\", "/") in blob:
        return True
    if name in blob and "reports/" in blob:
        return True
    return False


def _collect_report_files(repo: Path) -> List[Path]:
    root = repo / "reports"
    if not root.is_dir():
        return []
    out: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in REPORT_SUFFIXES:
            out.append(p)
    return out


def _classify(
    repo: Path,
    paths: List[Path],
    retention_days: int,
    ref_blob: str,
    default_session: str,
    now: datetime,
) -> Tuple[List[Path], List[Tuple[Path, str]], List[Path]]:
    """Returns (keep_as_is, move_to_session_dest, delete)."""
    keep: List[Path] = []
    move: List[Tuple[Path, str]] = []
    delete: List[Path] = []
    cutoff = max(0, retention_days) * 86400
    for p in paths:
        if is_allowed_report_rel(repo, p):
            keep.append(p)
            continue
        rel = p.relative_to(repo).as_posix()
        name = p.name
        try:
            mtime = p.stat().st_mtime
        except OSError:
            delete.append(p)
            continue
        age_sec = now.timestamp() - mtime
        sess = _infer_session_date(p, repo, default_session)
        if not SESSION_FOLDER_RE.match(sess):
            sess = default_session
        referenced = _referenced_in_daily(rel, name, ref_blob)
        if age_sec <= cutoff or referenced:
            dest_dir = repo / "reports" / "daily" / sess / "evidence"
            move.append((p, str(dest_dir)))
        else:
            delete.append(p)
    return keep, move, delete


def _unique_dest(dest_dir: Path, base_name: str) -> Path:
    dest = dest_dir / base_name
    if not dest.exists():
        return dest
    stem = Path(base_name).stem
    suf = Path(base_name).suffix
    for i in range(1, 10_000):
        cand = dest_dir / f"{stem}_relocated_{i}{suf}"
        if not cand.exists():
            return cand
    h = hashlib.sha256(base_name.encode()).hexdigest()[:8]
    return dest_dir / f"{stem}_{h}{suf}"


def _apply_move(repo: Path, moves: List[Tuple[Path, str]], log: List[str]) -> None:
    for src, ddir in moves:
        dest_dir = Path(ddir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = _unique_dest(dest_dir, src.name)
        try:
            shutil.move(str(src), str(dest))
            log.append(f"MOVE `{src.relative_to(repo)}` -> `{dest.relative_to(repo)}`")
        except OSError as e:
            log.append(f"MOVE_FAIL `{src}`: {e}")


def _apply_delete(repo: Path, paths: List[Path], log: List[str]) -> None:
    for p in paths:
        try:
            p.unlink()
            log.append(f"DELETE `{p.relative_to(repo)}`")
        except OSError as e:
            log.append(f"DELETE_FAIL `{p}`: {e}")


def _prune_empty_dirs(reports: Path) -> None:
    """Remove empty directories under reports/ (bottom-up), keep reports/daily skeleton."""
    if not reports.is_dir():
        return
    all_dirs = sorted(
        [p for p in reports.rglob("*") if p.is_dir()],
        key=lambda x: len(x.parts),
        reverse=True,
    )
    for d in all_dirs:
        try:
            if d.exists() and not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass


def _dir_breakdown(paths: List[Path], repo: Path) -> Dict[str, int]:
    from collections import defaultdict as dd

    d: Dict[str, int] = dd(int)
    for p in paths:
        try:
            rel = p.relative_to(repo / "reports")
        except ValueError:
            d["(other)"] += 1
            continue
        top = rel.parts[0] if rel.parts else "reports"
        d[top] += 1
    return dict(sorted(d.items(), key=lambda x: (-x[1], x[0])))


def _write_inventory_md(
    path: Path,
    repo: Path,
    keep: List[Path],
    move: List[Tuple[Path, str]],
    delete: List[Path],
    now: datetime,
    retention_days: int,
) -> None:
    lines = [
        "# Repo report inventory (global)",
        "",
        f"- **UTC:** {now.isoformat()}",
        f"- **Scope:** `reports/**/*.md|.json|.csv` (excludes paths allowed as non-report: see `report_path_rules.py`; `reports/state/**` is permanent telemetry).",
        f"- **Retention rule for (C):** mtime age > {retention_days} days and not referenced from any `DAILY_MARKET_SESSION_REPORT.md` text.",
        "",
        "## Counts",
        "",
        f"| Class | Count | Meaning |",
        f"|-------|-------|---------|",
        f"| A — KEEP (canonical layout + state) | {len(keep)} | `daily/<date>/DAILY_*` or `daily/.../evidence/` or `reports/state/` |",
        f"| B — MOVE | {len(move)} | Recent or referenced; target session `evidence/` |",
        f"| C — DELETE | {len(delete)} | Stale orphan disposable report |",
        f"| **Total scanned** | {len(keep) + len(move) + len(delete)} | |",
        "",
        "## Sample — move (B) (first 40)",
        "",
    ]
    for src, ddir in move[:40]:
        sess = Path(ddir).name if Path(ddir).parent.name == "evidence" else ddir
        lines.append(f"- `{src.relative_to(repo)}` → `{ddir}/`")
    if len(move) > 40:
        lines.append(f"- … and {len(move) - 40} more")
    lines.extend(["", "## Sample — delete (C) (first 60)", ""])
    for p in delete[:60]:
        lines.append(f"- `{p.relative_to(repo)}`")
    if len(delete) > 60:
        lines.append(f"- … and {len(delete) - 60} more")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_relocation_md(path: Path, repo: Path, move: List[Tuple[Path, str]], log: List[str], now: datetime) -> None:
    lines = [
        "# Repo report relocation (session evidence normalization)",
        "",
        f"- **UTC:** {now.isoformat()}",
        f"- **Moves executed:** {len(move)}",
        "",
        "## Log (first 200 lines)",
        "",
    ]
    lines.extend(f"- {x}" for x in log[:200] if x.startswith("MOVE"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_deletion_md(
    path: Path, repo: Path, delete: List[Path], log: List[str], now: datetime
) -> None:
    bd = _dir_breakdown(delete, repo)
    lines = [
        "# Repo report deletion (stale purge)",
        "",
        f"- **UTC:** {now.isoformat()}",
        f"- **Total deleted:** {len(delete)}",
        "",
        "## Breakdown by top-level under reports/",
        "",
        "| Segment | Count |",
        "|---------|-------|",
    ]
    for k, v in bd.items():
        lines.append(f"| `{k}` | {v} |")
    lines.extend(["", "## Sample filenames", ""])
    for p in delete[:80]:
        lines.append(f"- `{p.relative_to(repo)}`")
    if len(delete) > 80:
        lines.append(f"- … and {len(delete) - 80} more")
    lines.extend(["", "## Delete log sample", ""])
    lines.extend(f"- {x}" for x in [x for x in log if x.startswith("DELETE")][:300])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=REPO)
    ap.add_argument("--retention-days", type=int, default=3)
    ap.add_argument(
        "--default-session-et",
        default="2026-03-26",
        help="YYYY-MM-DD when filename has no date token",
    )
    ap.add_argument("--apply", action="store_true", help="Move and delete; default is plan only")
    ap.add_argument("--json-summary", type=Path, default=None)
    ap.add_argument("--emit-inventory-md", type=Path, default=None)
    ap.add_argument("--emit-relocation-md", type=Path, default=None)
    ap.add_argument("--emit-deletion-md", type=Path, default=None)
    args = ap.parse_args()
    repo = args.repo.resolve()
    now = _now_utc()
    files = _collect_report_files(repo)
    ref_blob = _daily_reference_blob(repo)
    keep, move, delete = _classify(
        repo, files, args.retention_days, ref_blob, args.default_session_et, now
    )

    if args.emit_inventory_md:
        _write_inventory_md(args.emit_inventory_md, repo, keep, move, delete, now, args.retention_days)

    log: List[str] = []
    if args.apply:
        _apply_move(repo, move, log)
        _apply_delete(repo, delete, log)
        _prune_empty_dirs(repo / "reports")
        if args.emit_relocation_md:
            _write_relocation_md(args.emit_relocation_md, repo, move, log, now)
        if args.emit_deletion_md:
            _write_deletion_md(args.emit_deletion_md, repo, delete, log, now)

    summary = {
        "utc": now.isoformat(),
        "retention_days": args.retention_days,
        "default_session_et": args.default_session_et,
        "total_report_like_files_scanned": len(files),
        "keep_allowed_layout": len(keep),
        "move_to_session_evidence": len(move),
        "delete_stale_or_unreferenced": len(delete),
        "apply": args.apply,
    }
    print(json.dumps(summary, indent=2))
    if args.json_summary:
        args.json_summary.parent.mkdir(parents=True, exist_ok=True)
        args.json_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        args.json_summary.with_name(args.json_summary.stem + "_actions.json").write_text(
            json.dumps(log[:50_000], indent=2), encoding="utf-8"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
