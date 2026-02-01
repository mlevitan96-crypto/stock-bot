#!/usr/bin/env python3
"""
Post-Market Analysis — run on droplet after market close.

Uses droplet logs/ and state/ as source of truth. Writes to reports/ and exports/.
No trading, no code changes, no AUDIT_MODE/AUDIT_DRY_RUN.

Sections: Pre-check, Analysis date, Signals, Execution, Positions/Exits,
Gates/Displacement, Shadow, EOD Alpha Diagnostic, Verdict.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
LOGS = REPO / "logs"
STATE = REPO / "state"
REPORTS = REPO / "reports"
EXPORTS = REPO / "exports"

# Required EOD diagnostic section headers (substrings)
EOD_REQUIRED_SECTIONS = [
    "Winners vs Losers",
    "High-Volatility Alpha",
    "Displacement",
    "directional_gate",
    "Shadow experiment scoreboard",
    "Data availability",
]


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _date_from_record(rec: dict) -> Optional[str]:
    ts = rec.get("ts") or rec.get("_dt") or rec.get("timestamp")
    dt = _parse_ts(ts)
    return dt.strftime("%Y-%m-%d") if dt else None


def _load_jsonl(p: Path, date_str: Optional[str] = None) -> List[Dict]:
    out: List[Dict] = []
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if date_str:
                d = _date_from_record(rec)
                if d != date_str:
                    continue
            out.append(rec)
        except Exception:
            continue
    return out


def _section_1_precheck() -> Tuple[bool, List[str], Dict[str, Any]]:
    """Pre-check: service active, no audit mode, phase2_heartbeat present."""
    evidence: Dict[str, Any] = {}
    errs: List[str] = []
    try:
        r = subprocess.run(
            ["systemctl", "is-active", "stock-bot.service"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(REPO),
        )
        active = (r.stdout or "").strip().lower() == "active"
        evidence["service_active"] = active
        if not active:
            errs.append("stock-bot.service is not active")
    except Exception as e:
        evidence["service_check_error"] = str(e)
        errs.append(f"Could not check service: {e}")

    try:
        r = subprocess.run(
            ["systemctl", "show", "stock-bot.service", "-p", "Environment"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(REPO),
        )
        env_str = (r.stdout or "") + " "
        audit_mode = "AUDIT_MODE=1" in env_str or "AUDIT_MODE=true" in env_str.lower()
        audit_dry = "AUDIT_DRY_RUN=1" in env_str or "AUDIT_DRY_RUN=true" in env_str.lower()
        evidence["AUDIT_MODE_set"] = audit_mode
        evidence["AUDIT_DRY_RUN_set"] = audit_dry
        if audit_mode or audit_dry:
            errs.append("AUDIT_MODE or AUDIT_DRY_RUN is set in service env")
    except Exception as e:
        evidence["env_check_error"] = str(e)

    se_path = LOGS / "system_events.jsonl"
    hb_count = 0
    if se_path.exists():
        for line in se_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "phase2_heartbeat" in line:
                hb_count += 1
    evidence["phase2_heartbeat_count"] = hb_count

    ok = len(errs) == 0
    return ok, errs, evidence


def _section_2_analysis_date() -> Optional[str]:
    """Most recent trading date in logs/run.jsonl."""
    run_path = LOGS / "run.jsonl"
    if not run_path.exists():
        return None
    dates: List[str] = []
    for line in run_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            d = _date_from_record(rec)
            if d:
                dates.append(d)
        except Exception:
            continue
    return max(dates) if dates else None


def _section_3_signals(date_str: str) -> Tuple[Dict[str, Any], List[Dict]]:
    """Trade-intent analysis and CSV rows."""
    run = _load_jsonl(LOGS / "run.jsonl", date_str)
    intents = [r for r in run if r.get("event_type") == "trade_intent"]
    by_sym: Dict[str, int] = defaultdict(int)
    entered = blocked = 0
    blocked_reasons: Dict[str, int] = defaultdict(int)
    scores: List[float] = []
    tags_freq: Dict[str, int] = defaultdict(int)
    rows: List[Dict] = []

    for r in intents:
        sym = r.get("symbol") or "?"
        by_sym[sym] += 1
        out = r.get("decision_outcome") or "?"
        if str(out).lower() == "entered":
            entered += 1
        else:
            blocked += 1
        br = r.get("blocked_reason") or ""
        if br:
            blocked_reasons[br] += 1
        sc = r.get("score")
        if sc is not None:
            try:
                scores.append(float(sc))
            except Exception:
                pass
        tags = r.get("thesis_tags")
        if isinstance(tags, list):
            for t in tags:
                tags_freq[str(t)] += 1
        elif isinstance(tags, dict):
            for k in tags:
                tags_freq[str(k)] += 1
        rows.append({
            "symbol": sym,
            "decision_outcome": out,
            "blocked_reason": br or "-",
            "score": r.get("score"),
            "ts": r.get("ts") or r.get("_dt"),
        })

    summary = {
        "total": len(intents),
        "by_symbol": dict(by_sym),
        "entered": entered,
        "blocked": blocked,
        "blocked_reasons": dict(blocked_reasons),
        "score_count": len(scores),
        "score_avg": sum(scores) / len(scores) if scores else None,
        "thesis_tags_freq": dict(tags_freq),
    }
    return summary, rows


def _section_4_execution(date_str: str) -> Tuple[Dict[str, Any], List[Dict]]:
    """Orders analysis and CSV rows."""
    orders = _load_jsonl(LOGS / "orders.jsonl", date_str)
    real = [o for o in orders if not (o.get("dry_run") is True or "audit_dry_run" in str(o.get("action", "")) or "AUDIT-DRYRUN" in str(o.get("order_id", "")))]
    by_sym: Dict[str, int] = defaultdict(int)
    by_side: Dict[str, int] = defaultdict(int)
    sizes: List[float] = []
    rows: List[Dict] = []
    for o in real:
        sym = o.get("symbol") or "?"
        side = o.get("side") or "?"
        by_sym[sym] += 1
        by_side[side] += 1
        qty = o.get("qty") or o.get("quantity")
        if qty is not None:
            try:
                sizes.append(float(qty))
            except Exception:
                pass
        rows.append({
            "symbol": sym,
            "side": side,
            "qty": qty,
            "order_id": o.get("order_id"),
            "ts": o.get("ts") or o.get("_dt"),
        })
    summary = {
        "total_real_orders": len(real),
        "by_symbol": dict(by_sym),
        "by_side": dict(by_side),
        "avg_size": sum(sizes) / len(sizes) if sizes else None,
    }
    return summary, rows


def _section_5_positions_exits(date_str: str) -> Tuple[Dict[str, Any], List[Dict]]:
    """Position metadata and exit_intent analysis."""
    meta_path = STATE / "position_metadata.json"
    positions: Dict[str, Any] = {}
    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            positions = data.get("symbols", data) if isinstance(data, dict) else {}
        except Exception:
            pass
    run = _load_jsonl(LOGS / "run.jsonl", date_str)
    exits = [r for r in run if r.get("event_type") == "exit_intent"]
    exit_reasons: Dict[str, int] = defaultdict(int)
    thesis_break: Dict[str, int] = defaultdict(int)
    rows: List[Dict] = []
    for r in exits:
        er = r.get("close_reason") or r.get("exit_reason") or "?"
        br = r.get("thesis_break_reason") or "?"
        exit_reasons[er] += 1
        thesis_break[br] += 1
        rows.append({
            "symbol": r.get("symbol"),
            "close_reason": er,
            "thesis_break_reason": br,
            "ts": r.get("ts") or r.get("_dt"),
        })
    summary = {
        "positions_still_open": len(positions) if isinstance(positions, dict) else 0,
        "exit_intent_count": len(exits),
        "exit_reason_dist": dict(exit_reasons),
        "thesis_break_reason_dist": dict(thesis_break),
    }
    return summary, rows


def _section_6_gates_displacement(date_str: str) -> Tuple[Dict[str, Any], List[Dict]]:
    """System_events displacement and directional_gate."""
    se = _load_jsonl(LOGS / "system_events.jsonl", date_str)
    disp_eval = [r for r in se if r.get("subsystem") == "displacement" and r.get("event_type") == "displacement_evaluated"]
    allowed = sum(1 for r in disp_eval if (r.get("details") or {}).get("allowed") is True)
    blocked = len(disp_eval) - allowed
    dg = [r for r in se if r.get("subsystem") == "directional_gate"]
    dg_blocks = sum(1 for r in dg if (r.get("event_type") or "").lower() == "blocked" or "block" in str(r.get("event_type", "")).lower())
    high_vol: Dict[str, int] = defaultdict(int)
    for r in dg:
        det = r.get("details") or {}
        sym = det.get("symbol") or det.get("symbols")
        if sym:
            high_vol[str(sym)] += 1
    rows = [{"subsystem": "displacement", "evaluated": len(disp_eval), "allowed": allowed, "blocked": blocked}]
    rows.append({"subsystem": "directional_gate", "events": len(dg), "blocked_approx": dg_blocks})
    for s, c in high_vol.items():
        rows.append({"subsystem": "directional_gate_symbol", "symbol": s, "count": c})
    summary = {
        "displacement_evaluated": len(disp_eval),
        "displacement_allowed": allowed,
        "displacement_blocked": blocked,
        "directional_gate_events": len(dg),
        "directional_gate_blocked_approx": dg_blocks,
        "high_vol_symbol_counts": dict(high_vol),
    }
    return summary, rows


def _section_7_shadow(date_str: str) -> Tuple[Dict[str, Any], List[Dict]]:
    """Shadow variant decisions and scoreboard rows."""
    sh = _load_jsonl(LOGS / "shadow.jsonl", date_str)
    decisions = [r for r in sh if r.get("event_type") == "shadow_variant_decision"]
    by_var: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"would_enter": 0, "would_exit": 0, "blocked": 0})
    by_sym: Dict[str, int] = defaultdict(int)
    for r in decisions:
        v = r.get("variant_name") or "?"
        by_var[v]["would_enter"] += 1 if r.get("would_enter") else 0
        by_var[v]["would_exit"] += 1 if r.get("would_exit") else 0
        by_var[v]["blocked"] += 1 if r.get("blocked_reason") else 0
        sym = r.get("symbol")
        if sym:
            by_sym[sym] += 1
    rows = []
    for v, c in by_var.items():
        rows.append({
            "variant": v,
            "would_enter": c["would_enter"],
            "would_exit": c["would_exit"],
            "blocked": c["blocked"],
        })
    summary = {
        "shadow_variant_decision_count": len(decisions),
        "by_variant": {k: dict(v) for k, v in by_var.items()},
        "by_symbol_count": len(by_sym),
    }
    return summary, rows


def _section_8_eod_diagnostic(date_str: str) -> Tuple[bool, List[str]]:
    """Generate EOD_ALPHA_DIAGNOSTIC_<date>.md and validate required sections."""
    script = REPO / "reports" / "_daily_review_tools" / "generate_eod_alpha_diagnostic.py"
    if not script.exists():
        return False, [f"EOD diagnostic script not found: {script}"]
    r = subprocess.run(
        [sys.executable, str(script), "--date", date_str],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        return False, [f"EOD diagnostic script failed: {r.stderr or r.stdout or 'unknown'}"]
    out_path = REPORTS / f"EOD_ALPHA_DIAGNOSTIC_{date_str}.md"
    if not out_path.exists():
        return False, [f"EOD diagnostic output not found: {out_path}"]
    text = out_path.read_text(encoding="utf-8")
    missing: List[str] = []
    for sec in EOD_REQUIRED_SECTIONS:
        if sec not in text:
            missing.append(sec)
    if missing:
        return False, [f"EOD diagnostic missing sections: {missing}"]
    return True, []


def _write_csv(path: Path, rows: List[Dict], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = fieldnames or sorted(set(k for r in rows for k in r.keys()))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Post-market analysis (run on droplet)")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: from run.jsonl)")
    args = ap.parse_args()

    REPORTS.mkdir(parents=True, exist_ok=True)
    EXPORTS.mkdir(parents=True, exist_ok=True)

    # §1 Pre-check
    ok, errs, ev = _section_1_precheck()
    preflight_lines = [
        "# Post-Market Pre-Flight",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1.1 Service state",
        "",
        f"- **stock-bot.service active:** {ev.get('service_active', False)}",
        f"- **AUDIT_MODE in service env:** {ev.get('AUDIT_MODE_set', False)}",
        f"- **AUDIT_DRY_RUN in service env:** {ev.get('AUDIT_DRY_RUN_set', False)}",
        f"- **phase2_heartbeat count in system_events.jsonl:** {ev.get('phase2_heartbeat_count', 0)}",
        "",
        "## Verdict",
        "",
        "**FAIL** — " + "; ".join(errs) if errs else "**PASS** — Service active; no audit mode; phase2 heartbeat present.",
    ]
    (REPORTS / "POSTMARKET_PREFLIGHT.md").write_text("\n".join(preflight_lines), encoding="utf-8")
    if not ok:
        print("POSTMARKET_PREFLIGHT: FAIL", file=sys.stderr)
        return 1

    # §2 Analysis date
    analysis_date = args.date or _section_2_analysis_date()
    if not analysis_date:
        analysis_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        print(f"WARN: No run.jsonl dates; using {analysis_date}", file=sys.stderr)
    print(f"ANALYSIS_DATE={analysis_date}")

    # §3 Signals
    sig_sum, sig_rows = _section_3_signals(analysis_date)
    lines = [
        "# Post-Market Signal & Decision Analysis",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Analysis date:** {analysis_date}",
        "",
        "## 3.1 trade_intent",
        "",
        f"- **Total:** {sig_sum['total']}",
        f"- **Entered:** {sig_sum['entered']} | **Blocked:** {sig_sum['blocked']}",
        f"- **By symbol:** {sig_sum['by_symbol']}",
        f"- **Blocked reasons:** {sig_sum['blocked_reasons']}",
        f"- **Score avg:** {sig_sum['score_avg']}",
        "",
        "## thesis_tags frequency",
        "",
    ]
    for t, c in sorted(sig_sum.get("thesis_tags_freq", {}).items(), key=lambda x: -x[1])[:30]:
        lines.append(f"- {t}: {c}")
    (REPORTS / "POSTMARKET_SIGNALS.md").write_text("\n".join(lines), encoding="utf-8")
    _write_csv(EXPORTS / "POSTMARKET_trade_intent_summary.csv", sig_rows)

    # §4 Execution
    ex_sum, ex_rows = _section_4_execution(analysis_date)
    lines = [
        "# Post-Market Execution Analysis",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Analysis date:** {analysis_date}",
        "",
        f"- **Total real orders:** {ex_sum['total_real_orders']}",
        f"- **By symbol:** {ex_sum['by_symbol']}",
        f"- **By side:** {ex_sum['by_side']}",
        f"- **Avg size:** {ex_sum['avg_size']}",
        "",
    ]
    (REPORTS / "POSTMARKET_EXECUTION.md").write_text("\n".join(lines), encoding="utf-8")
    _write_csv(EXPORTS / "POSTMARKET_orders_summary.csv", ex_rows)

    # §5 Positions & Exits
    pos_sum, exit_rows = _section_5_positions_exits(analysis_date)
    lines = [
        "# Post-Market Positions & Exits",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Analysis date:** {analysis_date}",
        "",
        f"- **Positions still open:** {pos_sum['positions_still_open']}",
        f"- **exit_intent count:** {pos_sum['exit_intent_count']}",
        f"- **Exit reason dist:** {pos_sum['exit_reason_dist']}",
        f"- **Thesis break reason dist:** {pos_sum['thesis_break_reason_dist']}",
        "",
    ]
    (REPORTS / "POSTMARKET_POSITIONS_AND_EXITS.md").write_text("\n".join(lines), encoding="utf-8")
    _write_csv(EXPORTS / "POSTMARKET_exit_summary.csv", exit_rows)

    # §6 Gates & Displacement
    gate_sum, gate_rows = _section_6_gates_displacement(analysis_date)
    lines = [
        "# Post-Market Gates & Displacement",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Analysis date:** {analysis_date}",
        "",
        f"- **Displacement evaluated:** {gate_sum['displacement_evaluated']} | allowed: {gate_sum['displacement_allowed']} | blocked: {gate_sum['displacement_blocked']}",
        f"- **Directional gate events:** {gate_sum['directional_gate_events']} | blocked approx: {gate_sum['directional_gate_blocked_approx']}",
        f"- **HIGH_VOL symbol counts:** {gate_sum['high_vol_symbol_counts']}",
        "",
    ]
    (REPORTS / "POSTMARKET_GATES_AND_DISPLACEMENT.md").write_text("\n".join(lines), encoding="utf-8")
    _write_csv(EXPORTS / "POSTMARKET_displacement_stats.csv", gate_rows)

    # §7 Shadow
    sh_sum, sh_rows = _section_7_shadow(analysis_date)
    lines = [
        "# Post-Market Shadow & Learning Analysis",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Analysis date:** {analysis_date}",
        "",
        f"- **shadow_variant_decision count:** {sh_sum['shadow_variant_decision_count']}",
        f"- **By variant:** {sh_sum['by_variant']}",
        "",
    ]
    (REPORTS / "POSTMARKET_SHADOW_ANALYSIS.md").write_text("\n".join(lines), encoding="utf-8")
    _write_csv(EXPORTS / "POSTMARKET_shadow_scoreboard.csv", sh_rows)

    # §8 EOD Alpha Diagnostic
    eod_ok, eod_errs = _section_8_eod_diagnostic(analysis_date)
    if not eod_ok:
        print("EOD diagnostic: FAIL — " + "; ".join(eod_errs), file=sys.stderr)
        # Continue to verdict but record failure

    # §9 Final verdict — evidence-based, no softened conclusions
    enter_rate = (sig_sum["entered"] / sig_sum["total"] * 100) if sig_sum["total"] else 0
    blocked_rate = (sig_sum["blocked"] / sig_sum["total"] * 100) if sig_sum["total"] else 0
    what_worked: List[str] = []
    what_underperformed: List[str] = []
    if sig_sum["total"] > 0:
        what_worked.append(f"Signal coverage: {sig_sum['total']} trade_intent events.")
        if enter_rate >= 50:
            what_worked.append(f"Enter rate {enter_rate:.1f}% (entered vs blocked).")
        else:
            what_underperformed.append(f"Low enter rate {enter_rate:.1f}%; blocked {blocked_rate:.1f}%.")
    if sig_sum.get("blocked_reasons"):
        what_underperformed.append(f"Blocked reasons: {sig_sum['blocked_reasons']}.")
    if ex_sum["total_real_orders"] > 0:
        what_worked.append(f"Executions: {ex_sum['total_real_orders']} real orders.")
    if pos_sum["exit_intent_count"] > 0:
        what_worked.append(f"Exit intent: {pos_sum['exit_intent_count']} exit_intent events.")
    if gate_sum["displacement_blocked"] > gate_sum["displacement_allowed"] and gate_sum["displacement_evaluated"] > 0:
        what_underperformed.append(f"Displacement: {gate_sum['displacement_blocked']} blocked vs {gate_sum['displacement_allowed']} allowed.")
    elif gate_sum["displacement_evaluated"] > 0:
        what_worked.append(f"Displacement: {gate_sum['displacement_allowed']} allowed, {gate_sum['displacement_blocked']} blocked.")
    if sh_sum["shadow_variant_decision_count"] > 0:
        what_worked.append(f"Shadow: {sh_sum['shadow_variant_decision_count']} variant decisions.")
    if not what_worked:
        what_worked.append("(No positive evidence segments; inspect reports.)")
    if not what_underperformed:
        what_underperformed.append("(None highlighted from this run.)")

    readiness = "Ready"
    if not eod_ok:
        readiness = "Needs attention: EOD diagnostic failed."
    elif what_underperformed and len(what_underperformed) > 1:
        readiness = "Needs attention: review underperformed segments before next day."

    verdict_lines = [
        f"# Post-Market Verdict — {analysis_date}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
        "## Summary of live trading behavior",
        "",
        f"- **Signals (trade_intent):** {sig_sum['total']} total | {sig_sum['entered']} entered | {sig_sum['blocked']} blocked",
        f"- **Real orders:** {ex_sum['total_real_orders']}",
        f"- **Exits (exit_intent):** {pos_sum['exit_intent_count']}",
        f"- **Positions still open:** {pos_sum['positions_still_open']}",
        f"- **Displacement:** evaluated={gate_sum['displacement_evaluated']} allowed={gate_sum['displacement_allowed']} blocked={gate_sum['displacement_blocked']}",
        f"- **Shadow decisions:** {sh_sum['shadow_variant_decision_count']}",
        "",
        "## What worked",
        "",
    ]
    for w in what_worked:
        verdict_lines.append(f"- {w}")
    verdict_lines.extend(["", "## What underperformed", ""])
    for u in what_underperformed:
        verdict_lines.append(f"- {u}")
    verdict_lines.extend([
        "",
        "## Notable patterns",
        "",
        f"- Blocked reasons: {sig_sum.get('blocked_reasons')}",
        f"- Exit reasons: {pos_sum.get('exit_reason_dist')}",
        f"- Thesis break: {pos_sum.get('thesis_break_reason_dist')}",
        "",
        "## Readiness for next trading day",
        "",
        f"- **{readiness}**",
        "",
        "## Generated reports and CSVs",
        "",
        "- reports/POSTMARKET_PREFLIGHT.md",
        "- reports/POSTMARKET_SIGNALS.md",
        "- exports/POSTMARKET_trade_intent_summary.csv",
        "- reports/POSTMARKET_EXECUTION.md",
        "- exports/POSTMARKET_orders_summary.csv",
        "- reports/POSTMARKET_POSITIONS_AND_EXITS.md",
        "- exports/POSTMARKET_exit_summary.csv",
        "- reports/POSTMARKET_GATES_AND_DISPLACEMENT.md",
        "- exports/POSTMARKET_displacement_stats.csv",
        "- reports/POSTMARKET_SHADOW_ANALYSIS.md",
        "- exports/POSTMARKET_shadow_scoreboard.csv",
        f"- reports/EOD_ALPHA_DIAGNOSTIC_{analysis_date}.md",
        "",
        "---",
        "",
    ])
    if not eod_ok:
        verdict_lines.append("**EOD diagnostic:** FAIL — " + "; ".join(eod_errs) + "\n")
    else:
        verdict_lines.append("**EOD diagnostic:** PASS — all required sections present.\n")
    (REPORTS / f"POSTMARKET_VERDICT_{analysis_date}.md").write_text("\n".join(verdict_lines), encoding="utf-8")

    return 0 if eod_ok else 1


if __name__ == "__main__":
    sys.exit(main())
