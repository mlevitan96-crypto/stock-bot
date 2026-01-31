#!/usr/bin/env python3
"""
Blocked Trade Intel Report. NO-APPLY.
Blocked counts by reason, intelligence present at block time, shadow profile deltas (hypothetical).
Output: reports/BLOCKED_TRADE_INTEL_<DATE>.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_jsonl(path: Path) -> list:
    out = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--base-dir", default=None)
    ap.add_argument("--blocked-snapshots-path", default="logs/blocked_trade_snapshots.jsonl")
    ap.add_argument("--shadow-path", default=None)
    args = ap.parse_args()

    base = Path(args.base_dir) if args.base_dir else REPO
    target_date = args.date
    logs_dir = base / "logs"
    state_dir = base / "state"
    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    blocked_path = state_dir / "blocked_trades.jsonl"
    blocked = _load_jsonl(blocked_path)
    blocked_snap_path = base / args.blocked_snapshots_path
    blocked_snapshots = _load_jsonl(blocked_snap_path) if blocked_snap_path.exists() else []

    def in_date(ts: str) -> bool:
        return str(ts or "")[:10] == target_date if ts else False

    blocked = [b for b in blocked if in_date(b.get("timestamp") or b.get("ts", ""))]
    blocked_snapshots = [s for s in blocked_snapshots if in_date(s.get("timestamp_utc", ""))]

    # If no blocked_snapshots yet, run linker inline
    if not blocked_snapshots and blocked:
        from telemetry.blocked_snapshot_linker import link_blocked_to_snapshots
        entry_snapshots = []
        for p in [f"logs/signal_snapshots_harness_{target_date}.jsonl", "logs/signal_snapshots.jsonl"]:
            snap_path = base / p
            if snap_path.exists():
                snaps = _load_jsonl(snap_path)
                entry_snapshots = [s for s in snaps if s.get("lifecycle_event") == "ENTRY_DECISION"]
                break
        linked = link_blocked_to_snapshots(blocked, entry_snapshots)
        from telemetry.blocked_snapshot_linker import write_blocked_snapshots
        write_blocked_snapshots(base, linked)
        blocked_snapshots = linked

    by_reason = defaultdict(int)
    for b in blocked:
        r = b.get("reason", "unknown")
        by_reason[r] += 1

    snapshot_linked_count = sum(1 for s in blocked_snapshots if s.get("snapshot_linked"))
    comp_present_any = defaultdict(int)
    comp_defaulted_any = defaultdict(int)
    for s in blocked_snapshots:
        for c in s.get("components_present", []):
            comp_present_any[c] += 1
        for c in s.get("components_defaulted", []):
            comp_defaulted_any[c] += 1

    shadow_path = args.shadow_path or base / "logs" / f"signal_snapshots_shadow_{target_date}.jsonl"
    shadow_section = []
    if Path(shadow_path).exists():
        shadows = _load_jsonl(shadow_path)
        shadows = [s for s in shadows if s.get("lifecycle_event") == "ENTRY_DECISION"]
        if shadows:
            by_profile = defaultdict(list)
            for s in shadows:
                prof = s.get("shadow_profile", "baseline")
                by_profile[prof].append(s.get("composite_score_v2") or 0)
            shadow_section = [
                "## 4. Shadow Profile Deltas (Hypothetical — NO-APPLY)",
                "",
                "Average composite score by shadow profile at ENTRY_DECISION (would NOT change block decisions):",
                "",
                "| Profile | Avg composite | n |",
                "|---------|---------------|---|",
            ]
            for prof in sorted(by_profile.keys()):
                vals = by_profile[prof]
                avg = sum(vals) / len(vals) if vals else 0
                shadow_section.append(f"| {prof} | {avg:.2f} | {len(vals)} |")
            shadow_section.extend(["", "**Disclaimer:** Hypothetical only. Shadow profiles do NOT change trading behavior.", ""])
    else:
        shadow_section = ["## 4. Shadow Profile Deltas", "", "(No shadow snapshots for this date.)", ""]

    lines = [
        f"# Blocked Trade Intel — {target_date}",
        "",
        "**Generated:** Observability-only. NO-APPLY.",
        "",
        "## 1. Blocked Counts by Reason",
        "",
        "| Reason | Count |",
        "|--------|-------|",
    ]
    for r, c in sorted(by_reason.items(), key=lambda x: -x[1]):
        lines.append(f"| {r} | {c} |")
    lines.extend([
        "",
        f"- **Total blocked:** {len(blocked)}",
        "",
        "## 2. Intelligence at Block Time",
        "",
        f"- Blocked trades linked to ENTRY_DECISION snapshot: {snapshot_linked_count} / {len(blocked_snapshots) or len(blocked)}",
        "",
        "### Component presence (linked blocks)",
        "",
        "| Component | Present | Defaulted |",
        "|-----------|---------|-----------|",
    ])
    all_comp = set(comp_present_any) | set(comp_defaulted_any)
    for c in sorted(all_comp):
        lines.append(f"| {c} | {comp_present_any.get(c, 0)} | {comp_defaulted_any.get(c, 0)} |")
    lines.extend([
        "",
        "## 3. Notes",
        "",
        "- Linkage uses symbol + time window (10 min) to nearest ENTRY_DECISION snapshot.",
        "- Components present/defaulted reflect decision-time intelligence; no \"unknown\" without cause.",
        "",
    ])
    lines.extend(shadow_section)
    lines.append("---")
    lines.append("*Generated by scripts/generate_blocked_trade_intel_report.py*")

    out_path = reports_dir / f"BLOCKED_TRADE_INTEL_{target_date}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
