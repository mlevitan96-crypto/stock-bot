#!/usr/bin/env python3
"""
Phase-2 Activation Proof: run verification commands, collect counts/samples, write
reports/PHASE2_ACTIVATION_PROOF_<DATE>.md. Run on droplet after restart + 5 min runtime.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"
LOGS = REPO / "logs"
STATE = REPO / "state"


def _run(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 30) -> Tuple[str, str, int]:
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd or REPO,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode
    except Exception as e:
        return "", str(e), -1


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"), help="YYYY-MM-DD")
    args = ap.parse_args()
    date_str = args.date

    lines: List[str] = []
    lines.append("# Phase-2 Activation Proof")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Date:** {date_str}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 0) log_sink_confirmed
    lines.append("## 0. log_sink_confirmed (system_events.jsonl)")
    lines.append("")
    se_path = LOGS / "system_events.jsonl"
    sink_matches: List[str] = []
    if se_path.exists():
        out, _, _ = _run(
            ["grep", "-n", "log_sink_confirmed", str(se_path)],
            timeout=15,
        )
        sink_matches = (out or "").splitlines()
    sink_ok = len(sink_matches) > 0
    lines.append(f"**Count:** {len(sink_matches)}")
    for ln in sink_matches[-5:]:
        lines.append(f"    {ln[:200]}")
    lines.append("")

    # 1) Phase-2 heartbeats (last 50)
    lines.append("## 1. Phase-2 heartbeats (last 50)")
    lines.append("")
    pattern = '"phase2"'  # match subsystem "phase2" or event_type "phase2_heartbeat" etc.
    all_matches: List[str] = []
    if se_path.exists():
        out, err, rc = _run(
            ["grep", "-n", pattern, str(se_path)],
            timeout=15,
        )
        all_matches = (out or "").splitlines()
    last_50 = all_matches[-50:] if len(all_matches) > 50 else all_matches
    count = len(all_matches)
    lines.append(f"**Count:** {count}")
    lines.append("")
    for ln in last_50[:20]:
        lines.append(f"    {ln[:200]}")
    if len(last_50) > 20:
        lines.append(f"    ... and {len(last_50) - 20} more")
    lines.append("")

    # 2) trade_intent
    lines.append("## 2. trade_intent (run.jsonl)")
    lines.append("")
    run_path = LOGS / "run.jsonl"
    ti_lines = []
    if run_path.exists():
        out2, _, _ = _run(
            ["grep", "-n", "trade_intent", str(run_path)],
            timeout=15,
        )
        ti_lines = (out2 or "").splitlines()
    lines.append(f"**Count:** {len(ti_lines)}")
    lines.append("")
    for ln in ti_lines[:10]:
        lines.append(f"    {ln[:200]}")
    if len(ti_lines) > 10:
        lines.append(f"    ... and {len(ti_lines) - 10} more")
    lines.append("")

    # 3) shadow_variant_decision
    lines.append("## 3. shadow_variant_decision (shadow.jsonl)")
    lines.append("")
    sh_path = LOGS / "shadow.jsonl"
    sv_lines: List[str] = []
    if sh_path.exists():
        out3, _, _ = _run(
            ["grep", "-n", "shadow_variant_decision", str(sh_path)],
            timeout=15,
        )
        sv_lines = (out3 or "").splitlines()
    lines.append(f"**Count:** {len(sv_lines)}")
    lines.append("")
    for ln in sv_lines[:10]:
        lines.append(f"    {ln[:200]}")
    if len(sv_lines) > 10:
        lines.append(f"    ... and {len(sv_lines) - 10} more")
    lines.append("")

    # 4) symbol_risk_features.json
    lines.append("## 4. symbol_risk_features.json")
    lines.append("")
    risk_path = STATE / "symbol_risk_features.json"
    n_syms = 0
    if risk_path and risk_path.exists():
        try:
            d = json.loads(risk_path.read_text(encoding="utf-8")) or {}
            syms = d.get("symbols") if isinstance(d.get("symbols"), dict) else {}
            n_syms = len([k for k in syms if isinstance(k, str) and not k.startswith("_")])
        except Exception as e:
            lines.append(f"**FAIL:** could not read or parse: {e}")
    else:
        lines.append("**FAIL:** file missing")
    lines.append(f"**Symbol count:** {n_syms}")
    lines.append("")

    # 5) EOD diagnostic
    lines.append("## 5. EOD Alpha Diagnostic")
    lines.append("")
    eod_path = REPORTS / f"EOD_ALPHA_DIAGNOSTIC_{date_str}.md"
    if not eod_path.exists():
        out5, err5, rc5 = _run(
            [sys.executable, "reports/_daily_review_tools/generate_eod_alpha_diagnostic.py", "--date", date_str],
            timeout=60,
        )
        if rc5 != 0:
            lines.append(f"**FAIL:** generate script exited {rc5}: {err5[:300]}")
        else:
            lines.append("**Generated.**")
    else:
        lines.append("**Exists.**")
    lines.append("")

    # 6) Pass/fail summary
    lines.append("## 6. PASS/FAIL summary")
    lines.append("")
    phase2_ok = count > 0
    ti_ok = len(ti_lines) > 0
    shadow_ok = len(sv_lines) > 0
    risk_ok = n_syms > 0
    eod_ok = (REPORTS / f"EOD_ALPHA_DIAGNOSTIC_{date_str}.md").exists()
    lines.append(f"- **log_sink_confirmed:** {'PASS' if sink_ok else 'FAIL'}")
    lines.append(f"- **phase2_heartbeat:** {'PASS' if phase2_ok else 'FAIL'}")
    lines.append(f"- **trade_intent (real or dry-run):** {'PASS' if ti_ok else 'FAIL'}")
    lines.append(f"- **shadow_variant_decision / summary:** {'PASS' if shadow_ok else 'FAIL'}")
    lines.append(f"- **symbol_risk_features (>0 symbols):** {'PASS' if risk_ok else 'FAIL'}")
    lines.append(f"- **EOD diagnostic present:** {'PASS' if eod_ok else 'FAIL'}")
    lines.append("")
    all_ok = sink_ok and phase2_ok and ti_ok and shadow_ok and risk_ok and eod_ok
    lines.append(f"**Overall:** {'PASS' if all_ok else 'FAIL'}")
    lines.append("")

    out_path = REPORTS / f"PHASE2_ACTIVATION_PROOF_{date_str}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
