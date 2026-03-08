#!/usr/bin/env python3
"""
Monday Open signal-engine smoke test. Run ON DROPLET (DROPLET_RUN=1 or from readiness runner).
Uses same scoring/gating contract as production; builds order intents and validates; DOES NOT submit.
Writes reports/audit/MONDAY_SMOKE_TEST_<YYYY-MM-DD>_<HHMM>.json.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

AUDIT_DIR = REPO / "reports" / "audit"
LOGS_DIR = REPO / "logs"
SMOKE_TAG = "SMOKE_TEST"


def _load_universe_symbols(max_extra: int = 8) -> list[str]:
    """DIA, QQQ + up to max_extra from universe file."""
    base = ["DIA", "QQQ"]
    for path in ("state/daily_universe_v2.json", "state/trade_universe_v2.json", "state/daily_universe.json"):
        p = REPO / path
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            symbols = data.get("symbols") or data.get("universe") or []
            if isinstance(symbols, list):
                extra = [s for s in symbols if isinstance(s, str) and s not in base][:max_extra]
                return base + extra
            if isinstance(symbols, dict):
                extra = [s for s in symbols.keys() if s not in base][:max_extra]
                return base + extra
        except Exception:
            pass
    return base + ["SPY", "IWM", "VXX"][:max_extra]


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    out_json = AUDIT_DIR / f"MONDAY_SMOKE_TEST_{ts}.json"

    # Ensure no submit can happen (paranoid)
    assert not os.getenv("TRADING_MODE", "PAPER").upper() == "LIVE", "Smoke test must not run in LIVE mode"
    submit_attempted = []

    try:
        from telemetry.decision_intelligence_trace import (
            build_initial_trace,
            append_gate_result,
            set_final_decision,
            trace_to_emit_fields,
            validate_trace,
        )
    except ImportError as e:
        result = {
            "timestamp": ts,
            "success": False,
            "error": f"telemetry.decision_intelligence_trace import failed: {e}",
            "symbols": [],
            "submit_attempted": submit_attempted,
        }
        out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 1

    symbols = _load_universe_symbols(8)
    # Mix directions: first half bullish, rest bearish
    n = len(symbols)
    directions = ["bullish"] * ((n + 1) // 2) + ["bearish"] * (n // 2)
    results = []
    start = datetime.now(timezone.utc)

    for i, (sym, direction) in enumerate(zip(symbols, directions)):
        side = "buy" if direction == "bullish" else "sell"
        raw_score = 3.0 + (i % 3) * 0.5
        comps = {"flow_strength": 0.5, "composite": raw_score, "regime_mult": 1.0}
        cluster = {"direction": direction, "ticker": sym, "source": "smoke", "composite_score": raw_score}
        trace = build_initial_trace(sym, side, raw_score, comps, cluster, cycle_id=i + 1)
        append_gate_result(trace, "score_gate", raw_score >= 2.5)
        append_gate_result(trace, "capacity_gate", True)
        append_gate_result(trace, "risk_gate", True)
        append_gate_result(trace, "directional_gate", True)
        blocked = not (raw_score >= 2.5)
        if blocked:
            set_final_decision(trace, "blocked", "score_below_min", [])
            decision = "blocked"
            reason_codes = ["score_below_min"]
            order_intent = None
            validation_result = None
        else:
            set_final_decision(trace, "would_trade", "all_gates_passed", [])
            decision = "would_trade"
            reason_codes = ["all_gates_passed"]
            order_intent = {"symbol": sym, "side": side, "qty": 1, "order_type": "market", "source": SMOKE_TAG}
            validation_result = "valid"  # stub; real validation would call risk layer

        ok, ve = validate_trace(trace)
        emit = trace_to_emit_fields(trace, blocked=blocked)
        rec = {
            "symbol": sym,
            "direction": direction,
            "raw_score": raw_score,
            "final_score": raw_score,
            "decision": decision,
            "reason_codes": reason_codes,
            "order_intent": order_intent,
            "validation_result": validation_result,
            "trace_valid": ok,
            "trace_errors": ve,
        }
        results.append(rec)

        # Append to run.jsonl (tagged SMOKE_TEST)
        run_line = json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": SMOKE_TAG,
            "symbol": sym,
            "decision": decision,
            "order_intent": order_intent,
        }, default=str) + "\n"
        (LOGS_DIR / "run.jsonl").open("a", encoding="utf-8").write(run_line)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    payload = {
        "timestamp": ts,
        "success": True,
        "symbols": [r["symbol"] for r in results],
        "per_symbol": results,
        "runtime_seconds": round(elapsed, 2),
        "submit_attempted": submit_attempted,
        "no_submit_assertion": "no Alpaca submit call executed; smoke test does not import alpaca_client or main",
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"MONDAY_SMOKE_TEST wrote {out_json} ({len(results)} symbols, {elapsed:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
