#!/usr/bin/env python3
"""
Validate backtest run artifacts per contract: config, provenance, metrics, trades, summary.
Writes to reports/governance/<RUN_ID>. Exit non-zero on FAIL.
Usage: python scripts/backtest_governance_check.py --backtest-dir reports/backtests/<RUN_ID> --governance-out reports/governance/<RUN_ID>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest-dir", required=True, help="Backtest run dir (e.g. reports/backtests/alpaca_backtest_<ts>)")
    ap.add_argument("--governance-out", required=True, help="Governance output dir (e.g. reports/governance/<RUN_ID>)")
    args = ap.parse_args()
    base = Path(args.backtest_dir)
    if not base.is_absolute():
        base = REPO / base
    gov_out = Path(args.governance_out)
    if not gov_out.is_absolute():
        gov_out = REPO / gov_out
    gov_out.mkdir(parents=True, exist_ok=True)

    failures = []
    # Required: provenance
    prov = base / "provenance.json"
    if not prov.exists() or prov.stat().st_size == 0:
        failures.append("provenance.json missing or empty")
    # Required: config (config.json or config_used.json or baseline has backtest_summary with config)
    cfg = base / "config.json"
    if not cfg.exists():
        cfg = base / "config_used.json"
    if not cfg.exists():
        s = base / "baseline" / "backtest_summary.json"
        if s.exists():
            try:
                d = json.loads(s.read_text(encoding="utf-8"))
                if d.get("config"):
                    cfg = base / "config_from_baseline.json"
                    cfg.write_text(json.dumps(d["config"], indent=2), encoding="utf-8")
            except Exception:
                pass
    if not cfg.exists() or cfg.stat().st_size == 0:
        failures.append("config.json / config_used.json missing or empty")
    # Required: metrics (metrics.json or baseline/backtest_summary.json)
    metrics = base / "metrics.json"
    if not metrics.exists():
        m2 = base / "baseline" / "backtest_summary.json"
        if m2.exists():
            metrics = m2
    if not metrics.exists() or metrics.stat().st_size == 0:
        failures.append("metrics.json or baseline/backtest_summary.json missing or empty")
    # Required: trades (trades.csv or baseline/backtest_trades.jsonl); empty OK (0 trades)
    trades = base / "trades.csv"
    if not trades.exists():
        t2 = base / "baseline" / "backtest_trades.jsonl"
        if t2.exists():
            trades = t2
    if not trades.exists():
        failures.append("trades.csv or baseline/backtest_trades.jsonl missing")
    # Required: summary.md (run dir root or summary/summary.md)
    summary = base / "summary.md"
    if not summary.exists() or summary.stat().st_size == 0:
        summary = base / "summary" / "summary.md"
    if not summary.exists() or summary.stat().st_size == 0:
        failures.append("summary.md missing or empty (check run dir or summary/summary.md)")

    verdict = "PASS" if not failures else "FAIL"
    report = {
        "verdict": verdict,
        "backtest_dir": str(base),
        "failures": failures,
        "checks": {
            "provenance": prov.exists() and prov.stat().st_size > 0,
            "config": (cfg.exists() and cfg.stat().st_size > 0) if cfg else False,
            "metrics": metrics.exists() and metrics.stat().st_size > 0,
            "trades": trades.exists() and trades.stat().st_size > 0,
            "summary_md": summary.exists() and summary.stat().st_size > 0,
        },
    }
    gov_report = gov_out / "backtest_governance_report.json"
    gov_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Backtest governance: {verdict}")
    for f in failures:
        print(f"  - {f}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
