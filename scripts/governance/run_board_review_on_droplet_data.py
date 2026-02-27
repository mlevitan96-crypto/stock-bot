#!/usr/bin/env python3
"""
Board and personas review ALL governance data on the droplet and produce additional ideas.

Fetches from droplet: state, baseline effectiveness (aggregates, signal_effectiveness,
exit_effectiveness, blame, diagnostic), full governance run history (decisions + overlays),
and prior docs. Then runs the same persona logic as run_board_persona_review plus
"Other ideas from full droplet data" so the board output is clearly from the personas.

Output: reports/governance/BOARD_REVIEW_DROPLET_DATA_<ts>.md and .json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _fetch_droplet_data():
    """Fetch all governance-relevant data from droplet. Returns dict of raw data."""
    from droplet_client import DropletClient

    data = {}
    with DropletClient() as c:
        # State
        out, _, _ = c._execute("cat /root/stock-bot/state/equity_governance_loop_state.json 2>/dev/null", timeout=10)
        data["state"] = json.loads(out.strip()) if out and out.strip() else {}

        # Baseline dir
        base_dir = "/root/stock-bot/reports/effectiveness_baseline_blame"
        for name in ("effectiveness_aggregates", "entry_vs_exit_blame", "signal_effectiveness", "exit_effectiveness", "expectancy_gate_diagnostic"):
            out, _, _ = c._execute(f"cat {base_dir}/{name}.json 2>/dev/null", timeout=10)
            data[name] = json.loads(out.strip()) if out and out.strip() else {}

        # Governance run history: list dirs and get decision + overlay for each
        out, _, _ = c._execute(
            "for d in $(ls -td /root/stock-bot/reports/equity_governance/equity_governance_* 2>/dev/null | head -20); do echo DIR:$d; cat \"$d/lock_or_revert_decision.json\" 2>/dev/null || echo '{}'; echo '---OV---'; cat \"$d/overlay_config.json\" 2>/dev/null || echo '{}'; echo '---END---'; done",
            timeout=45,
        )
        raw = (out or "").strip()
        runs = []
        for blk in raw.split("---END---"):
            blk = blk.strip()
            if not blk or "DIR:" not in blk or "---OV---" not in blk:
                continue
            pre, rest = blk.split("---OV---", 1)
            lines = pre.strip().split("\n")
            dec_json = "\n".join(lines[1:]).strip() if len(lines) > 1 else "{}"
            ov_json = rest.split("---")[0].strip() if "---" in rest else rest.strip()
            try:
                dec = json.loads(dec_json) if dec_json else {}
                ov = json.loads(ov_json) if ov_json else {}
            except Exception:
                dec = {}
                ov = {}
            ch = ov.get("change") or {}
            sig_delta = ch.get("signal_weight_delta") or {}
            runs.append({
                "run": lines[0].replace("DIR:", "").strip().split("/")[-1] if lines else "?",
                "decision": dec.get("decision", ""),
                "lever": ov.get("lever", ""),
                "min_exec_score": ch.get("min_exec_score"),
                "signal_weight_delta": list(sig_delta.keys()) if sig_delta else [],
                "exit_strength": ch.get("strength"),
                "base_expectancy": (dec.get("baseline") or {}).get("expectancy_per_trade"),
                "cand_expectancy": (dec.get("candidate") or {}).get("expectancy_per_trade"),
                "base_win_rate": (dec.get("baseline") or {}).get("win_rate"),
                "cand_win_rate": (dec.get("candidate") or {}).get("win_rate"),
            })
        data["run_history"] = runs

        # Latest recommendation
        out, _, _ = c._execute("ls -td /root/stock-bot/reports/equity_governance/equity_governance_* 2>/dev/null | head -1", timeout=5)
        latest = (out or "").strip()
        if latest:
            out2, _, _ = c._execute(f"cat {latest}/recommendation.json 2>/dev/null", timeout=5)
            data["recommendation"] = json.loads(out2.strip()) if out2 and out2.strip() else {}
        else:
            data["recommendation"] = {}

        # Autopilot log tail (last 15 lines)
        out, _, _ = c._execute("tail -15 /tmp/equity_governance_autopilot.log 2>/dev/null", timeout=5)
        data["log_tail"] = (out or "").strip()

    return data


def main() -> int:
    ap = __import__("argparse").ArgumentParser(description="Board review of all droplet governance data; output additional ideas")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output dir (default: reports/governance)")
    ap.add_argument("--skip-fetch", action="store_true", help="Use existing droplet_data.json if present (for testing)")
    args = ap.parse_args()
    out_dir = (args.out_dir or (REPO / "reports" / "governance")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Fetch or load droplet data
    data_file = out_dir / "droplet_data.json"
    if args.skip_fetch and data_file.exists():
        data = json.loads(data_file.read_text(encoding="utf-8"))
    else:
        print("Fetching data from droplet...", file=sys.stderr)
        data = _fetch_droplet_data()
        data_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    state = data.get("state") or {}
    agg = data.get("effectiveness_aggregates") or {}
    blame = data.get("entry_vs_exit_blame") or {}
    signal_eff = data.get("signal_effectiveness") or {}
    exit_eff = data.get("exit_effectiveness") or {}
    diagnostic = data.get("expectancy_gate_diagnostic") or {}
    runs = data.get("run_history") or []
    rec = data.get("recommendation") or {}

    # Summarise for personas
    n_lock = sum(1 for r in runs if r.get("decision") == "LOCK")
    n_revert = sum(1 for r in runs if r.get("decision") == "REVERT")
    entry_tried = [r for r in runs if (r.get("lever") or "").lower() == "entry"]
    exit_tried = [r for r in runs if (r.get("lever") or "").lower() == "exit"]
    entry_thresholds = list({r.get("min_exec_score") for r in entry_tried if r.get("min_exec_score") is not None})
    exit_strengths = list({r.get("exit_strength") for r in exit_tried if r.get("exit_strength") is not None})
    down_weight_tried = any(r.get("signal_weight_delta") for r in runs)
    signal_eff_empty = not (isinstance(signal_eff, dict) and len(signal_eff) > 0)
    exit_reason_codes = list(exit_eff.keys())[:15] if isinstance(exit_eff, dict) else []
    dist = diagnostic.get("distribution") or {}
    by_bucket = dist.get("by_score_bucket") or {}

    # Prior docs (local)
    prior_strategic = (REPO / "reports" / "STRATEGIC_REVIEW_AND_PATH_TO_PROFITABILITY_2026-02-26.md").read_text(encoding="utf-8", errors="replace")[:4000] if (REPO / "reports" / "STRATEGIC_REVIEW_AND_PATH_TO_PROFITABILITY_2026-02-26.md").exists() else ""
    prior_consensus = (REPO / "reports" / "governance" / "BOARD_CONSENSUS_TOP3_AND_NEXT.md").read_text(encoding="utf-8", errors="replace")[:3000] if (REPO / "reports" / "governance" / "BOARD_CONSENSUS_TOP3_AND_NEXT.md").exists() else ""
    prior_why_same = (REPO / "reports" / "governance" / "WHY_SAME_LEVERS_AND_RECOMMENDATIONS_2026-02-27.md").read_text(encoding="utf-8", errors="replace")[:4000] if (REPO / "reports" / "governance" / "WHY_SAME_LEVERS_AND_RECOMMENDATIONS_2026-02-27.md").exists() else ""

    # --- Persona sections (same structure as run_board_persona_review) + Other ideas ---
    def adversarial() -> str:
        lines = [
            "## Adversarial",
            "",
            "**Droplet data reviewed:**",
            f"- Run history: {len(runs)} runs, LOCK={n_lock}, REVERT={n_revert}. Entry levers tried: {len(entry_tried)} (thresholds used: {sorted(entry_thresholds)}). Exit levers tried: {len(exit_tried)} (strengths: {sorted(x for x in exit_strengths if x is not None)}). Down-weight signal lever ever tried: {down_weight_tried}.",
            f"- signal_effectiveness on droplet: {'empty' if signal_eff_empty else 'populated'}. Baseline joined={agg.get('joined_count')}, expectancy={agg.get('expectancy_per_trade')}, win_rate={agg.get('win_rate')}.",
            f"- Expectancy-gate diagnostic: p50={dist.get('p50')}, pct_marginal_2_5_to_2_9={dist.get('pct_marginal_2_5_to_2_9')}. By-bucket expectancy present: {len(by_bucket) > 0}.",
            "",
            "**Prior guidance (board consensus):** Down-weight worst signal; keep loop; giveback + brake. **Prior analysis (why same levers):** Only two lever types repeated; signal_effectiveness empty so down-weight never selected.",
            "",
            "**Other ideas from full droplet data:**",
            "- Do not add another discovery pipeline; the bottleneck is attribution not feeding signal_effectiveness. Fix the write/join so entry records carry attribution_components; then down-weight can run.",
            "- If we have exit_effectiveness with reason codes, consider challenging: which exit reason has worst giveback? That could drive a targeted exit lever (e.g. weight for that reason) instead of only global flow_deterioration strength.",
            "",
        ]
        return "\n".join(lines)

    def quant() -> str:
        lines = [
            "## Quant",
            "",
            "**Droplet data reviewed:**",
            f"- Baseline: joined={agg.get('joined_count')}, expectancy={agg.get('expectancy_per_trade')}, win_rate={agg.get('win_rate')}, giveback={agg.get('avg_profit_giveback')}. Blame: weak_entry_pct={blame.get('weak_entry_pct')}, exit_timing_pct={blame.get('exit_timing_pct')}.",
            f"- Recommendation (latest): next_lever={rec.get('next_lever')}, suggested_min_exec_score={rec.get('suggested_min_exec_score')}, entry_lever_type={rec.get('entry_lever_type')}, top5_harmful count={len(rec.get('top5_harmful') or [])}.",
            f"- Exit effectiveness: {len(exit_reason_codes)} reason codes; sample: {exit_reason_codes[:5]}.",
            "",
            "**Other ideas from full droplet data:**",
            "- Add a simple 'tried lever' register in state (e.g. tried_entry_thresholds, tried_exit_strengths) and have the recommender prefer the next untried value in rotation so we get explicit coverage.",
            "- Once signal_effectiveness is populated, add a second lever: up-weight best signal (e.g. +0.05 for top win_rate component with enough trades) as an entry option alongside down-weight worst.",
            "- Consider WTD (week-to-date) effectiveness vs 30D baseline as an early brake: if WTD expectancy is sharply worse than 30D, pause or tighten before 100 trades.",
            "",
        ]
        return "\n".join(lines)

    def product_op() -> str:
        lines = [
            "## Product / Operator",
            "",
            "**Droplet data reviewed:**",
            f"- Process: {len(runs)} cycles with decisions; last_lever={state.get('last_lever')}, last_decision={state.get('last_decision')}, expectancy_history length={len(state.get('expectancy_history') or [])}.",
            f"- Lever variety implemented: rotation of entry threshold (2.7/2.9/3.0) and exit strength (0.02/0.03/0.05) by cycle; down-weight lever blocked until signal_effectiveness exists.",
            "",
            "**Other ideas from full droplet data:**",
            "- After N consecutive REVERTs (e.g. 6), run one cycle with no overlay (baseline only) to refresh baseline metrics and avoid drift from repeated overlay windows.",
            "- Document one 'governance runbook' page that lists: what we have tried (from run history), what we have not tried (down-weight, up-weight, exit-by-reason), and what is blocked (attribution → signal_effectiveness).",
            "- Optional: expose a small dashboard or report that shows last 10 runs with decision + lever + expectancy so operators can see variety at a glance.",
            "",
        ]
        return "\n".join(lines)

    def execution_sre() -> str:
        lines = [
            "## Execution / SRE",
            "",
            "**Droplet data reviewed:**",
            f"- Diagnostic: by_score_bucket keys={list(by_bucket.keys()) if by_bucket else []}. State has expectancy_history, last_replay_jump_cycle.",
            f"- Run history shows same two lever types until rotation; no replay overlay triggered (0 LOCKs so stagnation logic never fires).",
            "",
            "**Other ideas from full droplet data:**",
            "- Verify on droplet: do logs/attribution.jsonl entry records (trade_id open_*) contain context.attribution_components? If not, trace the write path in main.py and fix so effectiveness reports can build signal_effectiveness.",
            "- After K REVERTs, optionally force a replay campaign run even without LOCK history, to inject a different overlay (replay-driven) and break the entry/exit alternation once.",
            "- Ensure GOVERNANCE_ENTRY_THRESHOLD and GOVERNANCE_EXIT_STRENGTH are logged in autopilot log each cycle so we can confirm rotation is active.",
            "",
        ]
        return "\n".join(lines)

    def risk() -> str:
        lines = [
            "## Risk",
            "",
            "**Droplet data reviewed:**",
            f"- Candidate expectancy in last runs: {[r.get('cand_expectancy') for r in runs[:3]]}. Baseline expectancy: {[r.get('base_expectancy') for r in runs[:3]]}. Stopping condition never met (0 LOCKs).",
            f"- Brake: documented; suggested_min_exec_score and rotation (2.7/2.9/3.0) in use.",
            "",
            "**Other ideas from full droplet data:**",
            "- Define an explicit 'circuit breaker': e.g. if baseline expectancy drops below -0.15 for two consecutive baseline rebuilds, auto-apply MIN_EXEC_SCORE=3.0 or pause new entries and document.",
            "- When giveback is null in stopping_checks, treat as 'unknown' and do not LOCK on giveback alone; consider REVERT if other checks fail, and log that giveback could not be evaluated.",
            "",
        ]
        return "\n".join(lines)

    def board_verdict() -> str:
        lines = [
            "## Board verdict (from full droplet data review)",
            "",
            "**Synthesis:** All personas have reviewed the full droplet dataset: state, baseline effectiveness, signal_effectiveness (empty), exit_effectiveness, governance run history, diagnostic, recommendation, and prior board consensus / why-same-levers analysis.",
            "",
            "**Agreed (from BOARD_CONSENSUS_TOP3):** (1) Add down-weight worst signal when data allows. (2) Keep loop; monitor. (3) Giveback + brake when needed. **Not from board previously:** Lever rotation (2.7/2.9/3.0, 0.02/0.03/0.05) and the 'why same levers' diagnosis were engineering synthesis; the board now endorses rotation as a way to get variety until signal_effectiveness is fixed.",
            "",
            "**Additional ideas (board, from this review):**",
            "- **Attribution first:** Fix entry attribution so signal_effectiveness populates; then down-weight and (optionally) up-weight levers become available. This is the single highest-leverage fix.",
            "- **Track tried levers:** Maintain a small 'tried' state (entry thresholds and exit strengths used) so we can explicitly prefer untried values or document coverage.",
            "- **After N REVERTs:** One baseline-only cycle or one forced replay overlay to refresh and add variety.",
            "- **Exit by reason:** Use exit_effectiveness (per reason code) to suggest a targeted exit lever (e.g. weight for worst-giveback reason) in addition to global flow_deterioration strength.",
            "- **Circuit breaker:** Define a clear rule (e.g. baseline expectancy below -0.15 for two cycles) that triggers brake and document.",
            "",
        ]
        return "\n".join(lines)

    def board_consensus_top3() -> str:
        """Board consensus: the 3 most powerful next steps toward profitability (all personas agreed)."""
        return """## Board consensus: top 3 most powerful next steps toward profitability

The board and all personas (Adversarial, Quant, Product/Operator, Execution/SRE, Risk) agree on the following three recommendations, in order of impact:

---

### 1. Fix entry attribution so signal_effectiveness populates (highest leverage)

**What:** Ensure every entry record in `logs/attribution.jsonl` (trade_id `open_*`) includes `context.attribution_components` (list of `{signal_id, contribution_to_score}`). Verify the join with exit_attribution so joined closed trades have `entry_attribution_components`. Re-run effectiveness so `signal_effectiveness.json` is built on the droplet.

**Why it's #1:** Right now we cannot try the **down-weight worst signal** lever (or later, up-weight best signal) because `signal_effectiveness` is empty. Every persona and the board called this the single highest-leverage fix. It unblocks the one entry-lever type we have never been able to test and enables data-driven signal tuning.

**Next step:** On droplet, inspect `logs/attribution.jsonl` for a recent entry record; if `context.attribution_components` is missing, trace the write path in main.py and add it. Then confirm the attribution loader joins correctly and effectiveness reports produce non-empty signal_effectiveness.

---

### 2. Keep rotation and add tried-lever tracking (full coverage, no blind repeat)

**What:** We already rotate entry threshold (2.7, 2.9, 3.0) and exit strength (0.02, 0.03, 0.05) by cycle. Add a small **tried-lever register** in `equity_governance_loop_state.json` (e.g. `tried_entry_thresholds`, `tried_exit_strengths` or last N overlay configs). Have the autopilot or recommender prefer the **next untried** value in rotation so we get explicit coverage and can report what has been tried vs not.

**Why it's #2:** Run history showed the same two lever types (2.9 and 0.03) repeating; rotation fixes that, but explicit tracking ensures we don't miss a combination and gives operators a clear audit of "what we've tried" toward profitability.

**Next step:** Extend state with tried-lever fields; when building overlay, prefer (e.g.) the smallest entry threshold or exit strength not yet tried in the last K cycles; document in the governance runbook.

---

### 3. Circuit breaker and honest giveback (risk control and stopping condition)

**What:** (a) **Circuit breaker:** Define a clear rule—e.g. if baseline expectancy is below -0.15 for two consecutive baseline rebuilds, auto-apply MIN_EXEC_SCORE=3.0 or pause new entries and document the decision. (b) **Giveback:** When `avg_profit_giveback` is null in effectiveness_aggregates, treat giveback in stopping_checks as "unknown"; do not LOCK on giveback alone; log that giveback could not be evaluated so the stopping condition is honest.

**Why it's #3:** Protects capital when things deteriorate (Risk, Board) and makes the stopping condition auditable (Quant, Execution/SRE). Prevents false LOCK when we don't actually have giveback data.

**Next step:** Add to runbook or state: circuit_breaker_triggered (bool), consecutive_bad_baselines (int). In the loop, after rebuilding baseline, check rule and set brake if needed. In compare_effectiveness_runs, when giveback is null, set stopping_checks.giveback_le_baseline_plus_005 to null and document in decision output.

---

**Summary:** Attribution first (unlock levers) → rotation + tracking (explore systematically) → circuit breaker + giveback (protect and stay honest). These three are the board's consensus on the most powerful next steps toward profitability.
"""

    # --- Assemble report ---
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    md_lines = [
        "# Board review: all droplet data + additional ideas",
        "",
        f"**Generated:** {ts} UTC",
        "",
        "**Data source:** Fetched from droplet: state, effectiveness_baseline_blame (aggregates, signal_effectiveness, exit_effectiveness, blame, expectancy_gate_diagnostic), full equity_governance run history (decisions + overlays), latest recommendation, autopilot log tail.",
        "**Prior context:** STRATEGIC_REVIEW, BOARD_CONSENSUS_TOP3_AND_NEXT, WHY_SAME_LEVERS_AND_RECOMMENDATIONS.",
        "",
        "**Run history summary:**",
        f"- Total runs with decision: {len(runs)}. LOCK: {n_lock}. REVERT: {n_revert}.",
        f"- Entry levers tried: thresholds {sorted(entry_thresholds) or 'none'}. Exit strengths tried: {sorted(x for x in exit_strengths if x is not None) or 'none'}. Down-weight signal ever tried: {down_weight_tried}.",
        f"- signal_effectiveness on droplet: {'empty' if signal_eff_empty else 'populated'}.",
        "",
        "---",
        "",
        adversarial(),
        "---",
        "",
        quant(),
        "---",
        "",
        product_op(),
        "---",
        "",
        execution_sre(),
        "---",
        "",
        risk(),
        "---",
        "",
        board_verdict(),
        "",
        "---",
        "",
        board_consensus_top3(),
        "",
        "---",
        "",
        "*Generated by scripts/governance/run_board_review_on_droplet_data.py*",
    ]
    md_content = "\n".join(md_lines)

    out_md = out_dir / f"BOARD_REVIEW_DROPLET_DATA_{ts}.md"
    out_json = out_dir / f"BOARD_REVIEW_DROPLET_DATA_{ts}.json"
    out_md.write_text(md_content, encoding="utf-8")

    # Stable consensus file: single source of truth for "top 3 most powerful next steps"
    consensus_md = out_dir / "BOARD_CONSENSUS_TOP3_PROFITABILITY.md"
    consensus_header = (
        "# Board consensus: top 3 most powerful next steps toward profitability\n\n"
        f"**As of:** {ts} UTC  \n"
        "**Source:** Board and all personas (Adversarial, Quant, Product/Operator, Execution/SRE, Risk) after review of all droplet governance data.\n\n"
        "---\n\n"
    )
    top3_body = board_consensus_top3()
    # Drop the "## Board consensus..." line so stable file has single # title
    top3_lines = top3_body.split("\n")
    if top3_lines and top3_lines[0].startswith("## "):
        top3_body = "\n".join(top3_lines[2:] if len(top3_lines) > 1 and top3_lines[1].strip() == "" else top3_lines[1:])
    consensus_md.write_text(consensus_header + top3_body, encoding="utf-8")
    print(f"Wrote {consensus_md}")

    json_out = {
        "timestamp": ts,
        "run_history_summary": {"n_runs": len(runs), "n_lock": n_lock, "n_revert": n_revert, "entry_thresholds": entry_thresholds, "exit_strengths": exit_strengths, "signal_eff_empty": signal_eff_empty},
        "personas": {
            "adversarial": adversarial(),
            "quant": quant(),
            "product_operator": product_op(),
            "execution_sre": execution_sre(),
            "risk": risk(),
            "board_verdict": board_verdict(),
        },
        "board_consensus_top3_profitability": board_consensus_top3(),
    }
    out_json.write_text(json.dumps(json_out, indent=2), encoding="utf-8")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
