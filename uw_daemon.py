#!/usr/bin/env python3
"""
UW Daemon - Central Signal Cache Producer

Goal:
- Continuously fetch UW data at a controlled cadence
- Write a single source-of-truth cache at data/uw_flow_cache.json
- Keep cache schema stable for consumers (main.py, enrichment, health checks)

This daemon is designed to be "boring":
- Backoff on API errors / rate limiting
- Atomic writes
- Never crashes the host service loop
"""

import os
import json
import time
import math
import random
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path

import requests

from config.registry import CacheFiles, append_jsonl, atomic_write_json


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_list(name: str, default_csv: str) -> List[str]:
    raw = os.getenv(name, default_csv)
    return [x.strip().upper() for x in raw.split(",") if x.strip()]


class UWClient:
    """Small UW client (mirrors main.py UWClient but standalone)."""

    def __init__(self, api_key: str, base: str = "https://api.unusualwhales.com"):
        self.api_key = api_key
        self.base = base
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = path if path.startswith("http") else f"{self.base}{path}"
        r = requests.get(url, headers=self.headers, params=params or {}, timeout=15)
        r.raise_for_status()
        return r.json()

    def get_option_flow(self, ticker: str, limit: int = 100) -> List[dict]:
        raw = self._get("/api/option-trades/flow-alerts", params={"symbol": ticker, "limit": limit})
        return raw.get("data", []) or []

    def get_top_net_impact(self, limit: int = 200) -> List[dict]:
        raw = self._get("/api/market/top-net-impact", params={"limit": limit})
        return raw.get("data", []) or []


def _summarize_flow(trades: List[dict]) -> Dict[str, Any]:
    """
    Produce a lightweight summary from UW flow alerts.
    We keep it conservative (consumer modules do deeper enrichment).
    """
    if not trades:
        return {"sentiment": "NEUTRAL", "conviction": 0.0, "flow_count": 0, "premium_usd": 0.0}

    bull_prem = 0.0
    bear_prem = 0.0
    bull_n = 0
    bear_n = 0

    for t in trades[:200]:
        try:
            option_type = (t.get("type") or "").lower()
            bid_prem = float(t.get("total_bid_side_prem") or 0)
            ask_prem = float(t.get("total_ask_side_prem") or 0)
            is_buy = ask_prem > bid_prem
            direction = "bullish" if (option_type == "call" and is_buy) or (option_type == "put" and not is_buy) else "bearish"
            prem = float(t.get("total_premium") or t.get("premium") or 0)
            if direction == "bullish":
                bull_prem += prem
                bull_n += 1
            else:
                bear_prem += prem
                bear_n += 1
        except Exception:
            continue

    total_prem = bull_prem + bear_prem
    net = bull_prem - bear_prem
    if abs(net) < max(50_000, 0.05 * total_prem):
        sent = "NEUTRAL"
    else:
        sent = "BULLISH" if net > 0 else "BEARISH"

    # Conviction: sigmoid of (abs(net) + total) on a log scale, clamped to [0, 1]
    # This is just a stable placeholder; learning happens downstream.
    strength = math.log10(max(1.0, abs(net))) + 0.5 * math.log10(max(1.0, total_prem))
    conviction = 1.0 / (1.0 + math.exp(-(strength - 8.0)))  # centered around ~$100M-ish scale

    return {
        "sentiment": sent,
        "conviction": round(float(conviction), 4),
        "flow_count": int(bull_n + bear_n),
        "premium_usd": round(float(total_prem), 2),
        "bull_premium_usd": round(float(bull_prem), 2),
        "bear_premium_usd": round(float(bear_prem), 2),
    }


def main():
    tickers = _env_list("TICKERS", "SPY,QQQ,AAPL,MSFT,NVDA,TSLA")
    poll_sec = _env_int("UW_DAEMON_POLL_SEC", 60)
    flow_limit = _env_int("UW_DAEMON_FLOW_LIMIT", 100)
    top_net_limit = _env_int("UW_DAEMON_TOP_NET_LIMIT", 200)

    # Rate safety
    min_sleep_on_error = _env_int("UW_DAEMON_MIN_SLEEP_ON_ERROR_SEC", 10)
    max_sleep_on_error = _env_int("UW_DAEMON_MAX_SLEEP_ON_ERROR_SEC", 180)

    api_key = os.getenv("UW_API_KEY", "")
    if not api_key:
        raise SystemExit("UW_API_KEY is required for uw_daemon.py")

    uw = UWClient(api_key=api_key)

    backoff = min_sleep_on_error
    last_top_net_ts = 0.0
    top_net_refresh_sec = max(60, poll_sec)  # refresh at most once per minute by default
    top_net_map: Dict[str, dict] = {}

    append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {
        "event": "UW_DAEMON_START",
        "tickers": len(tickers),
        "poll_sec": poll_sec,
        "flow_limit": flow_limit,
    })

    while True:
        cycle_start = time.time()
        try:
            # Refresh top net impact periodically (single call, many symbols)
            if time.time() - last_top_net_ts > top_net_refresh_sec:
                try:
                    rows = uw.get_top_net_impact(limit=top_net_limit)
                    top_net_map = {str(r.get("symbol") or r.get("ticker") or "").upper(): r for r in rows if (r.get("symbol") or r.get("ticker"))}
                    last_top_net_ts = time.time()
                except Exception as e:
                    append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {"event": "TOP_NET_FAIL", "error": str(e)})

            cache: Dict[str, Any] = {
                "_meta": {
                    "ts": int(time.time()),
                    "dt": _utc_iso(),
                    "source": "uw_daemon",
                    "tickers": len(tickers),
                }
            }

            for sym in tickers:
                # Small jitter to avoid bursty patterns
                time.sleep(0.05 + random.random() * 0.05)
                try:
                    trades = uw.get_option_flow(sym, limit=flow_limit)
                    summary = _summarize_flow(trades)

                    net = top_net_map.get(sym, {})
                    cache[sym] = {
                        "sentiment": summary["sentiment"],
                        "conviction": summary["conviction"],
                        # Consumer modules expect nested dicts; keep keys stable.
                        "dark_pool": {"sentiment": summary["sentiment"], "total_premium": 0.0},
                        "net_impact": {
                            "net_premium": float(net.get("net_premium") or 0),
                            "net_call_premium": float(net.get("net_call_premium") or 0),
                            "net_put_premium": float(net.get("net_put_premium") or 0),
                        },
                        "_flow": {
                            "count": summary["flow_count"],
                            "premium_usd": summary["premium_usd"],
                            "bull_premium_usd": summary["bull_premium_usd"],
                            "bear_premium_usd": summary["bear_premium_usd"],
                        }
                    }
                except Exception as e:
                    cache[sym] = {"sentiment": "NEUTRAL", "conviction": 0.0, "_error": str(e)}

            atomic_write_json(CacheFiles.UW_FLOW_CACHE, cache)
            append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {
                "event": "UW_DAEMON_WRITE_OK",
                "symbols": len(tickers),
                "elapsed_sec": round(time.time() - cycle_start, 3),
            })

            backoff = min_sleep_on_error
            # Sleep to next tick
            elapsed = time.time() - cycle_start
            time.sleep(max(1.0, poll_sec - elapsed))

        except Exception as e:
            append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {"event": "UW_DAEMON_FATAL", "error": str(e), "backoff_sec": backoff})
            time.sleep(backoff)
            backoff = min(max_sleep_on_error, int(backoff * 1.8) + 1)


if __name__ == "__main__":
    main()

