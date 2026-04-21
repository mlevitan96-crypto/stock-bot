#!/usr/bin/env python3
"""
Marginal gate overlap (Operation Apex — Q / Data).

Partitions blocked entry cohort for the strict era using:
  - state/blocked_trades.jsonl (reason / block_reason)
  - logs/run.jsonl (optional: trade_intent funnel + gate_summary overlap)

Alpha 10 / 11 reasons match ``src/alpha10_gate.py`` / ``src/alpha11_gate.py`` emit strings.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START  # noqa: E402

REASON_A10 = "alpha10_mfe_too_low"
REASON_A11 = "alpha11_flow_strength_below_gate"
REASON_DISP = "displacement_blocked"


def _parse_ts_epoch(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)):
            return float(raw)
        s = str(raw).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def _iter_jsonl(path: Path) -> Iterator[dict]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                yield o


def _blocked_reason(rec: dict) -> str:
    return str(rec.get("reason") or rec.get("block_reason") or "").strip()


def _blocked_ts_epoch(rec: dict) -> Optional[float]:
    return _parse_ts_epoch(rec.get("timestamp") or rec.get("ts") or rec.get("_dt"))


def _analyze_blocked(path: Path, floor_epoch: float) -> Dict[str, Any]:
    counts = defaultdict(int)
    sym_a10: Set[str] = set()
    sym_a11: Set[str] = set()
    sym_disp: Set[str] = set()
    total_epoch = 0
    for rec in _iter_jsonl(path):
        ts = _blocked_ts_epoch(rec)
        if ts is None or ts < floor_epoch:
            continue
        total_epoch += 1
        rsn = _blocked_reason(rec)
        sym = str(rec.get("symbol") or "").upper().strip()
        if rsn == REASON_A10:
            counts["alpha10_only"] += 1
            if sym:
                sym_a10.add(sym)
        elif rsn == REASON_A11:
            counts["alpha11_only"] += 1
            if sym:
                sym_a11.add(sym)
        elif rsn == REASON_DISP:
            counts["displacement_only"] += 1
            if sym:
                sym_disp.add(sym)
        else:
            counts["other_reason"] += 1

    marginal = (
        int(counts["alpha10_only"])
        + int(counts["alpha11_only"])
        + int(counts["displacement_only"])
    )
    uni = sym_a10 | sym_a11
    inter = sym_a10 & sym_a11
    jacc = (len(inter) / len(uni)) if uni else 0.0

    def pct(n: int, d: int) -> float:
        return 100.0 * float(n) / float(d) if d else 0.0

    out = {
        "source": str(path),
        "floor_epoch": floor_epoch,
        "blocked_rows_total_on_or_after_floor": total_epoch,
        "marginal_gate_rows": marginal,
        "counts": dict(counts),
        "pct_of_marginal": {
            "alpha10_only": pct(int(counts["alpha10_only"]), marginal),
            "alpha11_only": pct(int(counts["alpha11_only"]), marginal),
            "displacement_only": pct(int(counts["displacement_only"]), marginal),
        },
        "pct_of_all_blocked_in_epoch": {
            "alpha10_only": pct(int(counts["alpha10_only"]), total_epoch),
            "alpha11_only": pct(int(counts["alpha11_only"]), total_epoch),
            "displacement_only": pct(int(counts["displacement_only"]), total_epoch),
        },
        "symbol_overlap_alpha10_vs_alpha11": {
            "unique_symbols_alpha10": len(sym_a10),
            "unique_symbols_alpha11": len(sym_a11),
            "intersection": len(inter),
            "union": len(uni),
            "jaccard_index": round(jacc, 6),
        },
        "both_gates_failed_same_trace": None,
        "run_jsonl_trade_intent_blocked": None,
    }
    return out


def _analyze_run_trade_intents(path: Path, floor_epoch: float) -> Dict[str, Any]:
    if not path.is_file():
        return {"error": "missing", "path": str(path)}
    n_blocked = 0
    both_false = 0
    a10_first = 0
    a11_after_a10_ok = 0
    for rec in _iter_jsonl(path):
        if rec.get("event_type") != "trade_intent":
            continue
        ts = _parse_ts_epoch(rec.get("ts") or rec.get("_dt") or rec.get("timestamp"))
        if ts is None or ts < floor_epoch:
            continue
        outcome = str(rec.get("decision_outcome", "")).lower()
        if outcome == "entered":
            continue
        n_blocked += 1
        tr = rec.get("intelligence_trace")
        if not isinstance(tr, dict):
            continue
        gates = tr.get("gates") or {}
        if not isinstance(gates, dict):
            continue
        g10 = gates.get("alpha10_mfe_gate")
        g11 = gates.get("alpha11_flow_gate")
        p10 = g10.get("passed") if isinstance(g10, dict) else None
        p11 = g11.get("passed") if isinstance(g11, dict) else None
        if p10 is False and p11 is False:
            both_false += 1
        if p10 is False:
            a10_first += 1
        if p10 is True and p11 is False:
            a11_after_a10_ok += 1
    return {
        "path": str(path),
        "trade_intent_blocked_rows": n_blocked,
        "trace_both_alpha10_and_alpha11_passed_false": both_false,
        "trace_alpha10_failed": a10_first,
        "trace_alpha11_failed_after_alpha10_ok": a11_after_a10_ok,
    }


def _q_verdict(blocked: Dict[str, Any], run_extra: Optional[Dict[str, Any]]) -> str:
    m = int(blocked.get("marginal_gate_rows") or 0)
    c10 = int((blocked.get("counts") or {}).get("alpha10_only") or 0)
    c11 = int((blocked.get("counts") or {}).get("alpha11_only") or 0)
    lines = [
        "Q verdict (marginal gates, blocked_trades.jsonl):",
        f"  Marginal cohort (A10+A11+displacement) n={m}.",
        f"  Alpha10-only blocks: {c10} ({blocked.get('pct_of_marginal', {}).get('alpha10_only', 0):.2f}% of marginal).",
        f"  Alpha11-only blocks (passed A10 in live path): {c11} ({blocked.get('pct_of_marginal', {}).get('alpha11_only', 0):.2f}% of marginal).",
        "  Serial pipeline: a single blocked row cannot carry both A10 and A11 reasons; "
        "'both' in one event is expected to be ~0 unless traces show both gate failures.",
    ]
    ov = blocked.get("symbol_overlap_alpha10_vs_alpha11") or {}
    lines.append(
        f"  Symbol reuse (any-time in epoch) A10 vs A11: Jaccard={ov.get('jaccard_index', 0)} "
        f"on |union|={ov.get('union', 0)} symbols - overlap of *names* touched by each gate, not one veto applying twice."
    )
    if run_extra and "error" not in run_extra:
        bf = int(run_extra.get("trace_both_alpha10_and_alpha11_passed_false") or 0)
        lines.append(
            f"  run.jsonl blocked intents with both alpha10_mfe_gate and alpha11_flow_gate passed=false: {bf}."
        )
        if c11 > 0 and c10 > 0:
            lines.append(
                "  Interpretation: most 'overlap anxiety' is sequential (A10 consumes some flow before A11). "
                "High A10 share implies RF MFE floor is the first choke-point; high A11 share implies survivors "
                "still hit UW flow_strength floor."
            )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Marginal gate overlap audit (Apex).")
    ap.add_argument("--root", type=Path, default=REPO_ROOT, help="Repo root.")
    ap.add_argument(
        "--floor-epoch",
        type=float,
        default=float(STRICT_EPOCH_START),
        help="UTC epoch floor (default STRICT_EPOCH_START).",
    )
    ap.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Write structured JSON (default: reports/audit/marginal_gate_overlap.json under --root).",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    blocked_path = root / "state" / "blocked_trades.jsonl"
    run_path = root / "logs" / "run.jsonl"
    blocked = _analyze_blocked(blocked_path, float(args.floor_epoch))
    run_extra = _analyze_run_trade_intents(run_path, float(args.floor_epoch))
    blocked["both_gates_failed_same_trace"] = run_extra.get("trace_both_alpha10_and_alpha11_passed_false")
    blocked["run_jsonl_trade_intent_blocked"] = run_extra
    blocked["q_verdict_text"] = _q_verdict(blocked, run_extra)
    out_path = (args.out_json or (root / "reports" / "audit" / "marginal_gate_overlap.json")).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(blocked["q_verdict_text"])
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
