#!/usr/bin/env python3
"""
PnL lineage map integrity check (non-breaking).

Loads docs/pnl_audit/LINEAGE_MATRIX.json and classifies each row:
  RESOLVED | MOVED (likely refactor) | MISSING

Usage (repo root):
  python3 scripts/audit/alpaca_pnl_lineage_map_check.py
  python3 scripts/audit/alpaca_pnl_lineage_map_check.py --write-evidence
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parent.parent.parent


def _et_date() -> str:
    try:
        r = subprocess.run(
            ["bash", "-lc", "TZ=America/New_York date +%Y-%m-%d"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class RowResult:
    field_name: str
    emitter_status: str
    emitter_detail: str
    persistence_status: str
    persistence_detail: str
    overall: str


def check_emitter(repo: Path, loc: str) -> Tuple[str, str]:
    loc = (loc or "").strip()
    if not loc:
        return "MISSING", "empty_emitter"
    low = loc.lower()
    if "alpaca_trade_api" in low or low.startswith("broker"):
        return "RESOLVED", "external_broker_sdk"
    if ":CONTAINS:" in loc:
        relpath, rest = loc.split(":CONTAINS:", 1)
        needle = rest.strip()
        fp = repo / relpath.strip()
        if not fp.is_file():
            return "MOVED", f"file_missing:{relpath.strip()}"
        text = fp.read_text(encoding="utf-8", errors="replace")
        if needle in text:
            return "RESOLVED", f"substring:{needle[:40]}"
        return "MISSING", f"substring_not_found:{needle[:40]}"
    if loc.startswith("dashboard.py:"):
        fn = loc.split(":", 1)[1].strip()
        p = repo / "dashboard.py"
        if not p.is_file():
            return "MOVED", "dashboard.py_missing"
        text = p.read_text(encoding="utf-8", errors="replace")
        if fn.startswith("api_") or "_" in fn:
            if f"def {fn}" in text:
                return "RESOLVED", f"def {fn} found"
        return "MISSING", f"def {fn} not found"
    parts = loc.split(":", 1)
    if len(parts) != 2:
        return "MISSING", "emitter_parse_error"
    relpath, sym = parts[0].strip(), parts[1].strip()
    fp = repo / relpath
    if not fp.is_file():
        return "MOVED", f"file_missing:{relpath}"
    text = fp.read_text(encoding="utf-8", errors="replace")
    if "." in sym:
        _cls, meth = sym.rsplit(".", 1)
        if f"def {meth}" in text:
            return "RESOLVED", f"method {meth} present"
        return "MISSING", f"method {meth} not found in {relpath}"
    if f"def {sym}" in text:
        return "RESOLVED", f"def {sym} found"
    return "MISSING", f"def {sym} not found"


def _split_persistence_segments(raw: str) -> List[str]:
    out: List[str] = []
    for chunk in raw.split("|"):
        c = chunk.strip()
        if not c:
            continue
        if c.startswith("GET "):
            out.append(c)
            continue
        if "broker" in c.lower() or c.lower().startswith("activities"):
            out.append("broker_declared")
            continue
        # "logs/foo.jsonl (note)" -> path part
        first = c.split()[0].strip()
        if first.startswith(("logs/", "state/", "data/", "config/")):
            if "*" in first:
                out.append(first.split("*")[0].rstrip("/") + "/")  # e.g. logs/
            else:
                out.append(first)
        elif "/api/" in c:
            out.append(c)
    return out if out else [raw.strip()]


def check_persistence(repo: Path, raw: str) -> Tuple[str, str]:
    raw = (raw or "").strip()
    if not raw:
        return "MISSING", "empty_persistence"
    statuses: List[str] = []
    details: List[str] = []
    for seg in _split_persistence_segments(raw):
        if seg == "broker_declared" or "broker" in seg.lower():
            statuses.append("RESOLVED")
            details.append("broker_declared")
            continue
        if seg.startswith("GET ") or "/api/" in seg:
            statuses.append("RESOLVED")
            details.append("api_declared")
            continue
        if seg.startswith(("logs/", "state/", "data/", "config/")):
            p = repo / seg.rstrip("/")
            if p.is_file():
                statuses.append("RESOLVED")
                details.append(f"{seg}:file")
            elif p.is_dir() and os.access(p, os.W_OK):
                statuses.append("RESOLVED")
                details.append(f"{seg}:dir_writable")
            elif p.parent.is_dir() and os.access(p.parent, os.W_OK):
                statuses.append("RESOLVED")
                details.append(f"{seg}:parent_writable")
            else:
                statuses.append("MISSING")
                details.append(f"{seg}:no_path")
            continue
        statuses.append("MOVED")
        details.append(f"{seg}:unparsed")
    if "MISSING" in statuses:
        return "MISSING", "; ".join(details)
    if statuses and all(s == "RESOLVED" for s in statuses):
        return "RESOLVED", "; ".join(details)
    return "MOVED", "; ".join(details)


def overall(es: str, ps: str) -> str:
    if "MISSING" in (es, ps):
        return "MISSING"
    if "MOVED" in (es, ps):
        return "MOVED"
    return "RESOLVED"


def run_check(matrix_path: Path, repo: Path) -> Tuple[List[RowResult], Dict[str, Any]]:
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    fields = data.get("fields") or []
    rows: List[RowResult] = []
    summary = {"RESOLVED": 0, "MOVED": 0, "MISSING": 0}
    for f in fields:
        name = f.get("field_name", "?")
        es, ed = check_emitter(repo, f.get("emitter_code_location", ""))
        ps, pd = check_persistence(repo, f.get("persistence_location", ""))
        ov = overall(es, ps)
        summary[ov] = summary.get(ov, 0) + 1
        rows.append(RowResult(name, es, ed, ps, pd, ov))
    return rows, {"schema": data.get("schema_version"), "summary": summary, "field_count": len(fields)}


def write_markdown(rows: List[RowResult], meta: Dict[str, Any], out: Path) -> None:
    lines = [
        "# ALPACA PnL LINEAGE MAP CHECK\n\n",
        f"- schema_version: `{meta.get('schema')}`\n",
        f"- fields: **{meta.get('field_count')}**\n",
        f"- summary: `RESOLVED={meta['summary'].get('RESOLVED')}` `MOVED={meta['summary'].get('MOVED')}` `MISSING={meta['summary'].get('MISSING')}`\n\n",
        "| field | emitter | persistence | overall |\n",
        "|-------|---------|-------------|--------|\n",
    ]
    for r in rows:
        lines.append(
            f"| `{r.field_name}` | {r.emitter_status}: {r.emitter_detail} | {r.persistence_status}: {r.persistence_detail} | **{r.overall}** |\n"
        )
    lines.append("\n## Legend\n\n")
    lines.append("- **RESOLVED:** emitter symbol found in file and persistence path exists or parent writable / broker or API declared.\n")
    lines.append("- **MOVED:** emitter file missing or persistence path unexpected.\n")
    lines.append("- **MISSING:** def not found or required path not creatable.\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", type=Path, default=REPO / "docs" / "pnl_audit" / "LINEAGE_MATRIX.json")
    ap.add_argument("--repo", type=Path, default=REPO)
    ap.add_argument("--write-evidence", action="store_true")
    ap.add_argument("--evidence-dir", type=Path, default=None)
    args = ap.parse_args()
    # fix typo if I introduced
    rows, meta = run_check(args.matrix, args.repo)
    ev_dir = args.evidence_dir or (REPO / "reports" / "daily" / _et_date() / "evidence")
    if args.write_evidence:
        write_markdown(rows, meta, ev_dir / "ALPACA_PNL_LINEAGE_MAP_CHECK.md")
    print(json.dumps({**meta, "evidence": str(ev_dir / "ALPACA_PNL_LINEAGE_MAP_CHECK.md") if args.write_evidence else None}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
