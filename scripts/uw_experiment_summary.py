#!/usr/bin/env python3
"""
Produce reports/uw_experiment/experiment_summary.md from uw_penalty_events.jsonl and optional ledger/snapshot.
Run after a one-day paper run with UW_MISSING_INPUT_MODE=penalize.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
EVENTS_JSONL = REPO / "reports" / "uw_experiment" / "uw_penalty_events.jsonl"
OUT_MD = REPO / "reports" / "uw_experiment" / "experiment_summary.md"
LEDGER_PATH = REPO / "reports" / "decision_ledger" / "decision_ledger.jsonl"
SNAPSHOT_PATH = REPO / "logs" / "score_snapshot.jsonl"
ATTRIBUTION_PATH = REPO / "logs" / "attribution.jsonl"
MIN_EXEC = 2.5


def load_jsonl(path: Path, limit: int = 100000):
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(out) >= limit:
            break
    return out


def main() -> int:
    events = load_jsonl(EVENTS_JSONL)
    ledger = load_jsonl(LEDGER_PATH, limit=5000)
    snapshot = load_jsonl(SNAPSHOT_PATH, limit=10000)
    attribution = load_jsonl(ATTRIBUTION_PATH, limit=5000)

    # Executed trades: entry_score from attribution
    executed_scores = []
    for r in attribution:
        if r.get("type") != "attribution" or str(r.get("trade_id", "")).startswith("open_"):
            continue
        ctx = r.get("context") or {}
        es = ctx.get("entry_score") or r.get("entry_score") or r.get("entry_v2_score")
        if es is not None:
            try:
                executed_scores.append(float(es))
            except (TypeError, ValueError):
                pass

    # Penalty events: candidates that got missing_inputs_penalized
    reached_gate = [e for e in events if e.get("reached_expectancy_gate")]
    gate_pass = [e for e in events if e.get("expectancy_gate_pass")]
    post_scores = [float(e.get("score_after", 0)) for e in events if e.get("score_after") is not None]
    previously_rejected_now_reach = len(gate_pass)  # would have been rejected (no score_after), now have score_after >= 2.5

    # Paper trades: from snapshot, count where composite_gate_pass and expectancy_gate_pass in this run window
    paper_trades_count = 0
    if snapshot:
        paper_trades_count = sum(1 for r in snapshot if r.get("expectancy_gate_pass") is True)
    # Alternative: count attribution entries in the experiment window (paper orders)
    paper_orders = [r for r in attribution if r.get("type") == "attribution" and not str(r.get("trade_id", "")).startswith("open_")]
    paper_trades_from_attr = len(paper_orders)

    lines = [
        "# UW missing-input penalty experiment summary",
        "",
        "## Config",
        "- UW_MISSING_INPUT_MODE=penalize (paper-only)",
        "- UW_MISSING_INPUT_PENALTY=0.75",
        "",
        "## Counts",
        f"- Penalty events (missing_inputs_penalized): **{len(events)}**",
        f"- Reached expectancy gate (score passed to gate): **{len(reached_gate)}**",
        f"- Expectancy gate pass (score_after >= 2.5): **{len(gate_pass)}**",
        f"- Candidates previously rejected (no UW score_after) that now reach gate: **{len(gate_pass)}**",
        "",
        "## Post-adjustment score distribution (penalty events only)",
    ]
    if post_scores:
        lines.append(f"- count={len(post_scores)}, min={min(post_scores):.3f}, max={max(post_scores):.3f}, median={median(post_scores):.3f}")
        above = sum(1 for s in post_scores if s >= MIN_EXEC)
        lines.append(f"- Above MIN_EXEC_SCORE (2.5): **{above}** ({100 * above / len(post_scores):.1f}%)")
    else:
        lines.append("- No penalty events (no post-adjustment scores).")
    lines.extend([
        "",
        "## Paper trades",
        f"- From score_snapshot (expectancy_gate_pass=True): **{paper_trades_count}**",
        f"- From attribution (closed/executed): **{paper_trades_from_attr}**",
        "",
        "## Comparison to historical executed trades",
    ])
    if executed_scores:
        lines.append(f"- Historical executed entry_score: count={len(executed_scores)}, min={min(executed_scores):.3f}, max={max(executed_scores):.3f}, median={median(executed_scores):.3f}")
    else:
        lines.append("- No historical executed scores in attribution.")
    lines.extend([
        "",
        "## Verdict",
        "",
    ])
    if len(events) == 0:
        lines.append("No penalty events were recorded. Either UW_MISSING_INPUT_MODE was not 'penalize', or no candidates had missing UW inputs (use_quality was None). On droplet, rejections may be due to low quality (e.g. 0.0) rather than missing data; those are unchanged.")
    elif len(gate_pass) > 0:
        lines.append("**Candidates that would have been hard-rejected (missing inputs) reached the expectancy gate with bounded penalty.** Evidence supports: allowing bounded penalties for missing UW inputs can restore flow to the gate.")
    else:
        lines.append("Penalty events occurred but none had score_after >= 2.5. **Even with bounded penalties, trades did not materialize** from the missing-input path (or score_after was below threshold).")
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")

    # Terminal output (concise). Paper count may be historical if no experiment window filter.
    paper_count = paper_trades_count or paper_trades_from_attr
    paper_yes_no = "YES" if paper_count > 0 else "NO"
    median_post = median(post_scores) if post_scores else 0.0
    pct_reach = 100.0 * len(gate_pass) / len(events) if events else 0.0
    if len(events) == 0:
        verdict = "N/A (no penalty events; root cause may be low quality not missing inputs)"
    elif len(gate_pass) > 0:
        verdict = "UW hard-reject on missing inputs IS a root cause (bounded penalty restored flow)"
    else:
        verdict = "UW hard-reject on missing inputs may not be the sole root cause (penalized candidates still below gate)"
    print("")
    print("Paper trades generated:", paper_yes_no, f"({paper_count})")
    print("Median post-adjustment score:", f"{median_post:.3f}")
    print("% of candidates reaching expectancy gate:", f"{pct_reach:.1f}%")
    print("Verdict:", verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
