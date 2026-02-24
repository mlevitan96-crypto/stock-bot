#!/usr/bin/env python3
"""
Trading environment review (run on droplet).
Produces:
- Last N (default 150) closed trades with full entry + exit signal scores
- Full list of all entry and exit signal/component names and score stats
- Signal health: entry/exit signals firing (expectancy gate, ledger, orders)
- Persona profitability review: win rate by score bucket, how to improve

Output: reports/trading_environment_review/TRADING_ENVIRONMENT_REVIEW_<date>.md and .json
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

ATTRIBUTION = REPO / "logs" / "attribution.jsonl"
EXIT_ATTR = REPO / "logs" / "exit_attribution.jsonl"
GATE_TRUTH = REPO / "logs" / "expectancy_gate_truth.jsonl"
LEDGER = REPO / "reports" / "decision_ledger" / "decision_ledger.jsonl"
ORDERS = REPO / "logs" / "orders.jsonl"
SUBMIT_CALLED = REPO / "logs" / "submit_order_called.jsonl"
OUT_DIR = REPO / "reports" / "trading_environment_review"
DEFAULT_LAST_N = 150


def _ts_key(r: dict, exit_ts_key: str = "timestamp") -> str:
    ts = r.get(exit_ts_key) or r.get("ts") or r.get("exit_timestamp") or ""
    return str(ts)[:19] if ts else ""


def _parse_ts(ts: str) -> int | None:
    if not ts:
        return None
    try:
        s = str(ts).replace("Z", "+00:00")[:26]
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def load_closed_trades_with_scores(attr_path: Path, exit_path: Path, last_n: int) -> list[dict]:
    """Load last N closed equity trades with entry_score and exit scores. Prefer attribution for close events; join exit_attribution for v2 exit scores."""
    if not attr_path.exists():
        return []
    rows: list[dict] = []
    for line in attr_path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("type") != "attribution":
            continue
        tid = str(rec.get("trade_id") or "")
        if tid.startswith("open_"):
            continue
        symbol = str(rec.get("symbol", "")).upper()
        if not symbol or "TEST" in symbol:
            continue
        if rec.get("strategy_id") and rec.get("strategy_id") != "equity":
            continue
        ts = rec.get("ts") or rec.get("timestamp") or ""
        if not ts:
            continue
        ctx = rec.get("context") or {}
        entry_score = rec.get("entry_score")
        if entry_score is None:
            entry_score = ctx.get("entry_score")
        try:
            entry_score = float(entry_score) if entry_score is not None else None
        except (TypeError, ValueError):
            entry_score = None
        entry_components = ctx.get("attribution_components") or ctx.get("components") or {}
        if not isinstance(entry_components, dict):
            entry_components = {}
        pnl_usd = rec.get("pnl_usd")
        try:
            pnl_usd = float(pnl_usd) if pnl_usd is not None else None
        except (TypeError, ValueError):
            pnl_usd = None
        entry_ts = ctx.get("entry_ts") or ctx.get("entry_timestamp") or ""
        row = {
            "symbol": symbol,
            "timestamp": ts,
            "entry_timestamp": entry_ts or ts,
            "trade_id": tid,
            "entry_score": entry_score,
            "entry_components": entry_components,
            "pnl_usd": pnl_usd,
            "close_reason": ctx.get("close_reason") or rec.get("close_reason") or "",
            "v2_exit_score": None,
            "v2_exit_components": None,
        }
        rows.append(row)
    rows.sort(key=lambda x: _parse_ts(x["timestamp"]) or 0, reverse=True)
    rows = rows[: last_n * 2]
    exit_by_ts: dict[tuple[str, str], dict] = {}
    exit_by_entry_ts: dict[tuple[str, str], dict] = {}
    if exit_path.exists():
        for line in exit_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-5000:]:
            if not line.strip():
                continue
            try:
                ex = json.loads(line)
            except Exception:
                continue
            sym = str(ex.get("symbol", "")).upper()
            ts_ex = ex.get("timestamp") or ex.get("exit_timestamp") or ""
            entry_ts_ex = ex.get("entry_timestamp") or ex.get("entry_ts") or ""
            if not sym or not ts_ex:
                continue
            v = {"v2_exit_score": ex.get("v2_exit_score"), "v2_exit_components": ex.get("v2_exit_components") or {}}
            exit_by_ts[(sym, str(ts_ex)[:19])] = v
            if entry_ts_ex:
                exit_by_entry_ts[(sym, str(entry_ts_ex)[:19])] = v
    for r in rows:
        k_ts = (r["symbol"], str(r["timestamp"])[:19])
        k_entry = (r["symbol"], str(r.get("entry_timestamp") or r["timestamp"])[:19])
        for k in (k_ts, k_entry):
            if k in exit_by_ts:
                r["v2_exit_score"] = exit_by_ts[k].get("v2_exit_score")
                r["v2_exit_components"] = exit_by_ts[k].get("v2_exit_components") or {}
                break
            if k in exit_by_entry_ts:
                r["v2_exit_score"] = exit_by_entry_ts[k].get("v2_exit_score")
                r["v2_exit_components"] = exit_by_entry_ts[k].get("v2_exit_components") or {}
                break
    return rows[:last_n]


def signal_health(gate_path: Path, ledger_path: Path, orders_path: Path, submit_path: Path, days: int = 7) -> dict:
    """Count recent activity: gate truth, ledger, orders filled, submit_order_called."""
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    out = {"gate_truth_lines": 0, "ledger_lines": 0, "orders_filled": 0, "submit_called": 0}

    def count_jsonl(path: Path, ts_keys: tuple = ("ts", "timestamp", "ts_eval_epoch")) -> int:
        if not path.exists():
            return 0
        n = 0
        for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-5000:]:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                ts = None
                for k in ts_keys:
                    ts = r.get(k)
                    if ts is not None:
                        break
                t = _parse_ts(ts) if ts else None
                if t and t >= cutoff:
                    n += 1
            except Exception:
                continue
        return n

    out["gate_truth_lines"] = count_jsonl(gate_path, ("ts_eval_epoch", "ts_eval_iso", "ts"))
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3000:]:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts"))
                if t and t >= cutoff:
                    out["ledger_lines"] += 1
            except Exception:
                continue
    out["submit_called"] = count_jsonl(submit_path, ("ts", "timestamp"))
    if orders_path.exists():
        for line in orders_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-2000:]:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("timestamp"))
                if t and t < cutoff:
                    continue
                if "filled" in str(r.get("action") or "").lower() or r.get("status") == "filled":
                    out["orders_filled"] += 1
            except Exception:
                continue
    return out


def aggregate_signal_lists(trades: list[dict]) -> tuple[dict, dict]:
    """Build full list of entry and exit signal names with stats (mean, min, max, count)."""
    entry_agg: dict[str, list[float]] = defaultdict(list)
    exit_agg: dict[str, list[float]] = defaultdict(list)
    for t in trades:
        for name, val in (t.get("entry_components") or {}).items():
            try:
                v = float(val)
                entry_agg[name].append(v)
            except (TypeError, ValueError):
                pass
        for name, val in (t.get("v2_exit_components") or {}).items():
            try:
                v = float(val)
                exit_agg[name].append(v)
            except (TypeError, ValueError):
                pass
    def stats(d: dict) -> dict:
        out = {}
        for k, vals in d.items():
            if not vals:
                continue
            out[k] = {
                "count": len(vals),
                "mean": round(sum(vals) / len(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
            }
        return out
    return stats(entry_agg), stats(exit_agg)


def persona_profitability_review(trades: list[dict]) -> dict:
    """Win rate, avg PnL by entry score bucket and exit score bucket; recommendations."""
    if not trades:
        return {"win_rate_pct": None, "total_pnl": None, "by_entry_bucket": {}, "by_exit_bucket": {}, "recommendations": []}
    total_pnl = sum(float(t.get("pnl_usd") or 0) for t in trades)
    wins = sum(1 for t in trades if float(t.get("pnl_usd") or 0) > 0)
    win_rate = round(100.0 * wins / len(trades), 1) if trades else None

    def bucket_entry(s: float | None) -> str:
        if s is None:
            return "missing"
        if s < 2.5:
            return "low_<2.5"
        if s < 3.5:
            return "mid_2.5_3.5"
        return "high_>=3.5"

    def bucket_exit(s) -> str:
        if s is None:
            try:
                return "missing"
            except Exception:
                return "missing"
        try:
            s = float(s)
        except (TypeError, ValueError):
            return "missing"
        if s < 2.0:
            return "low_<2"
        if s < 3.0:
            return "mid_2_3"
        return "high_>=3"

    by_entry: dict[str, list[float]] = defaultdict(list)
    by_exit: dict[str, list[float]] = defaultdict(list)
    for t in trades:
        pnl = float(t.get("pnl_usd") or 0)
        by_entry[bucket_entry(t.get("entry_score"))].append(pnl)
        by_exit[bucket_exit(t.get("v2_exit_score"))].append(pnl)

    by_entry_out = {}
    for b, pnls in by_entry.items():
        by_entry_out[b] = {"count": len(pnls), "win_rate_pct": round(100.0 * sum(1 for p in pnls if p > 0) / len(pnls), 1) if pnls else None, "avg_pnl": round(sum(pnls) / len(pnls), 2) if pnls else None}
    by_exit_out = {}
    for b, pnls in by_exit.items():
        by_exit_out[b] = {"count": len(pnls), "win_rate_pct": round(100.0 * sum(1 for p in pnls if p > 0) / len(pnls), 1) if pnls else None, "avg_pnl": round(sum(pnls) / len(pnls), 2) if pnls else None}

    recommendations = []
    if win_rate is not None and win_rate < 50:
        recommendations.append("Win rate below 50%: consider tightening entry threshold (e.g. MIN_EXEC_SCORE) or improving exit timing (review v2_exit_score distribution vs PnL).")
    if by_entry_out.get("high_>=3.5"):
        hi = by_entry_out["high_>=3.5"]
        if hi.get("avg_pnl") is not None and hi["avg_pnl"] < 0:
            recommendations.append("High entry-score bucket (>=3.5) is losing on average: exits may be cutting winners too early or letting losers run; review exit signal weights and hold period.")
    if by_exit_out.get("missing", {}).get("count", 0) > len(trades) * 0.2:
        recommendations.append("Many trades have missing v2_exit_score: ensure exit_attribution is written on every full close (logs/exit_attribution.jsonl).")
    if not recommendations:
        recommendations.append("Baseline looks consistent. Consider: (1) regime-specific tuning, (2) per-symbol exit tuning, (3) adaptive weights review (state/signal_weights.json).")

    return {
        "win_rate_pct": win_rate,
        "total_pnl": round(total_pnl, 2),
        "trades_count": len(trades),
        "by_entry_bucket": by_entry_out,
        "by_exit_bucket": by_exit_out,
        "recommendations": recommendations,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Trading environment review on droplet")
    ap.add_argument("--last-n", type=int, default=DEFAULT_LAST_N, help="Last N trades to include")
    ap.add_argument("--days-health", type=int, default=7, help="Days for signal health window")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_md = OUT_DIR / f"TRADING_ENVIRONMENT_REVIEW_{date_str}.md"
    out_json = OUT_DIR / f"TRADING_ENVIRONMENT_REVIEW_{date_str}.json"

    trades = load_closed_trades_with_scores(ATTRIBUTION, EXIT_ATTR, args.last_n)
    health = signal_health(GATE_TRUTH, LEDGER, ORDERS, SUBMIT_CALLED, args.days_health)
    entry_signal_stats, exit_signal_stats = aggregate_signal_lists(trades)
    persona = persona_profitability_review(trades)

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "last_n": args.last_n,
        "trades_count": len(trades),
        "signal_health": health,
        "entry_signal_stats": entry_signal_stats,
        "exit_signal_stats": exit_signal_stats,
        "persona_profitability": persona,
        "trades": [
            {
                "symbol": t["symbol"],
                "timestamp": t["timestamp"],
                "entry_score": t["entry_score"],
                "v2_exit_score": t["v2_exit_score"],
                "pnl_usd": t["pnl_usd"],
                "close_reason": t["close_reason"],
                "entry_components": t["entry_components"],
                "v2_exit_components": t["v2_exit_components"],
            }
            for t in trades
        ],
    }
    out_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {out_json}")

    lines = [
        "# Trading environment review",
        "",
        f"Generated: {payload['generated_utc']}",
        f"Last **{args.last_n}** closed equity trades (from logs/attribution.jsonl + logs/exit_attribution.jsonl).",
        "",
        "## 1) Signal health (entry and exit signals firing)",
        "",
        f"- **Expectancy gate truth (last {args.days_health}d):** {health['gate_truth_lines']} lines",
        f"- **Decision ledger (last {args.days_health}d):** {health['ledger_lines']} lines",
        f"- **Orders filled (recent):** {health['orders_filled']}",
        f"- **Submit order called (recent):** {health['submit_called']}",
        "",
        "**Verdict:** Entry signals are firing if gate_truth and ledger have recent activity; exit signals are firing if exit_attribution has recent lines and trades below have v2_exit_score populated.",
        "",
        "## 2) Last 150 trades summary",
        "",
        f"- **Trades included:** {len(trades)}",
        f"- **With entry_score:** {sum(1 for t in trades if t.get('entry_score') is not None)}",
        f"- **With v2_exit_score:** {sum(1 for t in trades if t.get('v2_exit_score') is not None)}",
        "",
        "## 3) Full list of entry signal scores (component stats)",
        "",
    ]
    if entry_signal_stats:
        lines.append("| Signal | Count | Mean | Min | Max |")
        lines.append("|--------|-------|------|-----|-----|")
        for name, s in sorted(entry_signal_stats.items(), key=lambda x: -x[1]["count"]):
            lines.append(f"| {name} | {s['count']} | {s['mean']} | {s['min']} | {s['max']} |")
    else:
        lines.append("(No entry components found in attribution context.)")
    lines.extend([
        "",
        "## 4) Full list of exit signal scores (v2_exit_components stats)",
        "",
    ])
    if exit_signal_stats:
        lines.append("| Signal | Count | Mean | Min | Max |")
        lines.append("|--------|-------|------|-----|-----|")
        for name, s in sorted(exit_signal_stats.items(), key=lambda x: -x[1]["count"]):
            lines.append(f"| {name} | {s['count']} | {s['mean']} | {s['min']} | {s['max']} |")
    else:
        lines.append("(No v2_exit_components found; ensure exit_attribution is written on full closes.)")
    lines.extend([
        "",
        "## 5) Persona profitability review",
        "",
        f"- **Win rate:** {persona['win_rate_pct']}%",
        f"- **Total PnL (USD):** {persona['total_pnl']}",
        f"- **Trades count:** {persona['trades_count']}",
        "",
        "### By entry score bucket",
        "",
    ])
    for bucket, data in persona.get("by_entry_bucket", {}).items():
        lines.append(f"- **{bucket}:** count={data['count']}, win_rate={data['win_rate_pct']}%, avg_pnl={data['avg_pnl']}")
    lines.extend([
        "",
        "### By exit score bucket",
        "",
    ])
    for bucket, data in persona.get("by_exit_bucket", {}).items():
        lines.append(f"- **{bucket}:** count={data['count']}, win_rate={data['win_rate_pct']}%, avg_pnl={data['avg_pnl']}")
    lines.extend([
        "",
        "### How to get better",
        "",
    ])
    for rec in persona.get("recommendations", []):
        lines.append(f"- {rec}")
    lines.extend([
        "",
        "## 6) Full trade list (last 150 with scores)",
        "",
        "| # | Symbol | Timestamp | Entry score | Exit score | PnL USD | Close reason |",
        "|---|--------|-----------|-------------|------------|--------|--------------|",
    ])
    for i, t in enumerate(trades[:150], 1):
        es = t.get("entry_score")
        xs = t.get("v2_exit_score")
        es_str = f"{es:.2f}" if es is not None else "—"
        xs_str = f"{xs:.2f}" if xs is not None else "—"
        pnl = t.get("pnl_usd")
        pnl_str = f"{pnl:.2f}" if pnl is not None else "—"
        lines.append(f"| {i} | {t['symbol']} | {str(t['timestamp'])[:19]} | {es_str} | {xs_str} | {pnl_str} | {t.get('close_reason', '')[:20]} |")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_md}")

    print("")
    print("--- TERMINAL OUTPUT ---")
    print(f"Trades: {len(trades)} | Entry scores present: {sum(1 for t in trades if t.get('entry_score') is not None)} | Exit scores present: {sum(1 for t in trades if t.get('v2_exit_score') is not None)}")
    print(f"Signal health: gate_truth={health['gate_truth_lines']}, ledger={health['ledger_lines']}, filled={health['orders_filled']}")
    print(f"Win rate: {persona['win_rate_pct']}% | Total PnL: {persona['total_pnl']}")
    print("---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
