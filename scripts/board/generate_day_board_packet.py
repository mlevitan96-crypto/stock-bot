#!/usr/bin/env python3
"""
Generate day trading intelligence board packet (markdown).
Aggregates ledger, decision quality, signal profitability, scorecard, CSA verdict.
CSA + SRE + multi-persona governance.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate day board packet")
    ap.add_argument("--date", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--decision-quality", required=True)
    ap.add_argument("--signal-profitability", required=True)
    ap.add_argument("--scorecard", required=True)
    ap.add_argument("--verdict", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    paths = {
        "ledger": Path(args.ledger),
        "dq": Path(args.decision_quality),
        "sig": Path(args.signal_profitability),
        "scorecard": Path(args.scorecard),
        "verdict": Path(args.verdict),
    }
    for name, p in paths.items():
        if not p.exists():
            print(f"Missing {name}: {p}", file=sys.stderr)
            return 2

    ledger = json.loads(paths["ledger"].read_text(encoding="utf-8"))
    dq = json.loads(paths["dq"].read_text(encoding="utf-8"))
    sig = json.loads(paths["sig"].read_text(encoding="utf-8"))
    scorecard = json.loads(paths["scorecard"].read_text(encoding="utf-8"))
    verdict = json.loads(paths["verdict"].read_text(encoding="utf-8"))

    lines = [
        "# Day Trading Intelligence Board Packet",
        f"**Date:** {args.date}",
        "",
        "## Governance",
        f"- **CSA verdict:** {verdict.get('verdict', 'N/A')}",
        f"- **SRE:** {verdict.get('sre_verdict', 'N/A')}",
        f"- **Blockers:** {verdict.get('blockers', [])}",
        "",
        "## Ledger summary",
        f"- Executed: {len(ledger.get('executed') or [])}",
        f"- Blocked: {len(ledger.get('blocked') or [])}",
        f"- Counter-intel: {len(ledger.get('counter_intel') or [])}",
        "",
        "## Decision quality",
        f"- Blocks classified: {list(dq.get('blocks_classified') or {})[:10]}...",
        f"- Executed PnL sum: {dq.get('executed_pnl_sum')}",
        "",
        "## Signal profitability",
        f"- Sweep count: {sig.get('sweep_count')}",
        f"- Profitability entries: {len(sig.get('profitability') or [])}",
        "",
        "## Scorecard",
        f"- Ideas scored: {scorecard.get('count')}",
        f"- Dimensions: {scorecard.get('dimensions')}",
        "",
        "---",
        "*CSA + SRE + multi-persona; SHADOW-ONLY | FAIL-CLOSED*",
    ]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
