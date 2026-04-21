#!/usr/bin/env python3
"""
Alpha 11 flow-strength distribution + blocked shadow expectancy (Operation Apex — Q / Data).

Reads the last N ``trade_intent`` rows from ``logs/run.jsonl`` (strict-chain entry decisions:
entered + blocked). ``trade_intent`` is the persisted entry-intent record; there is no
separate ``entry_intent`` event type in this repo.

Bins ``flow_strength`` (UW) into operator buckets, then for **blocked** intents with bars
under ``artifacts/market_data/alpaca_bars.jsonl`` computes path-real shadow PnL at 60m
(variant A from ``run_blocked_why_pipeline`` — first bar at/after intent time, bar closes).

Usage:
  PYTHONPATH=. python3 scripts/audit/alpha11_flow_distribution.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_blocked_why_module():
    path = REPO_ROOT / "scripts" / "audit" / "run_blocked_why_pipeline.py"
    spec = importlib.util.spec_from_file_location("blocked_why_mod", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _iter_jsonl(path: Path):
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


def _deep_scan_flow_strength(obj: Any, depth: int = 0) -> Optional[float]:
    """Bounded DFS for ``flow_strength`` / ``uw_flow_strength`` / ``conviction`` in nested telemetry."""
    if depth > 10 or obj is None:
        return None
    if isinstance(obj, dict):
        for key in ("flow_strength", "uw_flow_strength", "conviction"):
            if key not in obj:
                continue
            v = obj.get(key)
            if v is None or isinstance(v, (dict, list)):
                continue
            try:
                f = float(v)
                if math.isfinite(f):
                    return f
            except (TypeError, ValueError):
                continue
        for v in obj.values():
            r = _deep_scan_flow_strength(v, depth + 1)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _deep_scan_flow_strength(v, depth + 1)
            if r is not None:
                return r
    return None


def _flow_strength_from_intent(rec: dict) -> Optional[float]:
    """Mirror ``src/alpha11_gate`` extraction: v2_uw_inputs.flow_strength / conviction, then snapshot proxies."""
    fs: Optional[float] = None

    def _from_uw(uw: Any) -> Optional[float]:
        if not isinstance(uw, dict):
            return None
        for k in ("flow_strength", "conviction"):
            v = uw.get(k)
            if v is None:
                continue
            try:
                f = float(v)
                if math.isfinite(f):
                    return f
            except (TypeError, ValueError):
                continue
        return None

    cm = rec.get("composite_meta")
    if isinstance(cm, dict):
        fs = _from_uw(cm.get("v2_uw_inputs"))
    cr = rec.get("composite_result")
    if fs is None and isinstance(cr, dict):
        fs = _from_uw(cr.get("v2_uw_inputs"))
    snap = rec.get("feature_snapshot")
    if fs is None and isinstance(snap, dict):
        for k in ("uw_flow_strength", "flow_strength", "conviction"):
            v = snap.get(k)
            if v is not None:
                try:
                    f = float(v)
                    if math.isfinite(f):
                        fs = f
                        break
                except (TypeError, ValueError):
                    continue
        if fs is None and isinstance(snap.get("v2_uw_inputs"), dict):
            fs = _from_uw(snap.get("v2_uw_inputs"))
    if fs is None:
        fs = _deep_scan_flow_strength(rec.get("feature_snapshot"))
    if fs is None:
        fs = _deep_scan_flow_strength(rec.get("intelligence_trace"))
    if fs is None:
        fs = _deep_scan_flow_strength(rec.get("blocked_reason_details"))
    return fs


def _flow_bin(fs: Optional[float]) -> str:
    if fs is None or not math.isfinite(fs):
        return "unknown"
    if fs >= 0.99:
        return "d1_0.99_1.00"
    if fs >= 0.95:
        return "d2_0.95_0.989"
    if fs >= 0.90:
        return "d3_0.90_0.949"
    return "d4_lt_0.90"


def _last_trade_intents(path: Path, n: int) -> List[dict]:
    buf: List[dict] = []
    for r in _iter_jsonl(path):
        if (r.get("event_type") or r.get("event")) != "trade_intent":
            continue
        buf.append(r)
        if len(buf) > max(n * 4, n + 5000):
            buf = buf[-(n * 2) :]
    return buf[-n:] if len(buf) >= n else buf


def _norm_side(row: Dict[str, Any]) -> str:
    for k in ("side", "direction"):
        x = str(row.get(k) or "").lower()
        if x in ("long", "buy", "bull", "bullish"):
            return "long"
        if x in ("short", "sell", "bear", "bearish"):
            return "short"
    return "long"


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpha11 flow distribution + blocked shadow expectancy.")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--n", type=int, default=1000, help="Last N trade_intent rows (default 1000).")
    ap.add_argument(
        "--bars",
        type=Path,
        default=None,
        help="Alpaca bars jsonl (default: <root>/artifacts/market_data/alpaca_bars.jsonl).",
    )
    ap.add_argument("--notional-usd", type=float, default=500.0, help="Sizing for shadow USD PnL.")
    ap.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Write JSON summary (default: reports/audit/alpha11_flow_distribution.json).",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    run_path = root / "logs" / "run.jsonl"
    bars_path = args.bars or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")

    bwp = _load_blocked_why_module()
    bars_by_sym = bwp.load_bars(bars_path)

    intents = _last_trade_intents(run_path, max(1, int(args.n)))
    if not intents:
        print("No trade_intent rows found.", file=sys.stderr)
        return 1

    counts_all: Dict[str, int] = defaultdict(int)
    counts_blocked: Dict[str, int] = defaultdict(int)
    shadow_pnl60: Dict[str, List[float]] = defaultdict(list)
    shadow_miss: Dict[str, int] = defaultdict(int)

    for rec in intents:
        fs = _flow_strength_from_intent(rec)
        b = _flow_bin(fs)
        counts_all[b] += 1
        if str(rec.get("decision_outcome", "")).lower() != "blocked":
            continue
        counts_blocked[b] += 1
        sym = str(rec.get("symbol") or "").upper().strip()
        ts = bwp._parse_ts(rec.get("ts") or rec.get("timestamp"))
        side = _norm_side(rec)
        if not sym or ts is None or side == "unknown":
            shadow_miss[b] += 1
            continue
        bsym = bars_by_sym.get(sym) or []
        if not bsym:
            shadow_miss[b] += 1
            continue
        px_hint = rec.get("feature_snapshot") or {}
        dp = None
        if isinstance(px_hint, dict):
            for k in ("last", "mid", "close", "last_price"):
                v = px_hint.get(k)
                if v is not None:
                    try:
                        dp = float(v)
                        break
                    except (TypeError, ValueError):
                        continue
        qty = bwp._qty_shares(dp, float(args.notional_usd))
        out, skips = bwp.compute_variant_pnls(bsym, ts, side, qty)
        va = out.get("variant_a") or {}
        p60 = va.get("pnl_60m")
        if p60 is not None and isinstance(p60, (int, float)) and math.isfinite(float(p60)):
            shadow_pnl60[b].append(float(p60))
        else:
            shadow_miss[b] += 1

    rows_out: List[Dict[str, Any]] = []
    bin_order = ("d1_0.99_1.00", "d2_0.95_0.989", "d3_0.90_0.949", "d4_lt_0.90", "unknown")
    for lab in bin_order:
        pnls = shadow_pnl60.get(lab) or []
        n_all = int(counts_all.get(lab, 0))
        n_blk = int(counts_blocked.get(lab, 0))
        exp_pct = (100.0 * (sum(pnls) / len(pnls)) / float(args.notional_usd)) if pnls else None
        rows_out.append(
            {
                "bin": lab,
                "intents_total": n_all,
                "intents_blocked": n_blk,
                "blocked_shadow_n_scored": len(pnls),
                "blocked_shadow_n_miss_bars": int(shadow_miss.get(lab, 0)),
                "blocked_shadow_expectancy_pct_notional_60m": round(exp_pct, 4) if exp_pct is not None else None,
                "blocked_shadow_mean_usd_pnl_60m": round(sum(pnls) / len(pnls), 4) if pnls else None,
            }
        )

    n_blk_total = sum(int(counts_blocked.get(lab, 0)) for lab in bin_order)
    below_gate = int(counts_blocked.get("d2_0.95_0.989", 0)) + int(counts_blocked.get("d3_0.90_0.949", 0)) + int(
        counts_blocked.get("d4_lt_0.90", 0)
    )
    gate_floor = 0.985
    verdict = (
        f"Among last {len(intents)} trade_intents, {n_blk_total} blocked. "
        f"Blocked mass in bins strictly below {gate_floor} is dominated by "
        f"d2+d3+d4 (n={below_gate}). Compare blocked_shadow_expectancy_pct_notional_60m in d2 vs unknown — "
        f"positive d2 shadow with negligible d1 blocked mass suggests the 0.985 floor is conservative; "
        f"negative or flat d2 suggests the floor is appropriate."
    )

    out_payload = {
        "root": str(root),
        "run_jsonl": str(run_path),
        "bars_path": str(bars_path),
        "bars_loaded_symbols": len(bars_by_sym),
        "trade_intents_analyzed": len(intents),
        "q_verdict": verdict,
        "bins": rows_out,
    }
    out_path = (args.out_json or (root / "reports" / "audit" / "alpha11_flow_distribution.json")).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")

    print("| bin | intents (all) | blocked | shadow n (60m) | miss bars | expectancy %notional@60m | mean USD@60m |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for row in rows_out:
        print(
            f"| `{row['bin']}` | {row['intents_total']} | {row['intents_blocked']} | "
            f"{row['blocked_shadow_n_scored']} | {row['blocked_shadow_n_miss_bars']} | "
            f"{row['blocked_shadow_expectancy_pct_notional_60m'] if row['blocked_shadow_expectancy_pct_notional_60m'] is not None else ''} | "
            f"{row['blocked_shadow_mean_usd_pnl_60m'] if row['blocked_shadow_mean_usd_pnl_60m'] is not None else ''} |"
        )
    print("")
    print(verdict)
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
