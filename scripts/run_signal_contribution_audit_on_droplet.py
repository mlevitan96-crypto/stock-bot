#!/usr/bin/env python3
"""
Signal contribution nuclear audit on DROPLET.
Uses DropletClient; runs in project_dir. Runs scripts/signal_audit_diagnostic.py on droplet,
captures JSON, writes report bundle to reports/signal_audit/<YYYYMMDD>/.
Verdict: FAIL if high-impact signal dead/muted, composite compressed, >20% signals ~0 contribution. PASS otherwise.
NO TUNING. NO STRATEGY CHANGES.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE_TAG = datetime.now(timezone.utc).strftime("%Y%m%d")
AUDIT_DIR = REPO / "reports" / "signal_audit" / DATE_TAG
ZERO_CONTRIBUTION_PCT_THRESHOLD = 20.0  # FAIL if more than this % of signals contribute ~0


def _run(c, command: str, timeout: int = 120):
    return c._execute_with_cd(command, timeout=timeout)


def _write_reports(data: dict, out_dir: Path) -> tuple[str, list]:
    """Write 00_summary.md through 08_verdict.md. Return (verdict, dead_or_muted_list)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    err = data.get("error")
    dead_or_muted = list(data.get("dead_or_muted") or [])
    dist = data.get("composite_distribution") or {}
    contrib = data.get("composite_contribution") or {}
    n_zero_contrib = sum(1 for c, v in contrib.items() if isinstance(v, dict) and (v.get("share_pct") or 0) == 0 and c != "freshness_factor")
    comp_names = [k for k in contrib.keys() if k != "freshness_factor"]
    n_signals = len(comp_names) or 1
    pct_zero_contrib = 100.0 * n_zero_contrib / n_signals
    compressed = (dist.get("pct_below_2", 0) or 0) >= 80 or (dist.get("mean", 1) or 0) < 1.5
    verdict = "FAIL" if (err or dead_or_muted or compressed or pct_zero_contrib > ZERO_CONTRIBUTION_PCT_THRESHOLD) else "PASS"

    # 01 Signal inventory
    inv = data.get("signal_inventory") or []
    lines = ["# 01 Signal inventory", "", "| name | source | weight | expected_range |"]
    for i in inv:
        lines.append(f"| {i.get('name', '')} | {i.get('source', '')} | {i.get('weight', '')} | {i.get('expected_range', '')} |")
    (out_dir / "01_signal_inventory.md").write_text("\n".join(lines), encoding="utf-8")

    # 02 Execution
    exec_counts = data.get("execution") or {}
    lines = ["# 02 Signal execution", "", "Executions per signal (sample size = {}).".format(data.get("sample_size", 0)), "", "```", json.dumps(exec_counts, indent=2), "```"]
    (out_dir / "02_signal_execution.md").write_text("\n".join(lines), encoding="utf-8")

    # 03 Signal values
    va = data.get("value_audit") or {}
    lines = ["# 03 Signal values", "", "| signal | min | max | mean | pct_zero | pct_nan | constant |"]
    for k, v in va.items():
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            k, v.get("min"), v.get("max"), v.get("mean"), v.get("pct_zero"), v.get("pct_nan"), v.get("constant")))
    (out_dir / "03_signal_values.md").write_text("\n".join(lines), encoding="utf-8")

    # 04 Weights
    wa = data.get("weight_audit") or {}
    lines = ["# 04 Signal weights", "", "```", json.dumps(wa, indent=2), "```"]
    (out_dir / "04_signal_weights.md").write_text("\n".join(lines), encoding="utf-8")

    # 05 Composite contribution
    lines = ["# 05 Composite contribution", "", "| signal | sum_abs | share_pct |"]
    for k, v in (data.get("composite_contribution") or {}).items():
        if isinstance(v, dict):
            lines.append("| {} | {} | {} |".format(k, v.get("sum_abs"), v.get("share_pct")))
    (out_dir / "05_composite_contribution.md").write_text("\n".join(lines), encoding="utf-8")

    # 06 Distribution
    lines = ["# 06 Distribution checks", "", "Composite score distribution (sample size = {}).".format(data.get("sample_size", 0)), "", "```", json.dumps(dist, indent=2), "```", "", "Compression near floor (pct_below_2>=80 or mean<1.5): **{}**".format(compressed)]
    (out_dir / "06_distribution_checks.md").write_text("\n".join(lines), encoding="utf-8")

    # 07 Dead/muted
    lines = ["# 07 Dead or muted signals", "", "| signal_name | failure_mode | suspected_root_cause | confidence |"]
    for d in dead_or_muted:
        lines.append("| {} | {} | {} | {} |".format(d.get("signal_name"), d.get("failure_mode"), d.get("suspected_root_cause"), d.get("confidence")))
    if not dead_or_muted:
        lines.append("(none)")
    (out_dir / "07_dead_or_muted_signals.md").write_text("\n".join(lines), encoding="utf-8")

    # 08 Verdict
    reasons = []
    if err:
        reasons.append("error: " + str(err))
    if data.get("sample_size", 0) == 0 and not err:
        reasons.append("no sample data (cache empty or no symbols)")
    if dead_or_muted:
        reasons.append("{} dead/muted signal(s)".format(len(dead_or_muted)))
    if compressed and data.get("sample_size", 0) > 0:
        reasons.append("composite distribution compressed near floor")
    elif compressed and data.get("sample_size", 0) == 0:
        reasons.append("no composite distribution (sample size 0)")
    if pct_zero_contrib > ZERO_CONTRIBUTION_PCT_THRESHOLD and data.get("sample_size", 0) > 0:
        reasons.append("{:.1f}% of signals contribute ~0 (>{:.0f}%)".format(pct_zero_contrib, ZERO_CONTRIBUTION_PCT_THRESHOLD))
    lines = [
        "# 08 Verdict",
        "",
        "## Verdict: **{}**".format(verdict),
        "",
        "## Composite distribution summary",
        "```",
        json.dumps(dist, indent=2),
        "```",
        "",
        "## Dead or muted (count = {})".format(len(dead_or_muted)),
        "; ".join(reasons) if reasons else "None.",
        "",
        "## Rules",
        "FAIL if: high-impact signal dead/muted, composite compressed, >{}% signals ~0 contribution.".format(ZERO_CONTRIBUTION_PCT_THRESHOLD),
        "PASS only if: all signals execute, all contribute non-zero mass, distribution sane.",
    ]
    (out_dir / "08_verdict.md").write_text("\n".join(lines), encoding="utf-8")

    # 00 Summary
    lines = [
        "# 00 Summary",
        "",
        "**Date:** " + DATE_TAG,
        "**Verdict:** " + verdict,
        "**Sample size:** " + str(data.get("sample_size", 0)),
        "**Composite (min/max/mean):** {} / {} / {}".format(dist.get("min"), dist.get("max"), dist.get("mean")),
        "**Dead or muted:** " + str(len(dead_or_muted)),
        "",
        "## Report sections",
        "01_signal_inventory.md … 08_verdict.md",
    ]
    (out_dir / "00_summary.md").write_text("\n".join(lines), encoding="utf-8")

    return verdict, dead_or_muted


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print("Error: {} Need DropletClient.".format(e), file=sys.stderr)
        return 1

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    print("Running signal contribution audit on droplet; report bundle: {}".format(AUDIT_DIR))

    with DropletClient() as c:
        out, err, rc = _run(c, "python3 scripts/signal_audit_diagnostic.py 2>/dev/null", timeout=90)
    raw = out or "{}"
    try:
        # JSON may be preceded by log lines
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("{"):
                data = json.loads(line)
                break
        else:
            data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"error": "Failed to parse diagnostic output", "raw_tail": raw[-500:] if len(raw) > 500 else raw}

    verdict, dead_or_muted = _write_reports(data, AUDIT_DIR)
    dist = data.get("composite_distribution") or {}

    print("")
    print("=== SIGNAL CONTRIBUTION AUDIT RESULT ===")
    print("Verdict: {}".format(verdict))
    print("Composite distribution: min={} max={} mean={}".format(dist.get("min"), dist.get("max"), dist.get("mean")))
    print("Dead or muted: {}".format(len(dead_or_muted)))
    for d in dead_or_muted:
        print("  - {} ({})".format(d.get("signal_name"), d.get("failure_mode")))
    print("Report bundle: {}".format(AUDIT_DIR))

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
