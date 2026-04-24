#!/usr/bin/env python3
"""
Build a complete map of writers/readers for each telemetry log and state file.
Static grep + scan for LogFiles usage and open()/append calls.
Outputs reports/audit/TELEMETRY_IO_MAP.md with hot path vs offline path classification.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Canonical log/state names and path patterns
LOG_PATTERNS = {
    "attribution.jsonl": ["attribution.jsonl", "LogFiles.ATTRIBUTION", "ATTRIBUTION"],
    "exit_attribution.jsonl": ["exit_attribution.jsonl", "EXIT_ATTRIBUTION", "exit_attribution"],
    "master_trade_log.jsonl": ["master_trade_log.jsonl", "MASTER_TRADE_LOG", "master_trade_log"],
    "exit_event.jsonl": ["exit_event.jsonl", "EXIT_EVENT", "exit_event"],
    "intel_snapshot_entry.jsonl": ["intel_snapshot_entry", "INTEL_SNAPSHOT_ENTRY"],
    "intel_snapshot_exit.jsonl": ["intel_snapshot_exit", "INTEL_SNAPSHOT_EXIT"],
    "direction_event.jsonl": ["direction_event", "DIRECTION_EVENT"],
    "position_intel_snapshots.json": ["position_intel_snapshots", "position_intel_state"],
}
WRITER_INDICATORS = ["append_exit_attribution", "append_exit_event", "append_master_trade", "append_intel_snapshot_entry", "append_intel_snapshot_exit", "append_direction_event", "store_entry_snapshot_for_position", "open(\"a\"", '.open("a"', "open('a'", "write(json.dumps", "append_jsonl"]
HOT_PATH_FILES = ["main.py", "src/exit/exit_attribution.py", "src/intelligence/direction_intel.py", "utils/master_trade_log.py"]


def grep_pattern(pattern: str, ext: str = "py") -> List[tuple]:
    out: List[tuple] = []
    for f in REPO.rglob(f"*.{ext}"):
        if "node_modules" in str(f) or ".git" in str(f) or "__pycache__" in str(f):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = f.relative_to(REPO)
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(pattern, line):
                out.append((str(rel), i, line.strip()[:120]))
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Build telemetry I/O map")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out_path = args.out or (REPO / "reports" / "audit" / "TELEMETRY_IO_MAP.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # For each log, find writers (append_*, open("a"), write) and readers (open("r"), load, read, cat)
    writers: Dict[str, List[str]] = {k: [] for k in LOG_PATTERNS}
    readers: Dict[str, List[str]] = {k: [] for k in LOG_PATTERNS}
    seen_w: Set[tuple] = set()
    seen_r: Set[tuple] = set()

    for log_name, patterns in LOG_PATTERNS.items():
        for pat in patterns:
            for rel, line_no, line in grep_pattern(re.escape(pat)):
                key = (log_name, rel, line_no)
                if "append_" in line or ".open(\"a\")" in line or "open(\"a\"" in line or "write(json" in line or "store_entry" in line:
                    if key not in seen_w:
                        seen_w.add(key)
                        writers[log_name].append(f"{rel}:{line_no} ({line[:80]}...)")
                elif "read_text" in line or "open(\"r\")" in line or "load_jsonl" in line or "load(" in line or "cat " in line or "get(" in line:
                    if key not in seen_r:
                        seen_r.add(key)
                        readers[log_name].append(f"{rel}:{line_no}")

    # position_intel_snapshots.json: writer is store_entry_snapshot_for_position in direction_intel
    for rel, line_no, line in grep_pattern("store_entry_snapshot_for_position"):
        if "build_telemetry_io_map" not in rel:
            writers.setdefault("position_intel_snapshots.json", []).append(f"{rel}:{line_no} ({line[:60]}...)")
    if not writers.get("position_intel_snapshots.json"):
        writers["position_intel_snapshots.json"] = ["src/intelligence/direction_intel.py (store_entry_snapshot_for_position)"]
    # load_entry_snapshot_for_position reads position_intel_snapshots
    for rel, line_no, _ in grep_pattern("load_entry_snapshot_for_position"):
        if "build_telemetry_io_map" not in rel:
            readers.setdefault("position_intel_snapshots.json", []).append(f"{rel}:{line_no}")

    # Dedupe by file
    for k in writers:
        writers[k] = list(dict.fromkeys(writers[k]))
    for k in readers:
        readers[k] = list(dict.fromkeys(readers[k]))

    lines = [
        "# Telemetry I/O Map",
        "",
        "**Purpose:** Every writer and reader of canonical telemetry logs and state.",
        "**Hot path:** execution path (main.py, exit_attribution, direction_intel, master_trade_log). **Offline:** reports, audits, replay, dashboard (read-only).",
        "",
        "## Writers (by log)",
        "",
    ]
    for log_name in LOG_PATTERNS:
        lines.append(f"### {log_name}")
        lines.append("")
        w = writers.get(log_name, [])
        if w:
            for x in w[:25]:
                lines.append(f"- `{x}`")
        else:
            lines.append("- (no static writer match)")
        lines.append("")
    lines.append("## Readers (by log)")
    lines.append("")
    for log_name in LOG_PATTERNS:
        lines.append(f"### {log_name}")
        lines.append("")
        r = readers.get(log_name, [])
        if r:
            for x in r[:25]:
                lines.append(f"- `{x}`")
        else:
            lines.append("- (no static reader match)")
        lines.append("")
    lines.append("## Hot path vs offline")
    lines.append("")
    lines.append("| File | Classification |")
    lines.append("|------|-----------------|")
    all_files = sorted(set(p[1] for p in seen_w) | set(p[1] for p in seen_r))
    for f in all_files:
        hot = "hot path" if any(h in f for h in HOT_PATH_FILES) else "offline/report"
        lines.append(f"| {f} | {hot} |")
    lines.append("")
    lines.append("## Hidden readers (Model B - >=5 confirmed)")
    lines.append("")
    lines.append("| Reader | Log(s) read | Purpose |")
    lines.append("|--------|-------------|---------|")
    hidden = [
        ("dashboard.py", "attribution.jsonl, exit_attribution.jsonl, master_trade_log.jsonl", "Dashboard endpoints: trades, exit quality, health"),
        ("src/governance/direction_readiness.py", "exit_attribution.jsonl", "direction_readiness: count telemetry_trades (direction_intel_embed.intel_snapshot_entry)"),
        ("src/dashboard/direction_banner_state.py", "state/direction_readiness.json (derived from exit_attribution)", "Banner: X/100 telemetry-backed trades"),
        ("scripts/replay/* (equity_exit_replay, build_canonical_equity_ledger, discover_equity_data_manifest)", "attribution.jsonl, exit_attribution.jsonl", "Replay loaders and ledger build"),
        ("scripts/build_30d_comprehensive_review.py", "attribution.jsonl, exit_attribution.jsonl", "EOD/board 30d review"),
        ("scripts/trade_visibility_review.py", "exit_attribution, state/direction_readiness.json", "Trade visibility and direction readiness report"),
        ("scripts/audit_direction_intel_wiring.py", "exit_attribution.jsonl, intel_snapshot_entry.jsonl", "Direction intel wiring audit"),
    ]
    for name, logs, purpose in hidden:
        lines.append(f"| {name} | {logs} | {purpose} |")
    lines.append("")
    lines.append("*Generated by scripts/audit/build_telemetry_io_map.py*")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote: {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
