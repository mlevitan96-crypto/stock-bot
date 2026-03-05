#!/usr/bin/env python3
"""
Enforce CSA gate: if verdict is not PROCEED, require CSA_RISK_ACCEPTANCE_<mission-id>.md.
On failure write reports/audit/CSA_GATE_BLOCKER_<mission-id>.md and exit non-zero.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser(description="Enforce CSA gate before promotion")
    ap.add_argument("--mission-id", required=True, help="Mission identifier")
    ap.add_argument("--csa-verdict-json", required=True, help="Path to CSA_VERDICT_<mission-id>.json")
    ap.add_argument(
        "--require-override-for",
        nargs="+",
        default=["HOLD", "ESCALATE", "ROLLBACK"],
        help="Verdicts that require risk acceptance file (default: HOLD ESCALATE ROLLBACK)",
    )
    ap.add_argument("--base-dir", default="", help="Repo base dir (default: script repo)")
    args = ap.parse_args()

    base = Path(args.base_dir).resolve() if args.base_dir else REPO
    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    verdict_path = base / args.csa_verdict_json if not Path(args.csa_verdict_json).is_absolute() else Path(args.csa_verdict_json)
    if not verdict_path.exists():
        blocker_path = audit_dir / f"CSA_GATE_BLOCKER_{args.mission_id}.md"
        blocker_path.write_text(
            f"# CSA gate blocker\n\n**Mission ID:** {args.mission_id}\n\n"
            f"Verdict file not found: {verdict_path}\n\n"
            f"Generate with: run_chief_strategy_auditor.py --mission-id {args.mission_id} ...\n",
            encoding="utf-8",
        )
        print(f"CSA gate FAIL: verdict file not found: {verdict_path}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(verdict_path.read_text(encoding="utf-8"))
    except Exception as e:
        blocker_path = audit_dir / f"CSA_GATE_BLOCKER_{args.mission_id}.md"
        blocker_path.write_text(
            f"# CSA gate blocker\n\n**Mission ID:** {args.mission_id}\n\n"
            f"Verdict file invalid: {e}\n",
            encoding="utf-8",
        )
        print(f"CSA gate FAIL: invalid verdict JSON: {e}", file=sys.stderr)
        return 1

    verdict = (payload.get("verdict") or "").strip().upper()
    require_override = [v.strip().upper() for v in args.require_override_for]

    if verdict == "PROCEED":
        print("CSA gate: PROCEED — pass")
        return 0

    if verdict not in require_override:
        # Verdict is something else (e.g. typo); treat as blocking
        require_override = require_override + [verdict] if verdict else require_override

    risk_acceptance_path = audit_dir / f"CSA_RISK_ACCEPTANCE_{args.mission_id}.md"
    if risk_acceptance_path.exists():
        print(f"CSA gate: {verdict} — override present: {risk_acceptance_path}")
        return 0

    blocker_path = audit_dir / f"CSA_GATE_BLOCKER_{args.mission_id}.md"
    lines = [
        "# CSA gate blocker",
        "",
        f"**Mission ID:** {args.mission_id}",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "This verdict requires an explicit risk acceptance artifact before promotion.",
        "",
        "## Required",
        "",
        f"Create `reports/audit/CSA_RISK_ACCEPTANCE_{args.mission_id}.md` with:",
        "",
        "- CSA verdict summary (copy from CSA_FINDINGS or CSA_VERDICT)",
        "- What we are overriding (HOLD / ESCALATE / ROLLBACK)",
        "- Why override is justified now",
        "- Explicit risk accepted",
        "- Rollback plan + tripwires",
        "- Sign-off line (human)",
        "",
        "See docs/governance/CHIEF_STRATEGY_AUDITOR.md for template.",
        "",
    ]
    blocker_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"CSA gate FAIL: verdict={verdict} requires override; missing {risk_acceptance_path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
