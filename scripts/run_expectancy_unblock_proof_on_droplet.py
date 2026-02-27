#!/usr/bin/env python3
"""
Collect unblock proof from droplet after expectancy fix: gate.jsonl + tmux pane (EXPECTANCY_DEBUG).
Wait 15 min then fetch; parse cycle_summary, expectancy_blocked, EXPECTANCY_DEBUG lines.
Write reports/expectancy_gate_fix/unblock_proof.md.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "reports" / "expectancy_gate_fix"
WAIT_SEC = 15 * 60  # 15 minutes


def _run(c, command: str, timeout: int = 60):
    return c._execute_with_cd(command, timeout=timeout)


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Waiting {WAIT_SEC // 60} minutes for cycles...")
    time.sleep(WAIT_SEC)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        out_gate, _, _ = _run(c, "tail -n 600 logs/gate.jsonl 2>/dev/null || true", timeout=20)
        out_pane, _, _ = _run(c, "tmux capture-pane -pt stock_bot_paper_run -S -400 2>/dev/null || echo ''", timeout=10)
        out_run, _, _ = _run(c, "tail -n 100 logs/run.jsonl 2>/dev/null || true", timeout=10)

    gate_text = out_gate or ""
    pane_text = out_pane or ""
    run_text = out_run or ""

    # Parse gate.jsonl: cycle_summary (considered, orders), expectancy_blocked by reason
    cycle_summaries = []
    expectancy_blocked_reasons = Counter()
    for line in gate_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = d.get("msg") or ""
        if msg == "cycle_summary":
            cycle_summaries.append({
                "considered": d.get("considered", 0),
                "orders": d.get("orders", 0),
                "gate_counts": d.get("gate_counts") or {},
            })
        elif "expectancy_blocked" in str(d.get("gate_type", "")) or (msg == "expectancy_blocked"):
            reason = d.get("reason", d.get("msg", ""))
            expectancy_blocked_reasons[reason] += 1

    # Parse EXPECTANCY_DEBUG from pane
    debug_lines = []
    for line in pane_text.splitlines():
        if "EXPECTANCY_DEBUG" in line:
            debug_lines.append(line.strip())
    # Parse: EXPECTANCY_DEBUG SYM: composite_score=X, score_used_by_expectancy=X, expectancy_floor=X, decision=pass|fail (reason)
    example_traces = []
    pass_count = 0
    fail_count = 0
    for line in debug_lines[-80:]:  # last 80
        m = re.search(r"composite_score=([\d.]+).*?score_used_by_expectancy=([\d.]+).*?expectancy_floor=([\d.]+).*?decision=(pass|fail)", line)
        if m:
            comp, used, floor, decision = m.group(1), m.group(2), m.group(3), m.group(4)
            reason = "unknown"
            rm = re.search(r"\(([^)]+)\)\s*$", line)
            if rm:
                reason = rm.group(1)
            example_traces.append({"symbol": line.split()[1].rstrip(":") if " " in line else "?", "composite_score": comp, "score_used_by_expectancy": used, "expectancy_floor": floor, "decision": decision, "reason": reason})
            if decision == "pass":
                pass_count += 1
            else:
                fail_count += 1

    # Totals from cycle_summary (last 10 cycles)
    last_cycles = cycle_summaries[-10:] if len(cycle_summaries) > 10 else cycle_summaries
    total_considered = sum(x["considered"] for x in last_cycles)
    total_orders = sum(x["orders"] for x in last_cycles)
    candidate_count_last = last_cycles[-1]["considered"] if last_cycles else 0
    orders_last = last_cycles[-1]["orders"] if last_cycles else 0

    # score_floor_breach share
    total_blocked = sum(expectancy_blocked_reasons.values())
    score_floor_breach_count = expectancy_blocked_reasons.get("score_floor_breach", 0)
    score_floor_breach_pct = (100.0 * score_floor_breach_count / total_blocked) if total_blocked else 0
    expectancy_pass_count = pass_count  # from EXPECTANCY_DEBUG; else infer from gate_counts
    if not debug_lines and last_cycles:
        # Infer: if gate_counts has expectancy_blocked:expectancy_passed, use that
        for cy in last_cycles:
            gc = cy.get("gate_counts") or {}
            for k, v in gc.items():
                if "expectancy_passed" in k:
                    expectancy_pass_count += int(v)
                if "score_floor_breach" in k:
                    score_floor_breach_count += int(v)

    # Three example traces
    three = example_traces[-3:] if len(example_traces) >= 3 else example_traces

    lines = [
        "# Expectancy gate fix — Unblock proof",
        "",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Proof window:** ~15 min after deploy",
        "",
        "## Aggregated (last 10 cycles / proof window)",
        f"- candidate_count (considered) last cycle: **{candidate_count_last}**",
        f"- total considered (last 10 cycles): **{total_considered}**",
        f"- orders_submitted_count (last cycle): **{orders_last}**",
        f"- total orders (last 10 cycles): **{total_orders}**",
        f"- expectancy_pass_count (from EXPECTANCY_DEBUG or gate_counts): **{expectancy_pass_count}**",
        f"- score_floor_breach blocks: **{score_floor_breach_count}** (of {total_blocked} expectancy_blocked)",
        f"- score_floor_breach share: **{score_floor_breach_pct:.1f}%**",
        "",
        "## Gate counts (expectancy_blocked by reason)",
        "```",
        json.dumps(dict(expectancy_blocked_reasons.most_common(10)), indent=2),
        "```",
        "",
        "## Last cycle_summary entries (up to 5)",
        "```",
        json.dumps(last_cycles[-5:], indent=2),
        "```",
        "",
        "## Example candidate traces (EXPECTANCY_DEBUG)",
        "```",
        json.dumps(three, indent=2) if three else "(no EXPECTANCY_DEBUG lines in captured pane)",
        "```",
        "",
        "## PASS criteria",
        f"- expectancy_pass_count > 0: **{'PASS' if expectancy_pass_count > 0 else 'FAIL'}**",
        f"- score_floor_breach not ~100%: **{'PASS' if score_floor_breach_pct < 95 else 'FAIL'}**",
        f"- orders_submitted_count > 0 or clear cap: **{'PASS' if total_orders > 0 or candidate_count_last == 0 else 'REVIEW'}**",
        "",
        "## Verdict",
        ("**PASS**" if (expectancy_pass_count > 0 and score_floor_breach_pct < 95) else "**FAIL**"),
    ]
    (OUT_DIR / "unblock_proof.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'unblock_proof.md'}")
    print(f"expectancy_pass_count={expectancy_pass_count}, total_orders={total_orders}, score_floor_breach%={score_floor_breach_pct:.1f}")
    return 0 if (expectancy_pass_count > 0 and score_floor_breach_pct < 95) else 1


if __name__ == "__main__":
    sys.exit(main())
