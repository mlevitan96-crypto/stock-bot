#!/usr/bin/env python3
"""
Run direction-conditioned replay on 30d cohort (OFFLINE, REPLAY-ONLY).

Scenarios:
  A) Baseline — direction = original (flow sentiment)
  B) Suppress longs on crash days — if vol_regime==high and futures_direction==down: block long
  C) Favor shorts on crash days — if vol_regime==high and futures_direction==down: flip long->short
  D) Regime-conditioned — bear/crash: shorts only; bull: longs only; chop/neutral: require alignment
  E) Multi-signal vote — direction = sign(weighted sum of direction_components)

Output: reports/replay/direction_replay_30d_results.json and reports/board/DIRECTION_REPLAY_30D_RESULTS.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.governance.droplet_authority import add_droplet_authority_args, require_droplet_authority


def _get_component_direction(components: Dict[str, Dict], name: str) -> str:
    c = (components or {}).get(name) or {}
    v = c.get("normalized_value") or c.get("contribution_to_direction_score")
    if v is None:
        return "flat"
    try:
        x = float(v)
        if x > 0.1:
            return "up"
        if x < -0.1:
            return "down"
    except (TypeError, ValueError):
        pass
    return "flat"


def _get_vol_regime(components: Dict[str, Dict]) -> str:
    c = (components or {}).get("volatility_direction") or {}
    raw = c.get("raw_value")
    if isinstance(raw, str):
        return (raw or "mid").lower()
    return "mid"


def _weighted_vote(components: Dict[str, Dict], weights: Dict[str, float] | None = None) -> float:
    if not weights:
        weights = {
            "premarket_direction": 0.15,
            "overnight_direction": 0.15,
            "futures_direction": 0.25,
            "volatility_direction": 0.15,
            "breadth_direction": 0.1,
            "macro_direction": 0.1,
            "uw_direction": 0.1,
        }
    total = 0.0
    for name, w in weights.items():
        c = (components or {}).get(name) or {}
        v = c.get("normalized_value") or c.get("contribution_to_direction_score")
        if v is not None:
            try:
                total += float(v) * w
            except (TypeError, ValueError):
                pass
    return total


def _scenario_baseline(trade: Dict, recon: Dict) -> str:
    return trade.get("side", "long")


def _scenario_suppress_longs_crash(trade: Dict, recon: Dict) -> str | None:
    side = trade.get("side", "long")
    comps = recon.get("direction_components") or {}
    vol = _get_vol_regime(comps)
    fut = _get_component_direction(comps, "futures_direction")
    if side == "long" and vol == "high" and fut == "down":
        return None  # block
    return side


def _scenario_favor_shorts_crash(trade: Dict, recon: Dict) -> str:
    side = trade.get("side", "long")
    comps = recon.get("direction_components") or {}
    vol = _get_vol_regime(comps)
    fut = _get_component_direction(comps, "futures_direction")
    if side == "long" and vol == "high" and fut == "down":
        return "short"
    return side


def _scenario_regime_conditioned(trade: Dict, recon: Dict) -> str | None:
    regime = (trade.get("regime_at_entry") or "").strip().lower()
    side = trade.get("side", "long")
    if regime in ("bear", "crash", "panic", "risk_off"):
        return "short"  # shorts only
    if regime in ("bull", "risk_on"):
        return "long"  # longs only
    # chop / neutral: require futures alignment
    comps = recon.get("direction_components") or {}
    fut = _get_component_direction(comps, "futures_direction")
    if side == "long" and fut == "down":
        return None
    if side == "short" and fut == "up":
        return None
    return side


def _scenario_multi_signal_vote(trade: Dict, recon: Dict) -> str:
    comps = recon.get("direction_components") or {}
    vote = _weighted_vote(comps)
    if vote > 0.05:
        return "long"
    if vote < -0.05:
        return "short"
    return trade.get("side", "long")  # tie: keep original


def _pnl_for_side(entry_price: float, exit_price: float, qty: float, side: str) -> float:
    if side == "long":
        return (exit_price - entry_price) * qty
    return (entry_price - exit_price) * qty


def _run_scenario(
    cohort: Tuple[Dict, ...],
    reconstructions: List[Dict],
    scenario_fn,
    name: str,
) -> Dict[str, Any]:
    recon_by_key: Dict[str, Dict] = {}
    for r in reconstructions:
        k = f"{r.get('symbol')}|{str(r.get('entry_ts'))[:19]}"
        recon_by_key[k] = r

    pnls: List[float] = []
    by_regime: Dict[str, List[float]] = {}
    for t in cohort:
        k = f"{t.get('symbol')}|{str(t.get('entry_ts'))[:19]}"
        recon = recon_by_key.get(k, {})
        effective_side = scenario_fn(t, recon)
        if effective_side is None:
            continue  # blocked
        entry_price = float(t.get("entry_price") or 0)
        exit_price = float(t.get("exit_price") or 0)
        qty = float(t.get("qty") or 1)
        pnl = _pnl_for_side(entry_price, exit_price, qty, effective_side)
        pnls.append(pnl)
        reg = (t.get("regime_at_entry") or "unknown").strip() or "unknown"
        by_regime.setdefault(reg, []).append(pnl)

    total_pnl = sum(pnls)
    n = len(pnls)
    n_blocked = len(cohort) - n
    expectancy = total_pnl / n if n else 0.0
    wins = sum(1 for p in pnls if p > 0)
    win_rate = wins / n if n else 0.0

    # max_drawdown (cumulative)
    cum = 0.0
    peak = 0.0
    dd = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    max_drawdown = dd

    # tail_loss: worst 5% of trades (by PnL)
    sorted_pnl = sorted(pnls)
    tail_n = max(1, int(len(sorted_pnl) * 0.05))
    tail_loss = sum(sorted_pnl[:tail_n]) if sorted_pnl else 0.0

    by_regime_summary = {reg: {"total_pnl": sum(v), "count": len(v), "win_rate": sum(1 for x in v if x > 0) / len(v) if v else 0} for reg, v in by_regime.items()}

    return {
        "scenario": name,
        "total_pnl": round(total_pnl, 2),
        "expectancy_per_trade": round(expectancy, 4),
        "win_rate": round(win_rate, 4),
        "max_drawdown": round(max_drawdown, 2),
        "tail_loss": round(tail_loss, 2),
        "n_trades": n,
        "n_blocked": n_blocked,
        "by_regime": by_regime_summary,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default="")
    ap.add_argument("--end-date", default="")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--recon-file", default="", help="Path to direction_reconstruction_30d.jsonl")
    ap.add_argument("--out-json", default="", help="Path to results JSON")
    ap.add_argument("--out-md", default="", help="Path to results MD")
    add_droplet_authority_args(ap)
    args = ap.parse_args()
    require_droplet_authority("run_direction_replay_30d", args, REPO)
    base = Path(args.base_dir) if args.base_dir else REPO
    recon_path = Path(args.recon_file) if args.recon_file else REPO / "reports" / "replay" / "direction_reconstruction_30d.jsonl"
    out_json = Path(args.out_json) if args.out_json else REPO / "reports" / "replay" / "direction_replay_30d_results.json"
    out_md = Path(args.out_md) if args.out_md else REPO / "reports" / "board" / "DIRECTION_REPLAY_30D_RESULTS.md"

    from scripts.replay.load_30d_backtest_cohort import load_30d_backtest_cohort
    from datetime import datetime, timezone
    end_date = args.end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cohort, window_days = load_30d_backtest_cohort(base, end_date, args.days)

    if not cohort:
        print("No cohort loaded; run with logs present (e.g. on droplet).", file=sys.stderr)
        return 1

    # Load reconstructions (must match cohort order or key by symbol|entry_ts)
    reconstructions: List[Dict] = []
    if recon_path.exists():
        for line in recon_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                reconstructions.append(json.loads(line))
            except Exception:
                continue
    # If no recon file, build minimal recon per trade (synthetic from regime)
    if len(reconstructions) != len(cohort):
        from scripts.replay.reconstruct_direction_30d import reconstruct_direction_components
        reconstructions = []
        for t in cohort:
            comps, conf, src = reconstruct_direction_components(t)
            reconstructions.append({
                "trade_id": t.get("trade_id"),
                "symbol": t.get("symbol"),
                "entry_ts": t.get("entry_ts"),
                "direction_components": comps,
                "direction_confidence": conf,
                "regime_at_entry": t.get("regime_at_entry"),
                "reconstruction_source": src,
            })

    scenarios = [
        (_scenario_baseline, "A_baseline"),
        (_scenario_suppress_longs_crash, "B_suppress_longs_crash"),
        (_scenario_favor_shorts_crash, "C_favor_shorts_crash"),
        (_scenario_regime_conditioned, "D_regime_conditioned"),
        (_scenario_multi_signal_vote, "E_multi_signal_vote"),
    ]
    results: List[Dict] = []
    for fn, name in scenarios:
        results.append(_run_scenario(cohort, reconstructions, fn, name))

    baseline_pnl = next((r["total_pnl"] for r in results if r["scenario"] == "A_baseline"), 0.0)
    for r in results:
        r["pnl_delta_vs_baseline"] = round((r["total_pnl"] - baseline_pnl), 2)

    # Reconstruction source breakdown (from reconstruction file or built list)
    recon_telemetry = sum(1 for r in reconstructions if (r.get("reconstruction_source") or "").strip().lower() == "telemetry")
    recon_synthetic = sum(1 for r in reconstructions if "synthetic" in (r.get("reconstruction_source") or "").strip().lower())
    recon_total = len(reconstructions)
    pct_telemetry = 100.0 * recon_telemetry / recon_total if recon_total else 0.0
    pct_synthetic = 100.0 * recon_synthetic / recon_total if recon_total else 0.0

    payload = {
        "window_start": window_days[0] if window_days else "",
        "window_end": window_days[-1] if window_days else "",
        "n_cohort": len(cohort),
        "reconstruction_source": {"total": recon_total, "telemetry": recon_telemetry, "telemetry_pct": round(pct_telemetry, 2), "synthetic": recon_synthetic, "synthetic_pct": round(pct_synthetic, 2)},
        "results": results,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {out_json}")

    # Markdown report
    lines = [
        "# Direction Replay 30D — Results",
        "",
        f"**Window:** {payload['window_start']} to {payload['window_end']}. **Cohort:** {payload['n_cohort']} trades.",
        "",
        "## Reconstruction source breakdown",
        "",
        f"- Total trades in reconstruction: **{recon_total}**",
        f"- Telemetry (direction_intel_embed at entry): **{recon_telemetry}** ({pct_telemetry:.1f}%)",
        f"- Synthetic (from regime_at_entry): **{recon_synthetic}** ({pct_synthetic:.1f}%)",
        "",
        "**Note:** If synthetic > 10%, this replay is not actionable for promotion (see DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md if generated).",
        "",
        "## Scenario summary",
        "",
        "| Scenario | Total PnL | PnL Δ vs baseline | Expectancy | Win rate | Max DD | Tail loss | N trades | N blocked |",
        "|----------|-----------|-------------------|------------|----------|--------|-----------|----------|-----------|",
    ]
    for r in results:
        lines.append(
            f"| {r['scenario']} | {r['total_pnl']} | {r.get('pnl_delta_vs_baseline', 0)} | {r['expectancy_per_trade']} | {r['win_rate']:.1%} | {r['max_drawdown']} | {r['tail_loss']} | {r['n_trades']} | {r.get('n_blocked', 0)} |"
        )
    # Regime breakdown (from baseline)
    baseline_result = next((r for r in results if r["scenario"] == "A_baseline"), None)
    if baseline_result and baseline_result.get("by_regime"):
        lines.append("## Regime breakdown (baseline)")
        lines.append("")
        lines.append("| Regime | Total PnL | Count | Win rate |")
        lines.append("|--------|-----------|-------|----------|")
        for reg, v in baseline_result["by_regime"].items():
            wr = v.get("win_rate", 0)
            lines.append(f"| {reg} | {v.get('total_pnl', 0):.2f} | {v.get('count', 0)} | {wr:.1%} |")
        lines.append("")

    lines.extend([
        "## Would this have prevented being all-long on crash days?",
        "",
        "- **B_suppress_longs_crash:** Blocks new longs when vol_regime==high and futures_direction==down; reduces exposure on crash days but does not open shorts.",
        "- **C_favor_shorts_crash:** Flips long->short in that same condition; would have opened shorts on crash days (if flow had been long).",
        "- **D_regime_conditioned:** Bear/crash regime -> shorts only; bull -> longs only; chop requires futures alignment. Strongest regime-based filter.",
        "- **E_multi_signal_vote:** Direction from weighted vote of premarket, overnight, futures, vol, breadth, macro, UW; can flip some longs to shorts when vote < 0.",
        "",
        "## Recommendation",
        "",
        "**Promote / Do not promote:** See board persona appendix. **Safest first:** B (suppress longs on crash) is the least invasive; C and D change direction and need backtest validation on out-of-sample period before promotion.",
        "",
        "---",
        "## Phase 5 — Multi-model and board persona commentary",
        "",
        "### Model A (implementation correctness)",
        "- Reconstruction: When direction_intel_embed.intel_snapshot_entry exists, components are from live telemetry; otherwise synthetic from regime_at_entry. Synthetic mapping: bear/crash -> vol high, futures down; bull -> vol low, futures up.",
        "- Scenarios B/C use vol_regime from volatility_direction.raw_value and futures_direction from components; if missing, default flat/mid.",
        "- PnL for flipped short: (entry_price - exit_price) * qty. Blocked trades contribute zero PnL and reduce n_trades.",
        "",
        "### Model B (strategy and overfitting risk)",
        "- Single 30d cohort: results are in-sample. Promoting a scenario on this alone risks overfitting.",
        "- B and C only act when vol_regime==high and futures_direction==down; if that combination was rare in the 30d window, the delta may be small or noisy.",
        "- D is aggressive (bear/crash = shorts only); may improve in true bear periods but hurt in chop.",
        "- Recommendation: Use this report for hypothesis generation; validate on a different 30d or walk-forward before any live change.",
        "",
        "### Equity Skeptic",
        "Replay shows hypothetical PnL under different direction rules. Without out-of-sample validation, do not promote. Prefer B (suppress longs) as first experiment; C/D change sign of exposure and need regime accuracy.",
        "",
        "### Risk Officer",
        "B reduces long exposure in crash conditions without adding short risk. C and D add short exposure; ensure sizing and risk limits are defined before any promotion. Tail loss and max_drawdown in the table should inform capital allocation.",
        "",
        "### Innovation Officer",
        "Run the same scenarios on a different 30d window (e.g. prior 30d) and compare. If B consistently improves or holds PnL with lower drawdown, propose a 1-week paper test with B only.",
        "",
        "### Customer Advocate",
        "If baseline was 'all long on crash days,' B would have blocked some of those longs; C would have flipped them to short. The table quantifies the hypothetical effect. Transparency: document which scenario (if any) is chosen for a future test and why.",
        "",
        "### SRE",
        "Replay is offline; no operational impact. If a scenario is promoted to config, add feature flag and kill switch; log which rule applied per trade for audit.",
        "",
    ])
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
