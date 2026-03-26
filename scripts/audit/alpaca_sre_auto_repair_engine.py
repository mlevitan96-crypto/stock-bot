"""
SRE auto-repair engine: classify strict-chain failures, apply additive playbooks, re-verify.

Wraps strict gate + alpaca_strict_six_trade_additive_repair.apply_backfill_for_trade_ids.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
_AUDIT = str(REPO / "scripts" / "audit")
if _AUDIT not in sys.path:
    sys.path.insert(0, _AUDIT)

import alpaca_sre_repair_playbooks as pb  # noqa: E402

UNKNOWN = pb.UNKNOWN
classify_trade = pb.classify_trade
reasons_for_trade_id = pb.reasons_for_trade_id
classify_emitter_regression = pb.classify_emitter_regression


def _all_incomplete_tids(gate: Dict[str, Any]) -> List[str]:
    s: Set[str] = set()
    for v in (gate.get("incomplete_trade_ids_by_reason") or {}).values():
        for tid in v or []:
            s.add(str(tid))
    return sorted(s)


def _gate(root: Path, open_ts: float, forward_since: float) -> Dict[str, Any]:
    sys.path.insert(0, str(REPO))
    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    return evaluate_completeness(
        root,
        open_ts_epoch=open_ts,
        forward_since_epoch=forward_since,
        audit=True,
    )


def _load_repair_mod():
    import importlib.util

    path = REPO / "scripts" / "audit" / "alpaca_strict_six_trade_additive_repair.py"
    spec = importlib.util.spec_from_file_location("alpaca_strict_six_trade_additive_repair", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("repair module load failed")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_sre_auto_repair(
    root: Path,
    open_ts_epoch: float,
    forward_since_epoch: float,
    repair_max_rounds: int,
    repair_sleep_seconds: int,
    repair_mod: Any = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, str], Dict[str, Any]]:
    """
    Returns:
      final_gate,
      repair_actions_applied (audit trail),
      classification_per_trade_id (last snapshot for incomplete tids),
      engine_meta (flags, before/after counts)
    """
    if repair_mod is None:
        repair_mod = _load_repair_mod()

    repair_actions: List[Dict[str, Any]] = []
    classification_per_trade_id: Dict[str, str] = {}

    gate = _gate(root, open_ts_epoch, forward_since_epoch)
    initial_incomplete = int(gate.get("trades_incomplete") or 0)
    meta: Dict[str, Any] = {
        "initial_trades_incomplete": initial_incomplete,
        "initial_trades_seen": gate.get("trades_seen"),
        "emitter_regression_gate": classify_emitter_regression(gate),
        "immediate_unknown_escalation": False,
        "rounds_executed": 0,
    }

    if initial_incomplete == 0:
        meta["final_trades_incomplete"] = 0
        return gate, repair_actions, classification_per_trade_id, meta

    incomplete_tids = _all_incomplete_tids(gate)
    for tid in incomplete_tids:
        classification_per_trade_id[tid] = classify_trade(reasons_for_trade_id(gate, tid))

    known = [t for t in incomplete_tids if classification_per_trade_id.get(t) != UNKNOWN]
    if not known:
        meta["immediate_unknown_escalation"] = True
        meta["final_trades_incomplete"] = initial_incomplete
        return gate, repair_actions, classification_per_trade_id, meta

    for rnum in range(1, max(1, int(repair_max_rounds)) + 1):
        inc_before = int(gate.get("trades_incomplete") or 0)
        if inc_before == 0:
            break

        incomplete_tids = _all_incomplete_tids(gate)
        for tid in incomplete_tids:
            classification_per_trade_id[tid] = classify_trade(reasons_for_trade_id(gate, tid))

        known_apply = [t for t in incomplete_tids if classification_per_trade_id.get(t) != UNKNOWN]
        if not known_apply:
            meta["rounds_executed"] = rnum - 1
            meta["final_trades_incomplete"] = int(gate.get("trades_incomplete") or 0)
            return gate, repair_actions, classification_per_trade_id, meta

        by_class = {t: classification_per_trade_id[t] for t in known_apply}
        batch = repair_mod.apply_backfill_for_trade_ids(root, known_apply)
        repair_actions.append(
            {
                "round": rnum,
                "trades_incomplete_before": inc_before,
                "classification_for_batch": by_class,
                "playbook": "additive_strict_chain_unified",
                **batch,
            }
        )
        time.sleep(max(0, int(repair_sleep_seconds)))
        gate = _gate(root, open_ts_epoch, forward_since_epoch)
        inc_after = int(gate.get("trades_incomplete") or 0)
        repair_actions[-1]["trades_incomplete_after"] = inc_after
        meta["rounds_executed"] = rnum

        incomplete_tids = _all_incomplete_tids(gate)
        for tid in incomplete_tids:
            classification_per_trade_id[tid] = classify_trade(reasons_for_trade_id(gate, tid))

        if inc_after == 0:
            break

    meta["final_trades_incomplete"] = int(gate.get("trades_incomplete") or 0)
    meta["emitter_regression_final"] = classify_emitter_regression(gate)
    return gate, repair_actions, classification_per_trade_id, meta
