#!/usr/bin/env python3
"""
B1 — DATA DISCOVERY (EQUITY).
Locate historical equity trade logs, truth datasets, attribution, exit_attribution, bar data.
Writes reports/replay/equity_data_manifest.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    manifest = {
        "strategy": "equity",
        "repo": str(REPO),
        "sources": {},
        "paths": {},
    }

    # Logs (attribution, exit_attribution) — equity trades when strategy_id not set or equity
    logs = REPO / "logs"
    for name, f in [
        ("attribution", logs / "attribution.jsonl"),
        ("exit_attribution", logs / "exit_attribution.jsonl"),
    ]:
        manifest["paths"][name] = str(f)
        manifest["sources"][name] = {"path": str(f), "exists": f.exists(), "description": f"Live equity trade {name}"}

    # Truth root (droplet: STOCKBOT_TRUTH_ROOT; local may have reports or var)
    truth_candidates = [
        REPO / "reports" / "truth",
        REPO / "var" / "lib" / "stock-bot" / "truth",
        Path("/var/lib/stock-bot/truth"),
    ]
    truth_picked = truth_candidates[0]
    for p in truth_candidates:
        if p.exists():
            truth_picked = p
            break
    manifest["paths"]["truth_root"] = str(truth_picked)
    manifest["sources"]["truth_root"] = {"path": str(truth_picked), "exists": truth_picked.exists()}

    # Effectiveness / blame outputs (from run_effectiveness_reports)
    eff_dirs = list((REPO / "reports").glob("effectiveness_*")) + list((REPO / "reports").glob("**/effectiveness_baseline_blame"))
    manifest["paths"]["effectiveness_dirs"] = [str(d) for d in eff_dirs[:20]]
    manifest["sources"]["effectiveness"] = {"dirs_sample": manifest["paths"]["effectiveness_dirs"], "description": "Effectiveness report dirs (aggregates, blame, signal/exit)"}

    # Bar data (OHLCV for replay)
    bars = REPO / "data" / "bars"
    manifest["paths"]["bars_dir"] = str(bars)
    manifest["sources"]["bars"] = {"path": str(bars), "exists": bars.exists(), "description": "OHLCV bars for price paths"}

    # Backtest dirs (historical equity runs)
    backtests = list((REPO / "backtests").glob("*")) if (REPO / "backtests").exists() else []
    manifest["paths"]["backtest_dirs"] = [str(d) for d in backtests[:30]]
    manifest["sources"]["backtests"] = {"dirs_sample": manifest["paths"]["backtest_dirs"], "description": "Backtest output dirs (exits, attribution)"}

    out = REPO / "reports" / "replay" / "equity_data_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
