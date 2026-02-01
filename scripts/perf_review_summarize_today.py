#!/usr/bin/env python3
"""
Synthesize PERF_TODAY_SUMMARY.md from raw JSON reports.

Inputs: reports/PERF_TODAY_RAW_STATS.json, PERF_TODAY_TRADES.json,
        PERF_TODAY_SIGNALS.json, PERF_TODAY_GATES.json, PERF_TODAY_REGIME.json
Output: reports/PERF_TODAY_SUMMARY.md

Sections: Executive Summary, Trade Quality, Signal & Gate Attribution,
Regime Fit, Operational Friction, Tuning Brief (Cursor), Model-Level Recommendations,
Dual Perspective (Cursor vs Model).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"


def _load(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _section_1_executive(raw: Dict) -> List[str]:
    stats = raw.get("stats") or {}
    date = raw.get("date") or "unknown"
    lines = [
        "# Performance Review — Today",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Date:** {date}",
        "",
        "## 1) Executive Summary",
        "",
        f"- **Net PnL (USD):** {stats.get('net_pnl_usd', 0)}",
        f"- **Win rate (%):** {stats.get('win_rate_pct', 0)}",
        f"- **Max drawdown (USD):** {stats.get('max_drawdown_usd', 0)}",
        f"- **Trade count:** {stats.get('total_trades', 0)}",
        "",
    ]
    verdict = "No trades today; metrics N/A."
    if stats.get("total_trades", 0) > 0:
        pnl = stats.get("net_pnl_usd", 0)
        wr = stats.get("win_rate_pct", 0)
        verdict = f"Today was {'profitable' if pnl > 0 else 'flat/negative'} with {stats.get('total_trades')} trades and {wr}% win rate; main drivers: trade mix and gate/signal behavior."
    lines.append(f"**One-sentence verdict:** {verdict}")
    lines.append("")
    return lines


def _section_2_trade_quality(trades_data: Dict, raw: Dict) -> List[str]:
    trades = trades_data.get("trades") or []
    stats = raw.get("stats") or {}
    lines = [
        "## 2) Trade Quality",
        "",
        f"- **R-multiples / win quality:** Avg win USD = {stats.get('avg_win_usd', 0)}; avg loss USD = {stats.get('avg_loss_usd', 0)}.",
        "",
    ]
    if not trades:
        lines.append("No closed trades; distribution N/A.")
        lines.append("")
        return lines
    pnls = [(t.get("pnl_usd") or 0) for t in trades if t.get("pnl_usd") is not None]
    if pnls:
        sorted_t = sorted([t for t in trades if t.get("pnl_usd") is not None], key=lambda x: float(x.get("pnl_usd", 0)))
        best_5 = sorted_t[-5:][::-1]
        worst_5 = sorted_t[:5]
        lines.append("**Best 5 trades (by PnL):**")
        for t in best_5:
            lines.append(f"- {t.get('symbol')} PnL={t.get('pnl_usd')} USD — {t.get('close_reason') or '—'}")
        lines.append("")
        lines.append("**Worst 5 trades:**")
        for t in worst_5:
            lines.append(f"- {t.get('symbol')} PnL={t.get('pnl_usd')} USD — {t.get('close_reason') or '—'}")
    lines.append("")
    return lines


def _section_3_signal_gate(signals: Dict, gates: Dict) -> List[str]:
    lines = [
        "## 3) Signal & Gate Attribution",
        "",
        f"- **Trade intents:** {signals.get('trade_intent_count', 0)} total; entered: {signals.get('entered', 0)}, blocked: {signals.get('blocked', 0)}.",
        f"- **Blocked reasons:** {signals.get('blocked_reasons', {})}",
        "",
        "**Per-signal family (from intelligence_trace):**",
        "",
    ]
    by_sig = signals.get("by_signal_family") or {}
    if by_sig:
        for name, v in sorted(by_sig.items(), key=lambda x: -((x[1].get("pnl_sum") or 0))):
            lines.append(f"- **{name}:** count={v.get('count')}, entered={v.get('entered')}, blocked={v.get('blocked')}, PnL sum≈{v.get('pnl_sum', 0):.2f}")
    else:
        lines.append("(No signal-family breakdown in intelligence_trace today.)")
    lines.append("")
    lines.append("**Gates:**")
    lines.append(f"- Displacement: evaluated={gates.get('displacement_evaluated', 0)}, allowed={gates.get('displacement_allowed', 0)}, blocked={gates.get('displacement_blocked', 0)}")
    lines.append(f"- Directional gate: events={gates.get('directional_gate_events', 0)}, blocked≈{gates.get('directional_gate_blocked_approx', 0)}")
    lines.append("")
    return lines


def _section_4_regime(regime: Dict) -> List[str]:
    lines = [
        "## 4) Regime Fit",
        "",
        f"- **Source:** {regime.get('source', 'none')}",
        f"- **Dominant regime:** {regime.get('dominant_regime', 'UNKNOWN')}",
        f"- **Trend bucket:** {regime.get('trend_bucket', 'unknown')}; **Volatility bucket:** {regime.get('volatility_bucket', '')}",
        "",
        "Whether the strategy is aligned or fighting the tape depends on today's regime vs. system comfort zone (e.g. trend vs chop). Use regime_timeline and state/regime_detector_state for full context.",
        "",
    ]
    return lines


def _section_5_operational(raw: Dict) -> List[str]:
    meta = raw.get("meta") or {}
    lines = [
        "## 5) Operational Friction",
        "",
        f"- **Self-heal events today:** {meta.get('self_heal_count', 0)}",
        "",
    ]
    events = meta.get("self_heal_events") or []
    if events:
        for e in events[:10]:
            lines.append(f"  - {e.get('event_type')} @ {e.get('ts')}")
    lines.append(f"- **Telemetry computed keys:** {meta.get('telemetry_computed_keys', [])}")
    lines.append("")
    lines.append("Any WARNs or telemetry gaps that coincided with performance swings should be reviewed in logs.")
    lines.append("")
    return lines


def _section_6_tuning_brief(raw: Dict, signals: Dict, gates: Dict) -> List[str]:
    lines = [
        "## 6) Tuning Brief (Cursor's Implementation-Aware Recommendations)",
        "",
        "Evidence-backed recommendations; **not applied** in this pass.",
        "",
    ]
    stats = raw.get("stats") or {}
    n_trades = stats.get("total_trades", 0)
    pnl = stats.get("net_pnl_usd", 0)
    blocked = signals.get("blocked", 0)
    total_ti = signals.get("trade_intent_count", 0)
    disp_blocked = gates.get("displacement_blocked", 0)
    # Generate a few concrete recommendations based on data
    recs: List[Dict] = []
    if total_ti > 0 and blocked / total_ti > 0.7:
        recs.append({
            "tag": "PARAM_TUNING",
            "observation": f"Block rate {100*blocked/total_ti:.0f}% ({blocked}/{total_ti} trade_intent blocked).",
            "hypothesis": "Over-blocking may reduce opportunity; gates or score thresholds may be too strict.",
            "proposed": "Add diagnostic: log blocked_reason distribution by hour; consider relaxing displacement or directional_gate thresholds in config if regime supports it.",
        })
    if disp_blocked > 0:
        recs.append({
            "tag": "SAFE_DIAGNOSTIC",
            "observation": f"Displacement blocked {disp_blocked} evaluation(s) today.",
            "hypothesis": "Displacement is protecting capital but may also block good rotations.",
            "proposed": "Emit telemetry when displacement blocks (symbol, score_delta, PnL of incumbent) for later analysis.",
        })
    if n_trades == 0 and total_ti > 0:
        recs.append({
            "tag": "STRUCTURAL",
            "observation": "Zero realized trades despite trade_intent events.",
            "hypothesis": "Execution path or gates may be preventing all entries.",
            "proposed": "Trace execution from trade_intent to order: confirm orders.jsonl and attribution.jsonl are written; check for safe mode or audit flags.",
        })
    if n_trades > 0 and pnl < 0:
        recs.append({
            "tag": "PARAM_TUNING",
            "observation": f"Net PnL negative ({pnl} USD) with {n_trades} trades.",
            "hypothesis": "Exits or position sizing may be suboptimal; or entries are poor quality.",
            "proposed": "Review exit_intent reasons and trailing-stop/time-exit settings; consider tightening entry score threshold (MIN_EXEC_SCORE) or reducing size.",
        })
    recs.append({
        "tag": "SAFE_DIAGNOSTIC",
        "observation": "Signal-family PnL attribution is best-effort from intelligence_trace.",
        "hypothesis": "Better attribution improves tuning.",
        "proposed": "Add per-trade signal_family snapshot to attribution or exit_attribution for robust signal performance tables.",
    })
    for r in recs:
        lines.append(f"- **[{r['tag']}]**")
        lines.append(f"  - **Observation:** {r['observation']}")
        lines.append(f"  - **Hypothesis:** {r['hypothesis']}")
        lines.append(f"  - **Proposed change:** {r['proposed']}")
        lines.append("")
    return lines


def _section_7_model_level(raw: Dict, signals: Dict, regime: Dict) -> List[str]:
    lines = [
        "## 7) Model-Level Recommendations (High-Level Strategy Perspective)",
        "",
        "Summary for Mark (no code):",
        "",
    ]
    stats = raw.get("stats") or {}
    n = stats.get("total_trades", 0)
    pnl = stats.get("net_pnl_usd", 0)
    reg = regime.get("dominant_regime", "UNKNOWN")
    axes = [
        "**Regime alignment:** Ensure strategy comfort zone (e.g. trend-following vs mean-reversion) matches today's regime; consider regime filter or reduced size in hostile regimes.",
        "**Entry quality:** If losses are concentrated in a few symbols or themes, tighten universe or signal weights for those; improve entry timing (e.g. pullback vs breakout).",
        "**Exit quality:** If winners are cut early or losers run, review trailing-stop, time-exit, and thesis-break logic.",
        "**Over- vs under-blocking:** If many blocked intents would have been winners, consider relaxing gates; if losses come from bad entries that passed, consider tightening.",
        "**Position sizing / capital at risk:** Align exposure with volatility and regime; avoid over-concentration in single names.",
    ]
    for a in axes:
        lines.append(f"- {a}")
    lines.append("")
    if n == 0:
        lines.append("**Structural note:** Zero realized trades suggest the problem may still be execution/data (orders not filled, attribution not written) or regime (all intents blocked). Differentiate before strategy changes.")
    elif pnl < 0:
        lines.append("**Structural note:** Negative PnL with realized trades suggests the issue is strategy (entry/exit/sizing) or regime mismatch, not merely data completeness.")
    lines.append("")
    return lines


def _section_8_dual_perspective(raw: Dict, signals: Dict, gates: Dict, regime: Dict) -> List[str]:
    stats = raw.get("stats") or {}
    lines = [
        "## 8) Dual Perspective: Cursor vs Model",
        "",
        "### 8.1 Cursor (Implementation-Aware)",
        "",
        "Concrete, code/config-adjacent recommendations (tagged):",
        "",
    ]
    cursor_bullets = [
        "- **SAFE_DIAGNOSTIC:** Add telemetry when displacement blocks (symbol, score_delta) for blocked-trade analysis.",
        "- **SAFE_DIAGNOSTIC:** Add per-trade signal_family snapshot to attribution for robust signal performance tables.",
        "- **PARAM_TUNING:** If block rate is high, log blocked_reason by hour and consider relaxing displacement/gate thresholds in config.",
        "- **PARAM_TUNING:** If PnL is negative with many trades, review MIN_EXEC_SCORE and trailing-stop/time-exit params.",
        "- **STRUCTURAL:** If zero trades despite intents, trace execution path (trade_intent → orders.jsonl → attribution) and check safe mode / audit flags.",
    ]
    for b in cursor_bullets:
        lines.append(b)
    lines.append("")
    lines.append("### 8.2 Model (Strategy-Level)",
    )
    lines.append("")
    if stats.get("total_trades", 0) == 0:
        lines.append("If we assume the data is now correct and complete, zero trades imply either **over-blocking** (gates/score too strict) or **no valid signals** (universe/regime). Differentiate with blocked_reason counts and shadow variant would_enter rates. Structural changes: consider regime filter (trade only in favorable regimes), relax gates in backtest to compare would-be PnL, or broaden universe if signals are sparse.")
    else:
        lines.append("If we assume the data is correct and complete, losses are likely due to **entry quality**, **exit timing**, or **regime mismatch**. Structural changes that would most likely improve expectancy: (1) align timeframes with regime (e.g. shorter in chop); (2) tighten entry filter or reduce size in high-vol regimes; (3) improve exit logic (trailing vs thesis-break); (4) add regime filter to reduce trading in hostile regimes; (5) diversify symbols/themes to reduce single-name risk.")
    lines.append("")
    return lines


def main() -> int:
    raw = _load(REPORTS / "PERF_TODAY_RAW_STATS.json")
    trades_data = _load(REPORTS / "PERF_TODAY_TRADES.json")
    signals = _load(REPORTS / "PERF_TODAY_SIGNALS.json")
    gates = _load(REPORTS / "PERF_TODAY_GATES.json")
    regime = _load(REPORTS / "PERF_TODAY_REGIME.json")

    out: List[str] = []
    out.extend(_section_1_executive(raw))
    out.extend(_section_2_trade_quality(trades_data, raw))
    out.extend(_section_3_signal_gate(signals, gates))
    out.extend(_section_4_regime(regime))
    out.extend(_section_5_operational(raw))
    out.extend(_section_6_tuning_brief(raw, signals, gates))
    out.extend(_section_7_model_level(raw, signals, regime))
    out.extend(_section_8_dual_perspective(raw, signals, gates, regime))

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "PERF_TODAY_SUMMARY.md").write_text("\n".join(out), encoding="utf-8")
    print(f"[OK] Wrote {REPORTS / 'PERF_TODAY_SUMMARY.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
