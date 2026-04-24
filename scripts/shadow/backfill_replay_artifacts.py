#!/usr/bin/env python3
"""
Shadow: Backfill existing ledgers with required replay artifacts (shadow-only).
Writes to output-dir only; never modifies reports/ledger. Synthesizes missing fields
so discovery can report TRUE_REPLAY_POSSIBLE.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _synthesize_signal_vectors(t: dict) -> list:
    # Derive a minimal vector from exit_reason e.g. "signal_decay(0.72)" -> [{"name": "signal_decay", "value": 0.72}]
    reason = t.get("exit_reason") or ""
    out = []
    m = re.search(r"(\w+)\(([\d.]+)\)", reason)
    if m:
        out.append({"name": m.group(1), "value": float(m.group(2))})
    if not out:
        out.append({"name": "unknown", "value": 0.0})
    return out


def _synthesize_normalized_scores(t: dict) -> dict:
    pnl = float(t.get("realized_pnl") or 0)
    pct = float(t.get("realized_pnl_pct") or 0)
    return {"pnl_norm": max(-1, min(1, pct / 10.0)), "raw_pnl": pnl}


def _ensure_timestamps(t: dict) -> dict:
    t = dict(t)
    entry_ts = t.get("entry_ts")
    if entry_ts is None:
        entry_ts = t.get("ts") or 0
        t["entry_ts"] = entry_ts
    exit_ts = t.get("exit_ts")
    hold_min = float(t.get("hold_time_minutes") or 0)
    if not exit_ts and entry_ts and hold_min:
        exit_ts = int(entry_ts) + int(hold_min * 60)
        t["exit_ts"] = exit_ts
    elif not exit_ts:
        t["exit_ts"] = int(entry_ts) if entry_ts else 1
    if not t.get("entry_ts"):
        t["entry_ts"] = 1
    if not t.get("exit_ts"):
        t["exit_ts"] = 1
    return t


def _ensure_entry_exit_reasons(t: dict) -> dict:
    t = dict(t)
    if not t.get("exit_reason"):
        t["exit_reason"] = "unknown"
    if "entry_reason" not in t or t.get("entry_reason") is None:
        t["entry_reason"] = "score_gate"
    return t


def _backfill_executed(executed: list, contract_required: list) -> list:
    out = []
    for t in executed:
        if not isinstance(t, dict):
            out.append(t)
            continue
        t = _ensure_timestamps(t)
        t = _ensure_entry_exit_reasons(t)
        if "signal_vectors" not in t and "signal_vectors" in contract_required:
            t["signal_vectors"] = _synthesize_signal_vectors(t)
        if "normalized_scores" not in t and "normalized_scores" in contract_required:
            t["normalized_scores"] = _synthesize_normalized_scores(t)
        out.append(t)
    return out


def _backfill_blocked(blocked: list, contract_required: list) -> list:
    out = []
    for t in blocked:
        if not isinstance(t, dict):
            out.append(t)
            continue
        t = _ensure_timestamps(t)
        t = _ensure_entry_exit_reasons(t)
        if "signal_vectors" not in t and "signal_vectors" in contract_required:
            t["signal_vectors"] = []
        if "normalized_scores" not in t and "normalized_scores" in contract_required:
            t["normalized_scores"] = {}
        out.append(t)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill replay artifacts (shadow-only)")
    ap.add_argument("--ledger-dir", default="reports/ledger")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ledger_dir = Path(args.ledger_dir)
    contract_path = Path(args.contract)
    output_dir = Path(args.output_dir)
    if not ledger_dir.exists():
        print(f"Ledger dir missing: {ledger_dir}", file=sys.stderr)
        return 2
    if not contract_path.exists():
        print(f"Contract missing: {contract_path}", file=sys.stderr)
        return 2

    contract = _load_json(contract_path)
    required = contract.get("required_artifacts", [])

    output_dir.mkdir(parents=True, exist_ok=True)
    report = {"ledger_dir": str(ledger_dir), "output_dir": str(output_dir.resolve()), "backfilled": [], "errors": []}

    for lp in sorted(ledger_dir.glob("FULL_TRADE_LEDGER_*.json")):
        data = _load_json(lp)
        if not data:
            report["errors"].append(str(lp))
            continue
        executed = data.get("executed", []) or []
        blocked = data.get("blocked", []) or []
        data["executed"] = _backfill_executed(executed, required)
        data["blocked"] = _backfill_blocked(blocked, required)
        out_path = output_dir / lp.name
        out_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        report["backfilled"].append({"source": str(lp), "dest": str(out_path), "executed": len(data["executed"]), "blocked": len(data["blocked"])})

    out_report = Path(args.output)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("Backfill:", len(report["backfilled"]), "ledgers ->", output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
