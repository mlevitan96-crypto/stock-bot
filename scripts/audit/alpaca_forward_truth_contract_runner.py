#!/usr/bin/env python3
"""
Alpaca forward truth contract: rolling strict gate (last N hours) + bounded additive repair + CERT_OK / INCIDENT artifacts.

Exit codes: 0 = trades_incomplete==0 (CERT_OK), 2 = incident after bounded repair, 1 = runtime/config error.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO = Path(__file__).resolve().parents[2]


def _load_repair_module():
    path = REPO / "scripts" / "audit" / "alpaca_strict_six_trade_additive_repair.py"
    spec = importlib.util.spec_from_file_location("alpaca_strict_six_trade_additive_repair", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repair module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_sre_engine():
    path = REPO / "scripts" / "audit" / "alpaca_sre_auto_repair_engine.py"
    spec = importlib.util.spec_from_file_location("alpaca_sre_auto_repair_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load SRE engine from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _gate(root: Path, open_ts: float, forward_since: float) -> Dict[str, Any]:
    sys.path.insert(0, str(REPO))
    from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START, evaluate_completeness

    _ = STRICT_EPOCH_START  # policy C reference
    return evaluate_completeness(
        root,
        open_ts_epoch=open_ts,
        forward_since_epoch=forward_since,
        audit=True,
    )


def _all_incomplete_tids(gate: Dict[str, Any]) -> List[str]:
    s: Set[str] = set()
    for v in (gate.get("incomplete_trade_ids_by_reason") or {}).values():
        for tid in v:
            s.add(str(tid))
    return sorted(s)


def _classify_recoverable(root: Path, tids: List[str], repair_mod) -> Tuple[List[str], List[str]]:
    rec: List[str] = []
    unrec: List[str] = []
    for tid in tids:
        batch = repair_mod.build_lines_for_trade(root, tid)
        if batch:
            rec.append(tid)
        else:
            unrec.append(tid)
    return rec, unrec


def _reason_distribution(gate: Dict[str, Any]) -> Dict[str, int]:
    h = gate.get("reason_histogram") or {}
    return {str(k): int(v) for k, v in h.items()}


def _next_actions() -> Dict[str, str]:
    return {
        "missing_unified_exit_attribution_terminal": "Emit terminal alpaca_exit_attribution in logs/alpaca_unified_events.jsonl (src/exit/exit_attribution.py unified emitter).",
        "missing_unified_entry_attribution": "Ensure alpaca_entry_attribution or additive strict_backfill_alpaca_unified_events.jsonl (scripts/audit/alpaca_strict_six_trade_additive_repair.py).",
        "missing_exit_intent_for_canonical_trade_id": "Emit exit_intent on run.jsonl keyed by trade_key/canonical_trade_id, or additive strict_backfill_run.jsonl.",
        "no_orders_rows_with_canonical_trade_id": "Orders with canonical_trade_id joining alias set, or synthetic strict_backfill_orders.jsonl row.",
        "entry_decision_not_joinable_by_canonical_trade_id": "trade_intent entered with canonical_trade_id/trade_key in alias closure, or strict_backfill_run.jsonl.",
        "cannot_derive_trade_key": "Fix unified exit trade_key or trade_id schema open_<SYM>_<ISO>.",
        "cannot_resolve_join_aliases": "Add canonical_trade_id_resolved edges or align keys (telemetry gate AUTHORITATIVE_JOIN_KEY_RULE).",
        "missing_pnl_economic_closure": "exit_attribution.jsonl economic fields (pnl) from exit path.",
        "exit_attribution_missing_positive_exit_price": "exit_attribution exit_price > 0.",
        "trade_id_schema_unexpected": "Normalize trade_id to open_<SYM>_<ISO8601>.",
        "temporal_exit_before_entry": "Fix timestamps on exit vs entry.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca forward truth contract runner")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--window-hours", type=int, default=72)
    ap.add_argument("--repair-max-rounds", type=int, default=6)
    ap.add_argument("--repair-sleep-seconds", type=int, default=10)
    ap.add_argument("--repair-internal-rounds-per-iteration", type=int, default=1, help="max-repair-rounds per subprocess")
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--md-out", type=Path, required=True)
    ap.add_argument("--incident-md", type=Path, required=True)
    ap.add_argument("--incident-json", type=Path, required=True)
    args = ap.parse_args()

    root = args.root.resolve()
    try:
        repair_mod = _load_repair_module()
        sre = _load_sre_engine()
    except Exception as e:
        print(json.dumps({"error": "sre_repair_engine_load", "detail": str(e)}), file=sys.stderr)
        return 1

    now = time.time()
    window_sec = max(3600, int(args.window_hours) * 3600)
    window_start = now - window_sec

    sys.path.insert(0, str(REPO))
    from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START

    # Policy C explicit floor: cohort never starts before strict era constant.
    open_ts_epoch = max(float(STRICT_EPOCH_START), float(window_start))
    forward_since_epoch = open_ts_epoch

    run_record: Dict[str, Any] = {
        "contract": "alpaca_forward_truth",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "window_hours": int(args.window_hours),
        "open_ts_epoch": open_ts_epoch,
        "forward_since_epoch": forward_since_epoch,
        "STRICT_EPOCH_START": STRICT_EPOCH_START,
        "strict_epoch_policy": "explicit_max(STRICT_EPOCH_START, now - window_hours)",
        "repair_max_rounds": int(args.repair_max_rounds),
        "repair_sleep_seconds": int(args.repair_sleep_seconds),
        "sre_auto_repair_engine": True,
    }

    gate0 = _gate(root, open_ts_epoch, forward_since_epoch)
    run_record["initial_gate"] = gate0

    precheck = gate0.get("precheck") or []
    if precheck:
        run_record["error"] = "precheck_failed"
        run_record["precheck"] = precheck
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(run_record, indent=2, default=str), encoding="utf-8")
        args.md_out.write_text(
            "# Forward truth contract run\n\n**FAILED precheck**\n\n```json\n"
            + json.dumps(precheck, indent=2)
            + "\n```\n",
            encoding="utf-8",
        )
        return 1

    if gate0.get("code_structural_trade_intent_no_canonical_on_entered"):
        run_record["error"] = "structural_code_path"
        run_record["sre_failure_class"] = "EMITTER_REGRESSION"
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(run_record, indent=2, default=str), encoding="utf-8")
        args.md_out.write_text("# Forward truth contract\n\n**BLOCKED:** structural trade_intent path in main.py.\n", encoding="utf-8")
        return 1

    gate, repair_actions, class_map, engine_meta = sre.run_sre_auto_repair(
        root,
        open_ts_epoch,
        forward_since_epoch,
        int(args.repair_max_rounds),
        int(args.repair_sleep_seconds),
        repair_mod,
    )
    run_record["sre_repair_actions_applied"] = repair_actions
    run_record["sre_classification_per_trade_id"] = class_map
    run_record["sre_engine_meta"] = engine_meta
    run_record["repair_trace"] = repair_actions
    if int(args.repair_internal_rounds_per_iteration) != 1:
        run_record["note_repair_internal_rounds"] = (
            "SRE engine applies one additive batch per outer round; subprocess multi-round unused."
        )
    run_record["final_gate"] = gate
    incomplete = int(gate.get("trades_incomplete") or 0)

    cert_ok = incomplete == 0
    run_record["forward_truth_contract"] = "CERT_OK" if cert_ok else "INCIDENT"
    run_record["trades_incomplete_count"] = incomplete
    run_record["exit_code_intended"] = 0 if cert_ok else 2

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)

    if cert_ok:
        args.json_out.write_text(json.dumps(run_record, indent=2, default=str), encoding="utf-8")
        vac = bool(gate.get("trades_seen") == 0)
        args.md_out.write_text(
            f"# Alpaca forward truth contract — CERT_OK\n\n"
            f"- **UTC:** {run_record['run_utc']}\n"
            f"- **Window:** {args.window_hours}h (open_ts_epoch = max(STRICT_EPOCH, now−window))\n"
            f"- **trades_seen:** {gate.get('trades_seen')}\n"
            f"- **trades_incomplete:** 0\n"
            f"- **forward_trades_incomplete:** {gate.get('forward_trades_incomplete')}\n"
            f"- **vacuous cohort:** {vac}\n"
            f"- **Artifacts:** `{args.json_out}`\n",
            encoding="utf-8",
        )
        # No incident files on success (deterministic empty optional — spec asks for CERT_OK artifact; json+md suffice)
        for p in (args.incident_md, args.incident_json):
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        print("alpaca_forward_truth_contract_runner: exit 0 CERT_OK", file=sys.stderr)
        return 0

    # INCIDENT
    tids = _all_incomplete_tids(gate)
    sample = tids[:50]
    rec, unrec = _classify_recoverable(root, tids, repair_mod)
    sre_snap = {tid: run_record.get("sre_classification_per_trade_id", {}).get(tid) for tid in sample}
    incident: Dict[str, Any] = {
        "severity": "LEARNING_BLOCKER",
        "trades_incomplete_count": incomplete,
        "sample_trade_ids": sample,
        "reason_histogram": _reason_distribution(gate),
        "recoverable_trade_ids_count": len(rec),
        "unbackfillable_trade_ids": unrec[:50],
        "next_actions_by_reason": _next_actions(),
        "open_ts_epoch": open_ts_epoch,
        "forward_since_epoch": forward_since_epoch,
        "repair_iterations_attempted": int(args.repair_max_rounds),
        "sre_classification_sample": sre_snap,
        "sre_immediate_unknown_escalation": (run_record.get("sre_engine_meta") or {}).get(
            "immediate_unknown_escalation"
        ),
        "sre_actions_count": len(run_record.get("sre_repair_actions_applied") or []),
    }
    run_record["incident"] = incident

    args.json_out.write_text(json.dumps(run_record, indent=2, default=str), encoding="utf-8")
    args.incident_json.parent.mkdir(parents=True, exist_ok=True)
    args.incident_json.write_text(json.dumps(incident, indent=2, default=str), encoding="utf-8")

    args.md_out.write_text(
        f"# Alpaca forward truth contract — INCIDENT\n\n"
        f"Incompletes persist after {args.repair_max_rounds} repair iterations.\n\n"
        f"- **trades_incomplete:** {incomplete}\n"
        f"- See `{args.incident_json}` and full `{args.json_out}`.\n",
        encoding="utf-8",
    )

    reason_lines = "\n".join(f"| {k} | {v} |" for k, v in sorted(incident["reason_histogram"].items(), key=lambda x: -x[1]))
    args.incident_md.write_text(
        f"# INCIDENT — Alpaca strict forward truth\n\n"
        f"**Severity:** LEARNING_BLOCKER\n\n"
        f"| Field | Value |\n|-------|-------|\n"
        f"| trades_incomplete_count | {incomplete} |\n"
        f"| recoverable (additive path) | {len(rec)} |\n"
        f"| unbackfillable | {len(unrec)} |\n\n"
        f"## Sample trade_ids (max 50)\n\n```\n" + "\n".join(sample) + "\n```\n\n"
        f"## Reason distribution\n\n| reason | count |\n|---|---|\n{reason_lines}\n\n"
        f"## Unbackfillable (no exit+unified terminal for additive repair)\n\n```\n"
        + "\n".join(unrec[:50])
        + "\n```\n\n"
        f"## Next actions (by reason)\n\n"
        + "\n".join(f"- **{k}:** {v}" for k, v in list(_next_actions().items())[:12])
        + "\n",
        encoding="utf-8",
    )
    print("alpaca_forward_truth_contract_runner: exit 2 INCIDENT", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
