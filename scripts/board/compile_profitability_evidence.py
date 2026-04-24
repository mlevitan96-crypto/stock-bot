#!/usr/bin/env python3
"""
Compile a single evidence snapshot for profitability decision collaboration.
Aggregates ledger, CI impact, signal profitability, and Top-5 actions into one markdown.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Compile profitability evidence snapshot")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--ci-impact", default=None, help="Optional CSA_COUNTER_INTEL_IMPACT_<date>.json")
    ap.add_argument("--signal-profitability", default=None, help="Optional SIGNAL_PROFITABILITY_<date>.json")
    ap.add_argument("--top-actions", default=None, help="Optional PROFITABILITY_TOP_5_ACTIONS_<date>.md")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        print(f"Ledger missing: {ledger_path}", file=sys.stderr)
        return 2

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    executed = ledger.get("executed", []) or []
    blocked = ledger.get("blocked", []) or []
    counter_intel = ledger.get("counter_intel", []) or []
    summary = ledger.get("summary", {}) or {}

    lines = [
        "# Profitability Evidence Snapshot",
        "",
        f"**Date:** {ledger.get('date', 'N/A')}",
        "",
        "## Ledger",
        f"- Executed: {len(executed)}",
        f"- Blocked: {len(blocked)}",
        f"- Counter-intel: {len(counter_intel)}",
        f"- Summary: {summary}",
        "",
    ]

    if args.ci_impact and Path(args.ci_impact).exists():
        ci = json.loads(Path(args.ci_impact).read_text(encoding="utf-8"))
        lines.extend([
            "## Counter-Intel Impact",
            f"- Opportunity cost (USD): {ci.get('opportunity_cost_usd')}",
            f"- Event count: {ci.get('event_count')}",
            f"- Summary: {ci.get('summary', {})}",
            "",
        ])

    if args.signal_profitability and Path(args.signal_profitability).exists():
        sig = json.loads(Path(args.signal_profitability).read_text(encoding="utf-8"))
        lines.extend([
            "## Signal Profitability",
            f"- Sweep count: {sig.get('sweep_count')}",
            f"- Has non-zero delta: {sig.get('has_nonzero_delta')}",
            "",
        ])

    if args.top_actions and Path(args.top_actions).exists():
        top = Path(args.top_actions).read_text(encoding="utf-8")
        lines.extend([
            "## Top-5 Actions (Consensus)",
            "",
            top.strip(),
            "",
        ])

    lines.append("---")
    lines.append("*Evidence for single-path decision; executable within 48–72 hours.*")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
