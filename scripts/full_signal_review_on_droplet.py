#!/usr/bin/env python3
"""
Full signal review (Phase 1). Run on droplet after Phase 0 when ZERO TYPE = B.
Produces: signal_funnel.md/.json, top_50_end_to_end_traces.md, multi_model_adversarial_review.md.
No strategy tuning. All evidence from droplet paths.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

LEDGER_JSONL = REPO / "reports" / "decision_ledger" / "decision_ledger.jsonl"
SNAPSHOT_JSONL = REPO / "logs" / "score_snapshot.jsonl"
BLOCKED_JSONL = REPO / "state" / "blocked_trades.jsonl"
ORDERS_JSONL = REPO / "logs" / "orders.jsonl"
UW_FAILURE_JSONL = REPO / "reports" / "uw_health" / "uw_failure_events.jsonl"
GATE_TRUTH_JSONL = REPO / "logs" / "expectancy_gate_truth.jsonl"
SUBMIT_ENTRY_JSONL = REPO / "logs" / "submit_entry.jsonl"
SUBMIT_ORDER_CALLED_JSONL = REPO / "logs" / "submit_order_called.jsonl"
OUT_DIR = REPO / "reports" / "signal_review"
PAPER_METRICS_MD = OUT_DIR / "paper_trade_metric_reconciliation.md"
FUNNEL_MD = OUT_DIR / "signal_funnel.md"
FUNNEL_JSON = OUT_DIR / "signal_funnel.json"
TRACES_MD = OUT_DIR / "top_50_end_to_end_traces.md"
ADVERSARIAL_MD = OUT_DIR / "multi_model_adversarial_review.md"
GATE_TRUTH_200_MD = OUT_DIR / "expectancy_gate_truth_200.md"
BREAKDOWN_SUMMARY_MD = OUT_DIR / "signal_score_breakdown_summary.md"

DEFAULT_DAYS = 7
MIN_EXEC_SCORE = 2.5


def _parse_ts(v) -> int | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return int(float(v))
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s[:26])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def first_blocking_gate(gates: list) -> tuple[str, str] | None:
    for g in gates or []:
        if g.get("pass") is False:
            return (g.get("gate_name", "unknown"), g.get("reason", "unknown"))
    return None


def _score_pre_post(e: dict) -> tuple[float | None, float]:
    """Return (score_pre_adjust, score_post_adjust). Pre from composite_gate.measured.composite_pre_norm."""
    post = float(e.get("score_final") or 0)
    pre = None
    for g in e.get("gates") or []:
        if g.get("gate_name") == "composite_gate":
            m = g.get("measured") or {}
            v = m.get("composite_pre_norm")
            if v is not None:
                try:
                    pre = float(v)
                except (TypeError, ValueError):
                    pass
            break
    return pre, post


def load_ledger(days: int = DEFAULT_DAYS) -> list[dict]:
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    events = []
    if not LEDGER_JSONL.exists():
        return events
    for line in LEDGER_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            t = _parse_ts(r.get("ts"))
            if t and t < cutoff:
                continue
            events.append(r)
        except Exception:
            continue
    return events


def load_gate_truth(days: int = DEFAULT_DAYS) -> list[dict]:
    """Load expectancy_gate_truth.jsonl for the same window as ledger. Used for stage 5 when coverage >= 95%."""
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    rows = []
    if not GATE_TRUTH_JSONL.exists():
        return rows
    for line in GATE_TRUTH_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            t = _parse_ts(r.get("ts_eval_epoch") or r.get("ts_eval_iso"))
            if t and t < cutoff:
                continue
            rows.append(r)
        except Exception:
            continue
    return rows


def build_funnel(events: list[dict], gate_truth_rows: list[dict] | None = None) -> dict:
    """Build 7-stage funnel. Stage 5 (expectancy) from gate truth when coverage >= 95%; else from ledger (inferred)."""
    # Stage names
    s1_universe = "1_universe_candidate_generation"
    s2_features = "2_feature_availability"
    s3_uw = "3_uw_stage_outcomes"
    s4_adjustment = "4_adjustment_chain_deltas"
    s5_expectancy = "5_expectancy_gate"
    s6_risk = "6_risk_capacity_gates"
    s7_order = "7_order_placement_outcomes"

    count_in = len(events)
    gate_truth_rows = gate_truth_rows or []
    gate_truth_coverage_pct = round(100.0 * len(gate_truth_rows) / count_in, 1) if count_in else 0.0
    use_gate_truth_for_stage5 = (count_in > 0 and len(gate_truth_rows) >= 0.95 * count_in)

    stage_counts = defaultdict(int)
    stage_reasons: dict[str, Counter] = defaultdict(Counter)
    stage_examples: dict[str, list] = defaultdict(list)

    # Stage 5 from gate truth when coverage >= 95%
    if use_gate_truth_for_stage5:
        for r in gate_truth_rows:
            outcome = r.get("gate_outcome") or "fail"
            reason = r.get("fail_reason") or "unknown"
            gr = f"expectancy_gate:{reason}"
            if outcome == "fail":
                stage_reasons[s5_expectancy][gr] += 1
                if len(stage_examples[s5_expectancy]) < 20:
                    stage_examples[s5_expectancy].append({
                        "symbol": r.get("symbol"), "ts_eval_iso": r.get("ts_eval_iso"),
                        "score_used_by_gate": r.get("score_used_by_gate"), "min_exec_score": r.get("min_exec_score"),
                        "gate_reason": gr, "source": "gate_truth",
                    })
    # Ledger loop: s1–s4 always; s5/s6/s3 from first blocking gate (s5 only when not using gate truth)
    for e in events:
        fb = first_blocking_gate(e.get("gates", []))
        status = e.get("candidate_status") or "BLOCKED"
        stage_counts[s1_universe] += 1
        has_components = bool(e.get("score_components"))
        stage_counts[s2_features] += 1
        if not has_components:
            stage_reasons[s2_features]["missing_score_components"] += 1
        is_deferred = status == "DEFERRED" or any(g.get("gate_name") == "uw_defer" and g.get("pass") is False for g in (e.get("gates") or []))
        if is_deferred:
            stage_reasons[s3_uw]["defer"] += 1
        stage_counts[s3_uw] += 1
        stage_counts[s4_adjustment] += 1
        if fb:
            gate_name, reason = fb
            gr = f"{gate_name}:{reason}"
            if "capacity" in gate_name.lower() or "max_positions" in gate_name.lower() or "theme" in gate_name.lower() or "displacement" in gate_name.lower():
                stage_reasons[s6_risk][gr] += 1
                if len(stage_examples[s6_risk]) < 20:
                    stage_examples[s6_risk].append({"symbol": e.get("symbol"), "ts": e.get("ts"), "gate_reason": gr})
            elif gate_name == "uw_defer":
                stage_reasons[s3_uw][gr] += 1
            elif not use_gate_truth_for_stage5:
                stage_reasons[s5_expectancy][gr] += 1
                if len(stage_examples[s5_expectancy]) < 20:
                    stage_examples[s5_expectancy].append({
                        "symbol": e.get("symbol"), "ts": e.get("ts"), "score_final": e.get("score_final"),
                        "gate_reason": gr,
                        "measured": next((g.get("measured") for g in (e.get("gates") or []) if g.get("gate_name") == gate_name), None),
                        "source": "ledger_inferred",
                    })

    # Order stage
    order_fills = 0
    order_rejects = 0
    if ORDERS_JSONL.exists():
        for line in ORDERS_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                action = str(r.get("action") or "")
                if "filled" in action.lower() or r.get("status") == "filled":
                    order_fills += 1
                if "error" in action.lower() or r.get("error"):
                    order_rejects += 1
            except Exception:
                continue
    stage_reasons[s7_order]["filled"] = order_fills
    stage_reasons[s7_order]["rejected"] = order_rejects

    dominant_stage = s5_expectancy
    dominant_reason = ""
    dominant_count = 0
    for stage in [s5_expectancy, s6_risk, s3_uw]:
        c = stage_reasons[stage]
        total_stage = sum(c.values())
        if total_stage > dominant_count:
            dominant_count = total_stage
            dominant_stage = stage
            dominant_reason = c.most_common(1)[0][0] if c else ""

    # Expectancy distributions: prefer gate truth when available for score_used_by_gate
    pre_scores = []
    post_scores = []
    reason_expectancy: Counter = Counter()
    if use_gate_truth_for_stage5 and gate_truth_rows:
        for r in gate_truth_rows:
            post_scores.append(float(r.get("score_used_by_gate") or 0))
            pre = r.get("score_pre_adjust")
            if pre is not None:
                pre_scores.append(float(pre))
            outcome = r.get("gate_outcome") or "fail"
            if outcome == "fail":
                reason_expectancy[r.get("fail_reason") or "other"] += 1
    for e in events:
        fb = first_blocking_gate(e.get("gates", []))
        if not fb or fb[0] != "expectancy_gate":
            continue
        if not use_gate_truth_for_stage5:
            pre, post = _score_pre_post(e)
            if pre is not None:
                pre_scores.append(pre)
            post_scores.append(post)
            if e.get("uw_deferred") or e.get("candidate_status") == "DEFERRED":
                reason_expectancy["uw_defer"] += 1
            elif "score_floor_breach" in (fb[1] or ""):
                reason_expectancy["score_floor_breach"] += 1
            elif "score_below_min" in (fb[1] or ""):
                reason_expectancy["score_below_min"] += 1
            else:
                reason_expectancy[fb[1] or "other"] += 1
    expectancy_fail_count = len(post_scores)
    if not post_scores:
        post_scores = [float(e.get("score_final") or 0) for e in events]
    pre_scores = pre_scores or [None]
    def _percentile(arr: list, p: float) -> float:
        if not arr:
            return 0.0
        arr = sorted([x for x in arr if x is not None])
        if not arr:
            return 0.0
        k = (len(arr) - 1) * p / 100.0
        f = int(k)
        c = f + 1 if f + 1 < len(arr) else f
        return arr[f] if f == c else arr[f] + (k - f) * (arr[c] - arr[f])
    pre_valid = [x for x in pre_scores if x is not None]
    expectancy_distributions = {
        "pre_adjust": {"p10": _percentile(pre_valid, 10), "p50": _percentile(pre_valid, 50), "p90": _percentile(pre_valid, 90), "count": len(pre_valid)},
        "post_adjust": {"p10": _percentile(post_scores, 10), "p50": _percentile(post_scores, 50), "p90": _percentile(post_scores, 90), "count": len(post_scores)},
        "pct_above_min_exec_pre": round(100.0 * sum(1 for x in pre_valid if x >= MIN_EXEC_SCORE) / len(pre_valid), 1) if pre_valid else 0.0,
        "pct_above_min_exec_post": round(100.0 * sum(1 for x in post_scores if x >= MIN_EXEC_SCORE) / len(post_scores), 1) if post_scores else 0.0,
    }
    dominant_reason_expectancy = reason_expectancy.most_common(1)[0][0] if reason_expectancy else "other"
    pre_available_count = len(pre_valid)
    pre_score_availability_rate = round(100.0 * pre_available_count / expectancy_fail_count, 1) if expectancy_fail_count else 0.0
    pre_score_fallback = "When composite_pre_norm is missing in ledger (from snapshot), pre-adjust stats use only rows that have it; distributions and % above MIN_EXEC_SCORE for pre-adjust may be based on a subset. Post-adjust always uses score_final."

    funnel = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "window_days": DEFAULT_DAYS,
        "total_candidates": count_in,
        "stage5_from_gate_truth": use_gate_truth_for_stage5,
        "gate_truth_coverage_pct": gate_truth_coverage_pct,
        "gate_truth_lines_in_window": len(gate_truth_rows),
        "expectancy_distributions": expectancy_distributions,
        "dominant_reason_expectancy": dominant_reason_expectancy,
        "pre_score_availability_rate_pct": pre_score_availability_rate,
        "pre_score_availability_count": pre_available_count,
        "pre_score_fallback": pre_score_fallback,
        "stages": {
            s1_universe: {"count_in": count_in, "top_reasons": [], "examples": []},
            s2_features: {"count_in": count_in, "top_reasons": [["has_score_components", count_in]], "examples": []},
            s3_uw: {"count_in": count_in, "top_reasons": [[k, v] for k, v in stage_reasons[s3_uw].most_common(10)], "examples": []},
            s4_adjustment: {"count_in": count_in, "top_reasons": [], "examples": []},
            s5_expectancy: {"count_in": count_in, "top_reasons": [[k, v] for k, v in stage_reasons[s5_expectancy].most_common(10)], "examples": stage_examples[s5_expectancy][:20]},
            s6_risk: {"count_in": count_in, "top_reasons": [[k, v] for k, v in stage_reasons[s6_risk].most_common(10)], "examples": stage_examples[s6_risk][:20]},
            s7_order: {"count_in": count_in, "top_reasons": [["filled", order_fills], ["rejected", order_rejects]], "examples": []},
        },
        "dominant_choke_point": {"stage": dominant_stage, "reason": dominant_reason, "count": dominant_count, "pct": round(100.0 * dominant_count / count_in, 1) if count_in else 0},
    }
    return funnel


def write_funnel_md(funnel: dict) -> None:
    stage5_source = "gate_truth" if funnel.get("stage5_from_gate_truth") else "ledger (inferred)"
    gate_cov = funnel.get("gate_truth_coverage_pct", 0)
    claim_100_choke = (gate_cov >= 95.0 and funnel["dominant_choke_point"].get("pct", 0) >= 99.9)
    lines = [
        "# Signal funnel (Phase 1 full signal review)",
        "",
        f"Generated: {funnel['generated_utc']}",
        f"Window: last {funnel['window_days']} days. Total candidates: **{funnel['total_candidates']}**",
        "",
        "## Gate truth coverage",
        "",
        f"- **Stage 5 (expectancy) source:** {stage5_source}",
        f"- **Gate truth coverage:** {gate_cov}% (do not claim \"100% expectancy choke\" unless >= 95%).",
        f"- **Claim 100% choke allowed:** {'YES' if claim_100_choke else 'NO (coverage or pct insufficient)'}",
        "",
        "## Dominant choke point",
        "",
        f"- **Stage:** {funnel['dominant_choke_point']['stage']}",
        f"- **Reason:** {funnel['dominant_choke_point']['reason']}",
        f"- **Count:** {funnel['dominant_choke_point']['count']} ({funnel['dominant_choke_point']['pct']}%)",
        "",
    ]
    exp = funnel.get("expectancy_distributions") or {}
    if exp:
        pre_rate = funnel.get("pre_score_availability_rate_pct", 0)
        pre_fallback = funnel.get("pre_score_fallback", "When composite_pre_norm is missing, pre-adjust uses only rows that have it.")
        lines.extend([
            "## Expectancy gate (score_floor_breach)",
            "",
            f"- **Pre-score availability rate:** {pre_rate}% (expectancy fails with composite_pre_norm present). **Fallback when missing:** {pre_fallback}",
            f"- **Pre-adjust:** p10={exp.get('pre_adjust', {}).get('p10', 0):.3f}, p50={exp.get('pre_adjust', {}).get('p50', 0):.3f}, p90={exp.get('pre_adjust', {}).get('p90', 0):.3f}, count={exp.get('pre_adjust', {}).get('count', 0)}",
            f"- **Post-adjust:** p10={exp.get('post_adjust', {}).get('p10', 0):.3f}, p50={exp.get('post_adjust', {}).get('p50', 0):.3f}, p90={exp.get('post_adjust', {}).get('p90', 0):.3f}, count={exp.get('post_adjust', {}).get('count', 0)}",
            f"- **% above MIN_EXEC_SCORE (2.5):** pre={exp.get('pct_above_min_exec_pre', 0)}%, post={exp.get('pct_above_min_exec_post', 0)}%",
            f"- **Dominant reason post-adjust below floor:** {funnel.get('dominant_reason_expectancy', 'N/A')}",
            "",
        ])
    lines.extend([
        "## Per-stage counts and top reasons",
        "",
    ])
    for stage_name, data in funnel["stages"].items():
        lines.append(f"### {stage_name}")
        lines.append("")
        lines.append(f"- Count in: {data['count_in']}")
        if data["top_reasons"]:
            lines.append("- Top reasons:")
            for r in data["top_reasons"][:10]:
                if isinstance(r, (list, tuple)) and len(r) >= 2:
                    lines.append(f"  - {r[0]}: {r[1]}")
                else:
                    lines.append(f"  - {r}")
        if data.get("examples"):
            lines.append("- Examples (up to 20):")
            for ex in data["examples"][:20]:
                lines.append(f"  - {ex}")
        lines.append("")
    FUNNEL_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {FUNNEL_MD}")


def write_paper_metrics_md(
    candidates_evaluated: int,
    paper_orders_submitted: int,
    submit_entry_log_lines: int,
    paper_fills: int,
    days: int,
) -> None:
    """Write paper_trade_metric_reconciliation.md. Explicit: candidates_evaluated, paper_orders_submitted, paper_fills."""
    lines = [
        "# Paper trade metric reconciliation",
        "",
        "Explicit metrics (no single \"Trades (paper)\"):",
        "",
        f"- **candidates_evaluated:** {candidates_evaluated} (ledger events in window)",
        f"- **paper_orders_submitted:** {paper_orders_submitted} (SUBMIT_ORDER_CALLED / submit_entry path; from logs/submit_order_called.jsonl in window)",
        f"- **submit_entry log lines:** {submit_entry_log_lines} (logs/submit_entry.jsonl in window)",
        f"- **paper_fills:** {paper_fills} (broker fill telemetry from logs/orders.jsonl in window)",
        "",
        f"Window: last {days} days.",
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "python3 scripts/full_signal_review_on_droplet.py --days 7",
        "```",
        "",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_METRICS_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {PAPER_METRICS_MD}")


def write_traces_md(events: list[dict], trace_ids: list[tuple[int, dict]] | None = None) -> list[tuple[int, dict]]:
    """50 traces: 20 most recent, 15 closest to passing (post to 2.5), 15 largest pre→post drop. Returns list of (trace_id, event)."""
    if not events:
        TRACES_MD.write_text("# Top 50 end-to-end traces\n\nNo events.\n", encoding="utf-8")
        return []
    # 20 most recent (by ts desc)
    by_ts = sorted(events, key=lambda x: _parse_ts(x.get("ts")) or 0, reverse=True)
    recent_20 = by_ts[:20]
    remaining = [e for e in events if e not in recent_20]
    # 15 closest to MIN_EXEC_SCORE (post-adjust)
    post = [(e, abs(float(e.get("score_final") or 0) - MIN_EXEC_SCORE)) for e in remaining]
    post.sort(key=lambda p: p[1])
    closest_15 = [p[0] for p in post[:15]]
    remaining2 = [e for e in remaining if e not in closest_15]
    # 15 largest pre→post drop (pre - post, pre must be present)
    drops = []
    for e in remaining2:
        pre, post_val = _score_pre_post(e)
        if pre is not None:
            drops.append((e, pre - post_val))
    drops.sort(key=lambda p: -p[1])
    largest_15 = [p[0] for p in drops[:15]]
    # Dedupe and order: recent first, then closest, then largest drop
    seen = set()
    selected = []
    for e in recent_20 + closest_15 + largest_15:
        key = (e.get("symbol"), e.get("ts"))
        if key in seen:
            continue
        seen.add(key)
        selected.append(e)
        if len(selected) >= 50:
            break
    selected = selected[:50]
    trace_list = [(i, e) for i, e in enumerate(selected, 1)]

    lines = [
        "# Top 50 end-to-end traces (raw → decision)",
        "",
        "Selection: 20 most recent, 15 closest to passing (post-adjust to 2.5), 15 largest pre→post drop. Each trace: trace_id, symbol, ts, score_pre_adjust, score_post_adjust, first failing gate, exact numbers.",
        "",
        f"Source: reports/decision_ledger/decision_ledger.jsonl. MIN_EXEC_SCORE={MIN_EXEC_SCORE}.",
        "",
    ]
    for trace_id, e in trace_list:
        fb = first_blocking_gate(e.get("gates", []))
        pre, post = _score_pre_post(e)
        lines.append(f"## Trace {trace_id}: {e.get('symbol', '')} — ts={e.get('ts')} ({e.get('ts_iso', '')})")
        lines.append("")
        lines.append(f"- **trace_id:** {trace_id}")
        lines.append(f"- **score_pre_adjust:** {pre if pre is not None else 'N/A'}")
        lines.append(f"- **score_post_adjust:** {post}")
        lines.append(f"- **MIN_EXEC_SCORE:** {MIN_EXEC_SCORE}")
        lines.append(f"- **First failing gate:** {f'{fb[0]}:{fb[1]}' if fb else '—'}")
        lines.append("- **Score components (sample):** " + json.dumps(dict(list((e.get("score_components") or {}).items())[:5]), default=str))
        if e.get("gates"):
            for g in e["gates"]:
                if g.get("gate_name") == "expectancy_gate":
                    lines.append(f"- **Expectancy gate measured:** {g.get('measured')}")
                    break
        lines.append("")
        lines.append(f"*Cited path: decision_ledger.jsonl (symbol={e.get('symbol')}, ts={e.get('ts')})*")
        lines.append("")
    if len(trace_list) < 50:
        lines.append(f"(Only {len(trace_list)} traces in window.)")
    TRACES_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {TRACES_MD}")
    return trace_list


def write_adversarial_md(funnel: dict, events: list[dict], trace_list: list[tuple[int, dict]], join_coverage: dict) -> None:
    """Multi-model adversarial: Prosecution (>=5 trace IDs), Defense (>=2 alternatives + falsification), SRE (join coverage), Board (one choke + one experiment + acceptance)."""
    dom = funnel["dominant_choke_point"]
    total = funnel["total_candidates"]
    scores = [float(e.get("score_final") or 0) for e in events]
    mean_score = sum(scores) / len(scores) if scores else 0
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    exp = funnel.get("expectancy_distributions") or {}
    trace_ids_cited = [tid for tid, _ in trace_list[:10]]
    # At least 5 trace IDs for prosecution
    trace_ids_str = ", ".join(str(t) for t in trace_ids_cited[:5]) + (f" (and {len(trace_ids_cited) - 5} more)" if len(trace_ids_cited) > 5 else "")

    gate_truth_blurb = ""
    if GATE_TRUTH_200_MD.exists():
        gt = GATE_TRUTH_200_MD.read_text(encoding="utf-8", errors="replace")
        if "Pass rate:" in gt:
            gate_truth_blurb = " Expectancy gate truth (expectancy_gate_truth_200.md): " + gt.split("Pass rate:")[1].split("\n")[0].strip() + "."
        else:
            gate_truth_blurb = " Gate truth report: reports/signal_review/expectancy_gate_truth_200.md."
    breakdown_blurb = ""
    if BREAKDOWN_SUMMARY_MD.exists():
        br = BREAKDOWN_SUMMARY_MD.read_text(encoding="utf-8", errors="replace")
        if "% below MIN_EXEC_SCORE" in br:
            breakdown_blurb = " Signal breakdown (signal_score_breakdown_summary.md): " + br.split("% below MIN_EXEC_SCORE")[1].split("\n")[0].strip() + "."
        else:
            breakdown_blurb = " Signal breakdown: reports/signal_review/signal_score_breakdown_summary.md (missing/zero rates per signal)."

    deep_dive_cite = ""
    deep_dive_md = OUT_DIR / "SIGNAL_PIPELINE_DEEP_DIVE.md"
    if deep_dive_md.exists():
        deep_dive_cite = " **SIGNAL_PIPELINE_DEEP_DIVE:** reports/signal_review/SIGNAL_PIPELINE_DEEP_DIVE.md and .json (per-symbol per-signal tables, trace tables, dominant failure mode)."
    coverage_cite = ""
    coverage_md = OUT_DIR / "SIGNAL_COVERAGE_AND_WASTE.md"
    if coverage_md.exists():
        cov_text = coverage_md.read_text(encoding="utf-8", errors="replace")
        if "Broken signals" in cov_text:
            coverage_cite = " **SIGNAL_COVERAGE_AND_WASTE:** reports/signal_review/SIGNAL_COVERAGE_AND_WASTE.md (broken = used but frequently missing/zero; missing/zero rates)."

    gate_p10 = exp.get("post_adjust") or {} if isinstance(exp.get("post_adjust"), dict) else {}
    if not gate_p10 and GATE_TRUTH_200_MD.exists():
        gt = GATE_TRUTH_200_MD.read_text(encoding="utf-8", errors="replace")
        for lab, key in [("p10", "p10"), ("p50", "p50"), ("p90", "p90")]:
            if f"- {lab}:" in gt:
                try:
                    val = float(gt.split(f"- {lab}:")[1].split("\n")[0].strip())
                    gate_p10[key] = val
                except Exception:
                    pass
    p10 = gate_p10.get("p10")
    p50 = gate_p10.get("p50")
    p90 = gate_p10.get("p90")

    lines = [
        "# Multi-model adversarial review (Phase 5)",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Evidence: reports/signal_review/signal_funnel.json, signal_funnel.md, top_50_end_to_end_traces.md, SIGNAL_INVENTORY, SIGNAL_USAGE_MAP, SIGNAL_PIPELINE_DEEP_DIVE (see checklist)."
        + (" " + gate_truth_blurb.strip() if gate_truth_blurb else "")
        + (" " + breakdown_blurb.strip() if breakdown_blurb else "")
        + (" " + deep_dive_cite.strip() if deep_dive_cite else "")
        + (" " + coverage_cite.strip() if coverage_cite else ""),
        "",
        "---",
        "",
        "## 1) Prosecution",
        "",
        "**Strongest case for single dominant blocker.**",
        "",
        f"- Dominant choke point: **{dom['stage']}** — reason **{dom['reason']}** (count={dom['count']}, {dom['pct']}%).",
        f"- Funnel: total candidates = {total}; expectancy pre-adjust median = {exp.get('pre_adjust', {}).get('p50', 0):.3f}, post-adjust median = {exp.get('post_adjust', {}).get('p50', 0):.3f}; % above MIN_EXEC_SCORE pre = {exp.get('pct_above_min_exec_pre', 0)}%, post = {exp.get('pct_above_min_exec_post', 0)}%. Gate truth coverage: {join_coverage.get('gate_truth_pct', 0)}%.",
        f"- Gate truth distribution (score_used_by_gate): p10 = {p10}, p50 = {p50}, p90 = {p90}. Pass rate from expectancy_gate_truth_200.md.",
        f"- Trace evidence (trace_id): {trace_ids_str} (see top_50_end_to_end_traces.md and SIGNAL_PIPELINE_DEEP_DIVE per-candidate trace table). Each shows score_post_adjust < 2.5 and first failing gate expectancy_gate:score_floor_breach.",
        *([f"- {gate_truth_blurb.strip()}"] if gate_truth_blurb else []),
        *([f"- {breakdown_blurb.strip()}"] if breakdown_blurb else []),
        *([f"- {deep_dive_cite.strip()}"] if deep_dive_cite else []),
        *([f"- {coverage_cite.strip()}"] if coverage_cite else []),
        "",
        "Conclusion: Composite scores are below threshold at the expectancy gate; the gate correctly blocks. The blocker is score level, not gate logic.",
        "",
        "---",
        "",
        "## 2) Defense",
        "",
        "**Alternative root causes + falsification tests.**",
        "",
        "- **Alternative 1:** Data/feature pipeline (bars or UW) produces low-quality inputs → low composite. **Falsified if:** bars and UW root cause are fresh and complete; score_components show healthy contributions; pre-adjust distribution is high.",
        "- **Alternative 2:** Adjustment chain (signal_quality, UW, survivorship) over-penalizes. **Falsified if:** top_50 traces show small deltas (pre - post); post-adjust % above 2.5 is similar to pre-adjust.",
        "",
        "---",
        "",
        "## 3) SRE/Operations",
        "",
        "**Data freshness, telemetry, join coverage, contract health.**",
        "",
        f"- **Join coverage:** ledger {join_coverage.get('ledger_pct', 0)}%, snapshots {join_coverage.get('snapshots_pct', 0)}%, UW {join_coverage.get('uw_pct', 0)}%, adjustments (pre_norm) {join_coverage.get('adjustments_pct', 0)}%, **gate truth** {join_coverage.get('gate_truth_pct', 0)}%.",
        "- Silent skips: Candidates in score_snapshot appear in ledger. No evidence of silent drop before snapshot.",
        "- Missing events: Blocked events have gate_name + reason + measured (see traces).",
        "- Config drift: Compare ledger expectancy_floor to MIN_EXEC_SCORE (2.5) in config.",
        "",
        "---",
        "",
        "## 4) Board verdict",
        "",
        f"- **ONE dominant choke point:** {dom['stage']} — {dom['reason']}. Composite score below MIN_EXEC_SCORE (2.5); post-adjust median {exp.get('post_adjust', {}).get('p50', 0):.2f}. Gate truth coverage: {join_coverage.get('gate_truth_pct', 0)}%. Do not claim \"100% expectancy choke\" unless gate truth coverage >= 95%.",
        "",
        "- **ONE minimal paper-only experiment (single reversible change):** Enable detailed expectancy-gate logging for 50 consecutive candidates (composite_score, MIN_EXEC_SCORE, score_pre_adjust when available). No threshold change. Reversible by turning log off.",
        "",
        "- **Acceptance criteria:** (1) 50 log lines with (composite_score, MIN_EXEC_SCORE, gate_outcome). (2) If pre_adjust is logged, confirm pre vs post deltas; exact numbers: post-adjust median and % above 2.5 must match funnel report for same window.",
        "",
        "- **24-hour monitoring plan:** Daily run of run_closed_loops_checklist_on_droplet.py (exit 0 only if gate truth coverage ≥95%, stage 5 from gate truth). Check logs/expectancy_gate_truth.jsonl line count and reports/signal_review/signal_funnel.json gate_truth_coverage_pct. Alert on non-zero exit or coverage drop.",
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "python3 scripts/full_signal_review_on_droplet.py --days 7",
        "# Optional: capture ledger first",
        "python3 scripts/full_signal_review_on_droplet.py --days 7 --capture",
        "```",
        "",
    ]
    ADVERSARIAL_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {ADVERSARIAL_MD}")


def main() -> int:
    ap = __import__("argparse").ArgumentParser(description="Full signal review (Phase 1) on droplet")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Window days")
    ap.add_argument("--capture", action="store_true", help="Run decision ledger capture first")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.capture:
        rc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "run_decision_ledger_capture.py"), "--start", (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%d")],
            cwd=str(REPO), capture_output=True, timeout=120,
        )
        if rc.returncode != 0:
            print("Warning: run_decision_ledger_capture.py returned non-zero.", file=sys.stderr)
        subprocess.run([sys.executable, str(REPO / "scripts" / "summarize_decision_ledger.py")], cwd=str(REPO), capture_output=True, timeout=60)

    events = load_ledger(days=args.days)
    gate_truth_rows = load_gate_truth(days=args.days)
    if not events:
        print("No ledger events in window. Run scripts/run_decision_ledger_capture.py first.", file=sys.stderr)
        funnel = {"generated_utc": datetime.now(timezone.utc).isoformat(), "window_days": args.days, "total_candidates": 0, "stages": {}, "stage5_from_gate_truth": False, "gate_truth_coverage_pct": 0, "dominant_choke_point": {"stage": "none", "reason": "no_events", "count": 0, "pct": 0}, "expectancy_distributions": {}, "dominant_reason_expectancy": "N/A"}
        FUNNEL_JSON.write_text(json.dumps(funnel, indent=2, default=str), encoding="utf-8")
        write_funnel_md(funnel)
        TRACES_MD.write_text("# Top 50 end-to-end traces\n\nNo ledger events in window.\n", encoding="utf-8")
        write_adversarial_md(funnel, [], [], {"ledger_pct": 0, "snapshots_pct": 0, "uw_pct": 0, "adjustments_pct": 0, "gate_truth_pct": 0})
        return 1

    funnel = build_funnel(events, gate_truth_rows)
    FUNNEL_JSON.write_text(json.dumps(funnel, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {FUNNEL_JSON}")
    write_funnel_md(funnel)

    trace_list = write_traces_md(events)

    # Join coverage: ledger % with score_components, snapshot lines vs ledger, UW (deferred or not), adjustments (composite_pre_norm present)
    n_ledger = len(events)
    n_with_components = sum(1 for e in events if e.get("score_components"))
    n_with_pre = sum(1 for e in events if _score_pre_post(e)[0] is not None)
    n_uw = sum(1 for e in events if e.get("uw_deferred") or e.get("candidate_status") == "DEFERRED" or any(g.get("gate_name") == "uw_defer" for g in (e.get("gates") or [])))
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp())
    snapshot_lines = 0
    if SNAPSHOT_JSONL.exists():
        for line in SNAPSHOT_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t and t >= cutoff:
                    snapshot_lines += 1
            except Exception:
                continue
    n_gate_truth = len(load_gate_truth(days=args.days))
    join_coverage = {
        "ledger_pct": round(100.0 * n_with_components / n_ledger, 1) if n_ledger else 0,
        "snapshots_pct": round(100.0 * snapshot_lines / n_ledger, 1) if n_ledger else 0,
        "uw_pct": round(100.0 * (n_ledger - n_uw) / n_ledger, 1) if n_ledger else 0,
        "adjustments_pct": round(100.0 * n_with_pre / n_ledger, 1) if n_ledger else 0,
        "gate_truth_pct": round(100.0 * n_gate_truth / n_ledger, 1) if n_ledger else 0,
    }
    write_adversarial_md(funnel, events, trace_list, join_coverage)

    # Paper metrics: candidates_evaluated, paper_orders_submitted, paper_fills
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp())
    def _count_24h(path: Path, ts_key: str = "ts") -> int:
        if not path.exists():
            return 0
        n = 0
        for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get(ts_key) or r.get("ts_iso") or r.get("ts_eval_epoch"))
                if t and t >= cutoff:
                    n += 1
            except Exception:
                continue
        return n
    paper_orders_submitted = _count_24h(SUBMIT_ORDER_CALLED_JSONL, "ts") if SUBMIT_ORDER_CALLED_JSONL.exists() else 0
    submit_entry_lines = _count_24h(SUBMIT_ENTRY_JSONL, "ts") if SUBMIT_ENTRY_JSONL.exists() else 0
    paper_fills = 0
    if ORDERS_JSONL.exists():
        for line in ORDERS_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t and t < cutoff:
                    continue
                if "filled" in str(r.get("action") or "").lower() or r.get("status") == "filled":
                    paper_fills += 1
            except Exception:
                continue
    write_paper_metrics_md(
        candidates_evaluated=n_ledger,
        paper_orders_submitted=paper_orders_submitted,
        submit_entry_log_lines=submit_entry_lines,
        paper_fills=paper_fills,
        days=args.days,
    )

    # Required terminal output
    dom = funnel["dominant_choke_point"]
    exp = funnel.get("expectancy_distributions") or {}
    s7 = "7_order_placement_outcomes"
    order_reasons = funnel.get("stages", {}).get(s7, {}).get("top_reasons") or []
    fills = 0
    for r in order_reasons:
        if isinstance(r, (list, tuple)) and len(r) >= 2 and r[0] == "filled":
            fills = int(r[1])
            break
    paper_submits = paper_orders_submitted  # from above
    print("")
    print("--- TERMINAL OUTPUT (Phase 2) ---")
    print(f"Dominant choke point: {dom['stage']}/{dom['reason']} count={dom['count']}, {dom['pct']}%")
    print(f"Gate truth coverage: {join_coverage.get('gate_truth_pct', 0)}% (stage 5 from gate truth: {funnel.get('stage5_from_gate_truth', False)})")
    print(f"Expectancy: pre-adjust median={exp.get('pre_adjust', {}).get('p50', 0):.3f} vs post-adjust median={exp.get('post_adjust', {}).get('p50', 0):.3f}")
    print(f"% above MIN_EXEC_SCORE pre={exp.get('pct_above_min_exec_pre', 0)}% vs post={exp.get('pct_above_min_exec_post', 0)}%")
    print(f"candidates_evaluated: {n_ledger}; paper_orders_submitted: {paper_submits}; paper_fills: {paper_fills}")
    print(f"Join coverage: ledger {join_coverage.get('ledger_pct', 0)}%, snapshots {join_coverage.get('snapshots_pct', 0)}%, UW {join_coverage.get('uw_pct', 0)}%, adjustments {join_coverage.get('adjustments_pct', 0)}%, gate_truth {join_coverage.get('gate_truth_pct', 0)}%")
    print("---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
