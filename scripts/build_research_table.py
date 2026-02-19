#!/usr/bin/env python3
"""
Build the research table: canonical components + group_sums + macro context + labels.
Reads: logs/score_snapshot.jsonl, state/blocked_trades.jsonl; optionally bars for SPY/symbols.
Writes: data/research/research_table.parquet, reports/research_dataset/build_log.md, schema.md.
Run from repo root. Usage: python3 scripts/build_research_table.py [--years 3] [--out data/research/research_table.parquet]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

CANONICAL_22 = [
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
    "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score",
    "freshness_factor",
]
GROUP_SUMS_KEYS = ["uw", "regime_macro", "other_components"]
SNAPSHOT_PATH = REPO / "logs" / "score_snapshot.jsonl"
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"
OUT_REPORT = REPO / "reports" / "research_dataset"


def _parse_ts(v):
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _date_str(dt) -> str | None:
    if dt is None:
        return None
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%d")
    return str(dt)[:10]


def load_snapshot_rows() -> list[dict]:
    rows = []
    if not SNAPSHOT_PATH.exists():
        return rows
    for line in SNAPSHOT_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        gates = r.get("gates") or {}
        if gates.get("block_reason") not in ("score_below_min", "expectancy_blocked:score_floor_breach"):
            continue
        ts = _parse_ts(r.get("ts") or r.get("ts_iso"))
        date_str = _date_str(ts)
        if not date_str or not r.get("symbol"):
            continue
        comp = r.get("weighted_contributions") or r.get("signal_group_scores") or {}
        if isinstance(comp, dict) and "components" in comp:
            comp = comp.get("components") or comp
        gs = r.get("group_sums") or {}
        row = {
            "date": date_str,
            "symbol": (r.get("symbol") or "").strip().upper(),
            "block_reason": gates.get("block_reason"),
            "composite_pre_norm": r.get("composite_pre_norm"),
            "composite_post_norm": r.get("composite_post_norm"),
        }
        for k in CANONICAL_22:
            row[f"comp_{k}"] = comp.get(k) if isinstance(comp.get(k), (int, float)) else 0.0
        for k in GROUP_SUMS_KEYS:
            row[f"gs_{k}"] = gs.get(k) if isinstance(gs.get(k), (int, float)) else 0.0
        rows.append(row)
    return rows


def load_blocked_rows() -> list[dict]:
    rows = []
    if not BLOCKED_PATH.exists():
        return rows
    for line in BLOCKED_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        reason = (r.get("reason") or r.get("block_reason") or "").strip()
        if reason not in ("score_below_min", "expectancy_blocked:score_floor_breach"):
            continue
        ts = _parse_ts(r.get("timestamp") or r.get("ts"))
        date_str = _date_str(ts)
        if not date_str or not r.get("symbol"):
            continue
        att = r.get("attribution_snapshot") or {}
        comp = att.get("weighted_contributions") or r.get("components") or {}
        gs = att.get("group_sums") or {}
        row = {
            "date": date_str,
            "symbol": (r.get("symbol") or "").strip().upper(),
            "block_reason": reason,
            "composite_pre_norm": att.get("composite_pre_norm") or r.get("composite_pre_norm"),
            "composite_post_norm": att.get("composite_post_norm") or r.get("composite_post_norm") or r.get("score"),
        }
        for k in CANONICAL_22:
            row[f"comp_{k}"] = comp.get(k) if isinstance(comp.get(k), (int, float)) else 0.0
        for k in GROUP_SUMS_KEYS:
            row[f"gs_{k}"] = gs.get(k) if isinstance(gs.get(k), (int, float)) else 0.0
        rows.append(row)
    return rows


def merge_rows(snapshot_rows: list[dict], blocked_rows: list[dict]) -> list[dict]:
    """Dedup by (date, symbol); prefer snapshot then blocked."""
    by_key = {}
    for r in blocked_rows:
        by_key[(r["date"], r["symbol"])] = r
    for r in snapshot_rows:
        by_key[(r["date"], r["symbol"])] = r
    return list(by_key.values())


def add_macro_and_labels(rows: list[dict], years: int) -> list[dict]:
    """Add spy_* and forward_return_* if bars available; else nulls."""
    try:
        import pandas as pd
    except ImportError:
        for r in rows:
            r["spy_1w_ret"] = None
            r["spy_1m_ret"] = None
            r["vol_regime_proxy"] = None
            r["forward_return_1d"] = r["forward_return_3d"] = r["forward_return_5d"] = r["forward_return_10d"] = r["forward_return_20d"] = None
            r["mfe_proxy"] = r["mae_proxy"] = None
        return rows

    dates = sorted(set(r["date"] for r in rows))
    if not dates:
        return rows
    start, end = dates[0], dates[-1]
    # Try load SPY bars (simplified: we'd need data.bars_loader or Alpaca)
    spy_ret = {}
    try:
        from data.bars_loader import load_bars
        for d in dates:
            try:
                bars = load_bars("SPY", d, timeframe="1Day", use_cache=True, fetch_if_missing=False)
                if bars and len(bars) >= 2:
                    # placeholder: use first/last close for 1d ret
                    c0 = float(bars[0].get("c", bars[0].get("close", 0)))
                    c1 = float(bars[-1].get("c", bars[-1].get("close", 0))) if len(bars) > 1 else c0
                    spy_ret[d] = (c1 - c0) / c0 if c0 else None
            except Exception:
                spy_ret[d] = None
    except ImportError:
        pass
    for r in rows:
        r["spy_1w_ret"] = spy_ret.get(r["date"])
        r["spy_2w_ret"] = None
        r["spy_1m_ret"] = None
        r["spy_ma_distance_proxy"] = None
        r["spy_ma_slope_proxy"] = None
        r["vol_regime_proxy"] = None
        r["breadth_pct_above_50dma"] = None
        r["forward_return_1d"] = r["forward_return_3d"] = r["forward_return_5d"] = r["forward_return_10d"] = r["forward_return_20d"] = None
        r["mfe_proxy"] = r["mae_proxy"] = None
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=3, help="Target years (document only if data shorter)")
    ap.add_argument("--out", default="data/research/research_table.parquet", help="Output Parquet path")
    args = ap.parse_args()
    out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    snapshot_rows = load_snapshot_rows()
    blocked_rows = load_blocked_rows()
    rows = merge_rows(snapshot_rows, blocked_rows)
    rows = add_macro_and_labels(rows, args.years)

    if not rows:
        OUT_REPORT.mkdir(parents=True, exist_ok=True)
        (OUT_REPORT / "build_log.md").write_text(
            "# Build Log\n\nNo rows (empty snapshot and blocked_trades or no matching block_reason).\n",
            encoding="utf-8",
        )
        (OUT_REPORT / "schema.md").write_text(
            "# Schema\n\nIntended: date, symbol, comp_* (22), gs_* (3), composite_pre_norm, composite_post_norm, macro cols, label cols.\n",
            encoding="utf-8",
        )
        print("No rows; build_log and schema written.")
        return 0

    try:
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_parquet(out_path, index=False)
    except ImportError:
        # No pandas/pyarrow: write JSONL for audit to consume
        out_path = out_path.with_suffix(".jsonl")
        with out_path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, default=str) + "\n")
    except Exception as e:
        out_path = out_path.with_suffix(".jsonl")
        with out_path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, default=str) + "\n")

    dates = sorted(set(r["date"] for r in rows))
    symbols = sorted(set(r["symbol"] for r in rows))
    start_date, end_date = dates[0], dates[-1]
    OUT_REPORT.mkdir(parents=True, exist_ok=True)
    build_log = [
        "# Build Log",
        "",
        f"- **Start date:** {start_date}",
        f"- **End date:** {end_date}",
        f"- **Row count:** {len(rows)}",
        f"- **Symbol count:** {len(symbols)}",
        f"- **Output:** {out_path.relative_to(REPO)}",
        f"- **Target years:** {args.years} (actual range: {len(dates)} days)",
        "",
    ]
    (OUT_REPORT / "build_log.md").write_text("\n".join(build_log), encoding="utf-8")
    schema_md = [
        "# Schema",
        "",
        "| Column | Type |",
        "|--------|------|",
    ]
    if rows:
        for k in sorted(rows[0].keys()):
            schema_md.append(f"| {k} | float/str |")
    (OUT_REPORT / "schema.md").write_text("\n".join(schema_md), encoding="utf-8")
    print(f"Built {len(rows)} rows, {start_date} -> {end_date}. See reports/research_dataset/build_log.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
