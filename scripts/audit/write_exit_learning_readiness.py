#!/usr/bin/env python3
"""
Phase 4 — Exit Learning Readiness check. CSA verification that we can:
- Reconstruct peak unrealized moment and signal state at peak
- Reconstruct exit eligibility timeline
- Answer "Which exit should have fired?" and "What signal component was decisive?"
Writes: reports/audit/EXIT_LEARNING_READINESS_<YYYY-MM-DD>.md
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

TRACE_PATH = REPO / "reports" / "state" / "exit_decision_trace.jsonl"
SCHEMA_PATH = REPO / "reports" / "audit" / "EXIT_DECISION_TRACE_SCHEMA.md"
REGISTRY_PATH = REPO / "reports" / "audit" / "SIGNAL_GRANULARITY_REGISTRY.json"
AUDIT_DIR = REPO / "reports" / "audit"
DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = AUDIT_DIR / f"EXIT_LEARNING_READINESS_{DATE}.md"

    trace_exists = TRACE_PATH.exists()
    trace_lines = 0
    trace_sample = {}
    if trace_exists:
        lines = TRACE_PATH.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        trace_lines = sum(1 for ln in lines if ln.strip())
        for line in lines[-3:]:
            line = line.strip()
            if line:
                try:
                    trace_sample = json.loads(line)
                    break
                except Exception:
                    pass

    schema_exists = SCHEMA_PATH.exists()
    registry_exists = REGISTRY_PATH.exists()
    registry_signals = 0
    if registry_exists:
        try:
            r = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            registry_signals = len(r.get("signals", []))
        except Exception:
            pass

    can_reconstruct_peak = trace_exists and trace_lines > 0 and "unrealized_pnl" in trace_sample and "signals" in trace_sample
    can_reconstruct_timeline = trace_exists and "ts" in trace_sample and "exit_eligible" in trace_sample and "exit_conditions" in trace_sample
    can_answer_which_exit = trace_exists and "exit_conditions" in trace_sample
    can_answer_decisive_component = trace_exists and "signals" in trace_sample and registry_signals > 0

    md = [
        "# Exit Learning Readiness",
        "",
        f"**Date:** {DATE}",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## CSA verification",
        "",
        "| Check | Status | Notes |",
        "|-------|--------|-------|",
        f"| Trace file exists | {'YES' if trace_exists else 'NO'} | `reports/state/exit_decision_trace.jsonl` |",
        f"| Trace record count | {trace_lines} | Append-only samples |",
        f"| Schema doc exists | {'YES' if schema_exists else 'NO'} | EXIT_DECISION_TRACE_SCHEMA.md |",
        f"| Signal registry exists | {'YES' if registry_exists else 'NO'} | {registry_signals} signals |",
        "",
        "## Reconstructability",
        "",
        "| Question | Can answer? |",
        "|----------|-------------|",
        f"| Peak unrealized moment + signal state at peak | {'YES' if can_reconstruct_peak else 'NO — need trace samples with unrealized_pnl + signals'} |",
        f"| Exit eligibility timeline | {'YES' if can_reconstruct_timeline else 'NO — need ts + exit_eligible + exit_conditions'} |",
        f"| Which exit should have fired? | {'YES' if can_answer_which_exit else 'NO — need exit_conditions'} |",
        f"| What signal component was decisive? | {'YES' if can_answer_decisive_component else 'NO — need signals + registry'} |",
        "",
        "## Conclusion",
        "",
    ]
    if trace_exists and schema_exists and registry_exists:
        md.append("**Exit learning is possible:** trace schema, registry, and (when trades run) trace data support reconstructing peak unrealized, signal state at peak, and exit eligibility. Decisive component is derivable from `exit_conditions` and `signals` per SIGNAL_GRANULARITY_REGISTRY.")
    else:
        md.append("**Gaps:** Ensure trace is populated on droplet (open positions sampled every N seconds), schema and registry are present. After first run with open positions, re-run this check.")
    md.append("")
    out_path.write_text("\n".join(md), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
