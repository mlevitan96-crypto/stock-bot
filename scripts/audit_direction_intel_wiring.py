#!/usr/bin/env python3
"""
Autonomous telemetry auditor: prove whether directional intelligence is
captured, persisted, and embedded correctly for live trades.

Reads: logs/intel_snapshot_entry.jsonl, logs/exit_attribution.jsonl.
Contract (direction_readiness): exit_attribution record must have
  direction_intel_embed (dict) and direction_intel_embed.intel_snapshot_entry
  a non-empty dict.

Usage: python scripts/audit_direction_intel_wiring.py [--base-dir .] [--out path]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from config.registry import Directories, LogFiles

# Paths (fallback if registry on droplet is older and missing these)
_PATH_INTEL_SNAPSHOT_ENTRY = getattr(LogFiles, "INTEL_SNAPSHOT_ENTRY", Directories.LOGS / "intel_snapshot_entry.jsonl")
_PATH_EXIT_ATTRIBUTION = getattr(LogFiles, "EXIT_ATTRIBUTION", Directories.LOGS / "exit_attribution.jsonl")


def _tail_jsonl(path: Path, n: int) -> List[Dict[str, Any]]:
    """Last n records (order preserved as in file)."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    records = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(records) >= n:
            break
    return list(reversed(records))


def audit_entry_capture(base: Path, n: int = 50) -> Tuple[dict, List[str]]:
    """Inspect last n ENTRY records (intel_snapshot_entry.jsonl). Returns (stats, issues)."""
    path = (base / _PATH_INTEL_SNAPSHOT_ENTRY).resolve()
    records = _tail_jsonl(path, n)
    stats = {"path": str(path), "total_inspected": len(records), "exists_and_nonempty": 0, "missing": 0, "empty": 0}
    issues = []
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            stats["missing"] += 1
            issues.append(f"Entry record {i+1}: not a dict")
            continue
        # Contract: record is the snapshot itself (append_intel_snapshot_entry writes payload + symbol + event)
        has_content = bool(rec.get("premarket_intel") or rec.get("timestamp") or rec.get("futures_intel") or rec.get("volatility_intel"))
        if has_content:
            stats["exists_and_nonempty"] += 1
        else:
            stats["empty"] += 1
            issues.append(f"Entry record {i+1}: no premarket_intel/timestamp/futures_intel/volatility_intel (keys: {list(rec.keys())[:10]})")
    if not records and path.exists():
        issues.append("intel_snapshot_entry.jsonl exists but has no valid JSONL records.")
    elif not path.exists():
        issues.append("intel_snapshot_entry.jsonl does not exist (entry capture never run).")
    return stats, issues


def audit_exit_embedding(base: Path, n: int = 200) -> Tuple[dict, List[str]]:
    """Inspect last n EXIT records (exit_attribution.jsonl). Returns (stats, issues)."""
    path = (base / _PATH_EXIT_ATTRIBUTION).resolve()
    records = _tail_jsonl(path, n)
    stats = {
        "path": str(path),
        "total_inspected": len(records),
        "has_direction_intel_embed": 0,
        "has_intel_snapshot_entry": 0,
        "intel_snapshot_entry_nonempty": 0,
        "missing_embed": 0,
        "embed_not_dict": 0,
        "snapshot_missing_or_empty": 0,
    }
    issues = []
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            continue
        embed = rec.get("direction_intel_embed")
        if embed is None:
            stats["missing_embed"] += 1
            continue
        if not isinstance(embed, dict):
            stats["embed_not_dict"] += 1
            issues.append(f"Exit record {i+1}: direction_intel_embed is not a dict (type={type(embed).__name__})")
            continue
        stats["has_direction_intel_embed"] += 1
        snapshot = embed.get("intel_snapshot_entry")
        if snapshot is None:
            stats["snapshot_missing_or_empty"] += 1
            issues.append(f"Exit record {i+1}: direction_intel_embed present but intel_snapshot_entry missing (keys: {list(embed.keys())})")
            continue
        if not isinstance(snapshot, dict):
            stats["snapshot_missing_or_empty"] += 1
            issues.append(f"Exit record {i+1}: intel_snapshot_entry is not a dict (type={type(snapshot).__name__})")
            continue
        stats["has_intel_snapshot_entry"] += 1
        if snapshot:
            stats["intel_snapshot_entry_nonempty"] += 1
        else:
            stats["snapshot_missing_or_empty"] += 1
            issues.append(f"Exit record {i+1}: intel_snapshot_entry is empty dict")
    if not path.exists():
        issues.append("exit_attribution.jsonl does not exist.")
    return stats, issues


def check_direction_readiness_contract() -> Dict[str, Any]:
    """Exact contract from src/governance/direction_readiness.py count_direction_intel_backed_trades."""
    return {
        "source": "src/governance/direction_readiness.py",
        "expects": "exit_attribution.jsonl",
        "per_record": [
            "rec.get('direction_intel_embed') is a dict",
            "embed = rec['direction_intel_embed']",
            "embed.get('intel_snapshot_entry') is a dict and non-empty (bool(snapshot))",
        ],
        "field_nesting": "direction_intel_embed.intel_snapshot_entry",
        "payload_source": "src/intelligence/direction_intel.py build_embed_payload_for_exit() returns {'intel_snapshot_entry': entry_snapshot, ...}",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit direction intel wiring (entry capture, exit embed)")
    ap.add_argument("--base-dir", type=Path, default=REPO)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--entry-n", type=int, default=50)
    ap.add_argument("--exit-n", type=int, default=200)
    args = ap.parse_args()
    base = args.base_dir.resolve()

    entry_stats, entry_issues = audit_entry_capture(base, n=args.entry_n)
    exit_stats, exit_issues = audit_exit_embedding(base, n=args.exit_n)
    contract = check_direction_readiness_contract()

    # Failure point
    failure_point = None
    fix_file = None
    fix_function = None
    if entry_stats["total_inspected"] == 0 and not (base / _PATH_INTEL_SNAPSHOT_ENTRY).exists():
        failure_point = "Entry capture never runs: logs/intel_snapshot_entry.jsonl missing or empty."
        fix_file = "main.py"
        fix_function = "Entry fill path: ensure capture_entry_intel_telemetry() is called with symbol and entry_ts; ensure entry_ts is persisted to position context so exit can look up."
    elif entry_stats["exists_and_nonempty"] < entry_stats["total_inspected"] and entry_stats["total_inspected"] > 0:
        failure_point = f"Entry records exist but some are empty or malformed ({entry_stats['empty'] + entry_stats['missing']} of {entry_stats['total_inspected']})."
        fix_file = "src/intelligence/direction_intel.py"
        fix_function = "append_intel_snapshot_entry(): ensure payload contains premarket_intel or timestamp; or src/intelligence/intel_sources.build_full_intel_snapshot() returns full snapshot."
    elif exit_stats["has_direction_intel_embed"] == 0 and exit_stats["total_inspected"] > 0:
        failure_point = "No exit_attribution record has direction_intel_embed (embed never attached or capture_exit_intel_telemetry always returns None/{})."
        fix_file = "main.py"
        fix_function = "Exit attribution block: capture_exit_intel_telemetry(symbol=symbol, entry_ts=entry_ts_iso_attr) must succeed and return dict with 'intel_snapshot_entry'. Check: (1) import/call not skipped by exception; (2) src/intelligence/direction_intel.capture_exit_intel_telemetry returns build_embed_payload_for_exit(...); (3) entry_ts at exit matches key used at entry in store_entry_snapshot_for_position (symbol:entry_ts[:19])."
    elif exit_stats["intel_snapshot_entry_nonempty"] == 0 and exit_stats["has_direction_intel_embed"] > 0:
        failure_point = "direction_intel_embed present but intel_snapshot_entry missing or empty on all records (key mismatch or embed built without entry snapshot)."
        fix_file = "src/intelligence/direction_intel.py"
        fix_function = "build_embed_payload_for_exit(): must receive non-empty entry_snapshot (from load_entry_snapshot_for_position or fallback to exit_snapshot). Ensure load_entry_snapshot_for_position(symbol, entry_ts) uses same key as store_entry_snapshot_for_position (symbol:entry_ts[:19]); or capture_exit_intel_telemetry is called with correct entry_ts from position context."
    elif exit_stats["intel_snapshot_entry_nonempty"] < exit_stats["total_inspected"] and exit_stats["total_inspected"] > 0:
        failure_point = f"Some exit records have non-empty intel_snapshot_entry ({exit_stats['intel_snapshot_entry_nonempty']}), others do not ({exit_stats['total_inspected'] - exit_stats['intel_snapshot_entry_nonempty']}). Entry lookup may fail for some (entry_ts/symbol key mismatch)."
        fix_file = "main.py / src/intelligence/direction_intel.py"
        fix_function = "Unify entry_ts format: at entry use the same entry_ts that will be stored in position context (e.g. from fill time or attribution); at exit pass context.get('entry_ts') to capture_exit_intel_telemetry. direction_intel.store_entry_snapshot_for_position key = symbol:entry_ts[:19]; load_entry_snapshot_for_position must use same."

    # Build report
    lines = [
        "# Direction Intel Wiring Audit",
        "",
        "**Goal:** Prove whether directional intelligence is captured, persisted, and embedded correctly for live trades.",
        "",
        "---",
        "",
        "## 1. Entry capture status",
        "",
        f"**Source:** `{entry_stats['path']}` (last {args.entry_n} records).",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Records inspected | {entry_stats['total_inspected']} |",
        f"| Exists and non-empty (premarket_intel / timestamp / futures_intel / volatility_intel) | {entry_stats['exists_and_nonempty']} |",
        f"| Empty or missing content | {entry_stats.get('empty', 0) + entry_stats.get('missing', 0)} |",
        "",
    ]
    if entry_issues:
        lines.append("**Issues:**")
        for q in entry_issues[:20]:
            lines.append(f"- {q}")
        if len(entry_issues) > 20:
            lines.append(f"- ... and {len(entry_issues) - 20} more.")
        lines.append("")
    lines.extend([
        "---",
        "",
        "## 2. Exit embedding status",
        "",
        f"**Source:** `{exit_stats['path']}` (last {args.exit_n} records).",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Records inspected | {exit_stats['total_inspected']} |",
        f"| Has direction_intel_embed | {exit_stats['has_direction_intel_embed']} |",
        f"| Has intel_snapshot_entry | {exit_stats['has_intel_snapshot_entry']} |",
        f"| intel_snapshot_entry non-empty (direction_readiness counts these) | {exit_stats['intel_snapshot_entry_nonempty']} |",
        f"| Missing embed | {exit_stats['missing_embed']} |",
        f"| Embed not dict | {exit_stats['embed_not_dict']} |",
        f"| Snapshot missing or empty | {exit_stats['snapshot_missing_or_empty']} |",
        "",
    ])
    if exit_issues:
        lines.append("**Issues:**")
        for q in exit_issues[:20]:
            lines.append(f"- {q}")
        if len(exit_issues) > 20:
            lines.append(f"- ... and {len(exit_issues) - 20} more.")
        lines.append("")
    lines.extend([
        "---",
        "",
        "## 3. Contract (direction_readiness expectation)",
        "",
        f"- **Source:** {contract['source']}",
        f"- **File:** {contract['expects']}",
        "- **Per record:**",
    ])
    for c in contract["per_record"]:
        lines.append(f"  - {c}")
    lines.extend([
        f"- **Field nesting:** `{contract['field_nesting']}`",
        f"- **Payload:** {contract['payload_source']}",
        "",
        "---",
        "",
        "## 4. Exact failure point (if any)",
        "",
    ])
    if failure_point:
        lines.append(failure_point)
        lines.append("")
        lines.append("**Concrete fix:**")
        lines.append(f"- **File:** `{fix_file}`")
        lines.append(f"- **Function / area:** {fix_function}")
    else:
        lines.append("No single failure point identified; entry capture and exit embedding both present and aligned with contract.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by scripts/audit_direction_intel_wiring.py (audit only; no strategy or replay changes).*")

    report = "\n".join(lines)
    out = args.out or (base / "reports" / "audit" / "DIRECTION_INTEL_WIRING_AUDIT.md")
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote: {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
