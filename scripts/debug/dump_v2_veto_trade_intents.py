#!/usr/bin/env python3
"""
Extract the last N trade_intent rows blocked by v2_agent_veto from logs/run.jsonl.

Prints:
  - Full feature_snapshot (optional --no-snapshot to skip)
  - v2_ml_row when present (post-restoration main.py); else recomputes via build_vanguard_feature_map
  - "Actuals" table: every ML feature | value | NaN/0? | source bucket
  - Near-misses today: trade_intent with v2_live_gate_proba or v2_shadow_proba > threshold (default 0.20)

Run on droplet (typical):
  cd /root/stock-bot && PYTHONPATH=. python3 scripts/debug/dump_v2_veto_trade_intents.py
  PYTHONPATH=. python scripts/debug/dump_v2_veto_trade_intents.py --run logs/run.jsonl --near-miss 0.2
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _is_blank(v: Any) -> bool:
    if v is None:
        return True
    try:
        fv = float(v)
        return not math.isfinite(fv)
    except (TypeError, ValueError):
        return True


def _is_zeroish(v: Any) -> bool:
    if _is_blank(v):
        return True
    try:
        return abs(float(v)) < 1e-12
    except (TypeError, ValueError):
        return False


def _source_bucket(name: str) -> str:
    n = str(name).lower()
    if "entry_uw" in n or n.startswith("uw_"):
        return "UW"
    if "scoreflow" in n:
        return "Scoreflow/Composite"
    if "direction_intel" in n:
        return "Intel/SIP embed"
    if n in ("hour_of_day", "entry_price", "qty", "strict_open_epoch_utc", "shadow_chop_block"):
        return "Session/price"
    if n in ("symbol_enc", "side_enc"):
        return "Categorical enc"
    return "Other"


def _load_trade_intents(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event_type") != "trade_intent":
                continue
            rows.append(rec)
    return rows


def _v2_vetoes(rows: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in reversed(rows):
        if (rec.get("decision_outcome") or "").lower() != "blocked":
            continue
        br = str(rec.get("blocked_reason") or "")
        if "v2_agent_veto" not in br:
            continue
        out.append(rec)
        if len(out) >= n:
            break
    return list(reversed(out))


def _recompute_ml_row(rec: Dict[str, Any]) -> Dict[str, float]:
    from telemetry.shadow_evaluator import build_vanguard_feature_map

    snap = rec.get("feature_snapshot") if isinstance(rec.get("feature_snapshot"), dict) else {}
    comps = snap.get("components") if isinstance(snap.get("components"), dict) else {}
    cluster: Dict[str, Any] = {}
    for k in ("cluster", "composite_meta", "direction_intel_embed", "v2_uw_inputs"):
        if k in rec and isinstance(rec[k], dict):
            cluster[k] = rec[k]
    return build_vanguard_feature_map(
        symbol=str(rec.get("symbol") or ""),
        side=str(rec.get("side") or "buy"),
        now_utc=datetime.now(timezone.utc),
        feature_snapshot=snap,
        comps=comps,
        cluster=cluster if cluster else {},
        trade_id=str(rec.get("trade_id") or "") or None,
    )


def _print_actuals_table(ml_row: Dict[str, Any], feature_order: List[str], score: Any) -> None:
    print()
    print("| Signal Name | Actual Live Value | NaN/0.0? | Source |")
    print("|-------------|-------------------|----------|--------|")
    for k in feature_order:
        v = ml_row.get(k)
        blank = _is_blank(v)
        z = _is_zeroish(v)
        flag = "NaN" if blank else ("0.0" if z else "ok")
        disp = "" if blank else (str(v)[:40] if v is not None else "")
        print(f"| {k[:56]} | {disp} | {flag} | {_source_bucket(k)} |")
    print()
    sf = ml_row.get("mlf_scoreflow_total_score")
    print(f"Note: trade_intent score (composite)={score!r}  mlf_scoreflow_total_score in ML row={sf!r}")
    if not _is_blank(score) and not _is_blank(sf):
        try:
            if float(sf) < 0.5 and float(score) >= 4.0:
                print(">>> BRIDGE SUSPECT: high composite score but near-zero mlf_scoreflow_total_score in ML row.")
        except (TypeError, ValueError):
            pass


def _near_misses(rows: List[Dict[str, Any]], day: date, pmin: float) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for rec in rows:
        ts = rec.get("ts") or rec.get("timestamp")
        if not ts:
            continue
        try:
            d = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date()
        except ValueError:
            continue
        if d != day:
            continue
        p_live = rec.get("v2_live_gate_proba")
        p_sh = rec.get("v2_shadow_proba")
        best = None
        for p in (p_live, p_sh):
            if p is None:
                continue
            try:
                fv = float(p)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(fv):
                continue
            best = fv if best is None else max(best, fv)
        if best is not None and best > pmin:
            hits.append(rec)
    hits.sort(key=lambda r: float(r.get("v2_live_gate_proba") or r.get("v2_shadow_proba") or 0.0), reverse=True)
    return hits[:10]


def _anchor_diagnosis(ml_row: Dict[str, Any], fo: List[str]) -> str:
    """Heuristic: worst among drivers if zero/nan."""
    drivers = [
        "mlf_scoreflow_total_score",
        "mlf_entry_uw_flow_strength",
        "mlf_entry_uw_darkpool_bias",
        "mlf_scoreflow_components_flow",
        "mlf_scoreflow_components_dark_pool",
    ]
    bad: List[str] = []
    for d in drivers:
        if d not in fo:
            continue
        v = ml_row.get(d)
        if _is_blank(v) or _is_zeroish(v):
            bad.append(d)
    if bad:
        return "Anchor (malnourished drivers): " + ", ".join(bad)
    nan_n = sum(1 for k in fo if k not in ("symbol_enc", "side_enc") and _is_blank(ml_row.get(k)))
    return f"No single named driver all-zero; global NaN-like features in row ≈ {nan_n} / {len(fo)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=REPO / "logs" / "run.jsonl", help="Path to run.jsonl")
    ap.add_argument("-n", type=int, default=3, help="How many recent v2 vetoes to show")
    ap.add_argument("--no-snapshot", action="store_true", help="Omit printing full feature_snapshot JSON")
    ap.add_argument("--near-miss", type=float, default=0.2, metavar="P", help="List trade_intents today with proba > P")
    ap.add_argument("--day", type=str, default="", help="ISO date YYYY-MM-DD (default: UTC today)")
    args = ap.parse_args()

    rows = _load_trade_intents(args.run)
    if not rows:
        print("No trade_intent rows found (empty or missing file):", args.run, file=sys.stderr)
        return 2

    meta_path = REPO / "models" / "vanguard_v2_profit_agent_features.json"
    fo = list(json.loads(meta_path.read_text(encoding="utf-8")).get("feature_names") or [])

    vetoes = _v2_vetoes(rows, args.n)
    if not vetoes:
        print("No blocked trade_intent with blocked_reason containing v2_agent_veto in:", args.run)
        print("Total trade_intent rows scanned:", sum(1 for r in rows if r.get("event_type") == "trade_intent"))
        return 1

    print("=== Last", len(vetoes), "v2_agent_veto trade_intent rows ===\n")
    for i, rec in enumerate(vetoes, 1):
        print("--- Record", i, "---")
        print("ts:", rec.get("ts"), "symbol:", rec.get("symbol"), "side:", rec.get("side"), "score:", rec.get("score"))
        print("blocked_reason:", rec.get("blocked_reason"))
        print("v2_row_nan_fraction:", rec.get("v2_row_nan_fraction"), "v2_row_nan_count:", rec.get("v2_row_nan_count"))
        print("v2_live_gate_proba:", rec.get("v2_live_gate_proba"), "v2_shadow_proba:", rec.get("v2_shadow_proba"))
        if not args.no_snapshot and isinstance(rec.get("feature_snapshot"), dict):
            print("feature_snapshot JSON:", json.dumps(rec["feature_snapshot"], default=str)[:12000])
            if len(json.dumps(rec["feature_snapshot"], default=str)) > 12000:
                print("... (feature_snapshot truncated in CLI; use jq for full)")
        ml_row = rec.get("v2_ml_row") if isinstance(rec.get("v2_ml_row"), dict) else None
        if not ml_row:
            print("(v2_ml_row missing — recomputing from feature_snapshot only; cluster keys absent on intent may skew)")
            ml_row = _recompute_ml_row(rec)
        print("v2_ml_row keys:", len(ml_row))
        _print_actuals_table(ml_row, fo, rec.get("score"))
        print(_anchor_diagnosis(ml_row, fo))
        print()

    if args.day:
        day = date.fromisoformat(args.day)
    else:
        day = datetime.now(timezone.utc).date()
    near = _near_misses(rows, day, args.near_miss)
    print(f"=== Near-misses (UTC {day}, proba > {args.near_miss}) ===")
    if not near:
        print("None.")
    else:
        for r in near[:3]:
            pl = r.get("v2_live_gate_proba")
            ps = r.get("v2_shadow_proba")
            br = r.get("blocked_reason")
            print(f"  {r.get('symbol')} live={pl} shadow={ps} blocked_reason={br!r} score={r.get('score')}")
            if (pl is None or (isinstance(pl, float) and pl <= args.near_miss)) and ps is not None:
                print("    primary signal: shadow path proba only (live gate row may not be on older intents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
