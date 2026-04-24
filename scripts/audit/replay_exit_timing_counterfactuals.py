#!/usr/bin/env python3
"""
Per-trade exit horizon counterfactuals: mark-to-market PnL at +1m/+5m/+15m/+30m/+60m from entry,
plus realized PnL and MFE/MAE/giveback when present in exit rows.

Read-only. Expects artifacts/market_data/alpaca_bars.jsonl (Alpaca bar dicts with t, c).

Usage:
  PYTHONPATH=. python3 scripts/audit/replay_exit_timing_counterfactuals.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]

HORIZONS_SEC = (60, 300, 900, 1800, 3600)
HORIZON_LABELS = ("plus_1m", "plus_5m", "plus_15m", "plus_30m", "plus_60m")


def parse_ts(x: Any) -> Optional[datetime]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return datetime.fromtimestamp(float(x), tz=timezone.utc)
    s = str(x)
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except Exception:
        return None


def load_exit_rows(root: Path) -> List[dict]:
    rows: List[dict] = []
    for f in sorted(root.glob("logs/exit_attribution*.jsonl")):
        with f.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def load_bars(path: Path) -> Dict[str, List[Tuple[datetime, float]]]:
    bars: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
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
            b = data.get("bars") or {}
            for sym, arr in b.items():
                if not isinstance(arr, list):
                    continue
                for bar in arr:
                    t = parse_ts(bar.get("t"))
                    c = bar.get("c")
                    if t is None or c is None:
                        continue
                    bars[sym.upper()].append((t, float(c)))
    for sym in list(bars.keys()):
        bars[sym].sort(key=lambda x: x[0])
    return dict(bars)


def find_price_at_or_after(bars_list: List[Tuple[datetime, float]], ts: datetime) -> Tuple[Optional[float], Optional[datetime]]:
    for t, c in bars_list:
        if t >= ts:
            return c, t
    return None, None


def pnl_at_price(entry_price: float, qty: float, side: str, px: float) -> float:
    s = str(side or "").lower()
    if s in ("sell", "short"):
        return (entry_price - px) * qty
    return (px - entry_price) * qty


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        f = float(x)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def extract_mfe_mae_giveback(r: dict) -> Dict[str, Any]:
    eq = r.get("exit_quality_metrics") if isinstance(r.get("exit_quality_metrics"), dict) else {}
    snap = r.get("snapshot") if isinstance(r.get("snapshot"), dict) else {}
    mfe = _safe_float(eq.get("mfe_pct")) or _safe_float(snap.get("mfe"))
    mae = _safe_float(eq.get("mae_pct")) or _safe_float(snap.get("mae"))
    pnl_pct = _safe_float(r.get("pnl_pct"))
    giveback = None
    if mfe is not None and pnl_pct is not None:
        giveback = mfe - pnl_pct
    return {"mfe_pct": mfe, "mae_pct": mae, "pnl_pct": pnl_pct, "giveback_mfe_minus_pnl_pct": giveback}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--alpaca-bars", type=Path, default=None)
    ap.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="Directory for PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.{json,md} (default: <root>/artifacts/profit_v2)",
    )
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    bars_path = args.alpaca_bars or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")
    ev = args.evidence_dir or (root / "artifacts" / "profit_v2")
    ev = ev.resolve()
    out_json = args.out_json or (ev / "PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.json")
    out_md = args.out_md or (ev / "PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.md")

    if not bars_path.is_file():
        print("ERROR: Missing bars file:", bars_path, file=sys.stderr)
        return 1

    rows = load_exit_rows(root)
    bars = load_bars(bars_path)

    per_trade: List[Dict[str, Any]] = []
    skipped: Dict[str, int] = defaultdict(int)

    for r in rows:
        sym = str(r.get("symbol") or "").upper()
        entry_ts = parse_ts(r.get("entry_ts") or r.get("entry_timestamp"))
        exit_ts = parse_ts(r.get("exit_ts") or r.get("timestamp"))
        ep = _safe_float(r.get("entry_price"))
        qty = _safe_float(r.get("qty"))
        side = str(r.get("side") or "")
        realized = _safe_float(r.get("pnl"))
        if not sym or entry_ts is None or ep is None or qty is None:
            skipped["missing_core_fields"] += 1
            continue
        blist = bars.get(sym)
        if not blist:
            skipped["missing_bars_symbol"] += 1
            continue

        horizons: Dict[str, Any] = {}
        for sec, label in zip(HORIZONS_SEC, HORIZON_LABELS):
            target = entry_ts + timedelta(seconds=sec)
            px, _ = find_price_at_or_after(blist, target)
            if px is None:
                horizons[label] = {"pnl_usd": None, "price": None, "skip": "no_bar_at_horizon"}
            else:
                horizons[label] = {"pnl_usd": round(pnl_at_price(ep, qty, side, px), 6), "price": px}

        late_exit_pnl = None
        if exit_ts is not None:
            px_e, _ = find_price_at_or_after(blist, exit_ts)
            if px_e is not None:
                late_exit_pnl = round(pnl_at_price(ep, qty, side, px_e), 6)

        per_trade.append(
            {
                "symbol": sym,
                "mode": r.get("mode"),
                "strategy": r.get("strategy"),
                "side": side,
                "entry_ts": entry_ts.isoformat().replace("+00:00", "Z"),
                "exit_ts": exit_ts.isoformat().replace("+00:00", "Z") if exit_ts else None,
                "realized_pnl_usd": realized,
                "horizon_pnl_usd": horizons,
                "pnl_usd_at_exit_bar": late_exit_pnl,
                "mfe_mae": extract_mfe_mae_giveback(r),
                "canonical_trade_id": r.get("canonical_trade_id"),
            }
        )

    summary = {
        "exit_rows_total": len(rows),
        "rows_with_full_horizons": sum(
            1
            for x in per_trade
            if all(
                x["horizon_pnl_usd"].get(lbl, {}).get("pnl_usd") is not None for lbl in HORIZON_LABELS
            )
        ),
        "skipped": dict(skipped),
        "bars_symbols": len(bars),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summary, "per_trade": per_trade, "horizon_labels_sec": dict(zip(HORIZON_LABELS, HORIZONS_SEC))}
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS\n",
        f"- **Exit rows:** {len(rows)}\n",
        f"- **Replay rows written:** {len(per_trade)}\n",
        f"- **Skipped:** `{json.dumps(dict(skipped), sort_keys=True)}`\n",
        f"- **Bars symbols loaded:** {len(bars)}\n",
        "\n## Horizon definitions\n",
        "Mark-to-market PnL at first 1Min bar at or after entry + offset (long: (px-entry)*qty; short: (entry-px)*qty).\n",
    ]
    out_md.write_text("".join(lines), encoding="utf-8")
    print("Wrote", out_json, "and", out_md, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
