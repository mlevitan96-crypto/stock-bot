#!/usr/bin/env python3
"""
Read-only Alpaca SRE sanity: strict gate summary + last N entry_decision_made snippets.
Run on droplet: cd /root/stock-bot && python3 scripts/_alpaca_sre_sanity_probe.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("STOCKBOT_ROOT", str(Path(__file__).resolve().parents[1]))).resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START, evaluate_completeness

    r = evaluate_completeness(ROOT, open_ts_epoch=STRICT_EPOCH_START, audit=False)
    summary = {
        "STRICT_EPOCH_START": STRICT_EPOCH_START,
        "LEARNING_STATUS": r.get("LEARNING_STATUS"),
        "trades_seen": r.get("trades_seen"),
        "trades_complete": r.get("trades_complete"),
        "trades_incomplete": r.get("trades_incomplete"),
        "forward_trades_seen": r.get("forward_trades_seen"),
        "forward_trades_complete": r.get("forward_trades_complete"),
        "learning_fail_closed_reason": r.get("learning_fail_closed_reason"),
        "precheck": r.get("precheck"),
    }
    print("=== STRICT_COMPLETENESS ===")
    print(json.dumps(summary, indent=2, default=str))

    logs = ROOT / "logs"
    run_paths = [logs / "run.jsonl", logs / "strict_backfill_run.jsonl"]
    edm: list[dict] = []
    for p in run_paths:
        if not p.is_file():
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for ln in lines:
            if not ln.strip():
                continue
            try:
                o = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if o.get("event_type") == "entry_decision_made":
                edm.append(o)
    last5 = edm[-5:]
    print("\n=== LAST_5_ENTRY_DECISION_MADE (run + strict_backfill_run) ===")
    for i, o in enumerate(last5, 1):
        sym = o.get("symbol")
        tid = o.get("trade_id")
        st = o.get("entry_intent_status")
        comps = o.get("entry_score_components") or {}
        ncomp = len(comps) if isinstance(comps, dict) else 0
        trace = o.get("signal_trace") or o.get("intelligence_trace")
        layers = None
        if isinstance(trace, dict):
            layers = trace.get("signal_layers")
        print(
            json.dumps(
                {
                    "i": i,
                    "symbol": sym,
                    "trade_id": tid,
                    "entry_intent_status": st,
                    "entry_score_total": o.get("entry_score_total"),
                    "n_entry_score_components": ncomp,
                    "has_signal_trace": bool(trace),
                    "has_signal_layers": bool(layers),
                    "sample_component_keys": list(comps.keys())[:12] if isinstance(comps, dict) else [],
                },
                default=str,
            )
        )

    # Last EDM full snippet (keys only + score) for SRE
    if edm:
        o = edm[-1]
        print("\n=== LAST_ENTRY_DECISION_MADE_KEYS ===")
        print(json.dumps(sorted(o.keys()), indent=0, default=str))
        st = o.get("signal_trace") or {}
        print("signal_trace_keys", sorted(st.keys()) if isinstance(st, dict) else None)

    # Scan run.jsonl tail for EDM score distribution (last 200 EDM rows)
    run_only = logs / "run.jsonl"
    scores: list[float] = []
    if run_only.is_file():
        try:
            for ln in run_only.read_text(encoding="utf-8", errors="replace").splitlines():
                if not ln.strip():
                    continue
                try:
                    o = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if o.get("event_type") != "entry_decision_made":
                    continue
                v = o.get("entry_score_total")
                if isinstance(v, (int, float)):
                    scores.append(float(v))
        except OSError:
            pass
    tail_scores = scores[-200:] if len(scores) > 200 else scores
    nz = sum(1 for x in tail_scores if x and x != 0.0)
    print("\n=== EDM_ENTRY_SCORE_TOTAL_LAST_UP_TO_200 ===")
    print(json.dumps({"n": len(tail_scores), "nonzero_count": nz, "last_5": tail_scores[-5:]}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
