#!/usr/bin/env python3
"""
Safe disk cleanup for the droplet. Run when disk is full or above threshold.
Does NOT touch retention-protected paths (see docs/DATA_RETENTION_POLICY.md).
Removes only old report/audit/experiment artifacts by date.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Must match docs/DATA_RETENTION_POLICY.md — never delete or truncate these.
RETENTION_PROTECTED = {
    "logs/exit_attribution.jsonl",
    "logs/attribution.jsonl",
    "logs/master_trade_log.jsonl",
    "state/blocked_trades.jsonl",
    "reports/state/exit_decision_trace.jsonl",
}

# (dir relative to repo, max_age_days, date pattern in filename)
# Pattern is regex; first group must be YYYY-MM-DD.
SAFE_CLEANUP_DIRS = [
    ("reports/audit", 90, re.compile(r"_(\d{4}-\d{2}-\d{2})\.(json|md)$")),
    ("reports/board", 90, re.compile(r"_(\d{4}-\d{2}-\d{2})\.(json|md)$")),
    ("reports/experiments", 90, re.compile(r"_(\d{4}-\d{2}-\d{2})\.(json|md)$")),
    ("reports/eod_manifests", 60, re.compile(r"EOD_MANIFEST_(\d{4}-\d{2}-\d{2})\.(json|md)$")),
]


def _disk_usage_pct(root: Path = Path("/")) -> float:
    try:
        stat = root.stat()
        # On Linux we need os.statvfs for real disk usage
        import os
        vfs = os.statvfs(str(root))
        total = vfs.f_blocks * vfs.f_frsize
        free = vfs.f_bavail * vfs.f_frsize
        used = total - free
        return (used / total * 100.0) if total else 0.0
    except Exception:
        return 0.0


def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _collect_safe_to_remove(base: Path, now: datetime) -> list[tuple[Path, int]]:
    out: list[tuple[Path, int]] = []
    for dir_rel, max_days, pattern in SAFE_CLEANUP_DIRS:
        dir_path = base / dir_rel
        if not dir_path.is_dir():
            continue
        cutoff = now - timedelta(days=max_days)
        for f in dir_path.iterdir():
            if not f.is_file():
                continue
            rel = f.relative_to(base).as_posix()
            if rel in RETENTION_PROTECTED:
                continue
            m = pattern.search(f.name)
            if not m:
                continue
            dt = _parse_date(m.group(1))
            if dt is None or dt >= cutoff:
                continue
            try:
                size = f.stat().st_size
            except OSError:
                continue
            out.append((f, size))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Safe droplet disk cleanup (retention-protected paths are never touched)")
    ap.add_argument("--threshold", type=float, default=85.0, help="Run cleanup only if disk usage exceeds this %% (default 85)")
    ap.add_argument("--dry-run", action="store_true", help="Only print what would be removed")
    ap.add_argument("--base-dir", default=None, help="Repo root (default: script repo)")
    ap.add_argument("--force", action="store_true", help="Run cleanup even if disk usage is below threshold")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO

    usage_pct = _disk_usage_pct()
    print(f"Disk usage: {usage_pct:.1f}%", file=sys.stderr)
    if not args.force and usage_pct < args.threshold:
        print("Below threshold; no cleanup.", file=sys.stderr)
        return 0

    now = datetime.now(timezone.utc)
    candidates = _collect_safe_to_remove(base, now)
    total_bytes = sum(s for _, s in candidates)

    if not candidates:
        print("No safe-to-remove files found.", file=sys.stderr)
        return 0

    print(f"Found {len(candidates)} file(s), {total_bytes / (1024*1024):.2f} MB", file=sys.stderr)
    if args.dry_run:
        for p, size in sorted(candidates, key=lambda x: x[0].name)[:50]:
            print(f"  [dry-run] would remove {p.relative_to(base)} ({size} bytes)")
        if len(candidates) > 50:
            print(f"  ... and {len(candidates) - 50} more", file=sys.stderr)
        return 0

    removed = 0
    for p, size in candidates:
        try:
            p.unlink()
            removed += 1
        except OSError as e:
            print(f"  Failed to remove {p}: {e}", file=sys.stderr)
    print(f"Removed {removed} file(s), freed ~{total_bytes / (1024*1024):.2f} MB. Disk usage now: {_disk_usage_pct():.1f}%", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
