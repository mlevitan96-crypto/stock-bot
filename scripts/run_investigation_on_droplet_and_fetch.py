#!/usr/bin/env python3
"""
Run investigation on droplet (baseline, full signal review, closed loops, optional signal breakdown)
and fetch report contents back. Prints data and writes fetched reports to reports/investigation/fetched/.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
FETCHED_DIR = REPO / "reports" / "investigation" / "fetched"


def _run(c, cmd: str, timeout: int = 120):
    """Execute on droplet with project_dir as cwd."""
    pd = c.project_dir
    full = f"cd {pd} && {cmd}"
    return c._execute(full, timeout=timeout)


def _cat(c, remote_path: str) -> str:
    """Read remote file content."""
    out, err, rc = _run(c, f"cat {remote_path} 2>/dev/null || echo '__MISSING__'", timeout=15)
    return out.strip() if out else ""


def main() -> int:
    try:
        from droplet_client import DropletClient
    except Exception as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        print("Set DROPLET_HOST (and key/password) or droplet_config.json", file=sys.stderr)
        return 1

    FETCHED_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    with DropletClient() as c:
        # 1) Git pull
        out, err, rc = _run(c, "git fetch origin && git pull origin main", timeout=60)
        results.append(("git_pull", rc, out[:500] + ("..." if len(out) > 500 else "")))
        print("--- GIT PULL ---")
        print(out[:800] if out else "(no output)")
        if rc != 0:
            print("Warning: git pull non-zero", file=sys.stderr)

        # 1b) Verify script presence (Phase 1)
        out0, err0, rc0 = _run(c, "python3 scripts/verify_droplet_script_presence.py", timeout=30)
        if out0:
            print("\n--- SCRIPT PRESENCE ---")
            print(out0[:400])
        # 1c) Signal inventory + usage map (Phase 1)
        _run(c, "python3 scripts/signal_inventory_on_droplet.py", timeout=30)
        _run(c, "python3 scripts/signal_usage_map_on_droplet.py", timeout=30)
        # 1d) Signal flow audit (load uw_cache, run composite for all cache symbols, get per-signal values + dead/muted)
        out_audit, err_audit, rc_audit = _run(c, "python3 scripts/signal_audit_diagnostic.py 2>/dev/null", timeout=90)
        if out_audit and out_audit.strip():
            try:
                import json as _json
                audit_json = _json.loads(out_audit.strip())
                (FETCHED_DIR / "signal_audit_diagnostic.json").write_text(_json.dumps(audit_json, indent=2, default=str), encoding="utf-8")
                print("\n--- SIGNAL AUDIT DIAGNOSTIC ---")
                print(f"sample_size={audit_json.get('sample_size', 0)}, error={audit_json.get('error')}, dead_or_muted={len(audit_json.get('dead_or_muted', []))}")
            except Exception:
                (FETCHED_DIR / "signal_audit_diagnostic_raw.txt").write_text(out_audit[:50000], encoding="utf-8")
        # 1d) Truth log enablement proof (Phase 2) — documents env state
        out_t, err_t, rc_t = _run(c, "python3 scripts/truth_log_enablement_proof_on_droplet.py", timeout=30)
        if out_t:
            print("\n--- TRUTH LOG ENABLEMENT ---")
            print(out_t[:300])
        # 2) Baseline snapshot
        out, err, rc = _run(c, "python3 scripts/investigation_baseline_snapshot_on_droplet.py", timeout=60)
        results.append(("baseline_snapshot", rc, out))
        print("\n--- BASELINE SNAPSHOT ---")
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)

        # 3) Full signal review (no --capture to avoid long run; use existing ledger)
        out, err, rc = _run(c, "python3 scripts/full_signal_review_on_droplet.py --days 7", timeout=120)
        results.append(("full_signal_review", rc, out))
        print("\n--- FULL SIGNAL REVIEW ---")
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)

        # 3b) Expectancy gate truth 200 (if enough lines)
        out_gt, _, _ = _run(c, "wc -l logs/expectancy_gate_truth.jsonl 2>/dev/null || echo '0'", timeout=10)
        n_gate = 0
        if out_gt:
            try:
                n_gate = int(out_gt.strip().split()[0])
            except Exception:
                pass
        if n_gate >= 200:
            _run(c, "python3 scripts/expectancy_gate_truth_report_200_on_droplet.py", timeout=30)
        else:
            print(f"\n--- EXPECTANCY GATE TRUTH 200: skipped (lines={n_gate}, need 200) ---")
        # 3c) Signal pipeline deep dive + coverage/waste (Phase 3–4)
        _run(c, "python3 scripts/signal_pipeline_deep_dive_on_droplet.py --symbols SPY,QQQ,COIN,NVDA,TSLA --n 25 --window-hours 168", timeout=60)
        _run(c, "python3 scripts/signal_coverage_and_waste_report_on_droplet.py", timeout=30)
        # 4a) Order reconciliation (Phase 4)
        out4a, err4a, rc4a = _run(c, "python3 scripts/order_reconciliation_on_droplet.py", timeout=30)
        if out4a:
            print("\n--- ORDER RECONCILIATION ---")
            print(out4a)
        # 4b) Closed loops checklist
        out, err, rc = _run(c, "python3 scripts/run_closed_loops_checklist_on_droplet.py", timeout=30)
        results.append(("closed_loops_checklist", rc, out))
        print("\n--- CLOSED LOOPS CHECKLIST ---")
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)

        # 5) Signal breakdown summary (if log has >= 100 lines)
        out, err, rc = _run(c, "wc -l logs/signal_score_breakdown.jsonl 2>/dev/null || echo '0'", timeout=10)
        n_breakdown = 0
        if out:
            try:
                n_breakdown = int(out.strip().split()[0])
            except Exception:
                pass
        if n_breakdown >= 100:
            out2, err2, rc2 = _run(c, "python3 scripts/signal_score_breakdown_summary_on_droplet.py", timeout=60)
            results.append(("signal_breakdown_summary", rc2, out2))
            print("\n--- SIGNAL BREAKDOWN SUMMARY ---")
            print(out2 or "(no output)")
        else:
            print(f"\n--- SIGNAL BREAKDOWN: skipped (lines={n_breakdown}, need 100) ---")

        # Fetch report files
        pd = c.project_dir
        to_fetch = [
            ("reports/investigation/BASELINE_SNAPSHOT.md", "BASELINE_SNAPSHOT.md"),
            ("reports/investigation/CLOSED_LOOPS_CHECKLIST.md", "CLOSED_LOOPS_CHECKLIST.md"),
            ("reports/investigation/DROPLET_SCRIPT_PRESENCE.md", "DROPLET_SCRIPT_PRESENCE.md"),
            ("reports/investigation/ORDER_RECONCILIATION.md", "ORDER_RECONCILIATION.md"),
            ("reports/investigation/TRUTH_LOG_ENABLEMENT_PROOF.md", "TRUTH_LOG_ENABLEMENT_PROOF.md"),
            ("reports/signal_review/signal_funnel.md", "signal_funnel.md"),
            ("reports/signal_review/signal_funnel.json", "signal_funnel.json"),
            ("reports/signal_review/paper_trade_metric_reconciliation.md", "paper_trade_metric_reconciliation.md"),
            ("reports/signal_review/multi_model_adversarial_review.md", "multi_model_adversarial_review.md"),
            ("reports/signal_review/signal_score_breakdown_summary.md", "signal_score_breakdown_summary.md"),
            ("reports/signal_review/expectancy_gate_truth_200.md", "expectancy_gate_truth_200.md"),
            ("reports/signal_review/SIGNAL_PIPELINE_DEEP_DIVE.md", "SIGNAL_PIPELINE_DEEP_DIVE.md"),
            ("reports/signal_review/SIGNAL_COVERAGE_AND_WASTE.md", "SIGNAL_COVERAGE_AND_WASTE.md"),
        ]
        for remote, local_name in to_fetch:
            content = _cat(c, f"{pd}/{remote}")
            if content and "__MISSING__" not in content:
                local_path = FETCHED_DIR / local_name
                local_path.write_text(content, encoding="utf-8")
                print(f"\nFetched: {remote} -> {local_path}")
                results.append((f"fetched_{local_name}", 0, f"{len(content)} chars"))
            else:
                results.append((f"fetched_{local_name}", 1, "missing or empty"))
    # Write SIGNAL_FLOW_FINDINGS.md from fetched signal_audit_diagnostic.json
    audit_path = FETCHED_DIR / "signal_audit_diagnostic.json"
    findings_path = REPO / "reports" / "investigation" / "SIGNAL_FLOW_FINDINGS.md"
    if audit_path.exists():
        try:
            import json as _json
            audit = _json.loads(audit_path.read_text(encoding="utf-8"))
            lines = [
                "# Signal flow findings (from droplet)",
                "",
                "Source: `scripts/signal_audit_diagnostic.py` run on droplet with `data/uw_flow_cache.json`. Same enrichment path as main.py (enrich_signal → compute_composite_score_v2).",
                "",
                "## Summary",
                "",
                f"- **Sample size:** {audit.get('sample_size', 0)} symbols",
                f"- **Error:** {audit.get('error') or 'None'}",
                f"- **Composite distribution:** {audit.get('composite_distribution', {})}",
                "",
                "## Signals not working / passing 0 / not wired",
                "",
            ]
            dead = audit.get("dead_or_muted") or []
            if dead:
                lines.append("| signal_name | failure_mode | suspected_root_cause | confidence |")
                lines.append("|-------------|--------------|----------------------|------------|")
                for d in dead:
                    lines.append(f"| {d.get('signal_name', '')} | {d.get('failure_mode', '')} | {d.get('suspected_root_cause', '')} | {d.get('confidence', '')} |")
            else:
                lines.append("(None identified as dead_or_muted by diagnostic.)")
            lines.extend(["", "## Value audit (per-signal across samples)", ""])
            va = audit.get("value_audit") or {}
            for name, v in sorted(va.items(), key=lambda x: (x[1].get("pct_zero", 100), -x[1].get("mean", 0) or 0)):
                lines.append(f"- **{name}:** mean={v.get('mean')}, pct_zero={v.get('pct_zero')}%, constant={v.get('constant')}")
            lines.extend(["", "## Per-symbol breakdown (SPY, QQQ, COIN, NVDA, TSLA)", ""])
            per = audit.get("per_symbol") or {}
            for sym in ["SPY", "QQQ", "COIN", "NVDA", "TSLA"]:
                p = per.get(sym) or {}
                if "error" in p:
                    lines.append(f"### {sym}: {p.get('error')}")
                else:
                    lines.append(f"### {sym}: score={p.get('score')}, missing={p.get('missing_components', [])}")
                    src = p.get("component_sources") or {}
                    comps = p.get("components") or {}
                    zero_or_missing = [n for n in comps if src.get(n) == "missing" or (comps.get(n) or 0) == 0]
                    if zero_or_missing:
                        lines.append(f"- Zero or missing: {', '.join(zero_or_missing)}")
                lines.append("")
            lines.append("## Root cause (why low scores)")
            lines.append("")
            dist = audit.get("composite_distribution") or {}
            mean_score = dist.get("mean")
            pct_below_2 = dist.get("pct_below_2")
            if mean_score is not None and float(mean_score) < 2.5:
                lines.append(f"Composite mean score is **{mean_score}** (below MIN_EXEC_SCORE 2.5). ")
            if dead:
                lines.append(f"**{len(dead)}** signals are dead or muted (zeroed, unweighted, or no contribution). ")
            lines.append("Primary drivers: (1) Many components default to 0.2 or 0.25 when data is missing (congress, shorts, institutional, market_tide, calendar, greeks, ftd, oi, etf, squeeze_score). (2) Flow/conviction/dark_pool/insider from UW cache—if cache is sparse or conviction/sentiment missing, flow component is small. (3) Freshness decay: if data is stale, composite_raw * freshness drops. Fix: ensure UW cache is populated and fresh; ensure expanded_intel has symbol data; check conviction/sentiment not None.")
            lines.append("")
            findings_path.parent.mkdir(parents=True, exist_ok=True)
            findings_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"\nWrote {findings_path}")
        except Exception as e:
            print(f"Could not write SIGNAL_FLOW_FINDINGS: {e}", file=sys.stderr)

    # Summary
    print("\n" + "=" * 60)
    print("INVESTIGATION RUN SUMMARY")
    print("=" * 60)
    for name, code, note in results:
        print(f"  {name}: exit={code}  {note[:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
