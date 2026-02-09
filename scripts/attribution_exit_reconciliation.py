#!/usr/bin/env python3
"""
Attribution vs Exit Reconciliation — match trades between attribution and exit_attribution.

For a date range: load logs/attribution.jsonl and logs/exit_attribution.jsonl;
match by trade_id or symbol+entry_ts/exit_ts; compare PnL, timestamps, quantities;
output unrealized vs realized differences, missing exits, mismatched qty. Report: JSON + md.

Usage: python scripts/attribution_exit_reconciliation.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--base-dir PATH] [--out-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else ""


def _iter_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Attribution vs exit attribution reconciliation")
    ap.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    ap.add_argument("--base-dir", type=Path, default=ROOT)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()
    base = args.base_dir.resolve()
    logs = base / "logs"
    attr_path = logs / "attribution.jsonl"
    exit_path = logs / "exit_attribution.jsonl"

    end_date = args.end or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_date = args.start or end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    attr_all = _iter_jsonl(attr_path)
    exit_all = _iter_jsonl(exit_path)

    # Filter by date (attribution: ts; exit: ts or exit_ts or timestamp)
    def in_range(r: dict, key_ts: str = "ts") -> bool:
        ts = r.get(key_ts) or r.get("timestamp") or r.get("exit_ts")
        d = _day_utc(str(ts or ""))
        return start_date <= d <= end_date

    attr = [r for r in attr_all if in_range(r)]
    exits = [r for r in exit_all if in_range(r, "ts") or in_range(r, "exit_ts") or in_range(r, "timestamp")]

    # Build keys: trade_id preferred; else symbol + entry_ts bucket
    def entry_ts_bucket(ts: str) -> str:
        if not ts:
            return ""
        s = str(ts)[:19]  # bucket to minute
        return s.replace("Z", "").replace("+00:00", "")

    def attr_key(r: dict) -> str:
        tid = r.get("trade_id") or r.get("position_id")
        if tid:
            return f"tid:{tid}"
        sym = (r.get("symbol") or "").upper()
        ts = r.get("entry_ts") or r.get("entry_timestamp") or r.get("ts") or r.get("timestamp")
        return f"sym:{sym}|{entry_ts_bucket(str(ts or ''))}"

    def exit_key(r: dict) -> str:
        tid = r.get("trade_id") or r.get("position_id")
        if tid:
            return f"tid:{tid}"
        sym = (r.get("symbol") or "").upper()
        ts = r.get("entry_ts") or r.get("entry_timestamp")
        return f"sym:{sym}|{entry_ts_bucket(str(ts or ''))}"

    attr_by_key: dict[str, list[dict]] = defaultdict(list)
    for r in attr:
        attr_by_key[attr_key(r)].append(r)
    exit_by_key: dict[str, list[dict]] = defaultdict(list)
    for r in exits:
        exit_by_key[exit_key(r)].append(r)

    # Match and compare
    matched = []
    missing_exit = []
    missing_attribution = []
    pnl_deltas: list[float] = []

    all_keys = set(attr_by_key) | set(exit_by_key)
    for k in all_keys:
        alist = attr_by_key.get(k) or []
        elist = exit_by_key.get(k) or []
        a = alist[0] if alist else None
        e = elist[0] if elist else None
        if a and not e:
            missing_exit.append({"key": k, "symbol": a.get("symbol"), "ts": a.get("ts") or a.get("timestamp")})
            continue
        if e and not a:
            missing_attribution.append({"key": k, "symbol": e.get("symbol"), "ts": e.get("ts") or e.get("timestamp")})
            continue
        if a and e:
            pnl_a = a.get("pnl_usd") or a.get("pnl")
            pnl_e = e.get("pnl_usd") or e.get("pnl")
            try:
                pa = float(pnl_a) if pnl_a is not None else None
                pe = float(pnl_e) if pnl_e is not None else None
            except (TypeError, ValueError):
                pa, pe = None, None
            delta = None
            if pa is not None and pe is not None:
                delta = pa - pe
                pnl_deltas.append(delta)
            qty_a = a.get("qty") or a.get("quantity")
            qty_e = e.get("qty") or e.get("quantity")
            qty_match = (qty_a == qty_e) or (qty_a is None and qty_e is None)
            matched.append({
                "key": k,
                "symbol": a.get("symbol"),
                "attribution_pnl": pa,
                "exit_pnl": pe,
                "pnl_delta": round(delta, 4) if delta is not None else None,
                "qty_match": qty_match,
            })

    avg_delta = sum(pnl_deltas) / len(pnl_deltas) if pnl_deltas else None
    total_attr_pnl = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in attr)
    total_exit_pnl = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in exits)
    headline_delta = total_attr_pnl - total_exit_pnl

    report = {
        "start_date": start_date,
        "end_date": end_date,
        "attribution_count": len(attr),
        "exit_attribution_count": len(exits),
        "matched_pairs": len(matched),
        "missing_exit_count": len(missing_exit),
        "missing_attribution_count": len(missing_attribution),
        "total_attribution_pnl": round(total_attr_pnl, 4),
        "total_exit_pnl": round(total_exit_pnl, 4),
        "headline_delta": round(headline_delta, 4),
        "avg_matched_pnl_delta": round(avg_delta, 4) if avg_delta is not None else None,
        "missing_exit_sample": missing_exit[:20],
        "missing_attribution_sample": missing_attribution[:20],
        "matched_sample": matched[:30],
    }

    md_lines = [
        "# Attribution vs Exit Reconciliation",
        f"Range: {start_date} to {end_date}",
        f"Attribution records: {len(attr)}",
        f"Exit attribution records: {len(exits)}",
        f"Matched pairs: {len(matched)}",
        f"Missing exit (in attribution, no exit_attribution): {len(missing_exit)}",
        f"Missing attribution (in exit_attribution, no attribution): {len(missing_attribution)}",
        "",
        f"**Total attribution PnL:** {total_attr_pnl:.2f}",
        f"**Total exit PnL:** {total_exit_pnl:.2f}",
        f"**Headline delta (attr - exit):** {headline_delta:.2f}",
        f"**Avg matched pair PnL delta:** {avg_delta:.4f}" if avg_delta is not None else "",
        "",
        "## Sample missing exits",
        "",
    ]
    for m in missing_exit[:10]:
        md_lines.append(f"- {m.get('key')} symbol={m.get('symbol')} ts={m.get('ts')}")
    md_lines.append("")
    md_lines.append("## Sample matched (PnL delta)")
    for m in matched[:10]:
        md_lines.append(f"- {m.get('key')} attr_pnl={m.get('attribution_pnl')} exit_pnl={m.get('exit_pnl')} delta={m.get('pnl_delta')} qty_match={m.get('qty_match')}")

    print(json.dumps(report, indent=2))
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "attribution_exit_reconciliation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (args.out_dir / "attribution_exit_reconciliation.md").write_text("\n".join(md_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
