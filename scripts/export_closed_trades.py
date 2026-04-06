#!/usr/bin/env python3
"""
Export recent closed trades from logs/attribution.jsonl to CSV (flat components for SPI diagnostics).

Usage:
  python3 scripts/export_closed_trades.py --out reports/stock_100_trades.csv --limit 100
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.registry import LogFiles


def _parse_ts(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        s = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except Exception:
        return None


def _load_closed_trades(base: Path, limit: int) -> List[Dict[str, Any]]:
    path = (base / LogFiles.ATTRIBUTION).resolve()
    trades: List[Dict[str, Any]] = []
    if not path.is_file():
        return trades
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get("type") != "attribution":
                continue
            trade_id = rec.get("trade_id") or ""
            if str(trade_id).startswith("open_"):
                continue
            ts = _parse_ts(rec.get("ts") or rec.get("timestamp"))
            if not ts:
                continue
            context = rec.get("context") if isinstance(rec.get("context"), dict) else {}
            pnl = float(rec.get("pnl_usd", 0) or 0)
            close_reason = context.get("close_reason") or rec.get("close_reason") or ""
            if pnl == 0.0 and not close_reason:
                continue
            rec["_ts"] = ts
            trades.append(rec)
        except Exception:
            continue
    trades.sort(key=lambda t: t.get("_ts") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return trades[:limit]


def _flatten_row(rec: Dict[str, Any]) -> Dict[str, str]:
    ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
    comps = ctx.get("components") if isinstance(ctx.get("components"), dict) else {}
    total_score_v = ctx.get("score")
    if total_score_v is None:
        total_score_v = ctx.get("entry_score")
    row: Dict[str, str] = {
        "trade_id": str(rec.get("trade_id") or ""),
        "timestamp_utc": rec["_ts"].isoformat() if rec.get("_ts") else "",
        "symbol": str(rec.get("symbol") or ""),
        "pnl_usd": str(rec.get("pnl_usd", "") or ""),
        "close_reason": str(ctx.get("close_reason") or rec.get("close_reason") or ""),
        "entry_score": str(ctx.get("entry_score") if ctx.get("entry_score") is not None else ""),
        "total_score": str(total_score_v if total_score_v is not None else ""),
    }
    for k, v in comps.items():
        row[f"component_{k}"] = "" if v is None else str(v)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO_ROOT, help="Repo root (default: parent of scripts/)")
    ap.add_argument("--out", type=Path, required=True, help="Output CSV path")
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()
    base = args.root.resolve()
    trades = _load_closed_trades(base, max(1, args.limit))
    if not trades:
        print("No closed trades found.", file=sys.stderr)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("trade_id,timestamp_utc,symbol,pnl_usd,close_reason\n", encoding="utf-8")
        return 1

    rows = [_flatten_row(t) for t in trades]
    fieldnames: List[str] = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
