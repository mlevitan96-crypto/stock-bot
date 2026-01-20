#!/usr/bin/env python3
"""
Droplet-native refresh for state/symbol_risk_features.json

Why:
- Weight tuning depends on realized vol/beta features.
- Worker may skip feature refresh when market is closed.

Env:
- Uses /root/stock-bot/.env if present (API keys)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set


ROOT = Path("/root/stock-bot")


def _load_env_map(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    try:
        if not path.exists():
            return env
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[len("export ") :].strip()
            v = v.strip().strip("'").strip('"')
            if k:
                env[k] = v
    except Exception:
        return env
    return env


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict):
                    out.append(r)
    except Exception:
        return []
    return out


def main() -> int:
    env = _load_env_map(ROOT / ".env")

    def _pick(*keys: str) -> str:
        for k in keys:
            v = env.get(k) or os.getenv(k)
            if v:
                return str(v)
        return ""

    api_key = _pick("APCA_API_KEY_ID", "ALPACA_API_KEY", "ALPACA_KEY", "API_KEY")
    api_secret = _pick("APCA_API_SECRET_KEY", "ALPACA_SECRET_KEY", "ALPACA_SECRET", "API_SECRET", "SECRET_KEY")
    base_url = _pick("APCA_API_BASE_URL", "ALPACA_BASE_URL", "BASE_URL") or "https://paper-api.alpaca.markets"

    # Heuristic fallback: accept any key containing API_KEY / SECRET / BASE_URL.
    if not api_key:
        for k, v in env.items():
            kk = k.upper()
            if "API_KEY" in kk and "SECRET" not in kk and v:
                api_key = v
                break
    if not api_secret:
        for k, v in env.items():
            kk = k.upper()
            if ("SECRET" in kk or "API_SECRET" in kk) and v:
                api_secret = v
                break
    if not base_url:
        for k, v in env.items():
            kk = k.upper()
            if "BASE_URL" in kk and v:
                base_url = v
                break

    if not api_key or not api_secret:
        raise SystemExit("Missing Alpaca credentials in environment/.env")

    import alpaca_trade_api as tradeapi

    api = tradeapi.REST(api_key, api_secret, base_url)

    # Build a symbol universe from existing logs (real + shadow), plus SPY.
    symbols: Set[str] = set()
    for r in _read_jsonl(ROOT / "logs/attribution.jsonl"):
        sym = r.get("symbol") or (r.get("context") or {}).get("symbol")
        if sym:
            symbols.add(str(sym).upper())
    for r in _read_jsonl(ROOT / "logs/shadow.jsonl"):
        sym = r.get("symbol")
        if sym:
            symbols.add(str(sym).upper())
    symbols.add("SPY")

    from structural_intelligence.symbol_risk_features import update_symbol_risk_features

    out = update_symbol_risk_features(api, symbols=sorted(symbols), benchmark="SPY", refresh_hours=0.0)

    # Print a small confirmation (stdout captured by runner).
    sy = out.get("symbols", {}) if isinstance(out, dict) else {}
    nonzero = None
    if isinstance(sy, dict):
        for k, v in sy.items():
            if not isinstance(v, dict):
                continue
            if float(v.get("realized_vol_20d") or 0.0) > 0 or float(v.get("beta_vs_spy") or 0.0) != 0:
                nonzero = (k, v)
                break

    print(
        json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "symbols": len(sy) if isinstance(sy, dict) else 0,
                "sample_nonzero": nonzero,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

