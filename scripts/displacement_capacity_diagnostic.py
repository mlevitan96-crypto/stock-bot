#!/usr/bin/env python3
"""
Displacement & Capacity Diagnostic — blocked counts by reason and mode:strategy.

Reads state/blocked_trades.jsonl (and optionally logs/system_events.jsonl for displacement events).
Outputs displacement_blocked, max_positions_reached, capacity by mode:strategy;
optional correlation with regime. Report: JSON + md.

Usage: python scripts/displacement_capacity_diagnostic.py [--days 14] [--base-dir PATH] [--out-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else ""


def _iter_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Displacement and capacity diagnostic")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--base-dir", type=Path, default=ROOT)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()
    base = args.base_dir.resolve()
    state_dir = base / "state"
    logs_dir = base / "logs"
    blocked_path = state_dir / "blocked_trades.jsonl"
    events_path = logs_dir / "system_events.jsonl"

    today = datetime.now(timezone.utc).date()
    days_back = max(1, min(args.days, 60))
    window_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_back)]

    blocked_raw = _iter_jsonl(blocked_path)
    blocked = [r for r in blocked_raw if _day_utc(r.get("ts") or r.get("timestamp") or "") in window_days]

    # Classify by reason
    displacement_count = 0
    max_positions_count = 0
    capacity_count = 0
    by_reason: dict[str, int] = defaultdict(int)
    by_mode_strategy: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for r in blocked:
        reason = str(r.get("reason") or r.get("blocked_reason") or "unknown").lower()
        by_reason[reason] += 1
        mode = r.get("mode") or "UNKNOWN"
        strategy = r.get("strategy") or "UNKNOWN"
        key = f"{mode}:{strategy}"
        if "displacement" in reason:
            displacement_count += 1
            by_mode_strategy[key]["displacement"] += 1
        if "max_pos" in reason or "capacity" in reason:
            if "max_pos" in reason:
                max_positions_count += 1
                by_mode_strategy[key]["max_positions"] += 1
            if "capacity" in reason:
                capacity_count += 1
                by_mode_strategy[key]["capacity"] += 1

    # Optional: displacement events from system_events (subsystem=displacement)
    displacement_evaluated = 0
    displacement_allowed = 0
    if events_path.exists():
        events = _iter_jsonl(events_path)
        recent = [e for e in events if _day_utc(e.get("ts") or e.get("timestamp") or "") in window_days]
        for e in recent:
            if e.get("subsystem") == "displacement" and e.get("event_type") == "displacement_evaluated":
                displacement_evaluated += 1
                details = e.get("details") or {}
                if details.get("allowed") is True:
                    displacement_allowed += 1

    # Regime: current state only (no per-day history unless stockbot packs)
    regime_label = "UNKNOWN"
    try:
        regime_path = state_dir / "regime_posture_state.json"
        if regime_path.exists():
            data = json.loads(regime_path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(data, dict):
                regime_label = data.get("regime_label") or data.get("regime") or "UNKNOWN"
    except Exception:
        pass

    report = {
        "window_days": window_days[:5],
        "total_blocked": len(blocked),
        "displacement_blocked": displacement_count,
        "max_positions_reached": max_positions_count,
        "capacity_blocked": capacity_count,
        "by_reason": dict(by_reason),
        "by_mode_strategy": {k: dict(v) for k, v in sorted(by_mode_strategy.items())},
        "displacement_events": {"evaluated": displacement_evaluated, "allowed": displacement_allowed},
        "current_regime": regime_label,
    }

    md_lines = [
        "# Displacement & Capacity Diagnostic",
        f"Window: last {days_back} days",
        f"Total blocked: {report['total_blocked']}",
        f"Displacement blocked: {displacement_count}",
        f"Max positions reached: {max_positions_count}",
        f"Capacity blocked: {capacity_count}",
        f"Displacement events (evaluated / allowed): {displacement_evaluated} / {displacement_allowed}",
        f"Current regime (state): {regime_label}",
        "",
        "## By reason (sample)",
        "",
    ]
    for reason, count in sorted(by_reason.items(), key=lambda x: -x[1])[:15]:
        md_lines.append(f"- **{reason}** {count}")
    md_lines.append("")
    md_lines.append("## By mode:strategy")
    for key in sorted(by_mode_strategy.keys()):
        vals = by_mode_strategy[key]
        md_lines.append(f"- **{key}** displacement={vals.get('displacement', 0)} max_positions={vals.get('max_positions', 0)} capacity={vals.get('capacity', 0)}")

    print(json.dumps(report, indent=2))
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "displacement_capacity_diagnostic.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (args.out_dir / "displacement_capacity_diagnostic.md").write_text("\n".join(md_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
