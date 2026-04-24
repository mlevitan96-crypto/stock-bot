#!/usr/bin/env python3
"""
CSA: Render promotion verdict from ledger, scorecard, SRE health.
FAIL-CLOSED: require SRE PASS and optional counter-intel gate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="CSA promotion verdict")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--scorecard", required=True)
    ap.add_argument("--sre-health", required=True)
    ap.add_argument("--require-counter-intel", action="store_true")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    scorecard_path = Path(args.scorecard)
    sre_path = Path(args.sre_health)
    if not ledger_path.exists():
        print(f"Ledger missing: {ledger_path}", file=sys.stderr)
        return 2
    if not scorecard_path.exists():
        print(f"Scorecard missing: {scorecard_path}", file=sys.stderr)
        return 2
    if not sre_path.exists():
        print(f"SRE health missing: {sre_path}", file=sys.stderr)
        return 2

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    sre = json.loads(sre_path.read_text(encoding="utf-8"))

    verdict = "PASS"
    blockers = []

    if sre.get("verdict") != "PASS":
        verdict = "FAIL"
        blockers.append("SRE_DAY_HEALTH not PASS")

    if args.require_counter_intel:
        n_ci = len(ledger.get("counter_intel") or [])
        if n_ci < 1:
            verdict = "FAIL"
            blockers.append("require_counter_intel: no counter-intel events")

    out = {
        "date": ledger.get("date"),
        "verdict": verdict,
        "blockers": blockers,
        "sre_verdict": sre.get("verdict"),
        "scorecard_ideas_count": len(scorecard.get("ideas") or scorecard.get("scores") or []),
        "notes": ["CSA + SRE; fail-closed on SRE and optional counter-intel."],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("CSA_VERDICT:", verdict, *blockers if blockers else [])
    return 3 if verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
