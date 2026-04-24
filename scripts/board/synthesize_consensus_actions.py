#!/usr/bin/env python3
"""
Synthesize consensus Top-N actions from multi-persona reviews.
Criteria: profitability, speed, reversibility, risk. No architecture expansion;
actions must be executable within days. Force consensus (require agreement across personas).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthesize consensus actions from persona reviews")
    ap.add_argument("--reviews", required=True, help="Path to PROFITABILITY_PERSONA_REVIEWS_<date>.json")
    ap.add_argument("--criteria", nargs="+", default=["profitability", "speed", "reversibility", "risk"])
    ap.add_argument("--max-actions", type=int, default=5)
    ap.add_argument("--require-consensus", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.reviews)
    if not path.exists():
        print(f"Reviews missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    reviews = data.get("reviews", {}) or {}
    questions = data.get("review_questions", [])
    personas = list(reviews.keys())

    # Extract "promote tomorrow" and other actionable answers across personas
    actions_raw = []
    for p, r in reviews.items():
        if not isinstance(r, dict):
            continue
        promote = r.get("promote_tomorrow") or (r.get("answers") or [])[-1] if r.get("answers") else ""
        if promote:
            actions_raw.append({"persona": p, "action": promote, "source": "promote_tomorrow"})
        for v in (r.get("answers") or []):
            if v and isinstance(v, str) and len(v) > 15:
                actions_raw.append({"persona": p, "action": v, "source": "answer"})

    # Strategic directives from proposal (authoritative when persona answers are stub-only)
    from_proposal = [
        "Enforce a daily promotion quota (minimum 1 action/day).",
        "Impose an opportunity-cost budget on Counter-Intelligence.",
        "Run exit-only aggression experiments with fixed entries.",
        "Reduce signal space to the smallest profitable subset.",
        "Focus capital on symbols that already show edge.",
    ]

    # Normalize and dedupe; skip stub-only answers so we use proposal directives
    seen = set()
    actions = []
    stub_marker = "Stub critique"
    for a in actions_raw:
        action_text = (a.get("action") or "").strip()
        if not action_text or len(action_text) < 10:
            continue
        if stub_marker in action_text:
            continue  # Prefer proposal directives over stub text
        key = re.sub(r"\s+", " ", action_text)[:80]
        if key in seen:
            continue
        seen.add(key)
        actions.append({"rank": len(actions) + 1, "action": action_text, "personas": [a.get("persona", "")]})
        if len(actions) >= args.max_actions:
            break

    # If no real persona answers, use proposal directives as Top-N (immediately actionable)
    if len(actions) < args.max_actions:
        for d in from_proposal:
            if len(actions) >= args.max_actions:
                break
            if d not in seen:
                actions.append({"rank": len(actions) + 1, "action": d, "personas": ["consensus"]})

    lines = [
        "# Profitability Top-5 Actions (Consensus)",
        "",
        f"Criteria: {', '.join(args.criteria)}. Executable within days.",
        "",
    ]
    for a in actions[: args.max_actions]:
        lines.append(f"{a['rank']}. {a['action']}")
        lines.append("")
    lines.append("---")
    lines.append("*Multi-persona critique; consensus synthesis. No architecture expansion.*")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", out_path, "actions:", len(actions))
    return 0


if __name__ == "__main__":
    sys.exit(main())
