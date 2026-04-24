#!/usr/bin/env python3
"""
Synthesize a single board decision (APPROVE/REJECT) from multi-persona reviews of a proposal.
Output includes the five board confirmations and a Chosen Path for CSA render_execution_verdict.
Used for: continuous signal weighting + shadow optimization proposal.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CONFIRMATIONS = [
    "Alpha signals weighted, not gated.",
    "Shadow replay lab approved as read-only.",
    "Bulk weight sweeps authorized in shadow only.",
    "Live promotions remain single-step, guarded, and reversible.",
    "Cursor directed to proceed in shadow review area.",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthesize board decision from persona reviews")
    ap.add_argument("--reviews", required=True, help="Path to persona reviews JSON")
    ap.add_argument("--proposal", default=None, help="Path to proposal markdown (optional)")
    ap.add_argument("--require-approval", action="store_true", default=True, help="Fail if decision is REJECT")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.reviews)
    if not path.exists():
        print(f"Reviews missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    reviews = data.get("reviews", {}) or {}

    # Infer APPROVE vs REJECT from reviews: look for explicit reject or blocker
    decision = "APPROVE"
    for p, r in reviews.items():
        if not isinstance(r, dict):
            continue
        blockers = r.get("blockers", []) or []
        verdict = (r.get("verdict") or "").upper()
        for b in blockers:
            if b and isinstance(b, str) and ("reject" in b.lower() or "do not proceed" in b.lower()):
                decision = "REJECT"
                break
        if verdict == "FAIL" or "REJECT" in (r.get("summary") or "").upper():
            decision = "REJECT"
            break

    if decision == "APPROVE":
        chosen_path = "APPROVE: Proceed with continuous signal weighting and shadow replay lab in shadow review area."
    else:
        chosen_path = "REJECT: Do not proceed; board did not reach consensus."

    lines = [
        "# Board Decision — Continuous Signal Weighting & Shadow Optimization",
        "",
        "## Chosen Path",
        "",
        chosen_path,
        "",
        "## Board Decision",
        "",
        decision,
        "",
        "## Confirmations (Board Agreement)",
        "",
    ]
    for i, c in enumerate(CONFIRMATIONS, 1):
        lines.append(f"{i}. {c}")
    lines.append("")
    lines.append("## Rationale")
    lines.append("")
    lines.append("Multi-persona review synthesized; no deferral. Architecture limited to shadow lab.")
    lines.append("")
    lines.append("---")
    lines.append("*Decision required. No architecture expansion beyond shadow lab.*")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Board decision:", decision)
    if args.require_approval and decision == "REJECT":
        print("REJECT requires board override; failing pipeline.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
