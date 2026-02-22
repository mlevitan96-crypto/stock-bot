#!/usr/bin/env python3
"""
Execution sensitivity: run baseline simulation with different slippage multipliers (0x, 1x, 2x)
and record net_pnl and win_rate per multiplier. Writes exec_sensitivity.json.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--slippage-multipliers", default="0.0,1.0,2.0")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    mult_str = getattr(args, "slippage_multipliers", "0.0,1.0,2.0")
    mults = [float(x.strip()) for x in mult_str.split(",") if x.strip()]

    results = []
    for mult in mults:
        subdir = out_dir / ("slippage_" + str(mult))
        subdir.mkdir(parents=True, exist_ok=True)
        cfg_path = REPO / (args.config or "configs/backtest_config.json")
        if not cfg_path.exists():
            cfg = {"lab_mode": True, "min_exec_score": 1.8, "slippage_model": {"type": "pct", "value": 0.0005 * mult}}
        else:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            base_val = (cfg.get("slippage_model") or {}).get("value", 0.0005)
            cfg["slippage_model"] = {"type": "pct", "value": base_val * mult}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cfg, f, indent=2)
            tmp_cfg = f.name
        try:
            cmd = [
                sys.executable,
                "scripts/run_simulation_backtest_on_droplet.py",
                "--bars", args.bars or "",
                "--config", tmp_cfg,
                "--out", str(subdir),
                "--lab-mode",
                "--min-exec-score", "1.8",
            ]
            r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=600)
            metrics_path = subdir / "metrics.json"
            if metrics_path.exists():
                m = json.loads(metrics_path.read_text(encoding="utf-8"))
                results.append({
                    "slippage_multiplier": mult,
                    "net_pnl": m.get("net_pnl"),
                    "win_rate_pct": m.get("win_rate_pct"),
                    "trades_count": m.get("trades_count"),
                })
            else:
                results.append({"slippage_multiplier": mult, "error": "no metrics.json"})
        finally:
            try:
                os.unlink(tmp_cfg)
            except Exception:
                pass

    out = {"slippage_multipliers": mults, "runs": results, "status": "ok"}
    (out_dir / "exec_sensitivity.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Exec sensitivity ->", str(out_dir / "exec_sensitivity.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
