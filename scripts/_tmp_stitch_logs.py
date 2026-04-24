#!/usr/bin/env python3
"""
Merge rotated / split run.jsonl fragments into one time-sorted, deduplicated file.

Inputs (under logs/):
  - run.jsonl (active)
  - run.jsonl.1, run.jsonl.2, ... (numbered rotations)
  - run.jsonl-*.gz or run.jsonl*.gz (optional gzip shards)

Dedup: exact normalized line string (strip) — identical JSON payloads only.

Usage:
  python3 scripts/_tmp_stitch_logs.py --root /root/stock-bot [--apply]

Without --apply: writes logs/run_stitched.jsonl only.
With --apply: after writing run_stitched.jsonl, backs up active run.jsonl then replaces it
  (stop writers first; pass --i-know-writers-stopped if stock-bot is stopped).
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


def _parse_ts(rec: Dict[str, Any]) -> float:
    for k in ("ts", "_dt", "timestamp"):
        v = rec.get(k)
        if v is None:
            continue
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v.strip().replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(s).timestamp()
            except ValueError:
                continue
    return 0.0


def _iter_lines_from_path(p: Path) -> Iterator[str]:
    if not p.is_file():
        return
    if p.suffix == ".gz" or str(p).endswith(".gz"):
        with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                yield line
        return
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line


def _discover_run_fragments(logs: Path) -> List[Path]:
    """Stable order: lowest suffix / name first so older rotations tend first."""
    base = logs / "run.jsonl"
    out: List[Path] = []
    if base.is_file():
        out.append(base)
    # Numbered backups run.jsonl.1 .. .99
    def _rot_key(pp: Path) -> Tuple[int, str]:
        m = re.match(r"^run\.jsonl\.(\d+)$", pp.name)
        return (int(m.group(1)), pp.name) if m else (999999, pp.name)

    for p in sorted(logs.glob("run.jsonl.*"), key=_rot_key):
        if p.is_file() and re.match(r"^run\.jsonl\.\d+$", p.name):
            out.append(p)
    for p in sorted(logs.glob("run.jsonl*.gz")):
        if p.is_file():
            out.append(p)
    for p in sorted(logs.glob("run.jsonl-*.gz")):
        if p.is_file() and p not in out:
            out.append(p)
    # De-dupe paths while preserving order
    seen = set()
    uniq: List[Path] = []
    for p in out:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def _load_all_records(fragments: List[Path]) -> List[Tuple[float, str, Dict[str, Any]]]:
    rows: List[Tuple[float, str, Dict[str, Any]]] = []
    bad = 0
    for fp in fragments:
        for raw in _iter_lines_from_path(fp):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if not isinstance(obj, dict):
                bad += 1
                continue
            sk = _parse_ts(obj)
            rows.append((sk, line, obj))
    if bad:
        print(f"warn: skipped {bad} malformed lines", file=sys.stderr)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/root/stock-bot")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="After stitch, mv run.jsonl -> backup and promote run_stitched.jsonl -> run.jsonl",
    )
    ap.add_argument(
        "--i-know-writers-stopped",
        action="store_true",
        help="Required with --apply to avoid accidental overwrite while bot is writing",
    )
    args = ap.parse_args()
    root = Path(args.root).resolve()
    logs = root / "logs"
    if not logs.is_dir():
        print(f"ERROR: missing logs dir {logs}", file=sys.stderr)
        return 2

    fragments = _discover_run_fragments(logs)
    if not fragments:
        print("ERROR: no run.jsonl fragments found", file=sys.stderr)
        return 2
    print("fragments:", len(fragments))
    for p in fragments[:20]:
        print(" ", p.name, p.stat().st_size if p.is_file() else 0)
    if len(fragments) > 20:
        print(" ...", len(fragments) - 20, "more")

    rows = _load_all_records(fragments)
    print("parsed_lines:", len(rows))
    rows.sort(key=lambda x: (x[0], x[1]))

    seen_lines: set = set()
    out_lines: List[str] = []
    for _sk, line, _obj in rows:
        if line in seen_lines:
            continue
        seen_lines.add(line)
        out_lines.append(line)

    print("after_dedupe:", len(out_lines))
    stitched = logs / "run_stitched.jsonl"
    tmp = stitched.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for line in out_lines:
            f.write(line + "\n")
    tmp.replace(stitched)
    print("wrote:", stitched, "bytes:", stitched.stat().st_size)

    active = logs / "run.jsonl"
    if args.apply:
        if not args.i_know_writers_stopped:
            print("ERROR: refuse --apply without --i-know-writers-stopped (stop stock-bot first)", file=sys.stderr)
            return 3
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = logs / f"run.jsonl.pre_stitch_{ts}"
        if active.exists():
            shutil.copy2(active, backup)
            print("backed_up_active_to:", backup)
        shutil.copy2(stitched, active)
        print("overwrote:", active, "from stitched copy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
