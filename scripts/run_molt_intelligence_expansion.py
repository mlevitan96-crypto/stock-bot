#!/usr/bin/env python3
"""
Molt Intelligence Expansion — load unified daily pack, run Molt workflow.

Loads reports/stockbot/YYYY-MM-DD/ and provides:
- load_wheel_attribution()
- load_equity_attribution()
- load_profitability_diagnostics()
- load_blocked_trades()
- load_regime_universe()

Generates/ensures STOCK_EOD_SUMMARY, STOCK_PROFITABILITY_DIAGNOSTICS, MEMORY_BANK_SNAPSHOT.
Moltbot reads raw attribution, wheel attribution, profitability diagnostics, blocked trades,
regime/universe, and writes its own conclusions.

Run: python scripts/run_molt_intelligence_expansion.py [--date YYYY-MM-DD] [--base-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else (default or {})
    except Exception:
        return default if default is not None else {}


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


def load_equity_attribution(base: Path, day: str) -> List[dict]:
    """Load equity attribution from daily pack or logs."""
    pack_path = base / "reports" / "stockbot" / day / "STOCK_EQUITY_ATTRIBUTION.jsonl"
    if pack_path.exists():
        return _iter_jsonl(pack_path)
    from scripts.run_stockbot_daily_reports import _load_equity_attribution
    return _load_equity_attribution(base, day)


def load_wheel_attribution(base: Path, day: str) -> List[dict]:
    """Load wheel attribution from daily pack or logs."""
    pack_path = base / "reports" / "stockbot" / day / "STOCK_WHEEL_ATTRIBUTION.jsonl"
    if pack_path.exists():
        return _iter_jsonl(pack_path)
    from scripts.run_stockbot_daily_reports import _load_wheel_attribution
    return _load_wheel_attribution(base, day)


def load_profitability_diagnostics(base: Path, day: str) -> dict:
    """Load profitability diagnostics from daily pack."""
    pack_path = base / "reports" / "stockbot" / day / "STOCK_PROFITABILITY_DIAGNOSTICS.json"
    return _load_json(pack_path, {})


def load_blocked_trades(base: Path, day: str) -> List[dict]:
    """Load blocked trades from daily pack or state."""
    pack_path = base / "reports" / "stockbot" / day / "STOCK_BLOCKED_TRADES.jsonl"
    if pack_path.exists():
        return _iter_jsonl(pack_path)
    from scripts.run_stockbot_daily_reports import _load_blocked_trades
    return _load_blocked_trades(base, day)


def load_regime_universe(base: Path, day: str) -> dict:
    """Load regime and universe from daily pack."""
    pack_path = base / "reports" / "stockbot" / day / "STOCK_REGIME_AND_UNIVERSE.json"
    return _load_json(pack_path, {})


def load_eod_summary(base: Path, day: str) -> dict:
    """Load EOD summary from daily pack."""
    pack_path = base / "reports" / "stockbot" / day / "STOCK_EOD_SUMMARY.json"
    return _load_json(pack_path, {})


def ensure_daily_pack(base: Path, day: str) -> Path:
    """Ensure daily pack exists; run run_stockbot_daily_reports if needed."""
    out_dir = base / "reports" / "stockbot" / day
    if not out_dir.exists() or not (out_dir / "STOCK_EOD_SUMMARY.json").exists():
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_stockbot_daily_reports.py"), "--date", day, "--base-dir", str(base)], check=True, cwd=str(base))
    return out_dir


def main() -> int:
    ap = argparse.ArgumentParser(description="Molt Intelligence Expansion")
    ap.add_argument("--date", default="", help="YYYY-MM-DD")
    ap.add_argument("--base-dir", default="", help="Repo root")
    args = ap.parse_args()
    day = args.date.strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = Path(args.base_dir) if args.base_dir else ROOT

    ensure_daily_pack(base, day)

    eq = load_equity_attribution(base, day)
    wh = load_wheel_attribution(base, day)
    prof = load_profitability_diagnostics(base, day)
    blocked = load_blocked_trades(base, day)
    regime = load_regime_universe(base, day)
    eod = load_eod_summary(base, day)

    print(f"Loaded for {day}: equity={len(eq)}, wheel={len(wh)}, blocked={len(blocked)}, regime={regime.get('regime', 'N/A')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
