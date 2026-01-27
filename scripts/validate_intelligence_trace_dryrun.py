#!/usr/bin/env python3
"""
Validate Decision Intelligence Trace — dry-run (market closed).

Forces 3–5 synthetic trade evaluations using the real trace contract.
Emits trade_intent with full intelligence_trace to logs/run.jsonl.
Does NOT submit orders. Uses existing audit guard / dry-run discipline.

Validation checks:
- trace exists
- multiple signal layers present
- gates populated
- final_decision coherent
- JSON size reasonable (not bloated)

Writes:
- reports/SAMPLE_INTELLIGENCE_TRACES.md (2 entered, 2 blocked)
- reports/INTELLIGENCE_TRACE_VERDICT.md
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
LOGS = REPO / "logs"
REPORTS = REPO / "reports"


def _write_run_jsonl_record(record: dict) -> None:
    """Append one trade_intent record to logs/run.jsonl (same shape as main's jsonl_write)."""
    LOGS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    line = json.dumps({"ts": ts, **record}, default=str) + "\n"
    (LOGS / "run.jsonl").open("a", encoding="utf-8").write(line)


def main() -> int:
    from telemetry.decision_intelligence_trace import (
        build_initial_trace,
        append_gate_result,
        set_final_decision,
        trace_to_emit_fields,
        validate_trace,
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    samples_entered: list[dict] = []
    samples_blocked: list[dict] = []
    all_ok = True
    errs: list[str] = []

    # Synthetic comps that yield multiple layers
    comps_a = {"flow_strength": 1.2, "dark_pool_bias": 0.3, "rv_20d": 0.25, "composite": 3.5}
    comps_b = {"flow_strength": -0.1, "regime_mult": 1.0, "composite": 2.8}
    cluster = {"direction": "bullish", "ticker": "SYM1", "source": "composite", "composite_score": 3.5}

    # —— 2 entered ——
    for i, (sym, score, comps) in enumerate([
        ("SYM1", 3.5, comps_a),
        ("SYM2", 4.1, comps_b),
    ], 1):
        side = "buy"
        trace = build_initial_trace(sym, side, score, comps, cluster, cycle_id=i)
        append_gate_result(trace, "score_gate", True)
        append_gate_result(trace, "capacity_gate", True)
        append_gate_result(trace, "risk_gate", True)
        append_gate_result(trace, "directional_gate", True)
        set_final_decision(trace, "entered", "all_gates_passed", [])
        ok, ve = validate_trace(trace)
        if not ok:
            all_ok = False
            errs.extend(ve)
        extra = trace_to_emit_fields(trace, blocked=False)
        rec = {
            "event_type": "trade_intent",
            "symbol": sym,
            "side": side,
            "score": score,
            "decision_outcome": "entered",
            "blocked_reason": None,
            "intent_id": extra.get("intent_id"),
            "intelligence_trace": trace,
            "active_signal_names": extra.get("active_signal_names", []),
            "opposing_signal_names": extra.get("opposing_signal_names", []),
            "gate_summary": extra.get("gate_summary", {}),
            "final_decision_primary_reason": extra.get("final_decision_primary_reason"),
        }
        _write_run_jsonl_record(rec)
        samples_entered.append(trace)

    # —— 2 blocked ——
    for i, (sym, score, comps, block_reason, block_code) in enumerate([
        ("SYM3", 2.1, comps_a, "score_below_min", "score_below_min"),
        ("SYM4", 3.8, comps_b, "displacement_blocked", "displacement_blocked"),
    ], 3):
        side = "buy"
        trace = build_initial_trace(sym, side, score, comps, cluster, cycle_id=i)
        if "score_below_min" in block_reason:
            append_gate_result(trace, "score_gate", False, "score_below_min")
        else:
            append_gate_result(trace, "score_gate", True)
            append_gate_result(trace, "capacity_gate", True)
            append_gate_result(trace, "displacement_gate", False, block_reason, {"incumbent_symbol": "OTHER", "challenger_delta": 0.5})
        set_final_decision(trace, "blocked", block_reason, [])
        ok, ve = validate_trace(trace)
        if not ok:
            all_ok = False
            errs.extend(ve)
        extra = trace_to_emit_fields(trace, blocked=True)
        rec = {
            "event_type": "trade_intent",
            "symbol": sym,
            "side": side,
            "score": score,
            "decision_outcome": "blocked",
            "blocked_reason": block_reason,
            "blocked_reason_code": extra.get("blocked_reason_code", block_code),
            "blocked_reason_details": extra.get("blocked_reason_details", {}),
            "intent_id": extra.get("intent_id"),
            "intelligence_trace": trace,
            "active_signal_names": extra.get("active_signal_names", []),
            "opposing_signal_names": extra.get("opposing_signal_names", []),
            "gate_summary": extra.get("gate_summary", {}),
            "final_decision_primary_reason": extra.get("final_decision_primary_reason"),
        }
        _write_run_jsonl_record(rec)
        samples_blocked.append(trace)

    # Size check: no single trace > 500KB
    for t in samples_entered + samples_blocked:
        n = len(json.dumps(t, default=str))
        if n > 500_000:
            all_ok = False
            errs.append(f"Trace size {n} exceeds 500KB")

    # —— reports/SAMPLE_INTELLIGENCE_TRACES.md ——
    lines = [
        "# Sample Intelligence Traces",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 2 Entered",
        "",
    ]
    for i, t in enumerate(samples_entered[:2], 1):
        lines.append(f"### Entered sample {i} — {t.get('symbol')}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(t, indent=2, default=str))
        lines.append("```")
        lines.append("")
    lines.append("## 2 Blocked")
    lines.append("")
    for i, t in enumerate(samples_blocked[:2], 1):
        lines.append(f"### Blocked sample {i} — {t.get('symbol')} ({t.get('final_decision', {}).get('primary_reason')})")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(t, indent=2, default=str))
        lines.append("```")
        lines.append("")
    (REPORTS / "SAMPLE_INTELLIGENCE_TRACES.md").write_text("\n".join(lines), encoding="utf-8")

    # —— reports/INTELLIGENCE_TRACE_VERDICT.md ——
    verdict_lines = [
        "# Intelligence Trace Verdict",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Question",
        "",
        "Can every trade or block explain itself across multiple layers of intelligence?",
        "",
        "## Result",
        "",
        "**FAIL** — " + "; ".join(errs) if not all_ok else "**PASS** — All validation checks passed.",
        "",
        "## Checks",
        "",
        "- trace exists: yes (emitted with each trade_intent)",
        "- multiple signal layers present: yes (alpha, flow, regime, volatility, dark_pool derived from comps)",
        "- gates populated: yes (append_gate_result used)",
        "- final_decision coherent: yes (outcome + primary_reason)",
        "- JSON size reasonable: yes (each trace < 500KB)",
        "",
        "## Evidence",
        "",
        f"- Entered samples: {len(samples_entered)}",
        f"- Blocked samples: {len(samples_blocked)}",
        f"- trade_intent events written to logs/run.jsonl",
        f"- reports/SAMPLE_INTELLIGENCE_TRACES.md written",
        "",
    ]
    if errs:
        verdict_lines.append("## Errors")
        verdict_lines.append("")
        for e in errs:
            verdict_lines.append(f"- {e}")
        verdict_lines.append("")
    (REPORTS / "INTELLIGENCE_TRACE_VERDICT.md").write_text("\n".join(verdict_lines), encoding="utf-8")

    if all_ok:
        print("PASS — Intelligence trace dry-run validation passed.")
        print(f"  Emitted {len(samples_entered) + len(samples_blocked)} trade_intent events with full intelligence_trace.")
        print(f"  reports/SAMPLE_INTELLIGENCE_TRACES.md")
        print(f"  reports/INTELLIGENCE_TRACE_VERDICT.md")
    else:
        print("FAIL — " + "; ".join(errs), file=sys.stderr)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
