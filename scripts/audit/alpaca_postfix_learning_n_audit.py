#!/usr/bin/env python3
"""
Postfix learning-only audit: evaluate strict completeness for the last N closes
with exit_attribution.timestamp strictly after --deploy-floor-ts.

Uses postfix_allow_intent_blocker=True (LIVE OK or explicit MISSING_INTENT_BLOCKER counts as live truth).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _ts_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--deploy-floor-ts", type=float, required=True, dest="deploy_floor_ts")
    ap.add_argument("--n", type=int, default=5, dest="n")
    ap.add_argument("--write-md", type=Path, default=None, help="Output markdown path")
    ap.add_argument("--open-ts-epoch", type=float, default=0.0, help="Exit window floor (use 0 for postfix-only)")
    args = ap.parse_args()

    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    r = evaluate_completeness(
        args.root.resolve(),
        open_ts_epoch=args.open_ts_epoch,
        audit=True,
        collect_complete_trade_ids=True,
        min_exit_ts_epoch=args.deploy_floor_ts,
        recent_closes_limit=args.n,
        postfix_allow_intent_blocker=True,
    )
    payload = json.dumps(r, indent=2, default=str)
    print(payload)

    if args.write_md:
        args.write_md.parent.mkdir(parents=True, exist_ok=True)
        ids = r.get("complete_trade_ids") or []
        lines = [
            f"# Alpaca postfix learning-only audit (last {args.n} closes)",
            "",
            f"- **UTC generated:** {datetime.now(timezone.utc).isoformat()}",
            f"- **deploy_floor_ts:** `{args.deploy_floor_ts}`",
            f"- **LEARNING_STATUS:** `{r.get('LEARNING_STATUS')}`",
            f"- **trades_seen (postfix window):** {r.get('trades_seen')}",
            f"- **trades_complete:** {r.get('trades_complete')}",
            f"- **trades_incomplete:** {r.get('trades_incomplete')}",
            f"- **postfix_insufficient_closes:** {r.get('postfix_insufficient_closes')}",
            f"- **learning_fail_closed_reason:** `{r.get('learning_fail_closed_reason')}`",
            "",
            "## complete_trade_ids",
            "",
        ]
        for tid in ids:
            lines.append(f"- `{tid}`")
        lines.extend(["", "## reason_histogram", "", "```json", json.dumps(r.get("reason_histogram"), indent=2), "```", ""])
        lines.extend(["## full_json", "", "```json", payload, "```", ""])
        args.write_md.write_text("\n".join(lines), encoding="utf-8")

    ok = (
        r.get("LEARNING_STATUS") == "ARMED"
        and not r.get("postfix_insufficient_closes")
        and r.get("trades_seen") == args.n
        and r.get("trades_complete") == args.n
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
