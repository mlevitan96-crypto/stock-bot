#!/usr/bin/env python3
"""
Alpha 11 "Good Stuff" audit: strict-complete cohort only (default: gate complete_trade_ids).

Reads logs/exit_attribution.jsonl (dedupe last per trade_id), joins telemetry fields on entry/exit.
Does NOT call live UW HTTP — uses persisted entry_uw / exit_uw / attribution_components on rows.

Usage:
  PYTHONPATH=/root/stock-bot python3 scripts/_tmp_alpha11_163_good_stuff_audit.py --root /root/stock-bot \\
    --out-json reports/alpha11_163_good_stuff_audit.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Tuple


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _dedupe_by_tid(path: Path) -> Dict[str, Dict[str, Any]]:
    m: Dict[str, Dict[str, Any]] = {}
    for rec in _iter_jsonl(path):
        tid = rec.get("trade_id")
        if tid:
            m[str(tid)] = rec
    return m


def _f(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _uw(rec: Dict[str, Any], which: str) -> Dict[str, Any]:
    u = rec.get(which)
    return u if isinstance(u, dict) else {}


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    """Pearson r; for binary ys this equals the point-biserial correlation with wins."""
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    vx = sum((a - mx) ** 2 for a in xs)
    vy = sum((b - my) ** 2 for b in ys)
    if vx <= 1e-18 or vy <= 1e-18:
        return None
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    return round(cov / math.sqrt(vx * vy), 6)


def _comp_entry(rec: Dict[str, Any]) -> Dict[str, Any]:
    c = rec.get("composite_components_at_entry")
    return c if isinstance(c, dict) else {}


def _contrib_sum(rec: Dict[str, Any], needles: Tuple[str, ...]) -> float:
    ac = rec.get("attribution_components")
    if not isinstance(ac, list):
        return 0.0
    s = 0.0
    for c in ac:
        if not isinstance(c, dict):
            continue
        sid = str(c.get("signal_id") or "").lower()
        if any(n in sid for n in needles):
            try:
                s += float(c.get("contribution_to_score") or 0.0)
            except (TypeError, ValueError):
                pass
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out-json", type=Path, default=Path("reports/alpha11_163_good_stuff_audit.json"))
    args = ap.parse_args()
    root = args.root.resolve()

    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    gate = evaluate_completeness(root, audit=False, collect_complete_trade_ids=True)
    tids = [str(x) for x in (gate.get("complete_trade_ids") or [])]
    by_tid = _dedupe_by_tid(root / "logs" / "exit_attribution.jsonl")

    rows: List[Dict[str, Any]] = []
    missing = 0
    for tid in tids:
        r = by_tid.get(tid)
        if not r:
            missing += 1
            continue
        rows.append(r)

    wins = [r for r in rows if (_f(r.get("pnl")) or 0.0) > 0]
    losses = [r for r in rows if (_f(r.get("pnl")) or 0.0) <= 0]

    def _series(rs: List[Dict[str, Any]], key_path: Tuple[str, str]) -> List[float]:
        out: List[float] = []
        which, k = key_path
        for r in rs:
            u = _uw(r, which)
            v = _f(u.get(k))
            if v is not None:
                out.append(v)
        return out

    def _mean(xs: List[float]) -> Optional[float]:
        return round(sum(xs) / len(xs), 6) if xs else None

    def _comp_series(rs: List[Dict[str, Any]], comp_key: str) -> List[float]:
        out: List[float] = []
        for r in rs:
            v = _f(_comp_entry(r).get(comp_key))
            if v is not None:
                out.append(v)
        return out

    metrics = {
        "n_gate_complete_trade_ids": len(tids),
        "n_exit_rows_matched": len(rows),
        "n_missing_exit_row": missing,
        "n_wins": len(wins),
        "n_losses": len(losses),
        "win_rate": round(len(wins) / len(rows), 4) if rows else None,
        "total_pnl_usd": round(sum(_f(r.get("pnl")) or 0.0 for r in rows), 4),
        "entry_uw_flow_strength_mean_win": _mean(_series(wins, ("entry_uw", "flow_strength"))),
        "entry_uw_flow_strength_mean_loss": _mean(_series(losses, ("entry_uw", "flow_strength"))),
        "entry_uw_darkpool_bias_mean_win": _mean(_series(wins, ("entry_uw", "darkpool_bias"))),
        "entry_uw_darkpool_bias_mean_loss": _mean(_series(losses, ("entry_uw", "darkpool_bias"))),
        "exit_uw_flow_strength_mean_win": _mean(_series(wins, ("exit_uw", "flow_strength"))),
        "exit_uw_flow_strength_mean_loss": _mean(_series(losses, ("exit_uw", "flow_strength"))),
        # Entry-time composite slices (same keys as uw_composite_v2 components / main SIGNAL_COMPONENTS)
        "composite_entry_flow_mean_win": _mean(_comp_series(wins, "flow")),
        "composite_entry_flow_mean_loss": _mean(_comp_series(losses, "flow")),
        "composite_entry_market_tide_mean_win": _mean(_comp_series(wins, "market_tide")),
        "composite_entry_market_tide_mean_loss": _mean(_comp_series(losses, "market_tide")),
        "composite_entry_greeks_gamma_mean_win": _mean(_comp_series(wins, "greeks_gamma")),
        "composite_entry_greeks_gamma_mean_loss": _mean(_comp_series(losses, "greeks_gamma")),
    }

    # Point-biserial correlation(win, X) == Pearson between binary win and X (aligned per row)
    def _aligned_win_x(
        rs: List[Dict[str, Any]], x_fn: Any
    ) -> Tuple[List[float], List[float]]:
        ys: List[float] = []
        xs: List[float] = []
        for r in rs:
            y = 1.0 if (_f(r.get("pnl")) or 0.0) > 0 else 0.0
            xv = x_fn(r)
            if xv is None:
                continue
            ys.append(y)
            xs.append(float(xv))
        return xs, ys

    def _corr_label(label: str, xs: List[float], ys: List[float]) -> Dict[str, Any]:
        r = _pearson(xs, ys)
        return {"signal": label, "n_pairs": len(xs), "pearson_with_win_binary": r}

    xs_fs, ys_fs = _aligned_win_x(rows, lambda r: _f(_uw(r, "entry_uw").get("flow_strength")))
    xs_conv, ys_conv = _aligned_win_x(
        rows, lambda r: _f(_uw(r, "entry_uw").get("conviction"))
    )
    xs_cf, ys_cf = _aligned_win_x(rows, lambda r: _f(_comp_entry(r).get("flow")))
    xs_ct, ys_ct = _aligned_win_x(rows, lambda r: _f(_comp_entry(r).get("market_tide")))
    xs_cg, ys_cg = _aligned_win_x(rows, lambda r: _f(_comp_entry(r).get("greeks_gamma")))

    corrs = [
        _corr_label("entry_uw.flow_strength", xs_fs, ys_fs),
        _corr_label("entry_uw.conviction", xs_conv, ys_conv),
        _corr_label("composite_components_at_entry.flow", xs_cf, ys_cf),
        _corr_label("composite_components_at_entry.market_tide", xs_ct, ys_ct),
        _corr_label("composite_components_at_entry.greeks_gamma", xs_cg, ys_cg),
    ]
    ranked_corr = sorted(
        (c for c in corrs if c.get("pearson_with_win_binary") is not None),
        key=lambda c: abs(float(c["pearson_with_win_binary"])),
        reverse=True,
    )

    # MFE/MAE from exit_quality_metrics (same spirit as _tmp_mfe_mae_analysis)
    def mfe_pct(r: Dict[str, Any]) -> Optional[float]:
        eq = r.get("exit_quality_metrics")
        if not isinstance(eq, dict):
            return None
        mfe = _f(eq.get("mfe"))
        ep = _f(r.get("entry_price"))
        if mfe is not None and ep and ep > 0:
            return abs(mfe) / ep * 100.0
        xp = _f(r.get("exit_price"))
        if ep and xp:
            return max(0.0, (max(ep, xp) - ep) / ep * 100.0)
        return None

    mfe_w = [x for x in (mfe_pct(r) for r in wins) if x is not None]
    mfe_l = [x for x in (mfe_pct(r) for r in losses) if x is not None]
    mfe_all = [x for x in (mfe_pct(r) for r in rows) if x is not None]

    def pctile(xs: List[float], p: float) -> Optional[float]:
        if not xs:
            return None
        s = sorted(xs)
        k = (len(s) - 1) * p / 100.0
        f = int(math.floor(k))
        c = min(f + 1, len(s) - 1)
        t = k - f
        return round(s[f] * (1 - t) + s[c] * t, 6)

    mfe_block = {
        "mfe_pct_p50_all": pctile(mfe_all, 50),
        "mfe_pct_p75_all": pctile(mfe_all, 75),
        "mfe_pct_p90_all": pctile(mfe_all, 90),
        "mfe_pct_mean_winners": _mean(mfe_w),
        "mfe_pct_mean_losers": _mean(mfe_l),
    }

    # Institutional "DNA" proxies: exit attribution components naming
    needles_flow = ("flow", "premium", "unusual", "uw_flow")
    needles_dp = ("darkpool", "dark_pool", "dp")
    needles_tide = ("market_tide", "tide", "mkt_tide")
    needles_gex = ("gex", "gamma", "spot_gex", "dealer")

    win_flow_c = sum(_contrib_sum(r, needles_flow) for r in wins)
    loss_flow_c = sum(_contrib_sum(r, needles_flow) for r in losses)
    win_dp_c = sum(_contrib_sum(r, needles_dp) for r in wins)
    loss_dp_c = sum(_contrib_sum(r, needles_dp) for r in losses)
    win_td_c = sum(_contrib_sum(r, needles_tide) for r in wins)
    loss_td_c = sum(_contrib_sum(r, needles_tide) for r in losses)
    win_gx_c = sum(_contrib_sum(r, needles_gex) for r in wins)
    loss_gx_c = sum(_contrib_sum(r, needles_gex) for r in losses)

    top3_families_pnl = sorted(
        [
            {
                "family": "flow",
                "winner_minus_loser_attribution_sum": round(win_flow_c - loss_flow_c, 6),
                "winner_sum": round(win_flow_c, 6),
                "loser_sum": round(loss_flow_c, 6),
            },
            {
                "family": "greeks_gamma",
                "winner_minus_loser_attribution_sum": round(win_gx_c - loss_gx_c, 6),
                "winner_sum": round(win_gx_c, 6),
                "loser_sum": round(loss_gx_c, 6),
            },
            {
                "family": "market_tide",
                "winner_minus_loser_attribution_sum": round(win_td_c - loss_td_c, 6),
                "winner_sum": round(win_td_c, 6),
                "loser_sum": round(loss_td_c, 6),
            },
        ],
        key=lambda d: abs(d["winner_minus_loser_attribution_sum"]),
        reverse=True,
    )

    dna = {
        "attribution_components_sum_exit_contribution_to_score": {
            "flow_family_total_winners": round(win_flow_c, 6),
            "flow_family_total_losers": round(loss_flow_c, 6),
            "darkpool_family_total_winners": round(win_dp_c, 6),
            "darkpool_family_total_losers": round(loss_dp_c, 6),
            "market_tide_family_total_winners": round(win_td_c, 6),
            "market_tide_family_total_losers": round(loss_td_c, 6),
            "gex_gamma_family_total_winners": round(win_gx_c, 6),
            "gex_gamma_family_total_losers": round(loss_gx_c, 6),
        },
        "note": "Sums are over v2_exit attribution_components on exit rows when present; sparse rows contribute 0.",
    }

    verdict = {
        "cohort": "strict_gate_complete_trade_ids_only",
        "primary_telemetry_driver_hypothesis": None,
        "caveat": "Live Unusual Whales MCP (Market Tide, Spot GEX, Dark Pool) was not invoked in this script; conclusions use persisted entry_uw/exit_uw and exit attribution_components only.",
    }
    # Rank drivers for winners vs losers by mean entry_uw delta
    fd = (metrics["entry_uw_flow_strength_mean_win"] or 0) - (metrics["entry_uw_flow_strength_mean_loss"] or 0)
    dd = (metrics["entry_uw_darkpool_bias_mean_win"] or 0) - (metrics["entry_uw_darkpool_bias_mean_loss"] or 0)
    ranked = sorted(
        [
            ("entry_uw.flow_strength_edge_win_vs_loss", fd),
            ("entry_uw.darkpool_bias_edge_win_vs_loss", dd),
            ("exit_attribution_components.flow_family_winner_minus_loser_sum", win_flow_c - loss_flow_c),
            ("exit_attribution_components.darkpool_family_winner_minus_loser_sum", win_dp_c - loss_dp_c),
            ("exit_attribution_components.market_tide_family_winner_minus_loser_sum", win_td_c - loss_td_c),
            ("exit_attribution_components.gex_gamma_family_winner_minus_loser_sum", win_gx_c - loss_gx_c),
        ],
        key=lambda x: abs(x[1]),
        reverse=True,
    )
    verdict["driver_rank_by_abs_effect"] = [{"signal": a, "effect": round(b, 6)} for a, b in ranked]
    if not rows:
        verdict["primary_telemetry_driver_hypothesis"] = None
        verdict["verdict_status"] = "INSUFFICIENT_DATA_NO_EXIT_ROWS_OR_EMPTY_STRICT_COHORT"
    else:
        verdict["primary_telemetry_driver_hypothesis"] = ranked[0][0] if ranked else None
        verdict["verdict_status"] = "OK"

    out = {
        "schema": "alpha11_163_good_stuff_audit_v1",
        "gate": {k: gate.get(k) for k in ("trades_seen", "trades_complete", "LEARNING_STATUS")},
        "metrics": metrics,
        "mfe_mae_cliff_163": mfe_block,
        "institutional_dna_from_persisted_telemetry": dna,
        "correlation_with_win_binary_point_biserial": {
            "ranked_by_abs_r": ranked_corr,
            "highest_abs_r_signal": ranked_corr[0]["signal"] if ranked_corr else None,
            "note": "Pearson(entry_signal, 1_win_else_0) over strict cohort rows with finite X; equals point-biserial when Y is binary.",
        },
        "top3_weighted_families_exit_attribution_contribution_sums": top3_families_pnl,
        "board_verdict": verdict,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(args.out_json)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
