#!/usr/bin/env python3
"""
Displacement deep-dive add-on (Phases 10–12).

Run on droplet:
  cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_displacement_deepdive_addon.py --root /root/stock-bot --evidence-et 2026-04-01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]

H_LABELS = ("pnl_1m", "pnl_5m", "pnl_15m", "pnl_30m", "pnl_60m")


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(float(v), tz=timezone.utc)
    s = str(v).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s.replace(" ", "T")[:32]).astimezone(timezone.utc)
    except Exception:
        return None


def _norm_dir(row: Dict[str, Any]) -> str:
    for k in ("side", "direction"):
        x = str(row.get(k) or "").lower()
        if x in ("long", "buy", "bull", "bullish"):
            return "long"
        if x in ("short", "sell", "bear", "bearish"):
            return "short"
    return "unknown"


def _safe_float(x: Any) -> Optional[float]:
    try:
        f = float(x)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def load_bars(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = payload.get("data") or {}
            bars = data.get("bars") or {}
            for sym, arr in bars.items():
                if not isinstance(arr, list):
                    continue
                su = str(sym).upper()
                for b in arr:
                    if not isinstance(b, dict):
                        continue
                    t = _parse_ts(b.get("t"))
                    if t is None:
                        continue
                    try:
                        o, h, l, c = float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    out[su].append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": int(b.get("v") or 0)})
    for sym in out:
        out[sym].sort(key=lambda x: x["t"])
    return dict(out)


def bar_idx_at_or_after(bars: List[Dict[str, Any]], ts: datetime) -> int:
    times = [b["t"] for b in bars]
    i = bisect_left(times, ts)
    return i if i < len(bars) else -1


def top_components(comps: Any, n: int = 3) -> List[Tuple[str, float]]:
    if not isinstance(comps, dict):
        return []
    scored: List[Tuple[str, float]] = []
    for k, v in comps.items():
        fv = _safe_float(v)
        if fv is not None:
            scored.append((str(k), fv))
    scored.sort(key=lambda x: abs(x[1]), reverse=True)
    return scored[:n]


def atr_abs_proxy(bars: List[Dict[str, Any]], end_idx: int, period: int = 14) -> Optional[float]:
    start = end_idx - period
    if start < 0:
        return None
    trs: List[float] = []
    for j in range(start, end_idx):
        b = bars[j]
        prev_c = bars[j - 1]["c"] if j > 0 else b["o"]
        tr = max(b["h"] - b["l"], abs(b["h"] - prev_c), abs(b["l"] - prev_c))
        trs.append(tr)
    return sum(trs) / len(trs) if trs else None


def mean_vol(bars: List[Dict[str, Any]], end_idx: int, period: int = 14) -> Optional[float]:
    start = max(0, end_idx - period)
    seg = bars[start:end_idx]
    if not seg:
        return None
    return float(sum(b["v"] for b in seg)) / len(seg)


def emulate_exit(
    bars: List[Dict[str, Any]],
    entry_idx: int,
    side: str,
    qty: float,
    entry_px: float,
    atr_a: float,
    k: float,
    m: float,
    max_bars: int,
) -> Optional[float]:
    if entry_idx < 0 or entry_idx >= len(bars) or atr_a <= 0 or max_bars < 1:
        return None
    stop_dist = k * atr_a
    tp_dist = m * atr_a
    end_i = min(len(bars) - 1, entry_idx + max_bars)
    if side == "long":
        sl = entry_px - stop_dist
        tp = entry_px + tp_dist
        for j in range(entry_idx, end_i + 1):
            b = bars[j]
            if b["l"] <= sl:
                return (sl - entry_px) * qty
            if b["h"] >= tp:
                return (tp - entry_px) * qty
        return (bars[end_i]["c"] - entry_px) * qty
    if side == "short":
        sl = entry_px + stop_dist
        tp = entry_px - tp_dist
        for j in range(entry_idx, end_i + 1):
            b = bars[j]
            if b["h"] >= sl:
                return (entry_px - sl) * qty
            if b["l"] <= tp:
                return (entry_px - tp) * qty
        return (entry_px - bars[end_i]["c"]) * qty
    return None


def load_snapshots(path: Path, max_lines: int = 50000) -> Dict[str, List[Tuple[float, Dict[str, Any]]]]:
    by_sym: Dict[str, List[Tuple[float, Dict[str, Any]]]] = defaultdict(list)
    if not path.is_file():
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    chunk = lines[-max_lines:] if len(lines) > max_lines else lines
    for ln in chunk:
        ln = ln.strip()
        if not ln:
            continue
        try:
            o = json.loads(ln)
        except json.JSONDecodeError:
            continue
        sym = str(o.get("symbol") or "").upper()
        ts = _parse_ts(o.get("ts_iso") or o.get("timestamp"))
        if not sym or ts is None:
            continue
        by_sym[sym].append((ts.timestamp(), o))
    for sym in by_sym:
        by_sym[sym].sort(key=lambda x: x[0])
    return dict(by_sym)


def snap_before(by_sym: Dict[str, List[Tuple[float, Dict[str, Any]]]], sym: str, tsec: float) -> Optional[Dict[str, Any]]:
    arr = by_sym.get(sym.upper())
    if not arr:
        return None
    ts_list = [a[0] for a in arr]
    i = bisect_left(ts_list, tsec) - 1
    if i < 0:
        return None
    return arr[i][1]


def session_et() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def _gini_impurity(y: List[int]) -> float:
    if not y:
        return 0.0
    n = len(y)
    p = sum(y) / n
    return 2 * p * (1 - p)


def best_univariate_split(
    X: List[List[float]], y: List[int], feat_names: List[str]
) -> List[Dict[str, Any]]:
    """Greedy single-threshold rules ranked by impurity reduction (train set)."""
    rules: List[Dict[str, Any]] = []
    n = len(y)
    if n < 20:
        return rules
    base = _gini_impurity(y)
    for j, name in enumerate(feat_names):
        vals = sorted({X[i][j] for i in range(n) if not math.isnan(X[i][j])})
        if len(vals) < 2:
            continue
        candidates = [vals[len(vals) // 4], vals[len(vals) // 2], vals[3 * len(vals) // 4]]
        for thr in candidates:
            for op in ("<=", ">"):
                left = [i for i in range(n) if (X[i][j] <= thr if op == "<=" else X[i][j] > thr)]
                right = [i for i in range(n) if i not in left]
                if len(left) < 30 or len(right) < 30:
                    continue
                yl = [y[i] for i in left]
                yr = [y[i] for i in right]
                g = base - (len(yl) / n) * _gini_impurity(yl) - (len(yr) / n) * _gini_impurity(yr)
                bad_rate_l = sum(yl) / len(yl)
                bad_rate_r = sum(yr) / len(yr)
                rules.append(
                    {
                        "feature": name,
                        "operator": op,
                        "threshold": round(thr, 6),
                        "impurity_reduction": round(g, 6),
                        "n_left": len(yl),
                        "n_right": len(yr),
                        "bad_rate_left": round(bad_rate_l, 4),
                        "bad_rate_right": round(bad_rate_r, 4),
                    }
                )
    rules.sort(key=lambda r: -r["impurity_reduction"])
    return rules[:10]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--evidence-et", type=str, default=None)
    ap.add_argument("--notional-usd", type=float, default=500.0)
    ap.add_argument("--min-exec-score", type=float, default=2.7)
    args = ap.parse_args()
    root = args.root.resolve()
    et = args.evidence_et or session_et()
    ev = root / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)

    cf_path = ev / "BLOCKED_COUNTERFACTUAL_PNL_FULL.json"
    if not cf_path.is_file():
        print("missing", cf_path)
        return 2

    cf = json.loads(cf_path.read_text(encoding="utf-8"))
    cf_by_key: Dict[str, Dict[str, Any]] = {}
    for row in cf.get("per_row", []):
        k = f"{row.get('symbol')}|{row.get('block_ts')}"
        cf_by_key[k] = row

    blocked_path = root / "state" / "blocked_trades.jsonl"
    blocked_rows: List[Dict[str, Any]] = []
    with blocked_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                blocked_rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    bars_map = load_bars(root / "artifacts" / "market_data" / "alpaca_bars.jsonl")
    snaps = load_snapshots(root / "logs" / "score_snapshot.jsonl")

    minute_counts: Counter[str] = Counter()
    for r in blocked_rows:
        ts = _parse_ts(r.get("timestamp"))
        if ts:
            minute_counts[ts.replace(second=0, microsecond=0).isoformat()] += 1

    override_rows: List[Dict[str, Any]] = []
    intent_unknown = 0
    pair_oc: Dict[Tuple[str, str], float] = defaultdict(float)

    for br in blocked_rows:
        reason = str(br.get("block_reason") or br.get("reason") or "")
        if reason != "displacement_blocked":
            continue
        sym = str(br.get("symbol") or "").upper()
        bts = _parse_ts(br.get("timestamp"))
        if not sym or bts is None:
            continue
        biso = bts.isoformat().replace("+00:00", "Z")
        key = f"{sym}|{biso}"
        cfrow = cf_by_key.get(key)
        if not cfrow or not cfrow.get("coverage"):
            continue

        direction = _norm_dir(br)
        score = br.get("score")
        comps = br.get("components") if isinstance(br.get("components"), dict) else {}
        top_c = top_components(comps, 5)
        displaced = str(br.get("displaced_symbol") or "UNKNOWN").upper()
        policy_reason = str(br.get("policy_reason") or "unknown_policy")[:200]

        if direction == "unknown" or score is None:
            intent_unknown += 1
            intent_status = "intent_unknown"
        else:
            intent_status = "intent_known"

        pva = cfrow.get("pnl_variant_a_usd") or {}
        p60 = _safe_float(pva.get("pnl_60m"))
        oc60 = max(p60 or 0.0, 0.0)
        pair_oc[(sym, displaced)] += oc60

        tsec = bts.timestamp()
        snap = snap_before(snaps, sym, tsec)
        snap_comps: Dict[str, float] = {}
        if snap:
            sgs = snap.get("signal_group_scores")
            if isinstance(sgs, dict):
                c = sgs.get("components")
                if isinstance(c, dict):
                    for kk, vv in c.items():
                        fv = _safe_float(vv)
                        if fv is not None:
                            snap_comps[str(kk)] = fv

        hour_utc = bts.hour
        tod = "pre_14" if hour_utc < 14 else "14_20" if hour_utc < 20 else "post_20"
        blist = bars_map.get(sym)
        vol_p = None
        atr_pp = None
        atr_a = None
        i0 = bar_idx_at_or_after(blist, bts) if blist else -1
        if blist and i0 >= 14:
            atr_a = atr_abs_proxy(blist, i0, 14)
            if atr_a and blist[i0 - 1]["c"] > 0:
                atr_pp = atr_a / blist[i0 - 1]["c"]
            vol_p = mean_vol(blist, i0, 14)

        minute_key = bts.replace(second=0, microsecond=0).isoformat()
        conc = float(minute_counts.get(minute_key, 0))

        dist_thr = None
        sf = _safe_float(score)
        if sf is not None:
            dist_thr = sf - float(args.min_exec_score)

        regime = br.get("regime_label") or br.get("market_regime")
        if snap and regime is None:
            regime = snap.get("regime_label")
        if isinstance(regime, dict):
            regime = str(regime.get("label") or regime.get("regime") or "")

        dp = _safe_float(br.get("decision_price") or br.get("would_have_entered_price"))
        qty = max(args.notional_usd / dp, 0.0001) if dp and dp > 0 else 1.0

        pretrade_key = hashlib.sha256(f"{sym}|{biso}|{direction}".encode()).hexdigest()[:24]

        override_rows.append(
            {
                "block_ts_iso": biso,
                "symbol": sym,
                "displaced_symbol": displaced,
                "intended_direction": direction,
                "intent_status": intent_status,
                "block_reason": reason,
                "veto_gate": "displacement_gate",
                "veto_reason": policy_reason,
                "score": score,
                "distance_to_min_exec_score": dist_thr,
                "top_components_blocked": [{"name": a, "value": b} for a, b in top_c],
                "score_snapshot_joined": bool(snap),
                "snap_components_top": [{"name": a, "value": b} for a, b in top_components(snap_comps, 3)],
                "counterfactual_variant_a_usd": {k: pva.get(k) for k in H_LABELS if k in pva},
                "time_of_day_bucket_utc": tod,
                "hour_utc": hour_utc,
                "volatility_proxy_atr_pct": atr_pp,
                "liquidity_proxy_avg_vol_14m": vol_p,
                "concurrency_blocks_same_minute": conc,
                "regime_label": regime,
                "pretrade_key": pretrade_key,
                "qty_notional": round(qty, 6),
                "_entry_idx": i0,
                "_atr_abs": atr_a,
                "_entry_px": blist[i0]["o"] if blist and i0 >= 0 else None,
            }
        )

    n_disp = len(override_rows)
    pct_unk = round(100.0 * intent_unknown / n_disp, 4) if n_disp else 0.0
    top5_pairs = sorted(pair_oc.items(), key=lambda x: -x[1])[:5]

    om = {
        "displacement_blocked_covered_rows": n_disp,
        "intent_unknown_count": intent_unknown,
        "intent_unknown_pct": pct_unk,
        "top_5_override_pairs_by_opportunity_cost_60m": [
            {"challenger_symbol": a[0], "displaced_symbol": a[1], "opportunity_cost_sum_pnl60_pos_usd": round(b, 4)}
            for a, b in top5_pairs
        ],
        "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in override_rows],
    }
    (ev / "DISPLACEMENT_OVERRIDE_MAP.json").write_text(json.dumps(om, indent=2), encoding="utf-8")

    md_om = [
        "# DISPLACEMENT_OVERRIDE_MAP\n",
        f"- Covered `displacement_blocked` rows with counterfactual coverage: **{n_disp}**\n",
        f"- `intent_unknown` (missing direction or score): **{intent_unknown}** (**{pct_unk}%**)\n",
        "\n## Top 5 override pairs by opportunity_cost (sum max(pnl_60m,0), USD)\n\n",
    ]
    for idx, item in enumerate(om["top_5_override_pairs_by_opportunity_cost_60m"], start=1):
        md_om.append(
            f"{idx}. **{item['challenger_symbol']}** vs incumbent **{item['displaced_symbol']}**: **{item['opportunity_cost_sum_pnl60_pos_usd']}** USD\n"
        )
    md_om.append("\n## JSON\n\n`DISPLACEMENT_OVERRIDE_MAP.json` (`rows` includes counterfactual columns + join flags).\n")
    (ev / "DISPLACEMENT_OVERRIDE_MAP.md").write_text("".join(md_om), encoding="utf-8")

    # Phase 11
    HKEY = "pnl_60m"
    feat_names = [
        "hour_utc",
        "dist_thr",
        "atr_pct",
        "log1p_vol",
        "log1p_conc",
        "snap_joined",
    ]
    X: List[List[float]] = []
    y: List[int] = []
    t_order: List[float] = []
    meta: List[Dict[str, Any]] = []

    for r in override_rows:
        p60 = _safe_float((r.get("counterfactual_variant_a_usd") or {}).get(HKEY))
        if p60 is None:
            continue
        bts = _parse_ts(r["block_ts_iso"])
        if bts is None:
            continue
        is_bad = 1 if p60 > 0 else 0
        atrp = r.get("volatility_proxy_atr_pct")
        volp = r.get("liquidity_proxy_avg_vol_14m")
        dist = r.get("distance_to_min_exec_score")
        row_x = [
            float(r["hour_utc"]),
            float(dist) if dist is not None else float("nan"),
            float(atrp) if atrp is not None else float("nan"),
            math.log1p(float(volp)) if volp is not None else float("nan"),
            math.log1p(float(r.get("concurrency_blocks_same_minute") or 0)),
            1.0 if r.get("score_snapshot_joined") else 0.0,
        ]
        X.append(row_x)
        y.append(is_bad)
        t_order.append(bts.timestamp())
        meta.append({"symbol": r["symbol"], "tod": r.get("time_of_day_bucket_utc")})

    # median impute for tree-like rules
    def col_median(j: int) -> float:
        col = [X[i][j] for i in range(len(X)) if not math.isnan(X[i][j])]
        return statistics.median(col) if col else 0.0

    med = [col_median(j) for j in range(len(feat_names))]
    Ximp = [[X[i][j] if not math.isnan(X[i][j]) else med[j] for j in range(len(feat_names))] for i in range(len(X))]

    rules_train = best_univariate_split(Ximp, y, feat_names)

    def predict_bad_top_rule(i: int, r0: Dict[str, Any]) -> int:
        j = feat_names.index(r0["feature"])
        thr = r0["threshold"]
        op = r0["operator"]
        v = Ximp[i][j]
        in_left = v <= thr if op == "<=" else v > thr
        if r0["bad_rate_left"] >= r0["bad_rate_right"]:
            return 1 if in_left else 0
        return 1 if not in_left else 0

    # time split stability: first 70% vs last 30% by timestamp
    order = sorted(range(len(t_order)), key=lambda i: t_order[i])
    cut = int(0.7 * len(order))
    train_i = set(order[:cut])
    test_i = set(order[cut:])
    train_acc_rules: List[Dict[str, Any]] = []
    if rules_train:
        r0 = rules_train[0]
        pred = [predict_bad_top_rule(i, r0) for i in range(len(Ximp))]
        tr = sum(1 for i in train_i if pred[i] == y[i]) / len(train_i) if train_i else float("nan")
        te = sum(1 for i in test_i if pred[i] == y[i]) / len(test_i) if test_i else float("nan")
        train_acc_rules = [{"rule_index": 0, "train_accuracy": round(tr, 4), "test_accuracy": round(te, 4)}]

    bad_n = sum(y)
    good_n = len(y) - bad_n
    baseline_bad_rate = bad_n / len(y) if y else 0

    # Symbol split: half symbols train half test
    sym_set = list({m["symbol"] for m in meta})
    sym_set.sort()
    sym_cut = len(sym_set) // 2
    train_sym = set(sym_set[:sym_cut])
    tr_s = {i for i in range(len(meta)) if meta[i]["symbol"] in train_sym}
    te_s = set(range(len(meta))) - tr_s
    sym_split_acc = None
    if rules_train:
        r0 = rules_train[0]
        sym_split_acc = {
            "train_sym_accuracy": round(sum(1 for i in tr_s if predict_bad_top_rule(i, r0) == y[i]) / len(tr_s), 4)
            if tr_s
            else None,
            "test_sym_accuracy": round(sum(1 for i in te_s if predict_bad_top_rule(i, r0) == y[i]) / len(te_s), 4)
            if te_s
            else None,
        }

    can_separate = bool(rules_train) and rules_train[0]["impurity_reduction"] > 0.001
    conclusion = (
        "A) We can separate GOOD vs BAD displacement blocks with decision-time features (see top rules)."
        if can_separate
        else "B) We cannot separate; missing feature(s) required — extend with UW subfields or intra-minute microstructure."
    )

    sep = {
        "horizon_classification": HKEY,
        "bad_definition": "pnl_60m_variant_a > 0",
        "good_definition": "pnl_60m_variant_a <= 0",
        "n_rows": len(y),
        "n_bad": bad_n,
        "n_good": good_n,
        "baseline_bad_rate": round(baseline_bad_rate, 4),
        "feature_names": feat_names,
        "top_10_univariate_rules": rules_train,
        "stability_time_split": train_acc_rules,
        "stability_symbol_split": sym_split_acc,
        "conclusion_AB": conclusion,
    }
    (ev / "DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json").write_text(json.dumps(sep, indent=2), encoding="utf-8")
    md_sep = [
        "# DISPLACEMENT_GOOD_VS_BAD_SEPARATION\n",
        f"- **Classification horizon:** `{HKEY}` Variant A\n",
        f"- **n:** {len(y)} (BAD={bad_n}, GOOD={good_n})\n",
        f"- **Conclusion:** {conclusion}\n",
        "\n## Top rules (univariate impurity reduction)\n\n",
        "```json\n",
        json.dumps(rules_train[:10], indent=2),
        "\n```\n",
    ]
    (ev / "DISPLACEMENT_GOOD_VS_BAD_SEPARATION.md").write_text("".join(md_sep), encoding="utf-8")

    # Phase 12 exit emulator grid
    ks = [0.5, 1.0, 1.5]
    ms = [0.5, 1.0]
    Ns = [15, 30, 60]
    grid_results: List[Dict[str, Any]] = []

    for k in ks:
        for m in ms:
            for N in Ns:
                pnls: List[float] = []
                for r in override_rows:
                    direction = r["intended_direction"]
                    if direction not in ("long", "short"):
                        continue
                    blist = bars_map.get(r["symbol"])
                    i0 = r["_entry_idx"]
                    atr_a = r["_atr_abs"]
                    ep = r["_entry_px"]
                    if blist is None or i0 < 0 or atr_a is None or ep is None:
                        continue
                    q = r["qty_notional"]
                    pnl = emulate_exit(blist, i0, direction, q, ep, atr_a, k, m, N)
                    if pnl is not None:
                        pnls.append(pnl)
                if pnls:
                    grid_results.append(
                        {
                            "k_atr_stop": k,
                            "m_atr_tp": m,
                            "N_max_minutes": N,
                            "n": len(pnls),
                            "mean_pnl_usd": round(statistics.mean(pnls), 6),
                            "p05_pnl_usd": round(sorted(pnls)[max(0, int(0.05 * (len(pnls) - 1)))], 6),
                        }
                    )

    pos_cells = sum(1 for g in grid_results if g["mean_pnl_usd"] > 0)
    persist = pos_cells >= max(1, len(grid_results) // 2) if grid_results else False
    em_out = {
        "proxy_documentation": {
            "atr": "14-bar mean true range in price units before entry bar",
            "stop": "entry +/- k*ATR (long below, short above)",
            "take_profit": "entry +/- m*ATR",
            "time_stop": "N minutes = N bars of 1Min data from entry bar",
        },
        "grid": grid_results,
        "opportunity_persists_majority_positive_mean_cells": persist,
        "cells_positive_mean_count": pos_cells,
        "cells_total": len(grid_results),
    }
    (ev / "DISPLACEMENT_EXIT_EMULATOR_RESULTS.json").write_text(json.dumps(em_out, indent=2), encoding="utf-8")
    md_em = [
        "# DISPLACEMENT_EXIT_EMULATOR_RESULTS\n",
        "## Hard gate answer\n\n",
        f"- **Does displacement opportunity persist under exit-emulator sensitivity?** **{'YES' if persist else 'NO'}** "
        f"— **{pos_cells}/{len(grid_results)}** grid cells have **mean_pnl_usd > 0** over covered displacement rows.\n",
        "\n## Grid (subset)\n\n",
        "```json\n",
        json.dumps(grid_results[:12], indent=2),
        "\n```\n",
    ]
    (ev / "DISPLACEMENT_EXIT_EMULATOR_RESULTS.md").write_text("".join(md_em), encoding="utf-8")

    print(ev)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
