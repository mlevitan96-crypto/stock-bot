#!/usr/bin/env python3
"""
Backfill state/position_metadata.json for open Alpaca positions using last
composite_calculated row per symbol in logs/scoring_flow.jsonl.

Does not change strategy; repairs hollow metadata after reconciliation drift.

Usage:
  python3 scripts/repair/repair_position_metadata_from_logs.py --dry-run
  python3 scripts/repair/repair_position_metadata_from_logs.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")


def _last_scores_from_scoring_flow(path: Path, limit_lines: int = 800_000) -> Dict[str, Tuple[float, dict, str]]:
    """symbol -> (score, components, ts) from last occurrence in file tail."""
    out: Dict[str, Tuple[float, dict, str]] = {}
    if not path.exists():
        return out
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    chunk = lines[-limit_lines:] if len(lines) > limit_lines else lines
    for line in chunk:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("msg") != "composite_calculated":
            continue
        sym = str(rec.get("symbol", "")).upper()
        if not sym:
            continue
        try:
            score = float(rec.get("score", 0) or 0)
        except (TypeError, ValueError):
            continue
        comps = rec.get("components") if isinstance(rec.get("components"), dict) else {}
        ts = str(rec.get("ts", ""))
        out[sym] = (score, comps, ts)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not args.dry_run and not args.apply:
        print("Specify --dry-run or --apply", file=sys.stderr)
        return 2

    import alpaca_trade_api as tradeapi  # type: ignore

    from config.registry import StateFiles, atomic_write_json
    from main import Config, load_metadata_with_lock

    flow_path = REPO / "logs" / "scoring_flow.jsonl"
    last_by_sym = _last_scores_from_scoring_flow(flow_path)

    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    positions = api.list_positions() or []

    meta_path = REPO / StateFiles.POSITION_METADATA
    metadata = load_metadata_with_lock(meta_path)
    if not isinstance(metadata, dict):
        metadata = {}

    now_iso = datetime.now(timezone.utc).isoformat()
    changes = []

    for p in positions:
        sym = str(getattr(p, "symbol", "")).upper()
        if not sym:
            continue
        row = last_by_sym.get(sym)
        if not row:
            changes.append({"symbol": sym, "action": "skip", "reason": "no_scoring_flow_match"})
            continue
        score, components, flow_ts = row
        prev = metadata.get(sym) if isinstance(metadata.get(sym), dict) else {}
        es = prev.get("entry_score")
        try:
            es_f = float(es) if es is not None else 0.0
        except (TypeError, ValueError):
            es_f = 0.0
        if es_f > 0 and isinstance(prev.get("v2"), dict) and prev.get("v2"):
            changes.append({"symbol": sym, "action": "skip", "reason": "already_instrumented"})
            continue

        qty = int(abs(float(getattr(p, "qty", 0) or 0)))
        side = "buy" if float(getattr(p, "qty", 0) or 0) > 0 else "sell"
        entry_price = float(getattr(p, "avg_entry_price", 0) or prev.get("entry_price") or 0)

        v2_ctx = {
            "repaired_from": "scoring_flow.jsonl",
            "repaired_at": now_iso,
            "flow_ts": flow_ts,
            "score_at_repair": score,
            "v2_uw_inputs": {},
            "v2_inputs": {},
        }
        merged = dict(prev)
        merged.update(
            {
                "entry_score": score,
                "components": components or merged.get("components") or {},
                "v2": {**v2_ctx, **(merged.get("v2") if isinstance(merged.get("v2"), dict) else {})},
                "entry_reason": merged.get("entry_reason") or "repaired_from_scoring_flow",
                "market_regime": merged.get("market_regime") or "unknown",
                "direction": merged.get("direction") or ("bullish" if side == "buy" else "bearish"),
                "side": side,
                "qty": qty,
                "entry_price": entry_price or merged.get("entry_price"),
                "metadata_repair": True,
                "updated_at": now_iso,
            }
        )
        if not merged.get("entry_ts"):
            merged["entry_ts"] = now_iso
        metadata[sym] = merged
        changes.append({"symbol": sym, "action": "repair", "entry_score": score})

    print(json.dumps({"changes": changes, "flow_symbols_loaded": len(last_by_sym)}, indent=2))
    if args.apply and any(c.get("action") == "repair" for c in changes):
        atomic_write_json(meta_path, metadata)
        print("Wrote", meta_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
