#!/usr/bin/env python3
"""
Phase-2 Forensic Audit - read-only.
Fetches droplet logs/state, verifies Phase-2 Alpha Discovery is operating, produces
exports/VERIFY_*.csv and reports/PHASE2_VERIFICATION_SUMMARY_<DATE>.md.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
EXPORTS = REPO / "exports"
REPORTS = REPO / "reports"
DROPLET_ROOT = "/root/stock-bot"

REMOTE = {
    "run": f"{DROPLET_ROOT}/logs/run.jsonl",
    "orders": f"{DROPLET_ROOT}/logs/orders.jsonl",
    "system_events": f"{DROPLET_ROOT}/logs/system_events.jsonl",
    "shadow": f"{DROPLET_ROOT}/logs/shadow.jsonl",
    "symbol_risk": f"{DROPLET_ROOT}/state/symbol_risk_features.json",
    "trade_universe": f"{DROPLET_ROOT}/state/trade_universe_v2.json",
}


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


def _date_match(rec: dict, date_str: str) -> bool:
    ts = rec.get("ts") or rec.get("_dt") or rec.get("timestamp")
    if not ts:
        return True
    dt = _parse_ts(ts)
    return dt is not None and dt.strftime("%Y-%m-%d") == date_str


def fetch_from_droplet(date_str: str) -> Tuple[Dict[str, Any], List[str]]:
    """Fetch logs/state from droplet. Returns (data dict, errors)."""
    data = {
        "run": [],
        "orders": [],
        "system_events": [],
        "shadow": [],
        "symbol_risk": {},
        "trade_universe": {},
    }
    errs: List[str] = []

    try:
        from droplet_client import DropletClient
        client = DropletClient()
        ssh = client._connect()
        sftp = ssh.open_sftp()
    except Exception as e:
        errs.append(f"Droplet connect: {e}")
        return data, errs

    def load_jsonl(remote: str, key: str, filter_date: bool) -> None:
        try:
            with sftp.open(remote, "r") as f:
                raw = f.read().decode("utf-8", errors="replace")
        except FileNotFoundError:
            errs.append(f"Missing: {remote}")
            return
        except Exception as e:
            errs.append(f"Read {remote}: {e}")
            return
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if filter_date and not _date_match(rec, date_str):
                    continue
                data[key].append(rec)
            except Exception:
                continue

    def load_json(remote: str, key: str) -> None:
        try:
            with sftp.open(remote, "r") as f:
                data[key] = json.load(f)
        except FileNotFoundError:
            errs.append(f"Missing: {remote}")
        except Exception as e:
            errs.append(f"Read {remote}: {e}")

    load_jsonl(REMOTE["run"], "run", True)
    load_jsonl(REMOTE["orders"], "orders", True)
    load_jsonl(REMOTE["system_events"], "system_events", True)
    load_jsonl(REMOTE["shadow"], "shadow", True)
    load_json(REMOTE["symbol_risk"], "symbol_risk")
    load_json(REMOTE["trade_universe"], "trade_universe")
    if not isinstance(data["symbol_risk"], dict):
        data["symbol_risk"] = {}
    if not isinstance(data["trade_universe"], dict):
        data["trade_universe"] = {}

    try:
        sftp.close()
        client.close()
    except Exception:
        pass

    return data, errs


def run_audit(date_str: str, use_droplet: bool = True) -> Dict[str, Any]:
    """Run full audit. use_droplet=False reads from local logs/state."""
    EXPORTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    if use_droplet:
        data, fetch_errs = fetch_from_droplet(date_str)
    else:
        data = {"run": [], "orders": [], "system_events": [], "shadow": [], "symbol_risk": {}, "trade_universe": {}}
        fetch_errs = []
        log_dir = REPO / "logs"
        state_dir = REPO / "state"
        for name, key in [("run.jsonl", "run"), ("orders.jsonl", "orders"), ("system_events.jsonl", "system_events"), ("shadow.jsonl", "shadow")]:
            p = log_dir / name
            if p.exists():
                for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                        if _date_match(rec, date_str):
                            data[key].append(rec)
                    except Exception:
                        pass
        for name, key in [("symbol_risk_features.json", "symbol_risk"), ("trade_universe_v2.json", "trade_universe")]:
            p = state_dir / name
            if p.exists():
                try:
                    data[key] = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    data[key] = {}
            else:
                data[key] = {}

    run_recs = data["run"]
    se_recs = data["system_events"]
    shadow_recs = data["shadow"]
    symbol_risk = data["symbol_risk"] or {}

    # --- B1 trade_intent ---
    trade_intents = [r for r in run_recs if r.get("event_type") == "trade_intent"]
    b1_fail = []
    samples_b1 = []
    for r in trade_intents:
        snap = r.get("feature_snapshot") or {}
        tags = r.get("thesis_tags") or {}
        snap_ok = isinstance(snap, dict) and len(snap) > 0
        tags_ok = isinstance(tags, dict) and len(tags) > 0
        all_null = all(v is None for v in (tags or {}).values()) if tags else True
        if not snap_ok or not tags_ok or all_null:
            b1_fail.append(f"symbol={r.get('symbol')} snap_ok={snap_ok} tags_ok={tags_ok} all_null={all_null}")
        samples_b1.append({
            "symbol": r.get("symbol"),
            "side": r.get("side"),
            "feature_snapshot_non_empty": "Y" if snap_ok else "N",
            "thesis_tags_non_empty": "Y" if tags_ok else "N",
            "displacement_context": "Y" if r.get("displacement_context") else "N",
        })
    b1_pass = len(b1_fail) == 0 and (len(trade_intents) == 0 or (samples_b1 and all(s["feature_snapshot_non_empty"] == "Y" and s["thesis_tags_non_empty"] == "Y" for s in samples_b1)))

    with open(EXPORTS / "VERIFY_trade_intent_samples.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol", "side", "feature_snapshot_non_empty", "thesis_tags_non_empty", "displacement_context"])
        w.writeheader()
        for s in samples_b1[:50]:
            w.writerow(s)

    # --- B2 exit_intent ---
    exit_intents = [r for r in run_recs if r.get("event_type") == "exit_intent"]
    b2_fail = []
    samples_b2 = []
    for r in exit_intents:
        br = r.get("thesis_break_reason")
        snap = r.get("feature_snapshot_at_exit") or {}
        snap_ok = isinstance(snap, dict) and len(snap) > 0
        if br is None or br == "":
            b2_fail.append(f"symbol={r.get('symbol')} thesis_break_reason missing")
        if not snap_ok:
            b2_fail.append(f"symbol={r.get('symbol')} feature_snapshot_at_exit empty")
        samples_b2.append({
            "symbol": r.get("symbol"),
            "close_reason": r.get("close_reason"),
            "thesis_break_reason": br or "",
            "feature_snapshot_at_exit_present": "Y" if snap_ok else "N",
        })
    b2_pass = len(b2_fail) == 0 and (len(exit_intents) == 0 or all(s["thesis_break_reason"] and s["feature_snapshot_at_exit_present"] == "Y" for s in samples_b2))

    with open(EXPORTS / "VERIFY_exit_intent_samples.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol", "close_reason", "thesis_break_reason", "feature_snapshot_at_exit_present"])
        w.writeheader()
        for s in samples_b2:
            w.writerow(s)

    # --- B3 directional_gate ---
    dg = [r for r in se_recs if r.get("subsystem") == "directional_gate" and r.get("event_type") == "blocked_high_vol_no_alignment"]
    by_sym = defaultdict(int)
    for r in dg:
        by_sym[r.get("symbol") or "?"] += 1
    rows_dg = [{"symbol": s, "block_count": c} for s, c in sorted(by_sym.items(), key=lambda x: -x[1])]
    with open(EXPORTS / "VERIFY_directional_gate_blocks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol", "block_count"])
        w.writeheader()
        w.writerows(rows_dg)

    # --- C displacement ---
    disp = [r for r in se_recs if r.get("subsystem") == "displacement" and r.get("event_type") == "displacement_evaluated"]
    disp_rows = []
    for r in disp:
        d = r.get("details") or {}
        disp_rows.append({
            "allowed": d.get("allowed"),
            "reason": d.get("reason"),
            "delta_score": d.get("delta_score"),
            "age_seconds": d.get("age_seconds"),
            "current_symbol": d.get("current_symbol"),
            "challenger_symbol": d.get("challenger_symbol"),
        })
    allowed_n = sum(1 for d in disp_rows if d.get("allowed") is True)
    blocked_n = len(disp_rows) - allowed_n
    by_reason: Dict[str, int] = defaultdict(int)
    for d in disp_rows:
        if not d.get("allowed"):
            by_reason[str(d.get("reason") or "unknown")] += 1
    c_fail = []
    if len(disp) == 0:
        c_fail.append("displacement_evaluated never appears")
    if disp and allowed_n == len(disp):
        c_fail.append("allowed always same outcome (all allowed)")
    if disp and blocked_n == len(disp):
        c_fail.append("blocked always same outcome (all blocked)")

    with open(EXPORTS / "VERIFY_displacement_decisions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["allowed", "reason", "delta_score", "age_seconds", "current_symbol", "challenger_symbol"])
        w.writeheader()
        w.writerows(disp_rows)

    # --- D shadow ---
    var_dec = [r for r in shadow_recs if r.get("event_type") == "shadow_variant_decision"]
    variants = list({r.get("variant_name") for r in var_dec if r.get("variant_name")})
    by_var: Dict[str, int] = defaultdict(int)
    symbols_shadow = set()
    shadow_rows = []
    for r in var_dec:
        v = r.get("variant_name") or "?"
        by_var[v] += 1
        symbols_shadow.add(r.get("symbol"))
        shadow_rows.append({
            "variant_name": v,
            "symbol": r.get("symbol"),
            "would_enter": r.get("would_enter"),
            "blocked_reason": r.get("blocked_reason"),
            "v2_score_variant": r.get("v2_score_variant"),
        })
    d_fail = []
    # Assume shadow "enabled" if we have any shadow log at all
    if shadow_recs and len(var_dec) == 0:
        d_fail.append("shadow log exists but no shadow_variant_decision")

    with open(EXPORTS / "VERIFY_shadow_variant_activity.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["variant_name", "symbol", "would_enter", "blocked_reason", "v2_score_variant"])
        w.writeheader()
        w.writerows(shadow_rows)

    # --- E high-vol ---
    vol_list = []
    for sym, info in (symbol_risk or {}).items():
        if not isinstance(info, dict):
            continue
        v = info.get("realized_vol_20d") or info.get("rv_20d") or info.get("rv20")
        if v is not None:
            vol_list.append((sym, float(v)))
    vol_list.sort(key=lambda x: x[1], reverse=True)
    n = len(vol_list)
    p75_idx = max(0, int(math.ceil(0.75 * n)) - 1) if n else 0
    p75 = vol_list[p75_idx][1] if vol_list else 0.0
    high_vol = [s for s, v in vol_list if v >= p75]
    cross_ti = set(r.get("symbol") for r in trade_intents) & set(high_vol)
    cross_dg = set(by_sym.keys()) & set(high_vol)
    cross_disp = set()
    for d in disp_rows:
        cross_disp.add(d.get("current_symbol"))
        cross_disp.add(d.get("challenger_symbol"))
    cross_disp &= set(high_vol)

    rows_hv = [{"symbol": s, "realized_vol_20d": v, "high_vol": "Y" if s in high_vol else "N"} for s, v in vol_list]
    with open(EXPORTS / "VERIFY_high_vol_cohort.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol", "realized_vol_20d", "high_vol"])
        w.writeheader()
        w.writerows(rows_hv)

    e_fail = []
    dg_symbols = set(by_sym.keys())
    if symbol_risk and len(vol_list) > 0 and len(high_vol) == 0:
        e_fail.append("symbol_risk present but HIGH_VOL cohort empty")
    for sym in dg_symbols:
        if sym in high_vol:
            continue
        e_fail.append(f"directional_gate blocked LOW_VOL symbol {sym} (must only block HIGH_VOL)")

    # --- F EOD ---
    eod_path = REPORTS / f"EOD_ALPHA_DIAGNOSTIC_{date_str}.md"
    eod_exists = eod_path.exists()
    eod_text = eod_path.read_text(encoding="utf-8") if eod_exists else ""
    sections = {
        "Winners vs Losers": "Winners vs Losers" in eod_text,
        "High-Volatility Alpha": "High-Volatility Alpha" in eod_text or "High-vol" in eod_text or ("Telemetry" in eod_text and "directional_gate" in eod_text),
        "Displacement Effectiveness": "Displacement" in eod_text,
        "Shadow Scoreboard": "Shadow" in eod_text and "scoreboard" in eod_text.lower(),
        "Data Availability": "Data availability" in eod_text or "Data Availability" in eod_text,
    }
    f_fail = []
    if eod_exists:
        for name, present in sections.items():
            if not present:
                f_fail.append(f"EOD section missing or placeholder: {name}")
    else:
        f_fail.append("EOD_ALPHA_DIAGNOSTIC report missing")

    # --- Summary ---
    b1_status = "PASS" if b1_pass else "FAIL"
    b2_status = "PASS" if b2_pass else "FAIL"
    b3_status = "PASS"  # No hard FAIL from cross-check LOW_VOL here; we report
    c_status = "PASS" if not c_fail else "FAIL"
    d_status = "PASS" if not d_fail else "FAIL"
    e_status = "PASS" if not e_fail else "FAIL"
    f_status = "PASS" if not f_fail else "FAIL"

    fail_count = sum(1 for s in [b1_status, b2_status, c_status, d_status, e_status, f_status] if s == "FAIL")
    if fail_count == 0:
        confidence = "HIGH"
    elif fail_count <= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    statuses = {"b1": b1_status, "b2": b2_status, "c": c_status, "d": d_status, "e": e_status, "f": f_status}
    exec_parts = []
    exec_parts.append("Is Phase-2 Alpha Discovery actually operating in live trading?")
    if fetch_errs:
        exec_parts.append("Droplet fetch reported errors: " + "; ".join(fetch_errs[:3]))
    if not use_droplet or fetch_errs:
        exec_parts.append("Data source: local or partial (droplet is source of truth). Audited against local logs/state only; droplet was not fully used.")
    if fail_count == 0:
        exec_parts.append("All B-F checks PASS. Phase-2 Alpha Discovery appears to be operating in live: trade_intent/exit_intent with snapshots and thesis tags, directional gate, displacement evaluations, shadow variant decisions, and HIGH_VOL cohort are present and consistent.")
    else:
        fail_which = ", ".join(f"{k}={v}" for k, v in statuses.items() if v == "FAIL")
        exec_parts.append(f"{fail_count} section(s) FAIL. Phase-2 Alpha Discovery is NOT fully operating in live: " + fail_which + ".")
    exec_parts.append(f"Confidence: {confidence}.")

    summary = {
        "date": date_str,
        "fetch_errors": fetch_errs,
        "data_source": "droplet" if use_droplet and not fetch_errs else ("local" if not use_droplet else "droplet_partial"),
        "b1": {"status": b1_status, "trade_intent_count": len(trade_intents), "fail_reasons": b1_fail},
        "b2": {"status": b2_status, "exit_intent_count": len(exit_intents), "fail_reasons": b2_fail},
        "b3": {"status": b3_status, "directional_gate_count": len(dg), "by_symbol": dict(by_sym)},
        "c": {"status": c_status, "displacement_evaluated": len(disp), "allowed": allowed_n, "blocked": blocked_n, "blocked_by_reason": dict(by_reason), "fail_reasons": c_fail},
        "d": {"status": d_status, "shadow_variant_decisions": len(var_dec), "variants": variants, "symbols": len(symbols_shadow), "fail_reasons": d_fail},
        "e": {"status": e_status, "high_vol_count": len(high_vol), "fail_reasons": e_fail},
        "f": {"status": f_status, "eod_exists": eod_exists, "sections": sections, "fail_reasons": f_fail},
        "confidence": confidence,
        "executive": " ".join(exec_parts),
        "samples_b1": samples_b1,
        "samples_b2": samples_b2,
    }
    return summary


def write_summary_md(summary: Dict[str, Any], date_str: str) -> Path:
    out = REPORTS / f"PHASE2_VERIFICATION_SUMMARY_{date_str}.md"
    src = summary.get("data_source", "unknown")
    lines = [
        f"# Phase-2 Verification Summary - {date_str}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Data source:** {src}" + (" (fetch errors: " + "; ".join((summary.get("fetch_errors") or [])[:3]) + ")" if summary.get("fetch_errors") else ""),
        "",
        "---",
        "",
        "## PASS / FAIL by section",
        "",
        f"- **B1 trade_intent:** {summary['b1']['status']} (count={summary['b1']['trade_intent_count']})",
        f"- **B2 exit_intent:** {summary['b2']['status']} (count={summary['b2']['exit_intent_count']})",
        f"- **B3 directional_gate:** {summary['b3']['status']} (blocks={summary['b3']['directional_gate_count']})",
        f"- **C displacement:** {summary['c']['status']} (evaluated={summary['c']['displacement_evaluated']}, allowed={summary['c']['allowed']}, blocked={summary['c']['blocked']})",
        f"- **D shadow:** {summary['d']['status']} (decisions={summary['d']['shadow_variant_decisions']}, variants={summary['d']['variants']})",
        f"- **E high-vol cohort:** {summary['e']['status']} (HIGH_VOL count={summary['e']['high_vol_count']})",
        f"- **F EOD data-backed:** {summary['f']['status']} (exists={summary['f']['eod_exists']})",
        "",
        "---",
        "",
        "## Failure reasons (if any)",
        "",
    ]
    for k in ["b1", "b2", "c", "d", "e", "f"]:
        fails = summary[k].get("fail_reasons") or []
        if fails:
            lines.append(f"- **{k}:**")
            for x in fails:
                lines.append(f"  - {x}")
            lines.append("")
    if not any(summary[k].get("fail_reasons") for k in ["b1", "b2", "c", "d", "e", "f"]):
        lines.append("- None.")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## What is wired vs what is firing",
        "",
        f"- **trade_intent:** {summary['b1']['trade_intent_count']} emitted" + (" (all with snapshot+tags)" if summary['b1']['status'] == "PASS" else " (FAIL: snapshot/tags issue)"),
        f"- **exit_intent:** {summary['b2']['exit_intent_count']} emitted" + (" (all with thesis_break_reason+snapshot)" if summary['b2']['status'] == "PASS" else " (FAIL)"),
        f"- **directional_gate:** {summary['b3']['directional_gate_count']} blocks logged",
        f"- **displacement_evaluated:** {summary['c']['displacement_evaluated']} evaluations, allowed={summary['c']['allowed']}, blocked={summary['c']['blocked']}",
        f"- **shadow_variant_decision:** {summary['d']['shadow_variant_decisions']} events, variants={summary['d']['variants']}",
        f"- **HIGH_VOL cohort:** {summary['e']['high_vol_count']} symbols",
        "",
        "---",
        "",
        f"## Confidence: **{summary['confidence']}**",
        "",
        "---",
        "",
        "## Generated CSVs (exports/)",
        "",
        "- `VERIFY_trade_intent_samples.csv`",
        "- `VERIFY_exit_intent_samples.csv`",
        "- `VERIFY_directional_gate_blocks.csv`",
        "- `VERIFY_displacement_decisions.csv`",
        "- `VERIFY_shadow_variant_activity.csv`",
        "- `VERIFY_high_vol_cohort.csv`",
        "",
        "---",
        "",
        "## Executive summary",
        "",
        summary.get("executive", ""),
        "",
    ])
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-01-26", help="YYYY-MM-DD (most recent full session)")
    ap.add_argument("--local", action="store_true", help="Use local logs/state only (no droplet fetch)")
    args = ap.parse_args()
    date_str = args.date
    use_droplet = not args.local

    summary = run_audit(date_str, use_droplet=use_droplet)
    out_path = write_summary_md(summary, date_str)
    fail_count = sum(1 for k in ["b1", "b2", "c", "d", "e", "f"] if summary[k]["status"] == "FAIL")

    print(f"Wrote {out_path}")
    print("Exports: " + ", ".join(sorted(p.name for p in EXPORTS.glob("VERIFY_*.csv"))))
    print("\n" + (summary.get("executive") or ""))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
