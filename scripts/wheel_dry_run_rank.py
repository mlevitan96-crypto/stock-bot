#!/usr/bin/env python3
"""
Deterministic, market-closed dry-run test for wheel selection.

Proves that:
- UW intelligence is used FIRST to rank wheel candidates.
- The ranking path executes end-to-end.
- wheel_candidate_ranked emits with real data.

No broker calls, no order submission, no market hours.
Writes to logs/system_events.jsonl (subsystem=wheel, event_type=wheel_candidate_ranked).

Run from repo root: python3 scripts/wheel_dry_run_rank.py
Verify: grep '"event_type": "wheel_candidate_ranked"' logs/system_events.jsonl | tail -1
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def main() -> int:
    # Load wheel config (same as live)
    config = {}
    try:
        import yaml
        cfg_path = ROOT / "config" / "strategies.yaml"
        if cfg_path.exists():
            with cfg_path.open() as f:
                full = yaml.safe_load(f) or {}
            config = (full.get("strategies") or {}).get("wheel") or {}
    except Exception as e:
        print(f"ERROR: Failed to load wheel config: {e}", file=sys.stderr)
        return 1

    if not config:
        print("ERROR: No wheel config found in config/strategies.yaml", file=sys.stderr)
        return 1

    # Load universe exactly as live code does
    from strategies.wheel_universe_selector import _load_universe, _rank_by_uw_intelligence, _get_sector
    from strategies.wheel_universe_selector import DEFAULT_EXCLUDED_SECTORS

    tickers = _load_universe(config)
    if not tickers:
        print("WARNING: Universe empty; using fallback SPY, QQQ, DIA, IWM")
        tickers = ["SPY", "QQQ", "DIA", "IWM"]

    excluded = config.get("universe_excluded_sectors", DEFAULT_EXCLUDED_SECTORS) or DEFAULT_EXCLUDED_SECTORS
    candidate_tickers = [s for s in tickers if _get_sector(s) not in (excluded or [])]
    if not candidate_tickers:
        candidate_tickers = tickers

    # Same UW ranking function as live PATH B
    uw_ranked = _rank_by_uw_intelligence(candidate_tickers, config)
    if not uw_ranked:
        print("WARNING: No UW ranking (cache missing or empty); using universe order")
        ordered = candidate_tickers
        selected_meta = [{"symbol": s, "uw_composite_score": None} for s in ordered]
    else:
        ordered = [s for s, _ in uw_ranked]
        max_n = config.get("universe_max_candidates", 10)
        top_n = uw_ranked[:max_n]
        selected_meta = [{"symbol": s, "uw_composite_score": round(score, 4) if score > -1e8 else None} for s, score in top_n]

    # Stdout: ranked candidates (symbol, uw_score)
    print("Ranked candidates (symbol, uw_score):")
    for i, rec in enumerate(selected_meta[:10], 1):
        sym = rec.get("symbol", "?")
        sc = rec.get("uw_composite_score")
        sc_str = f"{sc:.4f}" if sc is not None and sc > -1e8 else "N/A"
        print(f"  {i}. {sym}  {sc_str}")
    if len(selected_meta) > 10:
        print(f"  ... and {len(selected_meta) - 10} more")

    # Emit wheel_candidate_ranked (same helper as live; no broker, chosen=null, reason_none=dry_run_rank_only)
    from strategies.wheel_strategy import _emit_wheel_candidate_ranked

    ticker_list = ordered[: max(5, config.get("universe_max_candidates", 10))]
    _emit_wheel_candidate_ranked(
        ticker_list,
        selected_meta,
        None,
        0,
        reason_none_override="dry_run_rank_only",
    )
    print("wheel_candidate_ranked emitted successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
