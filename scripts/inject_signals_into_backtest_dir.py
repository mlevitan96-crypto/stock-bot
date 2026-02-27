#!/usr/bin/env python3
"""
Inject replay-time signals into an existing backtest dir (two-phase backtest).
Reads backtest_trades.jsonl and backtest_blocks.jsonl, computes signals at each
(symbol, timestamp) with a shared bar cache, merges signals in, overwrites files,
then runs Signal Edge Analysis. Use after run_30d_backtest_droplet.py --no-inject
so the backtest finishes fast and injection runs in a separate step (no SSH timeout).
Usage: python scripts/inject_signals_into_backtest_dir.py --backtest-dir backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from scripts.replay_signal_injection import (
        compute_signals_for_timestamp,
        make_cached_load_bars,
    )
except Exception:
    compute_signals_for_timestamp = None
    make_cached_load_bars = None


def _iter_jsonl(path: Path):
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


def inject_trades(backtest_dir: Path, cached_load) -> int:
    trades_path = backtest_dir / "backtest_trades.jsonl"
    if not trades_path.exists():
        print(f"[inject] No {trades_path}; skip trades.")
        return 0
    rows = list(_iter_jsonl(trades_path))
    if not rows:
        return 0
    n = 0
    with trades_path.open("w", encoding="utf-8") as f:
        for rec in rows:
            sym = rec.get("symbol")
            ts = rec.get("timestamp") or rec.get("ts")
            if compute_signals_for_timestamp and cached_load and sym and ts:
                try:
                    signals = compute_signals_for_timestamp(sym, ts, load_bars_fn=cached_load)
                    ctx = rec.get("context")
                    if isinstance(ctx, dict):
                        for k, v in signals.items():
                            if v is not None or k in ("regime_label", "sector_momentum"):
                                ctx[k] = v
                    for k, v in signals.items():
                        if v is not None or k in ("regime_label", "sector_momentum"):
                            rec[k] = v
                    n += 1
                except Exception:
                    pass
            f.write(json.dumps(rec, default=str) + "\n")
    return n


def inject_blocks(backtest_dir: Path, cached_load) -> int:
    blocks_path = backtest_dir / "backtest_blocks.jsonl"
    if not blocks_path.exists():
        print(f"[inject] No {blocks_path}; skip blocks.")
        return 0
    rows = list(_iter_jsonl(blocks_path))
    if not rows:
        return 0
    n = 0
    with blocks_path.open("w", encoding="utf-8") as f:
        for rec in rows:
            sym = rec.get("symbol")
            ts = rec.get("timestamp") or rec.get("ts")
            if compute_signals_for_timestamp and cached_load and sym and ts:
                try:
                    signals = compute_signals_for_timestamp(sym, ts, load_bars_fn=cached_load)
                    for k, v in signals.items():
                        if v is not None or k in ("regime_label", "sector_momentum"):
                            rec[k] = v
                    n += 1
                except Exception:
                    pass
            f.write(json.dumps(rec, default=str) + "\n")
    return n


def run_signal_edge_analysis(backtest_dir: Path) -> bool:
    try:
        from src.analysis.signal_edge_analysis import run_analysis, render_markdown_report
    except ImportError as e:
        print(f"[inject] Signal edge analysis import failed: {e}", file=sys.stderr)
        return False
    try:
        data = run_analysis(backtest_dir)
        report = render_markdown_report(data, backtest_dir)
        out_path = backtest_dir / "SIGNAL_EDGE_ANALYSIS_REPORT.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"[inject] Wrote {out_path}")
        return True
    except Exception as e:
        print(f"[inject] Signal edge analysis failed: {e}", file=sys.stderr)
        return False


def main() -> int:
    p = argparse.ArgumentParser(description="Inject signals into backtest dir and run edge analysis")
    p.add_argument("--backtest-dir", "-d", required=True, help="Path to backtest directory")
    p.add_argument("--no-analysis", action="store_true", help="Skip running signal edge analysis after inject")
    args = p.parse_args()
    backtest_dir = Path(args.backtest_dir)
    if not backtest_dir.is_absolute():
        backtest_dir = REPO_ROOT / backtest_dir
    if not backtest_dir.is_dir():
        print(f"Error: not a directory: {backtest_dir}", file=sys.stderr)
        return 1
    if compute_signals_for_timestamp is None or make_cached_load_bars is None:
        print("Error: replay_signal_injection not available.", file=sys.stderr)
        return 1

    cache = {}
    cached_load = make_cached_load_bars(cache, None)
    print(f"[inject] Injecting signals into {backtest_dir} (shared bar cache)...")
    nt = inject_trades(backtest_dir, cached_load)
    nb = inject_blocks(backtest_dir, cached_load)
    print(f"[inject] Injected: {nt} trades, {nb} blocks; cache size {len(cache)} (symbol,date) keys.")

    if not getattr(args, "no_analysis", False):
        print("[inject] Running signal edge analysis...")
        run_signal_edge_analysis(backtest_dir)
    print("[inject] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
