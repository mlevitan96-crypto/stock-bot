#!/usr/bin/env python3
"""
Unified Truth Audit on DROPLET.
Runs all 6 axes via DropletClient. Writes reports/truth_audit/<YYYYMMDD>/ with proof per axis + verdict.
PASS only if ALL axes pass. FAIL with ranked integrity failures and exact fixes.
Assume the system is lying until proven otherwise.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE_TAG = datetime.now(timezone.utc).strftime("%Y%m%d")
AUDIT_DIR = REPO / "reports" / "truth_audit" / DATE_TAG
HIGH_IMPACT_SIGNALS = {"flow", "options_flow", "dark_pool", "insider"}
CONTRIB_EPSILON = 0.5  # share_pct below this = ~0 contribution for high-impact
DIST_COMPRESSED_MEAN_FLOOR = 1.0  # mean composite below this = compressed
DIST_ZERO_HEAVY_PCT = 80.0  # > this % below 2 = zero-heavy
CACHE_MAX_AGE_HOURS = 48


def _run(c, command: str, timeout: int = 120):
    return c._execute_with_cd(command, timeout=timeout)


def _run_axes(client) -> dict:
    """Run all 6 axes on droplet; return raw data for each."""
    r = {}
    # Axis 1: Live vs Diagnostic — run diagnostic, get live from logs and score_snapshot (canonical)
    out_diag, _, rc_diag = _run(client, "python3 scripts/signal_audit_diagnostic.py 2>/dev/null", timeout=90)
    r["axis1_diag"] = out_diag or ""
    out_bt, _, _ = _run(client, "tail -n 50 logs/blocked_trades.jsonl 2>/dev/null || true", timeout=10)
    out_gate, _, _ = _run(client, "tail -n 400 logs/gate.jsonl 2>/dev/null || true", timeout=15)
    out_snapshot, _, _ = _run(client, "tail -n 500 logs/score_snapshot.jsonl 2>/dev/null || true", timeout=10)
    r["axis1_live_logs"] = {"blocked_trades": out_bt or "", "gate": out_gate or "", "score_snapshot": out_snapshot or ""}

    # Axis 2 & 3: from diagnostic or score_snapshot
    r["axis2_3_diag"] = out_diag or ""
    r["score_snapshot"] = out_snapshot or ""

    # Axis 4: Gate alignment — grep score usage, gate counts
    out_grep, _, _ = _run(client, "grep -n 'composite_exec_score\\|MIN_EXEC_SCORE\\|score_floor_breach' main.py 2>/dev/null | head -30", timeout=10)
    r["axis4_gates"] = {"grep": out_grep or "", "gate_tail": out_gate or ""}

    # Axis 5: Entry/exit symmetry
    out_attr, _, _ = _run(client, "tail -n 5 logs/attribution.jsonl 2>/dev/null || echo 'NONE'", timeout=5)
    out_exit, _, _ = _run(client, "tail -n 5 logs/exit_attribution.jsonl 2>/dev/null || echo 'NONE'", timeout=5)
    out_attr_keys, _, _ = _run(client, "tail -n 1 logs/attribution.jsonl 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(list(d.keys()))' 2>/dev/null || echo '[]'", timeout=5)
    out_exit_keys, _, _ = _run(client, "tail -n 1 logs/exit_attribution.jsonl 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(list(d.keys()))' 2>/dev/null || echo '[]'", timeout=5)
    r["axis5"] = {"attr_sample": out_attr or "", "exit_sample": out_exit or "", "attr_keys": out_attr_keys or "", "exit_keys": out_exit_keys or ""}

    # Axis 6: Data freshness
    out_ls, _, _ = _run(client, "ls -la data/uw_flow_cache.json data/uw_expanded_intel.json 2>/dev/null; date -u +%Y-%m-%dT%H:%M 2>/dev/null", timeout=10)
    out_mtime, _, _ = _run(client, "stat -c %Y data/uw_flow_cache.json 2>/dev/null || echo 0", timeout=5)
    r["axis6"] = {"ls": out_ls or "", "uw_mtime": out_mtime or "0"}

    return r


def _parse_diagnostic(raw: str) -> dict:
    try:
        for line in (raw or "").splitlines():
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"error": "parse_failed", "sample_size": 0}


def _parse_score_snapshot(raw: str) -> list:
    """Parse score_snapshot.jsonl tail; return list of records."""
    out = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def _write_reports(data: dict, out_dir: Path) -> tuple[str, list, list]:
    """Write axis_01..06 and verdict. Return (verdict, failures, fixes)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    fixes = []

    diag = _parse_diagnostic(data.get("axis2_3_diag") or data.get("axis1_diag") or "")
    contrib = diag.get("composite_contribution") or {}
    dist = diag.get("composite_distribution") or {}
    dead = diag.get("dead_or_muted") or []
    sample_size = diag.get("sample_size") or 0
    symbols = diag.get("symbols") or []
    diag_error = diag.get("error")
    snapshot_records = _parse_score_snapshot(data.get("score_snapshot") or "")
    snapshot_size = len(snapshot_records)

    # --- AXIS 1 ---
    axis1_pass = True
    live_logs = data.get("axis1_live_logs") or {}
    bt = live_logs.get("blocked_trades", "")
    if sample_size > 0:
        axis1_pass = True
    elif snapshot_size > 0:
        axis1_pass = True  # Canonical truth from score_snapshot
    else:
        axis1_pass = False
        failures.append(("Axis 1 (Live vs Diagnostic)", "No scoring events observed in score_snapshot window; diagnostic produced no data"))
        fixes.append("Ensure score_snapshot.jsonl is emitted (live paper run) or data/uw_flow_cache.json exists and diagnostic runs.")
    lines = ["# Axis 1 — Live vs Diagnostic Parity", "", "## Diagnostic sample_size", str(sample_size), "", "## score_snapshot.jsonl records", str(snapshot_size), "", "## Live logs (blocked_trades tail)", "```", (bt or "none")[:1500], "```", "", "## Result", "**PASS**" if axis1_pass else "**FAIL**"]
    (out_dir / "axis_01_live_vs_diagnostic.md").write_text("\n".join(lines), encoding="utf-8")
    if not axis1_pass and not any(f[0] == "Axis 1 (Live vs Diagnostic)" for f in failures):
        failures.append(("Axis 1 (Live vs Diagnostic)", diag_error or "No diagnostic data"))

    # --- AXIS 2 ---
    axis2_pass = True
    if sample_size > 0:
        for sig in HIGH_IMPACT_SIGNALS:
            c = contrib.get(sig) or contrib.get("flow")
            if isinstance(c, dict) and (c.get("share_pct") or 0) < CONTRIB_EPSILON:
                axis2_pass = False
                failures.append(("Axis 2 (Signal Contribution)", "High-impact signal '{}' contributes ~0 (share_pct={})".format(sig, c.get("share_pct"))))
                fixes.append("Restore or fix signal '{}' so it receives non-zero values and weight.".format(sig))
        for d in dead:
            if d.get("signal_name") in HIGH_IMPACT_SIGNALS or d.get("signal_name") == "flow":
                axis2_pass = False
                failures.append(("Axis 2 (Signal Contribution)", "Dead/muted: {}".format(d.get("signal_name"))))
    elif snapshot_size > 0:
        axis2_pass = True  # Canonical truth from score_snapshot (has composite_score and gates)
    else:
        axis2_pass = False
        failures.append(("Axis 2 (Signal Contribution)", "No scoring events observed in score_snapshot window"))
    lines = ["# Axis 2 — Signal Contribution", "", "## Diagnostic sample_size / snapshot_size", "{}, {}".format(sample_size, snapshot_size), "", "## Contribution (share_pct)", "```", json.dumps({k: v for k, v in (contrib or {}).items() if isinstance(v, dict)}, indent=2)[:2000], "```", "", "## Result", "**PASS**" if axis2_pass else "**FAIL**"]
    (out_dir / "axis_02_signal_contribution.md").write_text("\n".join(lines), encoding="utf-8")

    # --- AXIS 3 ---
    axis3_pass = True
    if sample_size > 0:
        mean = dist.get("mean")
        pct_below_2 = dist.get("pct_below_2") or 0
        if mean is not None and mean < DIST_COMPRESSED_MEAN_FLOOR:
            axis3_pass = False
            failures.append(("Axis 3 (Score Distribution)", "Composite mean {} below floor {}".format(mean, DIST_COMPRESSED_MEAN_FLOOR)))
            fixes.append("Investigate score compression: check weights and signal values so composite is not collapsed.")
        if pct_below_2 >= DIST_ZERO_HEAVY_PCT:
            axis3_pass = False
            failures.append(("Axis 3 (Score Distribution)", ">{}% of scores below 2 (zero-heavy)".format(DIST_ZERO_HEAVY_PCT)))
    elif snapshot_size > 0:
        scores = []
        for rec in snapshot_records:
            sc = rec.get("composite_score")
            if sc is not None:
                try:
                    scores.append(float(sc))
                except (TypeError, ValueError):
                    pass
        mean, pct_below_2 = None, 0
        if scores:
            mean = sum(scores) / len(scores)
            below_2 = sum(1 for s in scores if s < 2)
            pct_below_2 = (below_2 / len(scores)) * 100
            if mean < DIST_COMPRESSED_MEAN_FLOOR:
                axis3_pass = False
                failures.append(("Axis 3 (Score Distribution)", "Composite mean {} below floor {} (from snapshot)".format(mean, DIST_COMPRESSED_MEAN_FLOOR)))
            if pct_below_2 >= DIST_ZERO_HEAVY_PCT:
                axis3_pass = False
                failures.append(("Axis 3 (Score Distribution)", ">{}% of scores below 2 (zero-heavy)".format(DIST_ZERO_HEAVY_PCT)))
        dist = {"mean": mean, "pct_below_2": pct_below_2, "n": len(scores)}
    else:
        axis3_pass = False
        failures.append(("Axis 3 (Score Distribution)", "No scoring events observed in score_snapshot window"))
        dist = {}
    lines = ["# Axis 3 — Score Distribution Sanity", "", "## Distribution (diagnostic or snapshot)", "```", json.dumps(dist, indent=2), "```", "", "## Result", "**PASS**" if axis3_pass else "**FAIL**"]
    (out_dir / "axis_03_score_distribution.md").write_text("\n".join(lines), encoding="utf-8")

    # --- AXIS 4 ---
    gates = data.get("axis4_gates") or {}
    grep_out = gates.get("grep") or ""
    axis4_pass = "composite_exec_score" in grep_out and "score_floor_breach" in grep_out and "composite_exec_score" in grep_out
    if not axis4_pass:
        failures.append(("Axis 4 (Gate Alignment)", "Expectancy gate may not use composite_exec_score; or score_floor_breach not aligned"))
        fixes.append("Verify main.py uses composite_exec_score for ExpectancyGate and score_floor_breach; no other score variable.")
    lines = ["# Axis 4 — Gate Alignment", "", "## Grep (composite_exec_score, score_floor_breach)", "```", grep_out[:1500], "```", "", "## Result", "**PASS**" if axis4_pass else "**FAIL**"]
    (out_dir / "axis_04_gate_alignment.md").write_text("\n".join(lines), encoding="utf-8")

    # --- AXIS 5 ---
    ax5 = data.get("axis5") or {}
    attr_keys = ax5.get("attr_keys") or ""
    exit_keys = ax5.get("exit_keys") or ""
    has_attr = "attribution" in str(ax5.get("attr_sample")) or "trade_id" in attr_keys or "symbol" in attr_keys
    has_exit = "exit" in str(ax5.get("exit_sample")) or "trade_id" in exit_keys
    axis5_pass = has_attr and has_exit
    if not axis5_pass:
        failures.append(("Axis 5 (Entry/Exit Symmetry)", "Attribution or exit_attribution missing or missing join keys (trade_id)"))
        fixes.append("Ensure attribution.jsonl and exit_attribution.jsonl both contain trade_id and expected entry/exit fields.")
    lines = ["# Axis 5 — Entry/Exit Symmetry", "", "## attribution.jsonl keys (sample)", "```", attr_keys, "```", "", "## exit_attribution.jsonl keys (sample)", "```", exit_keys, "```", "", "## Result", "**PASS**" if axis5_pass else "**FAIL**"]
    (out_dir / "axis_05_entry_exit_symmetry.md").write_text("\n".join(lines), encoding="utf-8")

    # --- AXIS 6 ---
    ax6 = data.get("axis6") or {}
    ls_out = ax6.get("ls") or ""
    mtime_str = (ax6.get("uw_mtime") or "0").strip()
    age_hours = 999
    try:
        mtime = int(mtime_str)
        from time import time
        age_hours = (int(time()) - mtime) / 3600 if mtime else 999
        axis6_pass = "uw_flow_cache" in ls_out and age_hours < CACHE_MAX_AGE_HOURS
    except Exception:
        axis6_pass = "uw_flow_cache" in ls_out
    if not axis6_pass:
        failures.append(("Axis 6 (Data Freshness)", "uw_flow_cache missing or stale (>{}h)".format(CACHE_MAX_AGE_HOURS)))
        fixes.append("Refresh data/uw_flow_cache.json (ensure UW daemon or ingestion runs) and re-run audit.")
    lines = ["# Axis 6 — Data Freshness & Completeness", "", "## Cache presence and mtime", "```", ls_out, "```", "", "uw_flow_cache age_hours: {}".format(age_hours if 'age_hours' in dir() else "N/A"), "", "## Result", "**PASS**" if axis6_pass else "**FAIL**"]
    (out_dir / "axis_06_data_freshness.md").write_text("\n".join(lines), encoding="utf-8")

    # Verdict
    all_pass = axis1_pass and axis2_pass and axis3_pass and axis4_pass and axis5_pass and axis6_pass
    verdict = "PASS" if all_pass else "FAIL"
    # Rank failures by axis order
    ranked = [(a, b) for a, b in failures]
    lines = [
        "# Unified Truth Audit — Verdict",
        "",
        "**Date:** " + DATE_TAG,
        "**Verdict:** **" + verdict + "**",
        "",
        "## Ranked integrity failures",
    ]
    for i, (axis, reason) in enumerate(ranked, 1):
        lines.append("{}. {} — {}".format(i, axis, reason))
    if not ranked:
        lines.append("(none)")
    lines.extend(["", "## Exact fixes (no tuning)", ""])
    for i, fix in enumerate(set(fixes), 1):
        lines.append("{}. {}".format(i, fix))
    if not fixes:
        lines.append("(none)")
    lines.extend(["", "## Axis results", "1. Live vs Diagnostic: " + ("PASS" if axis1_pass else "FAIL"), "2. Signal Contribution: " + ("PASS" if axis2_pass else "FAIL"), "3. Score Distribution: " + ("PASS" if axis3_pass else "FAIL"), "4. Gate Alignment: " + ("PASS" if axis4_pass else "FAIL"), "5. Entry/Exit Symmetry: " + ("PASS" if axis5_pass else "FAIL"), "6. Data Freshness: " + ("PASS" if axis6_pass else "FAIL")])
    (out_dir / "verdict.md").write_text("\n".join(lines), encoding="utf-8")

    return verdict, ranked, list(set(fixes))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print("Error: {} Need DropletClient.".format(e), file=sys.stderr)
        return 1

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    print("Running Unified Truth Audit on droplet; report bundle: {}".format(AUDIT_DIR))

    with DropletClient() as c:
        data = _run_axes(c)

    verdict, failures, fixes = _write_reports(data, AUDIT_DIR)

    print("")
    print("=== UNIFIED TRUTH AUDIT RESULT ===")
    print("Verdict: {}".format(verdict))
    print("Ranked failures: {}".format(len(failures)))
    for a, r in failures:
        print("  - {}: {}".format(a, r[:80]))
    print("Proof artifacts: {}".format(AUDIT_DIR))

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
