#!/usr/bin/env python3
"""
Alpaca Quant Lab — Phase 4 Profit Discovery (combinatorial strategies, path-real PnL).
Run 30–60 min; outputs ALPACA_PROFIT_LAB_RAW_RESULTS.json and ALPACA_PROFIT_LAB_RANKED.md.
READ-ONLY: no live or paper execution changes.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "reports" / "audit"


def load_trades_frozen(csv_path: Path) -> list[dict]:
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(dict(r))
    return rows


def strategy_id(filters: dict) -> str:
    parts = [f"{k}={v}" for k, v in sorted(filters.items()) if v]
    return "|".join(parts) if parts else "all"


def run_profit_lab(
    frozen_csv: Path,
    out_raw: Path,
    out_ranked: Path,
    max_strategies: int = 5000,
) -> None:
    if not frozen_csv.exists():
        print(f"Missing {frozen_csv}", file=sys.stderr)
        sys.exit(1)
    rows = load_trades_frozen(frozen_csv)
    if not rows:
        print("No rows in TRADES_FROZEN", file=sys.stderr)
        sys.exit(1)

    strategies: dict[str, dict] = {}
    # 1) Full universe
    pnls = [float(r.get("realized_pnl_usd", 0) or 0) for r in rows]
    n = len(pnls)
    total = sum(pnls)
    strategies["all"] = {
        "strategy_id": "all",
        "filters": {},
        "total_pnl": round(total, 4),
        "trades": n,
        "expectancy": round(total / n, 6) if n else 0,
    }

    # 2) By entry_regime
    by_regime: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        reg = (r.get("entry_regime") or "unknown").strip() or "unknown"
        p = float(r.get("realized_pnl_usd", 0) or 0)
        by_regime[reg].append(p)
    for reg, pnls_r in by_regime.items():
        if len(pnls_r) < 5:
            continue
        sid = strategy_id({"entry_regime": reg})
        strategies[sid] = {
            "strategy_id": sid,
            "filters": {"entry_regime": reg},
            "total_pnl": round(sum(pnls_r), 4),
            "trades": len(pnls_r),
            "expectancy": round(sum(pnls_r) / len(pnls_r), 6),
        }

    # 3) By exit_regime
    by_exit_regime: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        reg = (r.get("exit_regime") or "unknown").strip() or "unknown"
        p = float(r.get("realized_pnl_usd", 0) or 0)
        by_exit_regime[reg].append(p)
    for reg, pnls_r in by_exit_regime.items():
        if len(pnls_r) < 5:
            continue
        sid = strategy_id({"exit_regime": reg})
        if sid not in strategies:
            strategies[sid] = {
                "strategy_id": sid,
                "filters": {"exit_regime": reg},
                "total_pnl": round(sum(pnls_r), 4),
                "trades": len(pnls_r),
                "expectancy": round(sum(pnls_r) / len(pnls_r), 6),
            }

    # 4) By side
    for side in ("long", "short"):
        subset = [float(r.get("realized_pnl_usd", 0) or 0) for r in rows if (r.get("side") or "").strip().lower() == side]
        if len(subset) < 5:
            continue
        sid = strategy_id({"side": side})
        strategies[sid] = {
            "strategy_id": sid,
            "filters": {"side": side},
            "total_pnl": round(sum(subset), 4),
            "trades": len(subset),
            "expectancy": round(sum(subset) / len(subset), 6),
        }

    # 5) By entry_regime + side (combo)
    for reg, pnls_r in by_regime.items():
        if len(pnls_r) < 10:
            continue
        for side in ("long", "short"):
            subset = [
                float(r.get("realized_pnl_usd", 0) or 0)
                for r in rows
                if ((r.get("entry_regime") or "").strip() or "unknown") == reg
                and (r.get("side") or "").strip().lower() == side
            ]
            if len(subset) < 5:
                continue
            sid = strategy_id({"entry_regime": reg, "side": side})
            strategies[sid] = {
                "strategy_id": sid,
                "filters": {"entry_regime": reg, "side": side},
                "total_pnl": round(sum(subset), 4),
                "trades": len(subset),
                "expectancy": round(sum(subset) / len(subset), 6),
            }

    list_strategies = list(strategies.values())
    by_pnl = sorted(list_strategies, key=lambda x: x["total_pnl"], reverse=True)[:20]
    by_exp = sorted(list_strategies, key=lambda x: x["expectancy"], reverse=True)[:20]

    raw = {
        "_meta": {
            "mission": "ALPACA_QUANT_CAUSALITY_PROFIT_DISCOVERY",
            "phase": 4,
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_source": str(frozen_csv),
        },
        "strategies": list_strategies,
        "summary": {
            "total_strategies_evaluated": len(list_strategies),
            "total_pnl": 0.0,
            "top_by_pnl": by_pnl,
            "top_by_expectancy": by_exp,
            "deduplicated_count": len(list_strategies),
        },
    }
    # Fix summary total_pnl: use "all" strategy
    if "all" in strategies:
        raw["summary"]["total_pnl"] = strategies["all"]["total_pnl"]

    out_raw.parent.mkdir(parents=True, exist_ok=True)
    with open(out_raw, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, default=str)

    with open(out_ranked, "w", encoding="utf-8") as f:
        f.write("# Alpaca Profit Lab — Ranked Strategies (Phase 4)\n\n")
        f.write("**Generated:** " + raw["_meta"]["generated_at"] + "\n\n")
        f.write("## Ranked by Total PnL (Top 20)\n\n")
        f.write("| Rank | Strategy ID | Filters | Total PnL | Trades | Expectancy |\n")
        f.write("|------|-------------|---------|-----------|--------|------------|\n")
        for i, s in enumerate(by_pnl, 1):
            flt = json.dumps(s.get("filters", {}))
            f.write(f"| {i} | {s['strategy_id']} | {flt} | {s['total_pnl']} | {s['trades']} | {s['expectancy']} |\n")
        f.write("\n## Ranked by Expectancy (Top 20)\n\n")
        f.write("| Rank | Strategy ID | Expectancy | Trades | Total PnL |\n")
        f.write("|------|-------------|------------|--------|------------|\n")
        for i, s in enumerate(by_exp, 1):
            f.write(f"| {i} | {s['strategy_id']} | {s['expectancy']} | {s['trades']} | {s['total_pnl']} |\n")
    print(f"Wrote {out_raw} and {out_ranked}")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Alpaca Profit Lab Phase 4 — combinatorial strategies, path-real PnL")
    ap.add_argument("--frozen-csv", type=Path, default=None, help="Path to TRADES_FROZEN.csv (default: latest report dir)")
    ap.add_argument("--out-raw", type=Path, default=AUDIT / "ALPACA_PROFIT_LAB_RAW_RESULTS.json", help="Output JSON")
    ap.add_argument("--out-ranked", type=Path, default=AUDIT / "ALPACA_PROFIT_LAB_RANKED.md", help="Output ranked MD")
    args = ap.parse_args()
    frozen = args.frozen_csv
    if not frozen:
        reports = REPO / "reports"
        candidates = sorted(reports.glob("alpaca_edge_*"), key=lambda p: p.stat().st_mtime, reverse=True)
        for d in candidates:
            c = d / "TRADES_FROZEN.csv"
            if c.exists():
                frozen = c
                break
        if not frozen:
            print("No TRADES_FROZEN.csv found under reports/alpaca_edge_*", file=sys.stderr)
            return 1
    run_profit_lab(frozen, args.out_raw, args.out_ranked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
