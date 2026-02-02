#!/usr/bin/env python3
"""
Unified Daily Intelligence Pack — Equity + Wheel + Profitability.

Creates reports/stockbot/YYYY-MM-DD/ with 9 files:
  1. STOCK_EOD_SUMMARY.md / .json
  2. STOCK_EQUITY_ATTRIBUTION.jsonl
  3. STOCK_WHEEL_ATTRIBUTION.jsonl
  4. STOCK_BLOCKED_TRADES.jsonl
  5. STOCK_PROFITABILITY_DIAGNOSTICS.md / .json
  6. STOCK_REGIME_AND_UNIVERSE.json
  7. MEMORY_BANK_SNAPSHOT.md

NO engine changes. Uses canonical fields per MEMORY_BANK.

Run: python scripts/run_stockbot_daily_reports.py [--date YYYY-MM-DD] [--base-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Canonical wheel fields per MEMORY_BANK §2.2.1
WHEEL_FIELDS = ["strategy_id", "phase", "option_type", "strike", "expiry", "dte", "delta_at_entry", "premium", "assigned", "called_away"]

# Blocked trade reason prefixes
BLOCKED_PREFIXES = ["displacement_blocked", "expectancy_blocked", "volatility_blocked", "risk_blocked"]


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else ""


def _iter_jsonl(path: Path) -> List[dict]:
    out: List[dict] = []
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


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else (default or {})
    except Exception:
        return default if default is not None else {}


def _load_equity_attribution(base: Path, day: str) -> List[dict]:
    attr = _iter_jsonl(base / "logs" / "attribution.jsonl")
    return [r for r in attr if _day_utc(str(r.get("ts") or r.get("timestamp") or "")) == day and (r.get("strategy_id") or "equity") == "equity"]


def _load_wheel_attribution(base: Path, day: str) -> List[dict]:
    telem = _iter_jsonl(base / "logs" / "telemetry.jsonl")
    wheel_telem = [r for r in telem if (r.get("strategy_id") or "") == "wheel" and _day_utc(str(r.get("_dt") or r.get("ts") or r.get("timestamp") or "")) == day]
    attr = _iter_jsonl(base / "logs" / "attribution.jsonl")
    wheel_attr = [r for r in attr if (r.get("strategy_id") or "") == "wheel" and _day_utc(str(r.get("ts") or r.get("timestamp") or "")) == day]
    seen = set()
    out: List[dict] = []
    for r in wheel_telem + wheel_attr:
        key = (r.get("symbol"), r.get("ts") or r.get("timestamp"), r.get("trade_id"))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return sorted(out, key=lambda x: str(x.get("ts") or x.get("timestamp") or ""))


def _load_blocked_trades(base: Path, day: str) -> List[dict]:
    raw = _iter_jsonl(base / "state" / "blocked_trades.jsonl")
    return [r for r in raw if _day_utc(str(r.get("ts") or r.get("timestamp") or "")) == day]


def _load_regime_universe(base: Path, day: str) -> dict:
    v2 = _load_json(base / "state" / "daily_universe_v2.json", {})
    symbols = v2.get("symbols") if isinstance(v2.get("symbols"), list) else []
    regime = v2.get("regime_label") or v2.get("regime") or "UNKNOWN"
    sectors = list(set(s.get("context", {}).get("sector", "UNKNOWN") for s in symbols if isinstance(s, dict) and isinstance(s.get("context"), dict)))
    return {
        "date": day,
        "regime": regime,
        "sectors": sectors,
        "symbol_count": len(symbols),
        "symbols": [s.get("symbol") for s in symbols[:50] if isinstance(s, dict)],
        "dispersion": v2.get("dispersion"),
        "volatility_bucket": v2.get("volatility_bucket"),
    }


def _build_eod_summary(base: Path, day: str, equity_attr: List[dict], wheel_attr: List[dict], blocked: List[dict], regime: dict) -> tuple[dict, str]:
    eq_pnl = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in equity_attr)
    wh_pnl = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in wheel_attr)
    total_pnl = eq_pnl + wh_pnl
    eq_wins = sum(1 for r in equity_attr if float(r.get("pnl_usd") or r.get("pnl") or 0) > 0)
    eq_total = len(equity_attr)
    win_rate = (eq_wins / eq_total * 100) if eq_total > 0 else 0
    exit_reasons: Dict[str, int] = defaultdict(int)
    for r in equity_attr + wheel_attr:
        reason = r.get("close_reason") or r.get("exit_reason") or "unknown"
        exit_reasons[reason] += 1
    top_exits = sorted(exit_reasons.items(), key=lambda x: -x[1])[:5]

    blocked_by_reason: Dict[str, int] = defaultdict(int)
    for r in blocked:
        reason = str(r.get("reason") or r.get("blocked_reason") or "unknown")
        for p in BLOCKED_PREFIXES:
            if p in reason or reason.startswith(p):
                blocked_by_reason[p] += 1
                break
        else:
            blocked_by_reason[reason] += 1

    data = {
        "date": day,
        "total_pnl_usd": round(total_pnl, 2),
        "equity_pnl_usd": round(eq_pnl, 2),
        "wheel_pnl_usd": round(wh_pnl, 2),
        "win_rate_pct": round(win_rate, 2),
        "regime": regime.get("regime", "UNKNOWN"),
        "sectors": regime.get("sectors", []),
        "equity_expectancy": round(eq_pnl / eq_total, 2) if eq_total > 0 else None,
        "wheel_expectancy": round(wh_pnl / len(wheel_attr), 2) if wheel_attr else None,
        "top_exit_reasons": dict(top_exits),
        "blocked_by_reason": dict(blocked_by_reason),
        "high_level_recommendations": [],
        "falsification_criteria": [],
    }
    md = f"""# Stock EOD Summary — {day}

- **Total PnL:** ${data['total_pnl_usd']:.2f} (Equity: ${data['equity_pnl_usd']:.2f}, Wheel: ${data['wheel_pnl_usd']:.2f})
- **Win Rate:** {data['win_rate_pct']}%
- **Regime:** {data['regime']}
- **Sectors:** {', '.join(data['sectors'][:10]) or 'N/A'}
- **Top Exit Reasons:** {dict(top_exits)}
- **Blocked by Reason:** {dict(blocked_by_reason)}
"""
    return data, md


def _build_profitability_diagnostics(base: Path, day: str, equity_attr: List[dict], wheel_attr: List[dict]) -> tuple[dict, str]:
    eq_by_sym: Dict[str, List[float]] = defaultdict(list)
    wh_by_sym: Dict[str, List[float]] = defaultdict(list)
    for r in equity_attr:
        sym = r.get("symbol") or "?"
        eq_by_sym[sym].append(float(r.get("pnl_usd") or r.get("pnl") or 0))
    for r in wheel_attr:
        sym = r.get("symbol") or "?"
        wh_by_sym[sym].append(float(r.get("pnl_usd") or r.get("pnl") or 0))

    expectancy_per_symbol = {}
    for sym, pnls in eq_by_sym.items():
        expectancy_per_symbol[sym] = round(sum(pnls) / len(pnls), 2) if pnls else 0
    for sym, pnls in wh_by_sym.items():
        if sym not in expectancy_per_symbol:
            expectancy_per_symbol[sym] = 0
        expectancy_per_symbol[sym] = round(expectancy_per_symbol[sym] + (sum(pnls) / len(pnls) if pnls else 0), 2)

    eq_exp = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in equity_attr) / len(equity_attr) if equity_attr else 0
    wh_exp = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in wheel_attr) / len(wheel_attr) if wheel_attr else 0

    data = {
        "date": day,
        "expectancy_per_symbol": expectancy_per_symbol,
        "expectancy_per_strategy": {"equity": round(eq_exp, 2), "wheel": round(wh_exp, 2)},
        "mae_mfe_distributions": {},
        "exit_efficiency_pct": None,
        "stop_efficiency_pct": None,
        "volatility_buckets": {},
        "shadow_vs_live_expectancy_delta": None,
        "top_10_actionable_insights": [],
    }
    try:
        eq_path = base / "telemetry" / day / "computed" / "exit_quality_summary.json"
        if eq_path.exists():
            eqq = _load_json(eq_path, {})
            if isinstance(eqq, dict):
                data["exit_efficiency_pct"] = eqq.get("exit_efficiency_pct")
                data["stop_efficiency_pct"] = eqq.get("stop_efficiency_pct")
                data["mae_mfe_distributions"] = eqq.get("mae_mfe", {}) or {}
    except Exception:
        pass

    md = f"""# Stock Profitability Diagnostics — {day}

- **Expectancy per symbol:** {json.dumps(expectancy_per_symbol)[:500]}...
- **Equity expectancy:** {eq_exp:.2f}
- **Wheel expectancy:** {wh_exp:.2f}
- **Exit efficiency:** {data['exit_efficiency_pct']}
- **Stop efficiency:** {data['stop_efficiency_pct']}
"""
    return data, md


def _build_memory_bank_snapshot(day: str, eod: dict, prof: dict, regime: dict, equity_attr: List[dict], wheel_attr: List[dict], blocked: List[dict]) -> str:
    lines = [
        f"## Memory Bank Snapshot — {day}",
        "",
        "### Symbol Expectancy",
        json.dumps(prof.get("expectancy_per_symbol", {}), indent=2),
        "",
        "### Wheel Expectancy",
        str(prof.get("expectancy_per_strategy", {}).get("wheel")),
        "",
        "### Volatility-Conditioned Performance",
        f"Regime: {regime.get('regime', 'N/A')}",
        "",
        "### Exit Efficiency Patterns",
        f"Exit efficiency: {prof.get('exit_efficiency_pct')}",
        f"Stop efficiency: {prof.get('stop_efficiency_pct')}",
        "",
        "### Blocked Trade Patterns",
        json.dumps(eod.get("blocked_by_reason", {}), indent=2),
        "",
        "### Governance Notes",
        f"Equity trades: {len(equity_attr)}, Wheel trades: {len(wheel_attr)}, Blocked: {len(blocked)}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Unified Daily Intelligence Pack")
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    ap.add_argument("--base-dir", default="", help="Repo root (default: script parent)")
    args = ap.parse_args()
    day = args.date.strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = Path(args.base_dir) if args.base_dir else ROOT

    out_dir = base / "reports" / "stockbot" / day
    out_dir.mkdir(parents=True, exist_ok=True)

    equity_attr = _load_equity_attribution(base, day)
    wheel_attr = _load_wheel_attribution(base, day)
    blocked = _load_blocked_trades(base, day)
    regime = _load_regime_universe(base, day)

    eod_data, eod_md = _build_eod_summary(base, day, equity_attr, wheel_attr, blocked, regime)
    prof_data, prof_md = _build_profitability_diagnostics(base, day, equity_attr, wheel_attr)

    (out_dir / "STOCK_EOD_SUMMARY.json").write_text(json.dumps(eod_data, indent=2, default=str), encoding="utf-8")
    (out_dir / "STOCK_EOD_SUMMARY.md").write_text(eod_md, encoding="utf-8")

    with (out_dir / "STOCK_EQUITY_ATTRIBUTION.jsonl").open("w", encoding="utf-8") as f:
        for r in equity_attr:
            f.write(json.dumps(r, default=str) + "\n")

    with (out_dir / "STOCK_WHEEL_ATTRIBUTION.jsonl").open("w", encoding="utf-8") as f:
        for r in wheel_attr:
            f.write(json.dumps(r, default=str) + "\n")

    with (out_dir / "STOCK_BLOCKED_TRADES.jsonl").open("w", encoding="utf-8") as f:
        for r in blocked:
            f.write(json.dumps(r, default=str) + "\n")

    (out_dir / "STOCK_PROFITABILITY_DIAGNOSTICS.json").write_text(json.dumps(prof_data, indent=2, default=str), encoding="utf-8")
    (out_dir / "STOCK_PROFITABILITY_DIAGNOSTICS.md").write_text(prof_md, encoding="utf-8")

    (out_dir / "STOCK_REGIME_AND_UNIVERSE.json").write_text(json.dumps(regime, indent=2, default=str), encoding="utf-8")

    mb_snap = _build_memory_bank_snapshot(day, eod_data, prof_data, regime, equity_attr, wheel_attr, blocked)
    (out_dir / "MEMORY_BANK_SNAPSHOT.md").write_text(mb_snap, encoding="utf-8")

    print(f"Wrote 9 files to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
