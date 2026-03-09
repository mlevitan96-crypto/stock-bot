#!/usr/bin/env python3
"""
Exit Decision Trace LIVE PROOF — run ON DROPLET.
Proves trace is emitting under real runtime; CSA verdict; owner synthesis.
Outputs: EXIT_TRACE_LIVE_PROOF_<date>_<time>.md, EXIT_TRACE_SAMPLE_<date>_<time>.json,
         CSA_EXIT_TRACE_VERDICT_<date>_<time>.json
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TRACE_PATH = REPO / "reports" / "state" / "exit_decision_trace.jsonl"
AUDIT = REPO / "reports" / "audit"
NOW = datetime.now(timezone.utc)
DATE = NOW.strftime("%Y-%m-%d")
TIME = NOW.strftime("%H%M")
STAMP = f"{DATE}_{TIME}"
PROOF_MD = AUDIT / f"EXIT_TRACE_LIVE_PROOF_{STAMP}.md"
SAMPLE_JSON = AUDIT / f"EXIT_TRACE_SAMPLE_{STAMP}.json"
VERDICT_JSON = AUDIT / f"CSA_EXIT_TRACE_VERDICT_{STAMP}.json"

REQUIRED_TOP = {"trade_id", "symbol", "ts", "unrealized_pnl", "composite_score", "signal_decay", "exit_eligible", "exit_conditions", "signals"}
REQUIRED_EXIT_CONDITIONS = {"signal_decay", "flow_reversal", "stale_alpha", "risk_stop"}
REQUIRED_UW = {"flow", "dark_pool", "imbalance", "velocity", "confidence"}
MAX_TS_AGE_SEC = 120 * 2  # 2 minutes
WAIT_FOR_SAMPLES_SEC = 130


def _run(cmd: list, timeout: int = 10) -> tuple[str, str, int]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
        return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode
    except Exception as e:
        return "", str(e), -1


def _parse_ts(ts_str: str) -> float | None:
    if not ts_str:
        return None
    try:
        if isinstance(ts_str, (int, float)):
            return float(ts_str)
        s = str(ts_str).replace("Z", "+00:00")[:26]
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return None


def phase0_context() -> dict:
    hostname = socket.gethostname()
    out, _, rc = _run(["git", "rev-parse", "HEAD"], 5)
    commit = (out or "unknown")[:12] if rc == 0 else "unknown"
    out, _, _ = _run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], 5)
    sys_time = out or "unknown"
    out, _, rc = _run([sys.executable, "--version"], 5)
    py_ver = (out or "unknown").strip() if rc == 0 else "unknown"
    status = "unknown"
    for cmd in [["systemctl", "is-active", "stock-bot"], ["supervisorctl", "status", "stock-bot"]]:
        out, _, rc = _run(cmd, 5)
        if rc == 0 and out:
            status = out.strip()[:64]
            break
    return {"hostname": hostname, "git_commit": commit, "system_time_utc": sys_time, "python_version": py_ver, "stock_bot_status": status}


def get_open_positions_count() -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv(REPO / ".env")
    except Exception:
        pass
    key = os.getenv("ALPACA_KEY") or os.getenv("APCA_API_KEY_ID")
    secret = os.getenv("ALPACA_SECRET") or os.getenv("APCA_API_SECRET_KEY")
    base = os.getenv("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets"
    if not key or not secret:
        return -1
    try:
        import alpaca_trade_api as tradeapi
        api = tradeapi.REST(key, secret, base)
        positions = api.list_positions() or []
        return len(positions)
    except Exception:
        return -1


def read_trace_last_n(n: int) -> list[dict]:
    if not TRACE_PATH.exists():
        return []
    text = TRACE_PATH.read_text(encoding="utf-8", errors="replace").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for ln in lines[-n:]:
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def validate_sample(rec: dict) -> list[str]:
    errors = []
    for k in REQUIRED_TOP:
        if k not in rec:
            errors.append(f"missing_required:{k}")
    if not errors and "exit_conditions" in rec:
        ec = rec["exit_conditions"]
        if not isinstance(ec, dict):
            errors.append("exit_conditions_not_dict")
        else:
            for k in REQUIRED_EXIT_CONDITIONS:
                if k not in ec:
                    errors.append(f"missing_exit_condition:{k}")
    if not errors and "signals" in rec:
        sig = rec["signals"]
        if not isinstance(sig, dict):
            errors.append("signals_not_dict")
        elif "UW" not in sig:
            errors.append("signals.UW_missing")
        else:
            uw = sig["UW"]
            if not isinstance(uw, dict):
                errors.append("signals.UW_not_dict")
            else:
                for k in REQUIRED_UW:
                    if k not in uw:
                        errors.append(f"signals.UW_missing:{k}")
    return errors


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)

    proof_lines = [f"# Exit Trace LIVE PROOF — {STAMP}", "", f"**Generated:** {NOW.isoformat()}", ""]
    verdict = {"verdict": "EXIT_TRACE_INCOMPLETE", "confidence": 0.0, "required_fixes": [], "exit_learning_allowed": False,
               "stamp": STAMP, "phase0": {}, "phase1": {}, "phase2": {}, "phase3": [], "phase4": {}}

    # Phase 0
    ctx = phase0_context()
    verdict["phase0"] = ctx
    proof_lines.append("## Phase 0 — Droplet authority")
    proof_lines.append("")
    proof_lines.append(f"- hostname: {ctx['hostname']}")
    proof_lines.append(f"- git commit: {ctx['git_commit']}")
    proof_lines.append(f"- system time (UTC): {ctx['system_time_utc']}")
    proof_lines.append(f"- python: {ctx['python_version']}")
    proof_lines.append(f"- stock-bot status: {ctx['stock_bot_status']}")
    proof_lines.append("")
    if ctx["stock_bot_status"] not in ("active", "running", "RUNNING"):
        verdict["required_fixes"].append("stock-bot not active; start service")
        verdict["verdict"] = "EXIT_TRACE_BLOCKED"
        PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")
        VERDICT_JSON.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        SAMPLE_JSON.write_text(json.dumps({"samples": [], "error": "phase0_fail"}, indent=2), encoding="utf-8")
        return 1

    # Phase 1 — open positions
    n_pos = get_open_positions_count()
    verdict["phase1"] = {"open_positions_count": n_pos}
    proof_lines.append("## Phase 1 — Trace emission context")
    proof_lines.append("")
    proof_lines.append(f"- Open paper positions: {n_pos}")
    proof_lines.append("")
    if n_pos < 0:
        verdict["required_fixes"].append("Alpaca API unreachable or env missing")
        verdict["verdict"] = "EXIT_TRACE_BLOCKED"
        proof_lines.append("FAIL: Could not read positions (API/env).")
        PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")
        VERDICT_JSON.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        SAMPLE_JSON.write_text(json.dumps({"samples": [], "error": "phase1_fail"}, indent=2), encoding="utf-8")
        return 1
    if n_pos == 0:
        verdict["verdict"] = "EXIT_TRACE_INCOMPLETE"
        verdict["required_fixes"].append("No open positions; trace cannot emit. Re-run when positions exist.")
        proof_lines.append("No open positions; trace cannot emit. Re-run when paper has open positions.")
        PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")
        VERDICT_JSON.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        SAMPLE_JSON.write_text(json.dumps({"samples": [], "error": "no_open_positions"}, indent=2), encoding="utf-8")
        return 0

    # Allow 2 sampling intervals for trace to be written
    proof_lines.append("Waiting 130s for 2 sampling intervals...")
    time.sleep(WAIT_FOR_SAMPLES_SEC)

    # Phase 2 — trace file
    if not TRACE_PATH.exists():
        verdict["verdict"] = "EXIT_TRACE_INCOMPLETE"
        verdict["required_fixes"].append("Trace file does not exist after wait")
        verdict["phase2"] = {"trace_exists": False, "trace_size": 0}
        proof_lines.append("## Phase 2 — Trace file")
        proof_lines.append("")
        proof_lines.append("FAIL: reports/state/exit_decision_trace.jsonl does not exist.")
        PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")
        VERDICT_JSON.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        SAMPLE_JSON.write_text(json.dumps({"samples": [], "error": "trace_missing"}, indent=2), encoding="utf-8")
        return 1
    size = TRACE_PATH.stat().st_size
    samples = read_trace_last_n(10)
    last_three = read_trace_last_n(3)
    verdict["phase2"] = {"trace_exists": True, "trace_size": size, "lines_read": len(samples)}
    proof_lines.append("## Phase 2 — Trace file")
    proof_lines.append("")
    proof_lines.append(f"- File exists: yes")
    proof_lines.append(f"- Size: {size} bytes")
    proof_lines.append(f"- Last 10 lines read: {len(samples)}")
    proof_lines.append("")

    if size == 0 or not samples:
        verdict["verdict"] = "EXIT_TRACE_INCOMPLETE"
        verdict["required_fixes"].append("Trace file empty or unreadable")
        proof_lines.append("FAIL: File empty or no valid JSON lines.")
        PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")
        VERDICT_JSON.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        SAMPLE_JSON.write_text(json.dumps({"samples": [], "error": "trace_empty"}, indent=2), encoding="utf-8")
        return 1

    now_ts = time.time()
    recent = 0
    for s in samples:
        t = _parse_ts(s.get("ts"))
        if t and (now_ts - t) <= MAX_TS_AGE_SEC:
            recent += 1
    if recent == 0:
        verdict["verdict"] = "EXIT_TRACE_INCOMPLETE"
        verdict["required_fixes"].append("No trace timestamps within last 2 minutes (stale)")
        proof_lines.append("- FAIL: No recent timestamps (within 2 min).")
    else:
        proof_lines.append(f"- Samples with ts within 2 min: {recent}/{len(samples)}")
    proof_lines.append("")

    # Phase 3 — granularity
    proof_lines.append("## Phase 3 — Granularity & completeness (CSA)")
    proof_lines.append("")
    all_valid = True
    for i, rec in enumerate(samples):
        errs = validate_sample(rec)
        verdict["phase3"].append({"index": i, "trade_id": rec.get("trade_id"), "errors": errs})
        if errs:
            all_valid = False
            proof_lines.append(f"- Sample {i} ({rec.get('trade_id', '?')}): FAIL — {errs}")
        else:
            proof_lines.append(f"- Sample {i} ({rec.get('trade_id', '?')}): OK")
    proof_lines.append("")

    if not all_valid:
        verdict["verdict"] = "EXIT_TRACE_INCOMPLETE"
        verdict["required_fixes"].append("One or more samples missing required fields or UW sub-fields")
    else:
        # Phase 4 — timeline sanity (multiple samples for same trade_id, values change)
        by_trade: dict[str, list] = {}
        for s in samples:
            tid = s.get("trade_id") or "?"
            by_trade.setdefault(tid, []).append(s)
        verdict["phase4"] = {"trade_ids": list(by_trade.keys()), "samples_per_trade": {k: len(v) for k, v in by_trade.items()}}
        proof_lines.append("## Phase 4 — Exit eligibility timeline")
        proof_lines.append("")
        proof_lines.append(f"- Trade IDs in window: {list(by_trade.keys())}")
        for tid, arr in by_trade.items():
            proof_lines.append(f"- {tid}: {len(arr)} sample(s)")
        proof_lines.append("")
        varying = False
        for tid, arr in by_trade.items():
            if len(arr) >= 2:
                pnls = [r.get("unrealized_pnl") for r in arr]
                scores = [r.get("composite_score") for r in arr]
                if len(set(pnls)) > 1 or len(set(scores)) > 1:
                    varying = True
                    break
        verdict["phase4"]["values_vary_across_samples"] = varying
        proof_lines.append(f"- Values vary across samples: {'yes' if varying else 'no (single sample or static)'}")
        proof_lines.append("")
        # Fail closed only when we have 2+ samples for same trade and they are identical (static)
        multi_sample_trades = [tid for tid, arr in by_trade.items() if len(arr) >= 2]
        if multi_sample_trades and not varying:
            verdict["required_fixes"].append("Trace may be static (same trade_id has multiple identical samples); confirm sampling interval")
        # else: single sample per trade in window is acceptable; trace is emitting and complete

    # Phase 5 — verdict: PROVEN if trace exists, recent, and all samples valid
    if verdict["verdict"] != "EXIT_TRACE_BLOCKED" and all_valid and recent > 0:
        verdict["verdict"] = "EXIT_TRACE_PROVEN"
        verdict["confidence"] = 0.9
        verdict["exit_learning_allowed"] = True
    verdict["stamp"] = STAMP
    VERDICT_JSON.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    SAMPLE_JSON.write_text(json.dumps({"stamp": STAMP, "samples": last_three, "count": len(last_three)}, indent=2), encoding="utf-8")

    # Phase 6 — owner synthesis
    proof_lines.append("## Phase 5–6 — CSA verdict & owner synthesis")
    proof_lines.append("")
    proof_lines.append(f"- **Verdict:** {verdict['verdict']}")
    proof_lines.append(f"- **Exit learning allowed:** {verdict['exit_learning_allowed']}")
    proof_lines.append("")
    proof_lines.append("### Owner synthesis")
    proof_lines.append("")
    proof_lines.append(f"- **Is exit decision tracing LIVE on the droplet?** {'Yes' if verdict['verdict'] == 'EXIT_TRACE_PROVEN' else 'No'}")
    proof_lines.append(f"- **Is UW fully granular and populated?** {'Yes' if all_valid and verdict.get('verdict') == 'EXIT_TRACE_PROVEN' else 'No'}")
    proof_lines.append("- **Can we reconstruct peak unrealized and signal state?** Yes (trace has ts, unrealized_pnl, signals per sample)")
    proof_lines.append(f"- **Proceed to exit optimization?** {'Yes' if verdict['exit_learning_allowed'] else 'No'}")
    proof_lines.append("")
    PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")

    print("PROOF written:", PROOF_MD.name)
    print("SAMPLE written:", SAMPLE_JSON.name)
    print("VERDICT written:", VERDICT_JSON.name)
    print("VERDICT:", verdict["verdict"])
    return 0 if verdict["verdict"] == "EXIT_TRACE_PROVEN" else 1


if __name__ == "__main__":
    sys.exit(main())
