#!/usr/bin/env python3
"""
Alpaca Bar Health Check (run on droplet or locally).

- Loads Alpaca API keys from env.
- For each symbol traded today (from logs/run.jsonl), calls Alpaca for 1Min bars for the day.
- Writes telemetry/YYYY-MM-DD/alpaca_bar_health.json (per-symbol status, count, error).
- Writes telemetry/YYYY-MM-DD/computed/bar_health_summary.json (summary of bar health).
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Repo root: when run on droplet, cwd is /root/stock-bot
REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Load .env so ALPACA_* keys are available when run from repo root
try:
    from dotenv import load_dotenv
    env_path = REPO / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
except Exception:
    pass

LOGS = REPO / "logs"
TELEMETRY_DIR = REPO / "telemetry"


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _date_from_record(rec: dict) -> Optional[str]:
    ts = rec.get("ts") or rec.get("_dt") or rec.get("timestamp")
    dt = _parse_ts(ts)
    return dt.strftime("%Y-%m-%d") if dt else None


def _load_run_jsonl_symbols(date_str: str) -> Set[str]:
    """Load unique symbols from trade_intent in run.jsonl for date_str."""
    symbols: Set[str] = set()
    run_path = LOGS / "run.jsonl"
    if not run_path.exists():
        return symbols
    for line in run_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            d = _date_from_record(rec)
            if d == date_str and rec.get("event_type") == "trade_intent":
                symbol = rec.get("symbol")
                if symbol and isinstance(symbol, str) and symbol.strip() and symbol != "?":
                    symbols.add(symbol.strip().upper())
        except Exception:
            continue
    return symbols


def _alpaca_api() -> Any:
    """Return Alpaca REST client or None if env missing."""
    try:
        key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
        secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
        base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        if not key or not secret:
            return None
        from alpaca_trade_api import REST
        return REST(key, secret, base_url=base)
    except Exception:
        return None


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def check_bar_health(date_str: str) -> Dict[str, Any]:
    """
    Check Alpaca bar availability for symbols traded on date_str.
    Returns {symbol: {status, count, error}, ...}.
    """
    api = _alpaca_api()
    if api is None:
        return {"error": "Alpaca API keys not found in environment"}

    symbols_to_check = _load_run_jsonl_symbols(date_str)
    if not symbols_to_check:
        return {"warning": f"No symbols found in logs/run.jsonl for {date_str}"}

    health_status: Dict[str, Any] = {}
    y, m, d = date_str.split("-")
    day_start = datetime(int(y), int(m), int(d), 13, 30, 0, tzinfo=timezone.utc)
    day_end = datetime(int(y), int(m), int(d), 20, 0, 0, tzinfo=timezone.utc)
    start_s = _iso(day_start)
    end_s = _iso(day_end)

    for symbol in sorted(list(symbols_to_check)):
        try:
            resp = api.get_bars(symbol, "1Min", start=start_s, end=end_s, limit=5000)
            df = getattr(resp, "df", None)
            count = len(df) if df is not None else 0
            if count > 0:
                health_status[symbol] = {"status": "OK", "count": count, "timeframe": "1Min"}
            else:
                health_status[symbol] = {"status": "MISSING", "count": 0, "error": "No 1Min bars returned"}
        except Exception as e:
            health_status[symbol] = {"status": "ERROR", "count": 0, "error": str(e)}

    return health_status


def build_summary(health_data: Dict[str, Any], date_str: str) -> Dict[str, Any]:
    """Build bar_health_summary.json content. Ignores top-level 'error'/'warning' keys."""
    symbol_keys = [s for s in health_data.keys() if s not in ("error", "warning")]
    total_symbols = len(symbol_keys)
    symbols_with_bars = sum(1 for s in symbol_keys if (health_data.get(s) or {}).get("status") == "OK")
    symbols_missing_bars = sum(1 for s in symbol_keys if (health_data.get(s) or {}).get("status") in ("MISSING", "ERROR"))
    missing_list = sorted([s for s in symbol_keys if (health_data.get(s) or {}).get("status") in ("MISSING", "ERROR")])

    details = {s: health_data[s] for s in symbol_keys if isinstance(health_data.get(s), dict)}
    summary = {
        "date": date_str,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_symbols": total_symbols,
        "symbols_with_bars": symbols_with_bars,
        "symbols_missing_bars": symbols_missing_bars,
        "percent_missing": round((symbols_missing_bars / total_symbols * 100), 2) if total_symbols else 0.0,
        "missing_list": missing_list,
        "details": details,
    }
    return summary


def run(date_str: str) -> Tuple[Path, Path]:
    """
    Run bar health check, write alpaca_bar_health.json and computed/bar_health_summary.json.
    Returns (health_path, summary_path).
    """
    output_dir = TELEMETRY_DIR / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    computed_dir = output_dir / "computed"
    computed_dir.mkdir(parents=True, exist_ok=True)

    health_data = check_bar_health(date_str)
    health_path = output_dir / "alpaca_bar_health.json"
    health_path.write_text(
        json.dumps(health_data, indent=2),
        encoding="utf-8",
    )

    summary = build_summary(health_data, date_str)
    summary_path = computed_dir / "bar_health_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return health_path, summary_path


if __name__ == "__main__":
    # Example usage: python scripts/check_alpaca_bar_health.py --date 2026-01-28
    import argparse
    ap = argparse.ArgumentParser(description="Alpaca Bar Health Check")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today UTC)")
    args = ap.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    health_path, summary_path = run(date_str)
    print(f"[OK] Wrote {health_path}")
    print(f"[OK] Wrote {summary_path}")

    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        pct = summary.get("percent_missing") or 0
        if summary.get("total_symbols", 0) > 0 and pct > 20:
            print("Counterfactuals and exit attribution may be incomplete.", file=sys.stderr)
    except Exception:
        pass
    sys.exit(0)
