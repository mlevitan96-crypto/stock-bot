#!/usr/bin/env python3
"""
SRE: Total system lock diagnostics — SIP/REST bar reachability + ML flattener smoke.

Usage (repo root):
  PYTHONPATH=. python scripts/sre/system_lock_diagnostics.py --root .
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _probe_alpaca_bars(root: Path) -> dict:
    out: dict = {"ok": False, "error": None, "last_bar_utc": None, "n_bars": 0}
    try:
        from dotenv import load_dotenv

        load_dotenv(root / ".env")
    except Exception:
        pass
    try:
        from config.registry import get_alpaca_trading_credentials

        k, s, base = get_alpaca_trading_credentials()
        if not k or not s:
            out["error"] = "missing_alpaca_credentials"
            return out
        from alpaca_trade_api.rest import REST

        api = REST(k, s, base_url=base or "https://paper-api.alpaca.markets")
        barset = api.get_bars("SPY", "1Min", limit=5)
        df = getattr(barset, "df", None)
        if df is None or len(df) == 0:
            out["error"] = "empty_bar_df"
            return out
        last = df.index[-1]
        last_dt = last.to_pydatetime() if hasattr(last, "to_pydatetime") else last
        if getattr(last_dt, "tzinfo", None) is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        else:
            last_dt = last_dt.astimezone(timezone.utc)
        age_min = (datetime.now(timezone.utc) - last_dt).total_seconds() / 60.0
        out["ok"] = True
        out["last_bar_utc"] = last_dt.isoformat()
        out["n_bars"] = int(len(df))
        out["age_minutes"] = round(age_min, 2)
    except Exception as e:
        out["error"] = str(e)[:400]
    return out


def _flattener_smoke(root: Path) -> dict:
    out: dict = {"ok": False, "csv": None, "error": None, "bytes": 0}
    csv_path = root / "artifacts" / "ml" / "_system_lock_flattener_smoke.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cmd = [
            sys.executable,
            str(root / "scripts" / "telemetry" / "alpaca_ml_flattener.py"),
            "--root",
            str(root),
            "--out",
            str(csv_path),
        ]
        r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            out["error"] = (r.stderr or r.stdout or "flattener_nonzero_exit")[:800]
            return out
        if not csv_path.is_file():
            out["error"] = "csv_missing"
            return out
        out["ok"] = True
        out["csv"] = str(csv_path)
        out["bytes"] = csv_path.stat().st_size
    except Exception as e:
        out["error"] = str(e)[:400]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="System lock diagnostics (bars + flattener smoke).")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    args = ap.parse_args()
    root = args.root.resolve()
    bars = _probe_alpaca_bars(root)
    flat = _flattener_smoke(root)
    print(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "root": str(root),
            "bars": bars,
            "flattener_smoke": flat,
            "run_jsonl": (root / "logs" / "run.jsonl").is_file(),
            "exit_attribution_jsonl": (root / "logs" / "exit_attribution.jsonl").is_file(),
        },
        flush=True,
    )
    return 0 if bars.get("ok") and flat.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
