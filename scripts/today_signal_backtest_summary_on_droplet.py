#!/usr/bin/env python3
"""
Today's signal backtest summary (run on droplet).

Reads today's (or --date) score_snapshot, blocked_trades, attribution, and uw_flow_cache.
Produces a summary: all signals, whether each fired, component scores, composite,
whether would have entered (composite + expectancy gates) or blocked, and direction (long/short).

Output: reports/investigation/today_backtest_YYYYMMDD/SUMMARY.md and summary.json

Usage (on droplet):
  python3 scripts/today_signal_backtest_summary_on_droplet.py [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

MIN_EXEC_SCORE = 2.5
SIGNAL_NAMES = [
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
    "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow",
    "squeeze_score", "freshness_factor",
]


def _day_utc(ts) -> str | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return None
    s = str(ts)
    if len(s) >= 10:
        return s[:10]
    return None


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Today's signal backtest summary (run on droplet)")
    ap.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--out-dir", default=None, help="Output dir (default: reports/investigation/today_backtest_<date>)")
    args = ap.parse_args()

    if args.date:
        target_date = args.date
    else:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    out_dir = Path(args.out_dir) if args.out_dir else REPO / "reports" / "investigation" / f"today_backtest_{target_date.replace('-', '')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = REPO / "logs" / "score_snapshot.jsonl"
    blocked_path = REPO / "state" / "blocked_trades.jsonl"
    attr_path = REPO / "logs" / "attribution.jsonl"
    cache_path = REPO / "data" / "uw_flow_cache.json"

    # Load snapshots for date
    snapshots = []
    for r in _iter_jsonl(snapshot_path):
        day = _day_utc(r.get("ts") or r.get("ts_iso"))
        if day == target_date:
            snapshots.append(r)

    # Load blocked for date
    blocked_ts = set()
    for r in _iter_jsonl(blocked_path):
        day = _day_utc(r.get("timestamp") or r.get("ts"))
        if day == target_date:
            ts = r.get("timestamp") or r.get("ts")
            sym = r.get("symbol")
            if sym and ts:
                blocked_ts.add((sym, int(ts) if isinstance(ts, (int, float)) else ts))

    # Load attribution (entered trades) for date
    entered = set()
    for r in _iter_jsonl(attr_path):
        if r.get("type") != "attribution":
            continue
        day = _day_utc(r.get("timestamp") or r.get("ts"))
        if day == target_date:
            ts = r.get("timestamp") or r.get("ts")
            sym = r.get("symbol")
            if sym and ts:
                entered.add((sym, int(ts) if isinstance(ts, (int, float)) else ts))

    # Load uw cache for direction (flow sentiment -> long/short)
    flow_sentiment = {}
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            for sym, data in (cache.items() if isinstance(cache, dict) else []):
                if not isinstance(data, dict):
                    continue
                sent = (data.get("sentiment") or data.get("flow_sentiment") or "").upper()
                if "BULL" in sent or sent == "BULLISH":
                    flow_sentiment[sym] = "long"
                elif "BEAR" in sent or sent == "BEARISH":
                    flow_sentiment[sym] = "short"
                else:
                    flow_sentiment[sym] = "neutral"
        except Exception:
            pass

    # Build per-candidate rows with signals, fired, scores, enter/blocked, direction
    rows = []
    for r in snapshots:
        sym = r.get("symbol")
        ts = r.get("ts")
        composite = float(r.get("composite_score") or 0)
        gates = r.get("gates") or {}
        comp_gate = gates.get("composite_gate_pass", False)
        exp_gate = gates.get("expectancy_gate_pass", False)
        block_reason = gates.get("block_reason") or ""
        components = r.get("weighted_contributions") or r.get("per_signal") or {}
        key = (sym, int(ts) if isinstance(ts, (int, float)) else ts)
        did_enter = key in entered
        was_blocked = key in blocked_ts
        direction = flow_sentiment.get(sym, "neutral")

        fired = {c: (float(components.get(c) or 0) != 0) for c in SIGNAL_NAMES}
        values = {c: round(float(components.get(c) or 0), 4) for c in SIGNAL_NAMES}

        rows.append({
            "symbol": sym,
            "timestamp": ts,
            "composite_score": round(composite, 3),
            "min_exec_score": MIN_EXEC_SCORE,
            "composite_gate_pass": comp_gate,
            "expectancy_gate_pass": exp_gate,
            "entered": did_enter,
            "blocked": was_blocked,
            "block_reason": block_reason,
            "direction": direction,
            "signals_fired": fired,
            "signal_values": values,
        })

    # Sort by composite desc then symbol
    rows.sort(key=lambda x: (-(x["composite_score"] or 0), x["symbol"] or ""))

    # Summary stats
    n_candidates = len(rows)
    n_entered = sum(1 for r in rows if r["entered"])
    n_blocked = sum(1 for r in rows if r["blocked"])
    n_above_min = sum(1 for r in rows if (r["composite_score"] or 0) >= MIN_EXEC_SCORE)
    n_long = sum(1 for r in rows if r["direction"] == "long")
    n_short = sum(1 for r in rows if r["direction"] == "short")

    # Per-signal: count fired across candidates
    signal_fire_counts = {c: sum(1 for r in rows if r["signals_fired"].get(c)) for c in SIGNAL_NAMES}

    out_json = {
        "date": target_date,
        "min_exec_score": MIN_EXEC_SCORE,
        "n_candidates": n_candidates,
        "n_entered": n_entered,
        "n_blocked": n_blocked,
        "n_above_min_exec": n_above_min,
        "n_direction_long": n_long,
        "n_direction_short": n_short,
        "signal_fire_counts": signal_fire_counts,
        "candidates": rows,
    }

    (out_dir / "summary.json").write_text(json.dumps(out_json, indent=2, default=str), encoding="utf-8")

    # Markdown summary
    md = [
        "# Today's Signal Backtest Summary",
        "",
        f"**Date:** {target_date}",
        f"**MIN_EXEC_SCORE:** {MIN_EXEC_SCORE}",
        "",
        "## Counts",
        f"- Candidates at expectancy gate: **{n_candidates}**",
        f"- Entered (attribution): **{n_entered}**",
        f"- Blocked: **{n_blocked}**",
        f"- Composite ≥ MIN_EXEC_SCORE: **{n_above_min}**",
        f"- Direction long: **{n_long}** | short: **{n_short}** | neutral: **{n_candidates - n_long - n_short}**",
        "",
        "## Signals fired (count of candidates with non-zero contribution)",
        "| Signal | Fired count |",
        "|--------|-------------|",
    ]
    for c in SIGNAL_NAMES:
        md.append(f"| {c} | {signal_fire_counts.get(c, 0)} |")
    md.append("")
    md.append("## Per-candidate: composite, gates, entered/blocked, direction, and signal values")
    md.append("")
    for r in rows[:50]:  # cap 50 for readability
        sym = r["symbol"]
        comp = r["composite_score"]
        cg = "pass" if r["composite_gate_pass"] else "fail"
        eg = "pass" if r["expectancy_gate_pass"] else "fail"
        ent = "yes" if r["entered"] else "no"
        blk = "blocked" if r["blocked"] else ""
        direc = r["direction"]
        top_signals = [c for c in SIGNAL_NAMES if r["signals_fired"].get(c)][:8]
        md.append(f"### {sym} (composite={comp}, composite_gate={cg}, expectancy_gate={eg}, entered={ent} {blk}, direction={direc})")
        md.append(f"- Fired: {', '.join(top_signals) or 'none'}")
        val_str = ", ".join(f"{c}={r['signal_values'].get(c, 0)}" for c in SIGNAL_NAMES[:12])
        md.append(f"- Values: {val_str}")
        md.append("")
    if len(rows) > 50:
        md.append(f"*... and {len(rows) - 50} more candidates (see summary.json).*")
        md.append("")

    (out_dir / "SUMMARY.md").write_text("\n".join(md), encoding="utf-8")

    print(f"Wrote {out_dir / 'summary.json'} and {out_dir / 'SUMMARY.md'}")
    print(f"Candidates: {n_candidates}, Entered: {n_entered}, Blocked: {n_blocked}, Composite>={MIN_EXEC_SCORE}: {n_above_min}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
