#!/usr/bin/env python3
"""
Read-only: inspect key UW cache fields for a few tickers on droplet.
"""

from __future__ import annotations

import json

from droplet_client import DropletClient


def main() -> int:
    tickers = ["AAPL", "SPY", "NVDA", "AMZN", "HOOD"]
    with DropletClient() as c:
        py = "\n".join(
            [
                "import json",
                "p='data/uw_flow_cache.json'",
                "d=json.load(open(p,'r'))",
                f"tickers={tickers!r}",
                "out={}",
                "for t in tickers:",
                "  x=d.get(t, {}) or {}",
                "  dp = x.get('dark_pool')",
                "  ftd = x.get('ftd_pressure') if isinstance(x, dict) else None",
                "  iv = x.get('iv_rank') if isinstance(x, dict) else None",
                "  oi = x.get('oi_change') if isinstance(x, dict) else None",
                "  etf = x.get('etf_flow') if isinstance(x, dict) else None",
                "  tide = x.get('market_tide') if isinstance(x, dict) else None",
                "  out[t]={",
                "    'has': bool(x),",
                "    'sentiment': x.get('sentiment'),",
                "    'conviction': x.get('conviction'),",
                "    'flow_trades_n': len(x.get('flow_trades') or []),",
                "    'dark_pool_type': type(dp).__name__,",
                "    'dark_pool_keys': list(dp.keys()) if isinstance(dp, dict) else None,",
                "    'dark_pool_total_notional_1h': (dp.get('total_notional_1h') if isinstance(dp, dict) else None),",
                "    'ftd_pressure_type': type(ftd).__name__,",
                "    'ftd_pressure_keys': list(ftd.keys()) if isinstance(ftd, dict) else None,",
                "    'iv_rank_type': type(iv).__name__,",
                "    'iv_rank_keys': list(iv.keys()) if isinstance(iv, dict) else None,",
                "    'oi_change_type': type(oi).__name__,",
                "    'oi_change_keys': list(oi.keys()) if isinstance(oi, dict) else None,",
                "    'etf_flow_type': type(etf).__name__,",
                "    'etf_flow_keys': list(etf.keys()) if isinstance(etf, dict) else None,",
                "    'market_tide_type': type(tide).__name__,",
                "    'market_tide_keys': list(tide.keys()) if isinstance(tide, dict) else None,",
                "    'gamma_exposure_levels_type': type(x.get('gamma_exposure_levels')).__name__,",
                "    '_last_update': x.get('_last_update'),",
                "  }",
                "print(json.dumps(out, indent=2, default=str))",
            ]
        )
        cmd = "cd /root/stock-bot && python3 - <<'PY'\n" + py + "\nPY\n"
        r = c.execute_command(cmd, timeout=60)
        print((r.get("stdout") or r.get("stderr") or "").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

