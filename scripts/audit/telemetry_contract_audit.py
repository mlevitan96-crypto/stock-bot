#!/usr/bin/env python3
"""
Telemetry contract audit: scan last N records of each canonical log,
validate schema, report missing fields, wrong nesting, empty dicts, type mismatches.
Writes reports/audit/TELEMETRY_CONTRACT_AUDIT.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from config.registry import Directories, LogFiles
except Exception:
    Directories = type("D", (), {"LOGS": Path("logs"), "STATE": Path("state")})()
    LogFiles = type("L", (), {
        "ATTRIBUTION": Directories.LOGS / "attribution.jsonl",
        "MASTER_TRADE_LOG": Directories.LOGS / "master_trade_log.jsonl",
        "EXIT_ATTRIBUTION": Directories.LOGS / "exit_attribution.jsonl",
        "EXIT_EVENT": getattr(Path("logs"), "exit_event.jsonl", Directories.LOGS / "exit_event.jsonl"),
        "INTEL_SNAPSHOT_ENTRY": getattr(Path("logs"), "intel_snapshot_entry.jsonl", Directories.LOGS / "intel_snapshot_entry.jsonl"),
        "INTEL_SNAPSHOT_EXIT": getattr(Path("logs"), "intel_snapshot_exit.jsonl", Directories.LOGS / "intel_snapshot_exit.jsonl"),
        "DIRECTION_EVENT": getattr(Path("logs"), "direction_event.jsonl", Directories.LOGS / "direction_event.jsonl"),
    })()

from src.contracts.telemetry_schemas import (
    validate_attribution,
    validate_master_trade_log,
    validate_exit_attribution,
    validate_exit_event,
    validate_intel_snapshot_entry,
    validate_intel_snapshot_exit,
    validate_direction_event,
    check_canonical_fields,
)


def _tail(path: Path, n: int) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(records) >= n:
            break
    return records[-n:] if len(records) > n else records


def audit_log(
    base: Path,
    rel_path: Path,
    validator: Callable[[Dict[str, Any]], Tuple[bool, List[str]]],
    log_name: str,
    n: int,
    check_canonical: bool = False,
    strict_canonical: bool = False,
) -> Dict[str, Any]:
    path = (base / rel_path).resolve()
    records = _tail(path, n)
    ok = 0
    issues_all: List[str] = []
    canonical_missing: List[str] = []
    for i, rec in enumerate(records):
        valid, issues = validator(rec)
        canon = check_canonical_fields(rec, log_name) if check_canonical else []
        if check_canonical:
            canonical_missing.extend(canon)
        if strict_canonical and log_name in ("exit_attribution", "exit_event") and canon:
            valid = False
            issues = issues + [f"missing canonical: {', '.join(canon)}"]
        if valid:
            ok += 1
        else:
            for q in issues:
                issues_all.append(f"record {i+1}: {q}")
    return {
        "path": str(path),
        "exists": path.exists(),
        "total": len(records),
        "valid": ok,
        "invalid": len(records) - ok,
        "issues": issues_all[:30],
        "canonical_missing": list(dict.fromkeys(canonical_missing)),
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Telemetry contract audit")
    ap.add_argument("--base-dir", type=Path, default=REPO)
    ap.add_argument("--n", type=int, default=100, help="Last N records per log")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--strict-canonical", action="store_true", help="Treat missing direction/side/position_side on exit_attribution/exit_event as blocking")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    n = args.n

    logs = [
        ("master_trade_log", getattr(LogFiles, "MASTER_TRADE_LOG", base / "logs" / "master_trade_log.jsonl"), validate_master_trade_log, True),
        ("attribution", getattr(LogFiles, "ATTRIBUTION", base / "logs" / "attribution.jsonl"), validate_attribution, True),
        ("exit_attribution", getattr(LogFiles, "EXIT_ATTRIBUTION", base / "logs" / "exit_attribution.jsonl"), validate_exit_attribution, True),
        ("exit_event", getattr(LogFiles, "EXIT_EVENT", base / "logs" / "exit_event.jsonl"), validate_exit_event, True),
        ("intel_snapshot_entry", getattr(LogFiles, "INTEL_SNAPSHOT_ENTRY", base / "logs" / "intel_snapshot_entry.jsonl"), validate_intel_snapshot_entry, False),
        ("intel_snapshot_exit", getattr(LogFiles, "INTEL_SNAPSHOT_EXIT", base / "logs" / "intel_snapshot_exit.jsonl"), validate_intel_snapshot_exit, False),
        ("direction_event", getattr(LogFiles, "DIRECTION_EVENT", base / "logs" / "direction_event.jsonl"), validate_direction_event, False),
    ]

    results = {}
    for name, rel_path, validator, check_canon in logs:
        rel = rel_path if isinstance(rel_path, Path) else Path(rel_path)
        if not str(rel).startswith(str(base)):
            rel = base / "logs" / rel.name if "logs" in str(rel) else base / rel
        results[name] = audit_log(base, rel, validator, name, n, check_canonical=check_canon, strict_canonical=getattr(args, "strict_canonical", False))

    out_path = args.out or (base / "reports" / "audit" / "TELEMETRY_CONTRACT_AUDIT.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Telemetry Contract Audit",
        "",
        f"**Base:** {base}",
        f"**Last N records per log:** {n}",
        "",
        "## Summary",
        "",
        "| Log | Path | Exists | Total | Valid | Invalid | Blocking |",
        "|-----|------|--------|-------|-------|---------|----------|",
    ]
    blocking = []
    for name, _, _, _ in logs:
        r = results[name]
        ex = "yes" if r["exists"] else "no"
        total = r["total"]
        valid = r["valid"]
        inv = r["invalid"]
        block = "yes" if (r["exists"] and inv > 0 and name in ("exit_attribution", "exit_event")) else "no"
        if block == "yes":
            blocking.append(name)
        path_short = Path(r["path"]).name
        lines.append(f"| {name} | {path_short} | {ex} | {total} | {valid} | {inv} | {block} |")
    lines.append("")
    lines.append("## Per-log details")
    lines.append("")
    for name, _, _, _ in logs:
        r = results[name]
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- **Path:** `{r['path']}`")
        lines.append(f"- **Exists:** {r['exists']}")
        lines.append(f"- **Total inspected:** {r['total']}")
        lines.append(f"- **Valid:** {r['valid']}")
        lines.append(f"- **Invalid:** {r['invalid']}")
        if r["issues"]:
            lines.append("- **Issues:**")
            for q in r["issues"]:
                lines.append(f"  - {q}")
        if r.get("canonical_missing"):
            lines.append(f"- **Canonical fields missing (advisory):** {r['canonical_missing']}")
        lines.append("")
    lines.append("## Blocking")
    lines.append("")
    if blocking:
        lines.append(f"Logs with schema failures that may block replay/readiness: **{', '.join(blocking)}**.")
    else:
        lines.append("No blocking schema failures in canonical logs.")
    lines.append("")
    lines.append("*Generated by scripts/audit/telemetry_contract_audit.py*")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote: {out_path}", file=sys.stderr)
    return 0 if not blocking else 1


if __name__ == "__main__":
    sys.exit(main())
