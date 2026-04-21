#!/usr/bin/env python3
"""
Operator ledger: lifetime canonical unique exits vs strict / apex completeness cohorts, cohort PnL, tier_sizing events.

- Lifetime: ``compute_canonical_trade_count(..., floor_epoch=None)`` (era_cut only; no strict epoch floor).
- Strict (code floor): ``evaluate_completeness(..., open_ts_epoch=STRICT_EPOCH_START)``.
- Apex (integrity arm): ``evaluate_completeness(..., open_ts_epoch=<arm UTC>)`` — same semantics as
  ``strict_completeness_snapshot.py`` when passed ``--open-ts-epoch`` (that flag is not on the CLI by default;
  use this script or call ``evaluate_completeness`` from Python).

Cohort PnL for Apex: exit_attribution rows whose ``trade_id`` parses to position **open** time >= arm
(deduped by ``trade_id``, last row wins), with ``learning_excluded_for_exit_record`` skipped.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("/root/stock-bot"))
    ap.add_argument(
        "--apex-arm-iso",
        default="2026-04-21T13:31:59+00:00",
        help="UTC integrity arm instant for Apex open_ts_epoch and open-time cohort PnL.",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root))

    from src.governance.canonical_trade_count import (
        _iter_exit_attribution,
        compute_canonical_trade_count,
    )
    from telemetry.alpaca_strict_completeness_gate import (
        STRICT_EPOCH_START,
        _parse_iso_ts,
        evaluate_completeness,
    )
    from utils.era_cut import learning_excluded_for_exit_record

    arm_ts = datetime.fromisoformat(args.apex_arm_iso.replace("Z", "+00:00")).timestamp()

    life = compute_canonical_trade_count(root, floor_epoch=None)
    snap_strict = evaluate_completeness(
        root, open_ts_epoch=float(STRICT_EPOCH_START), audit=True, collect_strict_cohort_trade_ids=True
    )
    snap_apex = evaluate_completeness(
        root, open_ts_epoch=float(arm_ts), audit=True, collect_strict_cohort_trade_ids=True
    )

    TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")

    def _open_epoch_from_tid(tid: str) -> Optional[float]:
        m = TID_RE.match(str(tid).strip())
        if not m:
            return None
        return _parse_iso_ts(m.group(2))

    def _pnl_from_exit(rec: dict) -> float:
        for k in ("realized_pnl_usd", "pnl_usd"):
            v = rec.get(k)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
        snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
        v = snap.get("pnl")
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
        v = rec.get("pnl")
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
        return 0.0

    def _bps_from_exit(rec: dict) -> Optional[float]:
        for k in ("net_pnl_bps", "pnl_bps"):
            if rec.get(k) is not None:
                try:
                    return float(rec[k])
                except (TypeError, ValueError):
                    pass
        snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
        for k in ("net_pnl_bps", "pnl_bps"):
            if snap.get(k) is not None:
                try:
                    return float(snap[k])
                except (TypeError, ValueError):
                    pass
        return None

    # Apex open-time cohort from exit_attribution (dedupe trade_id, last wins)
    apex_rows: Dict[str, dict] = {}
    for rec in _iter_exit_attribution(root / "logs" / "exit_attribution.jsonl"):
        if learning_excluded_for_exit_record(rec):
            continue
        tid = rec.get("trade_id")
        if not tid:
            continue
        oep = _open_epoch_from_tid(str(tid))
        if oep is None or oep < arm_ts:
            continue
        apex_rows[str(tid)] = rec

    pnl_sum = 0.0
    wins = losses = flats = 0
    bps_vals: List[float] = []
    for rec in apex_rows.values():
        pv = _pnl_from_exit(rec)
        pnl_sum += pv
        if pv > 1e-9:
            wins += 1
        elif pv < -1e-9:
            losses += 1
        else:
            flats += 1
        b = _bps_from_exit(rec)
        if b is not None:
            bps_vals.append(b)

    bps_vals.sort()
    mid = bps_vals[len(bps_vals) // 2] if bps_vals else None
    mean_bps = sum(bps_vals) / len(bps_vals) if bps_vals else None

    tier_rows = 0
    tier_by_sym: Dict[str, int] = defaultdict(int)
    p = root / "logs" / "system_events.jsonl"
    if p.is_file():
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if "tier_sizing_applied" not in line:
                    continue
                try:
                    o = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                ts = None
                for kk in ("ts", "timestamp", "time"):
                    if o.get(kk):
                        ts = _parse_iso_ts(o.get(kk))
                        break
                if ts is not None and ts < arm_ts:
                    continue
                tier_rows += 1
                sym = str(o.get("symbol") or "").upper()
                pl = o.get("payload")
                if isinstance(pl, dict):
                    sym = str(pl.get("symbol") or sym).upper()
                tier_by_sym[sym or "?"] += 1

    # Tier-2 subset of apex cohort: symbols that had tier_sizing_applied since arm (heuristic overlap)
    apex_syms: Set[str] = {str(r.get("symbol") or "").upper() for r in apex_rows.values()}
    tier_syms_hit = sorted([s for s in tier_by_sym if s in apex_syms])

    out: Dict[str, Any] = {
        "lifetime_canonical": {
            "unique_trade_keys_post_era_cut": life["total_trades_post_era"],
            "realized_pnl_sum_first_row_per_key_usd": life["realized_pnl_sum_usd"],
            "era_cut_excluded_rows": life["era_cut_excluded_rows"],
            "floor_epoch_utc": life.get("floor_epoch_utc"),
            "note": "No strict epoch floor; era_cut from config still excludes pre-era learning rows.",
        },
        "strict_STRICT_EPOCH_START": {
            "epoch_utc": datetime.fromtimestamp(float(STRICT_EPOCH_START), tz=timezone.utc).isoformat(),
            "evaluate_completeness": {
                k: snap_strict.get(k)
                for k in (
                    "LEARNING_STATUS",
                    "trades_seen",
                    "trades_complete",
                    "trades_incomplete",
                    "learning_fail_closed_reason",
                )
            },
            "strict_cohort_trade_ids_n": len(snap_strict.get("strict_cohort_trade_ids") or []),
        },
        "apex_integrity_arm": {
            "arm_utc": args.apex_arm_iso,
            "arm_epoch": arm_ts,
            "evaluate_completeness": {
                k: snap_apex.get(k)
                for k in (
                    "LEARNING_STATUS",
                    "trades_seen",
                    "trades_complete",
                    "trades_incomplete",
                    "learning_fail_closed_reason",
                )
            },
            "strict_cohort_trade_ids_n": len(snap_apex.get("strict_cohort_trade_ids") or []),
            "apex_open_time_cohort_exit_attribution": {
                "unique_trade_ids_open_on_or_after_arm": len(apex_rows),
                "sum_pnl_usd": round(pnl_sum, 4),
                "wins": wins,
                "losses": losses,
                "flat": flats,
                "median_net_pnl_bps": mid,
                "mean_net_pnl_bps": round(mean_bps, 6) if mean_bps is not None else None,
                "bps_populated_n": len(bps_vals),
            },
        },
        "tier_sizing_system_events_since_arm": {
            "tier_sizing_applied_rows": tier_rows,
            "symbols_top_15": dict(sorted(tier_by_sym.items(), key=lambda x: -x[1])[:15]),
            "apex_cohort_symbols_also_in_tier_events": tier_syms_hit[:40],
        },
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
