#!/usr/bin/env python3
"""
Phase 3: "Few stocks" deep dive. Run ON THE DROPLET.
Pulls from logs/signal_score_breakdown.jsonl + logs/expectancy_gate_truth.jsonl.
Outputs: reports/signal_review/SIGNAL_PIPELINE_DEEP_DIVE.md, SIGNAL_PIPELINE_DEEP_DIVE.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BREAKDOWN_JSONL = REPO / "logs" / "signal_score_breakdown.jsonl"
GATE_TRUTH_JSONL = REPO / "logs" / "expectancy_gate_truth.jsonl"
OUT_DIR = REPO / "reports" / "signal_review"
OUT_MD = OUT_DIR / "SIGNAL_PIPELINE_DEEP_DIVE.md"
OUT_JSON = OUT_DIR / "SIGNAL_PIPELINE_DEEP_DIVE.json"

DEFAULT_SYMBOLS = "SPY,QQQ,COIN,NVDA,TSLA"
DEFAULT_N = 25
DEFAULT_WINDOW_HOURS = 24


def _parse_ts(v) -> int | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return int(float(v))
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s[:26])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def _median(arr: list[float]) -> float:
    if not arr:
        return 0.0
    arr = sorted(arr)
    m = len(arr) // 2
    if len(arr) % 2:
        return float(arr[m])
    return (arr[m - 1] + arr[m]) / 2.0


def load_breakdown(window_hours: int) -> list[dict]:
    cutoff = int((datetime.now(timezone.utc) - timedelta(hours=window_hours)).timestamp())
    rows = []
    if not BREAKDOWN_JSONL.exists():
        return rows
    for line in BREAKDOWN_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            t = _parse_ts(r.get("ts_eval_epoch") or r.get("ts_eval"))
            if t and t < cutoff:
                continue
            rows.append(r)
        except Exception:
            continue
    return rows


def load_gate_truth(window_hours: int) -> list[dict]:
    cutoff = int((datetime.now(timezone.utc) - timedelta(hours=window_hours)).timestamp())
    rows = []
    if not GATE_TRUTH_JSONL.exists():
        return rows
    for line in GATE_TRUTH_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            t = _parse_ts(r.get("ts_eval_epoch") or r.get("ts_eval_iso"))
            if t and t < cutoff:
                continue
            rows.append(r)
        except Exception:
            continue
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=DEFAULT_SYMBOLS, help="Comma-separated symbols")
    ap.add_argument("--n", type=int, default=DEFAULT_N, help="Candidates per symbol")
    ap.add_argument("--window-hours", type=int, default=DEFAULT_WINDOW_HOURS, help="Time window")
    args = ap.parse_args()
    symbols_set = {s.strip() for s in args.symbols.split(",") if s.strip()}

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    breakdown_rows = load_breakdown(args.window_hours)
    gate_truth_rows = load_gate_truth(args.window_hours)
    gate_by_key: dict[tuple[str, str], dict] = {}
    for r in gate_truth_rows:
        sym = (r.get("symbol") or "").strip()
        tid = (r.get("trace_id") or r.get("ts_eval_iso") or "").strip()
        if sym and tid:
            gate_by_key[(sym, tid)] = r

    # Filter breakdown by symbols, then by most recent n per symbol
    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for r in breakdown_rows:
        sym = (r.get("symbol") or "").strip()
        if sym in symbols_set:
            by_symbol[sym].append(r)
    for sym in list(by_symbol.keys()):
        by_symbol[sym].sort(key=lambda x: _parse_ts(x.get("ts_eval_epoch") or x.get("ts_eval")) or 0, reverse=True)
        by_symbol[sym] = by_symbol[sym][: args.n]

    result = {
        "symbols": list(symbols_set),
        "n_per_symbol": args.n,
        "window_hours": args.window_hours,
        "per_symbol": {},
        "dominant_failure_modes": {},
    }

    md_lines = [
        "# Signal pipeline deep dive (Phase 3)",
        "",
        f"Symbols: {args.symbols}. N per symbol: {args.n}. Window: {args.window_hours}h.",
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "python3 scripts/signal_pipeline_deep_dive_on_droplet.py --symbols SPY,QQQ,COIN,NVDA,TSLA --n 25 --window-hours 24",
        "```",
        "",
    ]

    for symbol in sorted(symbols_set):
        candidates = by_symbol.get(symbol, [])
        if not candidates:
            result["per_symbol"][symbol] = {
                "per_signal_table": {},
                "trace_table": [],
                "dominant_failure_mode": "no_candidates",
            }
            result["dominant_failure_modes"][symbol] = "no_candidates"
            md_lines.append(f"## {symbol}")
            md_lines.append("")
            md_lines.append("No candidates in window.")
            md_lines.append("")
            continue

        # Per-signal aggregates across these candidates
        by_sig: dict[str, list[float]] = defaultdict(list)
        missing_count: dict[str, int] = defaultdict(int)
        zero_count: dict[str, int] = defaultdict(int)
        raw_vals: dict[str, list[float]] = defaultdict(list)
        for r in candidates:
            for s in r.get("signals") or []:
                name = s.get("signal_name") or "unknown"
                c = float(s.get("contribution") or 0.0)
                by_sig[name].append(c)
                raw_vals[name].append(float(s.get("raw_value") or 0.0))
                if s.get("is_missing"):
                    missing_count[name] += 1
                if s.get("is_zero"):
                    zero_count[name] += 1
        n_c = len(candidates)
        signal_names = sorted(set(by_sig.keys()))
        per_signal_table = {}
        for name in signal_names:
            per_signal_table[name] = {
                "missing_rate_pct": round(100.0 * missing_count[name] / n_c, 1) if n_c else 0,
                "zero_rate_pct": round(100.0 * zero_count[name] / n_c, 1) if n_c else 0,
                "median_raw_value": round(_median(raw_vals[name]), 4),
                "median_normalized_value": round(_median(by_sig[name]), 4),
                "median_contribution": round(_median(by_sig[name]), 4),
            }
        result["per_symbol"][symbol] = {"per_signal_table": per_signal_table, "trace_table": [], "dominant_failure_mode": None}

        # Trace table: top 5 contrib, top 5 missing/zero
        trace_table = []
        for r in candidates:
            tid = r.get("trace_id") or r.get("ts_eval") or ""
            gate_row = gate_by_key.get((symbol, tid))
            score_used = None
            min_exec = None
            if gate_row:
                score_used = gate_row.get("score_used_by_gate")
                min_exec = gate_row.get("min_exec_score")
            if score_used is None:
                score_used = r.get("composite_score_post")
            composite_pre = r.get("composite_score_pre")
            composite_post = r.get("composite_score_post")
            gate_outcome = r.get("gate_outcome") or (gate_row.get("gate_outcome") if gate_row else None)

            signals_list = r.get("signals") or []
            by_contrib = sorted(signals_list, key=lambda x: float(x.get("contribution") or 0), reverse=True)
            top5_contrib = [{"name": x.get("signal_name"), "contribution": float(x.get("contribution") or 0)} for x in by_contrib[:5]]
            missing_zero = [s for s in signals_list if s.get("is_missing") or s.get("is_zero")]
            missing_zero.sort(key=lambda x: (1 if x.get("is_missing") else 0, -float(x.get("contribution") or 0)))
            top5_missing_zero = [{"name": x.get("signal_name"), "is_missing": x.get("is_missing"), "is_zero": x.get("is_zero")} for x in missing_zero[:5]]

            trace_table.append({
                "ts": r.get("ts_eval"),
                "trace_id": tid,
                "composite_pre": composite_pre,
                "composite_post": composite_post,
                "score_used_by_gate": score_used,
                "min_exec_score": min_exec,
                "gate_outcome": gate_outcome,
                "top5_contributing": top5_contrib,
                "top5_missing_zero": top5_missing_zero,
            })
        result["per_symbol"][symbol]["trace_table"] = trace_table

        # Dominant failure mode
        missing_pct_avg = sum(per_signal_table[n]["missing_rate_pct"] for n in signal_names) / len(signal_names) if signal_names else 0
        zero_pct_avg = sum(per_signal_table[n]["zero_rate_pct"] for n in signal_names) / len(signal_names) if signal_names else 0
        median_composite = _median([float(r.get("composite_score_post") or 0) for r in candidates])
        pass_count = sum(1 for t in trace_table if t.get("gate_outcome") == "pass")
        if missing_pct_avg > 50:
            dom = "signals missing"
        elif zero_pct_avg > 70:
            dom = "signals zero"
        elif median_composite < 0.5 and pass_count == 0:
            dom = "genuinely low composite"
        else:
            dom = "adjustment crush" if median_composite > 0.5 and pass_count == 0 else "normalization crush"
        result["per_symbol"][symbol]["dominant_failure_mode"] = dom
        result["dominant_failure_modes"][symbol] = dom

        # MD: per-signal table
        md_lines.append(f"## {symbol}")
        md_lines.append("")
        md_lines.append("### Per-signal table")
        md_lines.append("")
        md_lines.append("| signal_name | missing_rate_pct | zero_rate_pct | median_raw | median_norm | median_contrib |")
        md_lines.append("|-------------|------------------|---------------|------------|-------------|----------------|")
        for name in signal_names:
            row = per_signal_table[name]
            md_lines.append(f"| {name} | {row['missing_rate_pct']} | {row['zero_rate_pct']} | {row['median_raw_value']} | {row['median_normalized_value']} | {row['median_contribution']} |")
        md_lines.append("")
        md_lines.append("### Per-candidate trace (sample 25)")
        md_lines.append("")
        md_lines.append("| ts | trace_id | composite_pre | composite_post | score_used_by_gate | min_exec_score | gate_outcome | top5_contrib | top5_missing_zero |")
        md_lines.append("|----|----------|---------------|----------------|--------------------|----------------|--------------|--------------|-------------------|")
        for t in trace_table[:25]:
            tc = ", ".join(f"{x['name']}={x['contribution']:.3f}" for x in t["top5_contributing"][:3])
            mz = ", ".join(x.get("name", "") for x in t["top5_missing_zero"][:3])
            md_lines.append(f"| {t['ts']} | {t['trace_id']} | {t['composite_pre']} | {t['composite_post']} | {t['score_used_by_gate']} | {t['min_exec_score']} | {t['gate_outcome']} | {tc[:40]} | {mz} |")
        md_lines.append("")
        md_lines.append(f"**Dominant failure mode:** {dom}")
        md_lines.append("")
    md_lines.append("")
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    def _serialize(obj):
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        if isinstance(obj, list):
            return [_serialize(x) for x in obj]
        if isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}
        return str(obj)

    OUT_JSON.write_text(json.dumps(_serialize(result), indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT_MD} and {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
