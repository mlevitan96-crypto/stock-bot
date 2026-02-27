#!/usr/bin/env python3
"""
Run on droplet: signal audit + full signal review; fetch results and write actionable MD + JSON.

Produces:
- reports/ACTIONABLE_SIGNAL_DATA_<date>.md  (summary, where we adjust, weights, funnel, actionable bullets)
- reports/ACTIONABLE_SIGNAL_DATA_<date>.json (machine-readable details)

Usage: python scripts/run_actionable_signal_data_on_droplet.py [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

REMOTE_ROOT = "/root/stock-bot"


def _run(c, cmd: str, timeout: int = 120) -> tuple[str, str, int]:
    pd = getattr(c, "project_dir", None) or REMOTE_ROOT
    return c._execute(f"cd {pd} && {cmd}", timeout=timeout)


def _cat(c, remote_path: str, timeout: int = 15) -> str:
    out, err, rc = _run(c, f"cat '{remote_path}' 2>/dev/null || echo '__MISSING__'", timeout=timeout)
    return (out or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    args = ap.parse_args()
    date_str = args.date or datetime.now(timezone.utc).date().isoformat().replace("-", "")

    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1

    out_dir = REPO / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"ACTIONABLE_SIGNAL_DATA_{date_str}.md"
    json_path = out_dir / f"ACTIONABLE_SIGNAL_DATA_{date_str}.json"

    payload = {
        "date": date_str,
        "where_we_adjust": {},
        "signal_audit": {},
        "signal_weights": {},
        "signal_funnel": {},
        "funnel_md": "",
        "breakdown_md": "",
        "actionable": [],
        "errors": [],
    }

    with DropletClient() as c:
        pd = getattr(c, "project_dir", None) or REMOTE_ROOT

        # --- 1) Where we adjust (reference) ---
        payload["where_we_adjust"] = {
            "composite_weights": "uw_composite_v2.py: WEIGHTS_V3, get_weight(), get_all_current_weights()",
            "adaptive_weights": "adaptive_signal_optimizer.py: AdaptiveSignalOptimizer, update_weights(), state/signal_weights.json",
            "overlay_overrides": "configs/overlays/promotion_candidate_1.json (merged in backtest/orchestrator)",
            "env_multipliers": "FLOW_WEIGHT_MULTIPLIER, UW_WEIGHT_MULTIPLIER, REGIME_WEIGHT_MULTIPLIER (env)",
        }

        # --- 2) Fetch current signal weights from droplet ---
        print("Fetching state/signal_weights.json from droplet...")
        weights_raw = _cat(c, f"{pd}/state/signal_weights.json", timeout=15)
        if weights_raw and "__MISSING__" not in weights_raw:
            try:
                payload["signal_weights"] = json.loads(weights_raw)
            except json.JSONDecodeError:
                payload["signal_weights"] = {"_raw_preview": weights_raw[:1000]}
        else:
            payload["signal_weights"] = {"_note": "File missing or empty on droplet"}

        # --- 3) Run signal audit diagnostic on droplet ---
        print("Running signal_audit_diagnostic.py on droplet...")
        out_audit, err_audit, rc_audit = _run(c, "python3 scripts/signal_audit_diagnostic.py 2>/dev/null", timeout=90)
        raw_audit = out_audit or "{}"
        for line in raw_audit.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    payload["signal_audit"] = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
        else:
            try:
                payload["signal_audit"] = json.loads(raw_audit)
            except json.JSONDecodeError:
                payload["signal_audit"] = {"error": "Failed to parse diagnostic", "raw_tail": raw_audit[-800:]}
        if rc_audit != 0 and err_audit:
            payload["errors"].append(f"signal_audit exit {rc_audit}: {err_audit[:200]}")

        # --- 4) Run full signal review on droplet ---
        print("Running full_signal_review_on_droplet.py on droplet...")
        out_review, err_review, rc_review = _run(c, "python3 scripts/full_signal_review_on_droplet.py 2>&1", timeout=180)
        if rc_review != 0 and err_review:
            payload["errors"].append(f"full_signal_review exit {rc_review}: {err_review[:200]}")

        # --- 5) Fetch signal_review artifacts ---
        funnel_json = _cat(c, f"{pd}/reports/signal_review/signal_funnel.json", timeout=15)
        if funnel_json and "__MISSING__" not in funnel_json:
            try:
                payload["signal_funnel"] = json.loads(funnel_json)
            except json.JSONDecodeError:
                payload["signal_funnel"] = {"_raw_preview": funnel_json[:1500]}
        funnel_md = _cat(c, f"{pd}/reports/signal_review/signal_funnel.md", timeout=15)
        if funnel_md and "__MISSING__" not in funnel_md:
            payload["funnel_md"] = funnel_md[:12000]
        breakdown_md = _cat(c, f"{pd}/reports/signal_review/signal_score_breakdown_summary.md", timeout=15)
        if breakdown_md and "__MISSING__" not in breakdown_md:
            payload["breakdown_md"] = breakdown_md[:8000]

        # --- 6) Build actionable bullets ---
        audit = payload["signal_audit"]
        dead = audit.get("dead_or_muted") or []
        contrib = audit.get("composite_contribution") or {}
        dist = audit.get("composite_distribution") or {}
        payload["actionable"] = []
        if dead:
            for d in dead:
                payload["actionable"].append(f"FIX: Signal '{d.get('signal_name')}' {d.get('failure_mode')} — {d.get('suspected_root_cause', '')}")
        zero_contrib = [k for k, v in contrib.items() if isinstance(v, dict) and (v.get("share_pct") or 0) == 0 and k != "freshness_factor"]
        if zero_contrib:
            payload["actionable"].append(f"REVIEW: Signals with ~0 contribution: {', '.join(zero_contrib[:15])}")
        mean_score = dist.get("mean")
        if mean_score is not None and float(mean_score) < 1.5:
            payload["actionable"].append("REVIEW: Composite score distribution compressed (mean < 1.5); consider threshold or weight rebalance.")
        if payload["signal_weights"].get("_note"):
            payload["actionable"].append("NOTE: state/signal_weights.json missing on droplet; adaptive weights may not be active.")
        if not payload["actionable"]:
            payload["actionable"].append("No critical issues; monitor composite contribution and dead/muted list.")
        # Derive from funnel if present
        funnel = payload.get("signal_funnel") or {}
        if isinstance(funnel, dict):
            dom = funnel.get("dominant_choke_point") or {}
            stage = dom.get("stage") or ""
            reason = (dom.get("reason") or "").lower()
            count = funnel.get("total_candidates") or 0
            if "expectancy" in stage and "score_floor" in reason and count > 0:
                payload["actionable"].insert(0, f"Score floor choke: 100% of {count} candidates blocked at {stage} ({reason}). Lower MIN_EXEC_SCORE for paper or increase weights so composite reaches >=2.5 to get executions.")
            cov = funnel.get("gate_truth_coverage_pct")
            if cov is not None and float(cov) == 0:
                payload["actionable"].append("Gate truth coverage 0%; enable expectancy_gate_truth logging for accurate choke reasons.")

    # --- 7) Write JSON (sanitize for serialization) ---
    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(x) for x in obj]
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        return str(obj)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(_sanitize(payload), f, indent=2)

    # --- 8) Write MD report ---
    lines = [
        "# Actionable Signal Data Report",
        "",
        f"**Date:** {date_str}",
        f"**Source:** Droplet (run at report generation time)",
        "",
        "---",
        "## 1. Where we adjust signals",
        "",
        "| Location | Description |",
        "|----------|-------------|",
    ]
    for k, v in (payload["where_we_adjust"] or {}).items():
        lines.append(f"| {k} | {v} |")
    lines.extend([
        "",
        "---",
        "## 2. Current signal weights (droplet state)",
        "",
        "```json",
        json.dumps(payload["signal_weights"], indent=2)[:4000],
        "```",
        "",
        "---",
        "## 3. Signal audit summary",
        "",
    ])
    if payload["signal_audit"].get("error"):
        lines.append(f"**Error:** {payload['signal_audit']['error']}")
    else:
        lines.append(f"- **Sample size:** {payload['signal_audit'].get('sample_size', 0)}")
        lines.append(f"- **Composite distribution:** min={dist.get('min')} max={dist.get('max')} mean={dist.get('mean')}")
        lines.append(f"- **Dead or muted:** {len(dead)}")
        if dead:
            for d in dead:
                lines.append(f"  - {d.get('signal_name')}: {d.get('failure_mode')} — {d.get('suspected_root_cause', '')}")
        contrib_table = payload["signal_audit"].get("composite_contribution") or {}
        if contrib_table:
            lines.append("")
            lines.append("| Signal | sum_abs | share_pct |")
            lines.append("|--------|--------|-----------|")
            for k, v in list(contrib_table.items())[:25]:
                if isinstance(v, dict):
                    lines.append(f"| {k} | {v.get('sum_abs')} | {v.get('share_pct')} |")
    lines.extend([
        "",
        "---",
        "## 4. Signal funnel / how signals hit the data",
        "",
    ])
    if payload["funnel_md"]:
        lines.append(payload["funnel_md"][:6000])
        if len(payload["funnel_md"]) > 6000:
            lines.append("\n... (truncated)")
    else:
        lines.append("*(signal_funnel.md not found or empty on droplet)*")
    if payload["breakdown_md"]:
        lines.extend(["", "### Score breakdown summary", "", payload["breakdown_md"][:4000]])
    lines.extend([
        "",
        "---",
        "## 5. Actionable items",
        "",
    ])
    for a in payload["actionable"]:
        lines.append(f"- {a}")
    lines.extend([
        "",
        "---",
        "## 6. JSON details",
        "",
        f"Full machine-readable payload: `reports/ACTIONABLE_SIGNAL_DATA_{date_str}.json`",
        "",
    ])
    if payload["errors"]:
        lines.extend(["", "### Errors", ""] + [f"- {e}" for e in payload["errors"]])

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")
    print("\n--- Actionable items ---")
    for a in payload["actionable"]:
        print(f"  • {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
