#!/usr/bin/env python3
"""
Read decision_ledger.jsonl and generate:
1) blocked_attribution_summary.md  — counts by gate, gate+reason, dominant blocker, top blocked by score/counterfactual
2) score_distribution.md           — final score vs threshold, per-component, distance-to-threshold
3) top_50_blocked_examples.md      — 50 concrete blocked cases with full breakdown
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER_DIR = REPO / "reports" / "decision_ledger"
LEDGER_JSONL = LEDGER_DIR / "decision_ledger.jsonl"


def load_events() -> list[dict]:
    events = []
    if not LEDGER_JSONL.exists():
        return events
    for line in LEDGER_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def first_blocking_gate(gates: list) -> tuple[str, str] | None:
    """Return (gate_name, reason) for first gate with pass=False."""
    for g in gates or []:
        if g.get("pass") is False:
            return (g.get("gate_name", "unknown"), g.get("reason", "unknown"))
    return None


def write_blocked_attribution_summary(events: list[dict]) -> None:
    blocked = [e for e in events if e.get("candidate_status") == "BLOCKED"]
    gate_counts: Counter = Counter()
    gate_reason_counts: Counter = Counter()
    for e in blocked:
        fb = first_blocking_gate(e.get("gates", []))
        if fb:
            gate_name, reason = fb
            gate_counts[gate_name] += 1
            gate_reason_counts[f"{gate_name}:{reason}"] += 1
    # Top blocked by score_final descending (counterfactual / replay pnl not in ledger yet)
    top_blocked_by_score = sorted(blocked, key=lambda x: float(x.get("score_final") or 0), reverse=True)[:20]

    lines = [
        "# Blocked attribution summary",
        "",
        "## Counts by gate (first failing gate)",
        "| Gate | Count |",
        "|------|-------|",
    ]
    for gate, count in gate_counts.most_common():
        lines.append(f"| {gate} | {count} |")
    if not gate_counts:
        lines.append("| (none) | 0 |")

    lines.extend([
        "",
        "## Counts by gate + reason",
        "| Gate:Reason | Count |",
        "|-------------|-------|",
    ])
    for gr, count in gate_reason_counts.most_common():
        lines.append(f"| {gr} | {count} |")
    if not gate_reason_counts:
        lines.append("| (none) | 0 |")

    lines.extend([
        "",
        "## Dominant blocker ranking",
    ])
    if gate_reason_counts:
        lines.append(f"1. **{gate_reason_counts.most_common(1)[0][0]}** ({gate_reason_counts.most_common(1)[0][1]} blocks)")
        for i, (gr, c) in enumerate(gate_reason_counts.most_common(5)[1:], 2):
            lines.append(f"{i}. {gr} ({c} blocks)")
    else:
        lines.append("(No blocked events with gate verdicts in ledger)")

    lines.extend([
        "",
        "## Top blocked candidates (by score_final descending)",
        "| Symbol | score_final | First blocker |",
        "|--------|-------------|---------------|",
    ])
    for e in top_blocked_by_score:
        sf = e.get("score_final", 0)
        fb = first_blocking_gate(e.get("gates", []))
        bl = f"{fb[0]}:{fb[1]}" if fb else "—"
        lines.append(f"| {e.get('symbol', '')} | {sf} | {bl} |")
    if not top_blocked_by_score:
        lines.append("| (none) | - | - |")

    out = LEDGER_DIR / "blocked_attribution_summary.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


def write_score_distribution(events: list[dict]) -> None:
    scores = [float(e.get("score_final") or 0) for e in events]
    thresholds_used = []
    for e in events:
        t = e.get("thresholds") or {}
        if isinstance(t.get("expectancy_floor"), (int, float)):
            thresholds_used.append(float(t["expectancy_floor"]))
        if isinstance(t.get("min_exec_score"), (int, float)):
            thresholds_used.append(float(t["min_exec_score"]))
    min_exec = min(thresholds_used) if thresholds_used else 2.5
    distances = [s - min_exec for s in scores]

    lines = [
        "# Score distribution",
        "",
        "## Final score vs threshold(s)",
        f"- Events: {len(events)}",
        f"- Score min: {min(scores) if scores else 0:.3f}",
        f"- Score max: {max(scores) if scores else 0:.3f}",
        f"- Score mean: {sum(scores)/len(scores) if scores else 0:.3f}",
        f"- Threshold (min_exec/expectancy_floor) used: {min_exec:.3f}",
        "",
        "## Distance to threshold",
        f"- Mean distance (score - threshold): {sum(distances)/len(distances) if distances else 0:.3f}",
        f"- Min distance: {min(distances) if distances else 0:.3f}",
        f"- Max distance: {max(distances) if distances else 0:.3f}",
        "",
        "## Per-component (sample from first event)",
    ]
    if events and events[0].get("score_components"):
        comp = events[0]["score_components"]
        for k, v in list(comp.items())[:15]:
            lines.append(f"- {k}: {v}")
    else:
        lines.append("(No score_components in ledger)")

    out = LEDGER_DIR / "score_distribution.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


def write_top_50_blocked_examples(events: list[dict]) -> None:
    blocked = [e for e in events if e.get("candidate_status") == "BLOCKED"]
    top50 = sorted(blocked, key=lambda x: float(x.get("score_final") or 0), reverse=True)[:50]

    lines = [
        "# Top 50 blocked examples",
        "",
        "Each section: raw signals, features, component scores + weights, final score vs threshold, gate verdicts (with measured values), order intent (if any).",
        "",
    ]
    for i, e in enumerate(top50, 1):
        lines.append(f"## Example {i}: {e.get('symbol', '')} (score_final={e.get('score_final')})")
        lines.append("")
        lines.append("### Signal raw")
        lines.append("```json")
        lines.append(json.dumps(e.get("signal_raw") or {}, indent=2, default=str)[:800])
        lines.append("```")
        lines.append("")
        lines.append("### Features")
        lines.append("```json")
        lines.append(json.dumps(e.get("features") or {}, indent=2, default=str)[:500])
        lines.append("```")
        lines.append("")
        lines.append("### Score components + weights")
        lines.append("```json")
        lines.append(json.dumps(e.get("score_components") or {}, indent=2, default=str)[:1200])
        lines.append("```")
        lines.append("")
        lines.append(f"### Final score vs threshold: {e.get('score_final')} | thresholds: {e.get('thresholds')}")
        lines.append("")
        lines.append("### Gate verdicts")
        for g in e.get("gates", []):
            lines.append(f"- **{g.get('gate_name')}**: pass={g.get('pass')}, reason={g.get('reason')}, params={g.get('params')}, measured={g.get('measured')}")
        lines.append("")
        lines.append("### Order intent")
        lines.append(str(e.get("order_intent")))
        lines.append("")
    if len(top50) < 50:
        lines.append(f"(Only {len(top50)} blocked examples in ledger)")
    out = LEDGER_DIR / "top_50_blocked_examples.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


def main() -> int:
    events = load_events()
    if not events:
        print("No events in decision_ledger.jsonl; run run_decision_ledger_capture.py first.", file=sys.stderr)
        LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    write_blocked_attribution_summary(events)
    write_score_distribution(events)
    write_top_50_blocked_examples(events)
    # Final report (first ~80 lines of blocked_attribution_summary, single most common gate+reason, top 3 distance stats)
    summary_path = LEDGER_DIR / "blocked_attribution_summary.md"
    dist_path = LEDGER_DIR / "score_distribution.md"
    if summary_path.exists():
        lines = summary_path.read_text(encoding="utf-8").splitlines()
        for line in lines[:80]:
            print(line)
    gate_reason_counts = Counter()
    for e in events:
        if e.get("candidate_status") != "BLOCKED":
            continue
        fb = first_blocking_gate(e.get("gates", []))
        if fb:
            gate_reason_counts[f"{fb[0]}:{fb[1]}"] += 1
    if gate_reason_counts:
        print("\n# Single most common gate+reason:", gate_reason_counts.most_common(1)[0][0])
    else:
        print("\n# Single most common gate+reason: (no blocked events)")
    if dist_path.exists():
        text = dist_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "distance" in line.lower() or "Distance" in line:
                print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
