#!/usr/bin/env python3
"""
Enrich counter-intel events so CI explains itself: couple to entry/exit signals,
blocked signal ids/weights, risk reason, and would_have_pnl.
Output: COUNTER_INTEL_ENRICHED_<date>.json for semantics assert and impact analysis.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Enrich counter-intel events with required semantic fields")
    ap.add_argument("--ledger", required=True, help="Path to FULL_TRADE_LEDGER_<date>.json")
    ap.add_argument("--require-fields", nargs="+", default=[
        "blocked_signal_ids", "blocked_signal_weights", "exit_signal_state",
        "risk_reason", "would_have_pnl",
    ])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.ledger)
    if not path.exists():
        print(f"Ledger missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    raw_events = list(data.get("counter_intel", []) or [])
    if not raw_events:
        # Use synthetic from emit if present; else one placeholder event
        raw_events = [{
            "symbol": "_governance",
            "decision": "counter_intel_emitted",
            "reason_codes": ["mandatory_ci_emit"],
            "source": "synthetic",
        }]

    required = set(args.require_fields or [])
    enriched = []
    for e in raw_events:
        if not isinstance(e, dict):
            continue
        out = dict(e)
        # Couple to entry + exit signals (derive or placeholder)
        out.setdefault("blocked_signal_ids", out.get("reason_codes") or ["unknown"])
        out.setdefault("blocked_signal_weights", {})
        if isinstance(out.get("blocked_signal_ids"), list) and not out.get("blocked_signal_weights"):
            out["blocked_signal_weights"] = {str(k): None for k in out["blocked_signal_ids"]}
        out.setdefault("exit_signal_state", {"exit_reason": out.get("reason_codes", [None])[0], "decay": None})
        out.setdefault("risk_reason", out.get("block_reason") or (out.get("reason_codes") or [None])[0] or "ci_block")
        out.setdefault("would_have_pnl", None)
        # Ensure explanation when field is missing/empty for semantics assert
        out.setdefault("_explanation", "Enriched from ledger; would_have_pnl requires shadow comparison.")
        for k in required:
            if k not in out:
                out[k] = None
                out["_explanation"] = (out.get("_explanation") or "") + f" {k}=placeholder."
        enriched.append(out)

    payload = {
        "date": data.get("date"),
        "events": enriched,
        "count": len(enriched),
        "required_fields": list(required),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, "events:", len(enriched))
    return 0


if __name__ == "__main__":
    sys.exit(main())
