#!/usr/bin/env python3
"""
CSA: Assert counter-intel semantic completeness.
FAIL-CLOSED: when --fail-on-missing-explanations, exit non-zero if any event
is missing required explanation for absent/missing fields.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert CI semantic completeness")
    ap.add_argument("--counter-intel", required=True, help="Path to COUNTER_INTEL_ENRICHED_<date>.json")
    ap.add_argument("--fail-on-missing-explanations", action="store_true", default=True)
    args = ap.parse_args()

    path = Path(args.counter_intel)
    if not path.exists():
        print(f"Counter-intel file missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    events = data.get("events", []) or []
    required_fields = set(data.get("required_fields", []) or [
        "blocked_signal_ids", "blocked_signal_weights", "exit_signal_state",
        "risk_reason", "would_have_pnl",
    ])

    missing_explanations = []
    for i, e in enumerate(events):
        if not isinstance(e, dict):
            missing_explanations.append((i, "event not a dict"))
            continue
        has_explanation = (e.get("_explanation") or "").strip()
        missing = [f for f in required_fields if e.get(f) is None or (isinstance(e.get(f), (list, dict)) and len(e.get(f) or []) == 0)]
        if missing and args.fail_on_missing_explanations and not has_explanation:
            missing_explanations.append((i, f"missing fields {missing} and no _explanation"))

    if missing_explanations:
        for idx, msg in missing_explanations:
            print(f"CI_SEMANTICS: event {idx} — {msg}", file=sys.stderr)
        print("CI_SEMANTICS: FAIL (missing explanations)", file=sys.stderr)
        return 3
    print("CI_SEMANTICS: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
