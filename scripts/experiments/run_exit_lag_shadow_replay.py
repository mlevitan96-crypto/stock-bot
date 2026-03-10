#!/usr/bin/env python3
"""
Exit-lag compression shadow replay. Run ON DROPLET.
Reads INTRADAY_EXIT_LAG_AND_GIVEBACK_<date>.json + exit_decision_trace (for Variant B).
Computes per-variant: realized PnL, max drawdown, win rate, tail loss, exit timing.
PAPER ONLY. No live exit logic or config changes.
Outputs: EXIT_LAG_SHADOW_RESULTS, EXIT_LAG_RISK_IMPACT, CSA_EXIT_LAG_VERDICT, EXIT_LAG_BOARD_PACKET.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXPERIMENTS = REPO / "reports" / "experiments"
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"
DATE_STR = "2026-03-09"


def _parse_ts(v) -> float | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).replace("Z", "+00:00").strip()
        if len(s) > 32:
            s = s[:32]
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return None


def _day_start_end(date_str: str) -> tuple[float, float]:
    try:
        start = datetime.fromisoformat(date_str + "T00:00:00+00:00").timestamp()
        end = datetime.fromisoformat(date_str + "T23:59:59.999999+00:00").timestamp()
        return start, end
    except Exception:
        return 0.0, 0.0


def _normalize_trade_id(tid: str) -> str:
    if not tid:
        return ""
    s = str(tid).strip()
    if s.startswith("live:"):
        parts = s.split(":", 2)
        if len(parts) >= 3:
            sym, iso = parts[1], parts[2]
            iso = iso.replace("+00:00", "Z").replace(" ", "T")
            if iso and not iso.endswith("Z") and "+" not in iso:
                iso = iso + "Z"
            return f"open_{sym}_{iso}"
    if not s.startswith("open_"):
        return s
    parts = s.split("_", 2)
    if len(parts) < 3:
        return s
    sym, iso = parts[1], parts[2]
    iso = str(iso).replace("+00:00", "Z").replace(" ", "T")
    if iso and not iso.endswith("Z") and "+" not in iso:
        iso = iso + "Z"
    return f"open_{sym}_{iso}"


def _load_trace_samples_by_trade(base: Path, date_str: str) -> dict[str, list[dict]]:
    """Load trace for date, group by normalized trade_id. Each sample has ts, unrealized_pnl."""
    trace_path = base / "reports" / "state" / "exit_decision_trace.jsonl"
    if not trace_path.exists():
        return {}
    start_ts, end_ts = _day_start_end(date_str)
    out = defaultdict(list)
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            ts = rec.get("ts") or rec.get("timestamp")
            t = _parse_ts(ts)
            if t is None or not (start_ts <= t <= end_ts):
                continue
            trade_id = rec.get("trade_id") or ""
            if not trade_id:
                continue
            key = _normalize_trade_id(trade_id)
            out[key].append({"ts": t, "unrealized_pnl": float(rec.get("unrealized_pnl") or 0)})
        except Exception:
            continue
    for k in out:
        out[k].sort(key=lambda x: x["ts"])
    return dict(out)


def _pnl_at_ts(samples: list[dict], target_ts: float) -> float | None:
    """First sample at or after target_ts; return unrealized_pnl. If no sample, None."""
    for s in samples:
        if s["ts"] >= target_ts:
            return s["unrealized_pnl"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Exit-lag shadow replay (paper only)")
    ap.add_argument("--date", default=DATE_STR)
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()
    date_str = args.date
    base = Path(args.base_dir) if args.base_dir else REPO
    EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    BOARD.mkdir(parents=True, exist_ok=True)

    lag_path = AUDIT / f"INTRADAY_EXIT_LAG_AND_GIVEBACK_{date_str}.json"
    if not lag_path.exists():
        print(f"BLOCKER: {lag_path} not found. Run forensic + surgical on droplet first.", file=sys.stderr)
        return 1

    data = json.loads(lag_path.read_text(encoding="utf-8"))
    trades = data.get("trades", [])
    if not trades:
        print("No trades in lag artifact.", file=sys.stderr)
        return 0

    trace_by_trade = _load_trace_samples_by_trade(base, date_str)

    variants = {
        "current": [],
        "A_first_eligibility": [],
        "B_persist_2m": [],
        "B_persist_5m": [],
        "B_persist_10m": [],
        "C_partial_50": [],
        "D_flow_reversal_only": [],
    }

    for t in trades:
        trade_id = t.get("trade_id")
        ts_exit = t.get("ts_exit")
        realized = float(t.get("realized_pnl_usd") or 0)
        first_ts = t.get("first_eligibility_ts")
        unrealized_first = t.get("unrealized_pnl_at_first_eligibility")
        first_firing = t.get("first_firing_condition")
        key = _normalize_trade_id(trade_id) if trade_id else ""
        samples = trace_by_trade.get(key, [])

        # Current (baseline)
        variants["current"].append({"trade_id": trade_id, "ts_exit": ts_exit, "pnl": realized})

        # A: exit at first eligibility
        pnl_a = unrealized_first if unrealized_first is not None else realized
        variants["A_first_eligibility"].append({"trade_id": trade_id, "ts_exit": first_ts if first_ts else ts_exit, "pnl": round(pnl_a, 4)})

        # B: exit at first_eligibility_ts + X min
        for x_min, name in [(2, "B_persist_2m"), (5, "B_persist_5m"), (10, "B_persist_10m")]:
            if first_ts and samples:
                target = first_ts + x_min * 60.0
                pnl_b = _pnl_at_ts(samples, target)
                if pnl_b is not None:
                    variants[name].append({"trade_id": trade_id, "ts_exit": target, "pnl": round(pnl_b, 4)})
                else:
                    variants[name].append({"trade_id": trade_id, "ts_exit": ts_exit, "pnl": realized})
            else:
                variants[name].append({"trade_id": trade_id, "ts_exit": ts_exit, "pnl": realized})

        # C: 50% at first eligibility, 50% at actual
        if unrealized_first is not None:
            pnl_c = 0.5 * unrealized_first + 0.5 * realized
            variants["C_partial_50"].append({"trade_id": trade_id, "ts_exit": ts_exit, "pnl": round(pnl_c, 4)})
        else:
            variants["C_partial_50"].append({"trade_id": trade_id, "ts_exit": ts_exit, "pnl": realized})

        # D: flow_reversal only early exit
        pnl_d = unrealized_first if (first_firing == "flow_reversal" and unrealized_first is not None) else realized
        variants["D_flow_reversal_only"].append({"trade_id": trade_id, "ts_exit": first_ts if (first_firing == "flow_reversal" and first_ts) else ts_exit, "pnl": round(pnl_d, 4)})

    def cum_drawdown(pnl_list: list[float], ts_list: list[float]) -> tuple[float, float]:
        order = sorted(range(len(pnl_list)), key=lambda i: (ts_list[i], i))
        cum = 0.0
        peak = 0.0
        max_dd = 0.0
        for i in order:
            cum += pnl_list[i]
            peak = max(peak, cum)
            max_dd = max(max_dd, peak - cum)
        return cum, max_dd

    results = {}
    for vname, rows in variants.items():
        pnls = [r["pnl"] for r in rows]
        ts_list = [r.get("ts_exit") or 0 for r in rows]
        total = sum(pnls)
        wins = sum(1 for p in pnls if p > 0)
        n = len(pnls)
        sorted_pnl = sorted(pnls)
        worst_5 = sorted_pnl[:5] if n >= 5 else sorted_pnl
        cum, max_dd = cum_drawdown(pnls, ts_list)
        results[vname] = {
            "total_realized_pnl_usd": round(total, 4),
            "max_drawdown_usd": round(max_dd, 4),
            "win_rate_pct": round(100.0 * wins / n, 2) if n else 0,
            "trade_count": n,
            "worst_5_trades_pnl": [round(x, 4) for x in worst_5],
            "tail_loss_sum": round(sum(worst_5), 4),
        }

    out = {
        "date": date_str,
        "mode": "paper_shadow_only",
        "variants": results,
        "current_baseline": results["current"],
    }
    (EXPERIMENTS / f"EXIT_LAG_SHADOW_RESULTS_{date_str}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Risk impact MD
    current_dd = results["current"]["max_drawdown_usd"]
    risk_lines = [
        "# Exit-Lag Risk Impact — " + date_str,
        "",
        "**Authority:** Droplet. Shadow only; no live change.",
        "",
        "## Drawdown vs current",
        "",
        f"- Current max drawdown (USD): {current_dd}",
        "",
    ]
    for vname, v in results.items():
        if vname == "current":
            continue
        dd = v["max_drawdown_usd"]
        diff = dd - current_dd
        flag = ""
        if diff > 5:
            flag = " — **FLAG: increased drawdown**"
        risk_lines.append(f"- **{vname}**: {dd} (Δ {diff:+.2f}){flag}")
    risk_lines.extend([
        "",
        "## Tail loss (worst 5 trades sum)",
        "",
    ])
    for vname, v in results.items():
        risk_lines.append(f"- **{vname}**: {v['tail_loss_sum']} USD")
    risk_lines.extend([
        "",
        "## Unacceptable risk patterns",
        "",
        "None identified if no variant increases drawdown by >$5 or amplifies tail loss materially. Review worst_5_trades for whipsaw/premature exits.",
        "",
    ])
    (EXPERIMENTS / f"EXIT_LAG_RISK_IMPACT_{date_str}.md").write_text("\n".join(risk_lines), encoding="utf-8")

    # CSA verdict
    best_total = max(results[k]["total_realized_pnl_usd"] for k in results)
    best_name = next(k for k in results if results[k]["total_realized_pnl_usd"] == best_total)
    current_total = results["current"]["total_realized_pnl_usd"]
    improvement = best_total - current_total
    current_tail = results["current"]["tail_loss_sum"]
    best_tail = results[best_name]["tail_loss_sum"]
    robust = "robust" if improvement >= 50 else "fragile"
    reduces_tail = best_name if (best_tail > current_tail) else None
    promotable = best_name if (improvement > 50 and results[best_name]["max_drawdown_usd"] <= current_dd + 10) else None
    recommendation = "reject_variants" if improvement < 0 else ("limited_paper_ab" if (improvement >= 50 and results[best_name]["max_drawdown_usd"] <= current_dd + 10) else "continue_shadow")
    verdict = {
        "date": date_str,
        "variant_improves_expectancy": best_name,
        "improvement_usd": round(improvement, 4),
        "current_realized_usd": round(current_total, 4),
        "best_shadow_realized_usd": round(best_total, 4),
        "improvement_robust_or_fragile": robust,
        "variant_reduces_tail_risk": reduces_tail,
        "promotable_to_limited_paper_ab": promotable,
        "recommendation": recommendation,
    }
    (AUDIT / f"CSA_EXIT_LAG_VERDICT_{date_str}.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")

    # Board packet
    board_lines = [
        "# Exit-Lag Board Packet — " + date_str,
        "",
        "## Summary of shadow results",
        "",
        f"- Current realized PnL (USD): {current_total}",
        f"- Best variant: **{best_name}** (shadow realized: {best_total} USD, Δ {improvement:+.2f})",
        f"- Max drawdown current: {current_dd} USD; best variant: {results[best_name]['max_drawdown_usd']} USD",
        "",
        "## Recommended next step",
        "",
        verdict["recommendation"].replace("_", " ").title() + ".",
        "",
        "## Non-actions",
        "",
        "- Do not promote any variant to live.",
        "- Do not change production exit config without explicit CSA + board approval.",
        "- Paper A/B (if any) remains limited and gated.",
        "",
    ]
    (BOARD / f"EXIT_LAG_BOARD_PACKET_{date_str}.md").write_text("\n".join(board_lines), encoding="utf-8")

    print("Wrote EXIT_LAG_SHADOW_RESULTS, EXIT_LAG_RISK_IMPACT, CSA_EXIT_LAG_VERDICT, EXIT_LAG_BOARD_PACKET for", date_str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
