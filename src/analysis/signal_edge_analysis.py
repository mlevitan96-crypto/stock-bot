"""
Signal Edge Analysis — measure per-signal, per-regime, per-bucket edge.
Reads backtest trades/exits/blocks; buckets by signal values; computes
win rate, average P&L, expectancy. NO trading logic changes.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

# Signal keys we attempt to extract from context (may be missing)
SIGNAL_KEYS = (
    "trend_signal",
    "momentum_signal",
    "volatility_signal",
    "regime_signal",
    "sector_signal",
    "reversal_signal",
    "breakout_signal",
    "mean_reversion_signal",
)
REGIME_LABELS = ("BULL", "BEAR", "RANGE", "MIXED", "UNKNOWN", "")


def _iter_jsonl(path: Path):
    """Yield JSON objects from a JSONL file."""
    if not path.exists():
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


def _bucket_signal(val: float, n_buckets: int = 3) -> str:
    """Bucket signal into negative / near-zero / positive (or more)."""
    if val is None:
        return "missing"
    try:
        v = float(val)
    except (TypeError, ValueError):
        return "missing"
    if n_buckets == 3:
        if v < -0.15:
            return "negative"
        if v > 0.15:
            return "positive"
        return "near_zero"
    # Quintiles-style: divide [-1,1] into n_buckets
    if v <= -1.0:
        return f"q1"
    if v >= 1.0:
        return f"q{n_buckets}"
    step = 2.0 / n_buckets
    for i in range(n_buckets):
        lo = -1.0 + i * step
        hi = -1.0 + (i + 1) * step
        if lo <= v < hi:
            return f"q{i + 1}"
    return f"q{n_buckets}"


def _regime_from_context(ctx: dict | None) -> str:
    """Extract regime label from context."""
    if not ctx or not isinstance(ctx, dict):
        return "UNKNOWN"
    r = ctx.get("market_regime") or ctx.get("regime") or ""
    if isinstance(r, str) and r.strip():
        return r.strip().upper()
    return "UNKNOWN"


def _regime_signal_from_label(label: str) -> float:
    """Map regime label to numeric signal (BULL=1, BEAR=-1, else 0)."""
    r = (label or "").strip().upper()
    if r == "BULL":
        return 1.0
    if r == "BEAR":
        return -1.0
    return 0.0


def _extract_signals_from_trade(trade: dict) -> dict[str, float | None]:
    """Extract signal values from trade context. Missing keys → None."""
    ctx = trade.get("context")
    if not isinstance(ctx, dict):
        ctx = {}
    out: dict[str, float | None] = {}
    for k in SIGNAL_KEYS:
        v = ctx.get(k)
        if v is not None and isinstance(v, (int, float)):
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                out[k] = None
        else:
            out[k] = None
    # Derive regime_signal from regime label if not present
    if out.get("regime_signal") is None:
        regime_label = _regime_from_context(ctx)
        out["regime_signal"] = _regime_signal_from_label(regime_label)
    # Use entry_score as composite proxy if no raw signals
    entry = trade.get("entry_score")
    if entry is not None and isinstance(entry, (int, float)):
        out["entry_score"] = float(entry)
    return out


def load_trades(backtest_dir: Path) -> list[dict]:
    """Load trades from backtest_trades.jsonl."""
    path = backtest_dir / "backtest_trades.jsonl"
    return list(_iter_jsonl(path))


def load_exits(backtest_dir: Path) -> list[dict]:
    """Load exits from backtest_exits.jsonl."""
    path = backtest_dir / "backtest_exits.jsonl"
    return list(_iter_jsonl(path))


def load_blocks(backtest_dir: Path) -> list[dict]:
    """Load blocks from backtest_blocks.jsonl."""
    path = backtest_dir / "backtest_blocks.jsonl"
    return list(_iter_jsonl(path))


def bucket_metrics(trades: list[dict], signal_key: str, get_value) -> dict[str, dict]:
    """
    Bucket trades by signal value; compute count, win rate, avg PnL, expectancy per bucket.
    get_value(trade) -> float | None.
    """
    buckets: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        val = get_value(t)
        if val is None:
            bucket = "missing"
        else:
            bucket = _bucket_signal(float(val))
        buckets[bucket].append(t)

    result: dict[str, dict] = {}
    for bucket, subset in buckets.items():
        pnls = [float(t.get("pnl_usd") or 0) for t in subset]
        wins = sum(1 for p in pnls if p > 0)
        losses = sum(1 for p in pnls if p < 0)
        n = len(subset)
        total_pnl = sum(pnls)
        avg_pnl = total_pnl / n if n else 0.0
        win_rate = (wins / n * 100.0) if n else 0.0
        avg_loss = sum(p for p in pnls if p < 0) / losses if losses else 0.0
        expectancy = (avg_pnl / abs(avg_loss)) if avg_loss and avg_loss != 0 else (float("nan") if n else 0.0)
        result[bucket] = {
            "count": n,
            "win_rate_pct": round(win_rate, 2),
            "avg_pnl_usd": round(avg_pnl, 2),
            "total_pnl_usd": round(total_pnl, 2),
            "expectancy": round(expectancy, 4) if expectancy == expectancy else None,
        }
    return result


def analyze_signal_global(trades: list[dict], signal_key: str) -> dict[str, dict]:
    """Global bucket metrics for a signal (or entry_score as proxy)."""
    def get_val(t):
        if signal_key == "entry_score":
            return t.get("entry_score")
        sigs = _extract_signals_from_trade(t)
        return sigs.get(signal_key)
    return bucket_metrics(trades, signal_key, get_val)


def analyze_signal_per_regime(trades: list[dict], signal_key: str) -> dict[str, dict[str, dict]]:
    """Per-regime bucket metrics for a signal."""
    by_regime: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        ctx = t.get("context") or {}
        regime = _regime_from_context(ctx)
        by_regime[regime].append(t)

    result: dict[str, dict[str, dict]] = {}
    for regime, subset in by_regime.items():
        def get_val(t):
            if signal_key == "entry_score":
                return t.get("entry_score")
            sigs = _extract_signals_from_trade(t)
            return sigs.get(signal_key)
        result[regime] = bucket_metrics(subset, signal_key, get_val)
    return result


def run_analysis(backtest_dir: Path) -> dict[str, Any]:
    """
    Run full signal edge analysis. Returns a dict suitable for report generation.
    """
    trades = load_trades(backtest_dir)
    exits = load_exits(backtest_dir)
    blocks = load_blocks(backtest_dir)

    # Check which signals exist in context
    sample_signals = {}
    if trades:
        sample_signals = _extract_signals_from_trade(trades[0])
    available_signals = [k for k in SIGNAL_KEYS if sample_signals.get(k) is not None]
    if "entry_score" not in sample_signals and any(t.get("entry_score") is not None for t in trades[:10]):
        available_signals.append("entry_score")
    # Always include entry_score and regime_signal (we can derive regime)
    signals_to_analyze = list(SIGNAL_KEYS) + ["entry_score"]
    signals_to_analyze = list(dict.fromkeys(signals_to_analyze))

    global_results: dict[str, dict[str, dict]] = {}
    regime_results: dict[str, dict[str, dict[str, dict]]] = {}

    for sig in signals_to_analyze:
        global_results[sig] = analyze_signal_global(trades, sig)
        regime_results[sig] = analyze_signal_per_regime(trades, sig)

    # Regime-only summary (no signal bucketing)
    regime_only: dict[str, dict] = {}
    by_regime: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        regime = _regime_from_context(t.get("context"))
        by_regime[regime].append(t)
    for regime, subset in by_regime.items():
        pnls = [float(t.get("pnl_usd") or 0) for t in subset]
        n = len(subset)
        wins = sum(1 for p in pnls if p > 0)
        total = sum(pnls)
        regime_only[regime] = {
            "count": n,
            "win_rate_pct": round(wins / n * 100.0, 2) if n else 0.0,
            "avg_pnl_usd": round(total / n, 2) if n else 0.0,
            "total_pnl_usd": round(total, 2),
        }

    return {
        "backtest_dir": str(backtest_dir),
        "trades_count": len(trades),
        "exits_count": len(exits),
        "blocks_count": len(blocks),
        "available_signals": available_signals,
        "signals_analyzed": signals_to_analyze,
        "global": global_results,
        "per_regime": regime_results,
        "regime_only": regime_only,
    }


def render_markdown_report(data: dict[str, Any], backtest_dir: Path) -> str:
    """Render analysis data as Markdown report."""
    lines = [
        "# Signal Edge Analysis Report",
        "",
        f"**Backtest dir:** `{data.get('backtest_dir', '')}`",
        f"**Trades:** {data.get('trades_count', 0)} | **Exits:** {data.get('exits_count', 0)} | **Blocks:** {data.get('blocks_count', 0)}",
        "",
        "---",
        "",
        "## 1. Data availability",
        "",
    ]
    avail = data.get("available_signals") or []
    if avail:
        lines.append("Signals found in trade context: " + ", ".join(avail) + ".")
    else:
        lines.append("No raw signal fields (trend_signal, momentum_signal, etc.) found in trade context.")
        lines.append("Using **entry_score** and **regime_signal** (derived from market_regime) for analysis.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Regime-level summary (no signal bucketing)")
    lines.append("")
    lines.append("| Regime | Trades | Win rate (%) | Avg P&L ($) | Total P&L ($) |")
    lines.append("|--------|--------|--------------|-------------|---------------|")
    for regime, m in (data.get("regime_only") or {}).items():
        rn = regime or "UNKNOWN"
        lines.append(f"| {rn} | {m.get('count', 0)} | {m.get('win_rate_pct', 0)} | {m.get('avg_pnl_usd', 0)} | {m.get('total_pnl_usd', 0)} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Global signal buckets (all regimes)")
    lines.append("")

    for sig in data.get("signals_analyzed") or []:
        g = (data.get("global") or {}).get(sig) or {}
        if not g:
            continue
        lines.append(f"### {sig}")
        lines.append("")
        lines.append("| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |")
        lines.append("|--------|--------|--------------|-------------|------------|")
        for bucket in ("negative", "near_zero", "positive", "missing"):
            if bucket not in g:
                continue
            m = g[bucket]
            ex = m.get("expectancy")
            ex_str = str(ex) if ex is not None else "—"
            lines.append(f"| {bucket} | {m.get('count', 0)} | {m.get('win_rate_pct', 0)} | {m.get('avg_pnl_usd', 0)} | {ex_str} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 4. Per-regime signal buckets (where applicable)")
    lines.append("")

    for sig in data.get("signals_analyzed") or []:
        pr = (data.get("per_regime") or {}).get(sig) or {}
        if not pr:
            continue
        lines.append(f"### {sig} (by regime)")
        lines.append("")
        for regime, buckets in sorted(pr.items()):
            rn = regime or "UNKNOWN"
            lines.append(f"**{rn}**")
            lines.append("")
            lines.append("| Bucket | Trades | Win rate (%) | Avg P&L ($) |")
            lines.append("|--------|--------|--------------|-------------|")
            for bucket in ("negative", "near_zero", "positive", "missing"):
                if bucket not in buckets:
                    continue
                m = buckets[bucket]
                lines.append(f"| {bucket} | {m.get('count', 0)} | {m.get('win_rate_pct', 0)} | {m.get('avg_pnl_usd', 0)} |")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 5. Summary for weight tuning")
    lines.append("")

    # Heuristic: positive edge = positive bucket has higher win rate or avg PnL than negative
    summary_lines = []
    for sig in data.get("signals_analyzed") or []:
        g = (data.get("global") or {}).get(sig) or {}
        pos = g.get("positive", {})
        neg = g.get("negative", {})
        if not pos or not neg:
            summary_lines.append(f"- **{sig}:** insufficient bucket data")
            continue
        pos_wr = pos.get("win_rate_pct") or 0
        neg_wr = neg.get("win_rate_pct") or 0
        pos_avg = pos.get("avg_pnl_usd") or 0
        neg_avg = neg.get("avg_pnl_usd") or 0
        if pos_wr > neg_wr and pos_avg > neg_avg:
            summary_lines.append(f"- **{sig}:** positive edge (positive bucket outperforms negative)")
        elif pos_wr < neg_wr and pos_avg < neg_avg:
            summary_lines.append(f"- **{sig}:** negative edge (positive bucket underperforms)")
        else:
            summary_lines.append(f"- **{sig}:** neutral/noisy (mixed or flat)")

    lines.extend(summary_lines)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 6. Limitations")
    lines.append("")
    lines.append("- This analysis is **descriptive**, not causal. Correlation does not imply causation.")
    lines.append("- Raw signals (trend_signal, momentum_signal, etc.) may not be logged in attribution context.")
    lines.append("- When missing, we use entry_score and regime_signal (derived from market_regime).")
    lines.append("- To enable full per-signal edge analysis, add raw signal fields to attribution context at entry.")
    lines.append("")
    return "\n".join(lines)
