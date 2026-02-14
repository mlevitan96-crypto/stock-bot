#!/usr/bin/env python3
"""
Central UW Client (v2 intelligence layer)
========================================

Non-negotiable goals:
- All UW HTTP calls should flow through this module (rate limit + daily budget + logging).
- Additive: does not change v1 composite behavior; safe to import.
- Regression-safe: supports UW_MOCK=1 for deterministic offline runs.

State:
- Daily/minute usage tracked in: state/uw_usage_state.json
- Response cache stored in: state/uw_cache/
"""

from __future__ import annotations

import hashlib
import json
import os
import inspect
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import requests

from config.registry import APIConfig, CacheFiles
from utils.state_io import read_json_self_heal

from src.uw.uw_spec_loader import is_valid_uw_path

try:
    from utils.system_events import log_system_event
except Exception:  # pragma: no cover
    def log_system_event(*args, **kwargs):  # type: ignore
        return None


UW_USAGE_STATE_PATH = Path("state/uw_usage_state.json")
UW_CACHE_DIR = Path("state/uw_cache")

def _caller_hint() -> str:
    try:
        for fr in inspect.stack()[2:12]:
            fn = fr.filename.replace("\\", "/")
            if fn.endswith("/src/uw/uw_client.py"):
                continue
            return f"{fn}:{fr.lineno}:{fr.function}"
    except Exception:
        pass
    return "unknown"


def _validate_endpoint_or_raise(endpoint: str) -> None:
    """
    Hard safety gate: block any UW endpoint not present in the official OpenAPI spec.
    Runs before rate limiting, caching, or network calls.
    """
    ep = str(endpoint or "").strip()
    if not ep:
        raise ValueError("Invalid UW endpoint: <empty>")
    if ep.startswith("http://") or ep.startswith("https://"):
        try:
            from urllib.parse import urlparse

            ep = urlparse(ep).path or ep
        except Exception:
            pass
    if not ep.startswith("/"):
        ep = "/" + ep

    if not is_valid_uw_path(ep):
        try:
            log_system_event(
                subsystem="uw",
                event_type="uw_invalid_endpoint_attempt",
                severity="ERROR",
                details={
                    "endpoint": ep,
                    "caller": _caller_hint(),
                    "timestamp": time.time(),
                },
            )
        except Exception:
            pass
        raise ValueError(f"Invalid UW endpoint: {ep}")


def _today_utc() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _atomic_write_json(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        return


@dataclass(frozen=True)
class UwCachePolicy:
    ttl_seconds: int = 0
    key_prefix: str = ""
    endpoint_name: str = ""
    max_calls_per_day: int = 0  # 0 means "no per-endpoint cap"


def _normalize_policy(cache_policy: Any) -> UwCachePolicy:
    if cache_policy is None:
        return UwCachePolicy(ttl_seconds=0)
    if isinstance(cache_policy, UwCachePolicy):
        return cache_policy
    if isinstance(cache_policy, dict):
        try:
            return UwCachePolicy(
                ttl_seconds=int(cache_policy.get("ttl_seconds", 0) or 0),
                key_prefix=str(cache_policy.get("key_prefix", "") or ""),
                endpoint_name=str(cache_policy.get("endpoint_name", "") or ""),
                max_calls_per_day=int(cache_policy.get("max_calls_per_day", 0) or 0),
            )
        except Exception:
            return UwCachePolicy(ttl_seconds=0)
    return UwCachePolicy(ttl_seconds=0)


def _cache_key(endpoint: str, params: Optional[Dict[str, Any]], policy: UwCachePolicy) -> str:
    payload = {"endpoint": str(endpoint), "params": params or {}, "prefix": policy.key_prefix}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _cache_path(key: str) -> Path:
    return UW_CACHE_DIR / f"{key}.json"


def _read_cache(key: str) -> Optional[Dict[str, Any]]:
    p = _cache_path(key)
    data = read_json_self_heal(p, default=None, heal=False, mkdir=True)
    if not isinstance(data, dict):
        return None
    return data


def _write_cache(key: str, record: Dict[str, Any]) -> None:
    p = _cache_path(key)
    _atomic_write_json(p, record)


def _load_usage_state() -> Dict[str, Any]:
    default = {
        "date": _today_utc(),
        "calls_today": 0,
        "by_endpoint": {},
        "minute_window": [],  # epoch seconds of recent calls
    }
    data = read_json_self_heal(UW_USAGE_STATE_PATH, default=default, heal=True, mkdir=True, on_event=None)
    if not isinstance(data, dict):
        return dict(default)
    # reset on date change
    if str(data.get("date")) != _today_utc():
        return dict(default)
    if not isinstance(data.get("minute_window"), list):
        data["minute_window"] = []
    if not isinstance(data.get("by_endpoint"), dict):
        data["by_endpoint"] = {}
    return data


def _save_usage_state(state: Dict[str, Any]) -> None:
    _atomic_write_json(UW_USAGE_STATE_PATH, state)


def _prune_minute_window(state: Dict[str, Any], *, now: float, window_sec: int = 60) -> None:
    try:
        w = state.get("minute_window", [])
        if not isinstance(w, list):
            state["minute_window"] = []
            return
        cutoff = now - float(window_sec)
        pruned = [float(x) for x in w if isinstance(x, (int, float)) and float(x) >= cutoff]
        state["minute_window"] = pruned[-1000:]  # safety bound
    except Exception:
        state["minute_window"] = []


def _limits() -> Tuple[int, int, float]:
    # Defaults per prompt (can be overridden via env)
    per_min = int(os.getenv("UW_RATE_LIMIT_PER_MIN", "120") or "120")
    per_day = int(os.getenv("UW_DAILY_LIMIT", "15000") or "15000")
    buf = float(os.getenv("UW_SAFETY_BUFFER", "0.95") or "0.95")
    return max(1, per_min), max(1, per_day), max(0.1, min(1.0, buf))


def _blocked(reason: str, *, endpoint: str, params: Optional[Dict[str, Any]] = None, wait_s: Optional[float] = None) -> Dict[str, Any]:
    try:
        log_system_event(
            subsystem="uw",
            event_type="uw_rate_limit_block",
            severity="WARN",
            details={"reason": reason, "endpoint": str(endpoint), "params": params or {}, "wait_s": wait_s},
        )
    except Exception:
        pass
    return {"data": [], "_blocked": True, "_reason": reason}


def _mock_response(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Deterministic pseudo-data for regression (no secrets, no network).
    sym = (params or {}).get("symbol") or (params or {}).get("ticker") or "SPY"
    return {
        "data": [
            {
                "symbol": str(sym).upper(),
                "flow_strength": 0.6,
                "darkpool_bias": 0.1,
                "sentiment": "BULLISH",
                "earnings_proximity": 3,
            }
        ],
        "_mock": True,
        "_endpoint": str(endpoint),
    }


# Default cache TTL (seconds) to reduce API load when caller does not pass cache_policy.
UW_DEFAULT_CACHE_TTL_SECONDS = 60


def _uw_retry_with_backoff(
    endpoint: str,
    params: Optional[Dict[str, Any]],
    url: str,
    headers: Dict[str, Any],
    timeout_s: float,
    max_attempts: int = 3,
) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
    """Execute GET with 3 attempts and exponential backoff. Returns (status, data, headers)."""
    import logging
    log = logging.getLogger(__name__)
    last_status, last_data, last_headers = 0, {"data": []}, {}
    for attempt in range(max_attempts):
        try:
            r = requests.get(url, headers=headers, params=params or {}, timeout=float(timeout_s))
            status = int(getattr(r, "status_code", 0) or 0)
            try:
                resp_headers = dict(getattr(r, "headers", {}) or {})
            except Exception:
                resp_headers = {}
            try:
                data = r.json() if r.content else {"data": []}
            except Exception:
                data = {"data": []}
            if status == 200:
                return status, data if isinstance(data, dict) else {"data": []}, resp_headers
            last_status, last_data, last_headers = status, data, resp_headers
            if status in (429, 503) and attempt < max_attempts - 1:
                wait_s = (2 ** attempt) + (attempt * 0.5)
                time.sleep(wait_s)
            else:
                break
        except Exception as e:
            last_status, last_data, last_headers = 0, {"data": []}, {}
            log.warning("uw_http_get attempt %s failed: %s", attempt + 1, e)
            if attempt < max_attempts - 1:
                time.sleep((2 ** attempt) + (attempt * 0.5))
    return last_status, last_data if isinstance(last_data, dict) else {"data": []}, last_headers


def uw_http_get(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    *,
    cache_policy: Any = None,
    timeout_s: float = 12.0,
) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
    """
    Low-level UW GET with:
    - minute + daily limits
    - optional cache (default 60s TTL when cache_policy not provided)
    - retry: 3 attempts, exponential backoff
    - structured logging for all UW calls
    Returns: (status_code, json_body, response_headers_dict)
    Never raises.
    """
    # Endpoint safety check MUST run before any other work.
    _validate_endpoint_or_raise(endpoint)

    policy = _normalize_policy(cache_policy)
    if policy.ttl_seconds <= 0:
        policy = UwCachePolicy(
            ttl_seconds=UW_DEFAULT_CACHE_TTL_SECONDS,
            key_prefix=policy.key_prefix,
            endpoint_name=policy.endpoint_name or "default",
            max_calls_per_day=policy.max_calls_per_day,
        )
    now = time.time()
    per_min, per_day, buf = _limits()

    # Mock mode (regression-safe)
    mock_mode = str(os.getenv("UW_MOCK", "")).strip() in ("1", "true", "TRUE", "yes", "YES")
    mock_enforce_limits = str(os.getenv("UW_MOCK_ENFORCE_LIMITS", "")).strip() in ("1", "true", "TRUE", "yes", "YES")
    if mock_mode and not mock_enforce_limits:
        return 200, _mock_response(endpoint, params=params), {}

    # Resolve URL
    base = str(APIConfig.UW_BASE_URL or "https://api.unusualwhales.com").rstrip("/")
    url = endpoint if str(endpoint).startswith("http") else f"{base}{str(endpoint)}"
    headers = APIConfig.get_uw_headers()

    # Cache lookup
    key = _cache_key(endpoint, params, policy)
    if policy.ttl_seconds > 0:
        rec = _read_cache(key)
        if isinstance(rec, dict):
            try:
                exp = float(rec.get("expires_at", 0.0) or 0.0)
                if exp > now and isinstance(rec.get("data"), dict):
                    try:
                        log_system_event(
                            subsystem="uw",
                            event_type="uw_call",
                            severity="INFO",
                            details={
                                "endpoint": str(endpoint),
                                "cache_hit": True,
                                "ttl_seconds": int(policy.ttl_seconds),
                                "endpoint_name": policy.endpoint_name,
                            },
                        )
                    except Exception:
                        pass
                    return 200, rec["data"], {"_cache": "hit"}
            except Exception:
                pass

    # Load/validate usage state
    st = _load_usage_state()
    _prune_minute_window(st, now=now, window_sec=60)
    minute_calls = len(st.get("minute_window", []) or [])
    calls_today = int(st.get("calls_today", 0) or 0)

    daily_cap = int(per_day * float(buf))
    if calls_today >= daily_cap:
        return 429, _blocked("daily_cap", endpoint=endpoint, params=params), {}
    if minute_calls >= per_min:
        # conservative wait estimate
        w = st.get("minute_window", []) or []
        wait_s = None
        try:
            oldest = float(w[0]) if w else None
            wait_s = max(0.0, 60.0 - (now - oldest)) if oldest else None
        except Exception:
            wait_s = None
        return 429, _blocked("per_minute_cap", endpoint=endpoint, params=params, wait_s=wait_s), {}

    # Per-endpoint cap
    if policy.max_calls_per_day and policy.endpoint_name:
        by = st.get("by_endpoint", {}) if isinstance(st.get("by_endpoint"), dict) else {}
        n = int((by.get(policy.endpoint_name) or 0))
        if n >= int(policy.max_calls_per_day):
            return 429, _blocked("endpoint_cap", endpoint=endpoint, params=params), {}

    # QUOTA TRACKING (existing contract): log every UW call (append-only)
    try:
        quota_log = CacheFiles.UW_API_QUOTA
        quota_log.parent.mkdir(parents=True, exist_ok=True)
        with quota_log.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "ts": int(now),
                        "url": url,
                        "params": params or {},
                        "source": "src/uw/uw_client",
                        "endpoint_name": policy.endpoint_name,
                    }
                )
                + "\n"
            )
    except Exception:
        pass

    # Execute request with retry (or deterministic mock with limits enforced)
    t0 = time.time()
    status = 0
    data: Dict[str, Any] = {"data": []}
    resp_headers: Dict[str, Any] = {}
    try:
        if mock_mode and mock_enforce_limits:
            status = 200
            data = _mock_response(endpoint, params=params)
            resp_headers = {}
        else:
            status, data, resp_headers = _uw_retry_with_backoff(
                endpoint, params, url, headers, timeout_s, max_attempts=3
            )
    except Exception as e:
        status = 0
        data = {"data": []}
        resp_headers = {}
        try:
            log_system_event(
                subsystem="uw",
                event_type="uw_call",
                severity="ERROR",
                details={
                    "endpoint": str(endpoint),
                    "params": params or {},
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "caller": _caller_hint(),
                },
            )
        except Exception:
            pass
        return status, data, resp_headers
    finally:
        # Record usage on attempted call (even non-200) to keep budget honest.
        try:
            st = _load_usage_state()
            _prune_minute_window(st, now=now, window_sec=60)
            st["minute_window"] = (st.get("minute_window", []) or []) + [now]
            st["calls_today"] = int(st.get("calls_today", 0) or 0) + 1
            if policy.endpoint_name:
                by = st.get("by_endpoint", {}) if isinstance(st.get("by_endpoint"), dict) else {}
                by[policy.endpoint_name] = int(by.get(policy.endpoint_name, 0) or 0) + 1
                st["by_endpoint"] = by
            _save_usage_state(st)
        except Exception:
            pass

    dt_ms = int((time.time() - t0) * 1000)
    try:
        log_system_event(
            subsystem="uw",
            event_type="uw_call",
            severity="INFO" if status == 200 else "WARN",
            details={
                "endpoint": str(endpoint),
                "endpoint_name": policy.endpoint_name,
                "params": params or {},
                "status": int(status),
                "cache_hit": False,
                "latency_ms": int(dt_ms),
                "caller": _caller_hint(),
            },
        )
    except Exception:
        pass

    # Cache write
    if policy.ttl_seconds > 0 and status == 200 and isinstance(data, dict):
        try:
            _write_cache(
                key,
                {
                    "ts": now,
                    "expires_at": now + float(policy.ttl_seconds),
                    "endpoint": str(endpoint),
                    "endpoint_name": policy.endpoint_name,
                    "params": params or {},
                    "data": data,
                },
            )
        except Exception:
            pass

    return status, data if isinstance(data, dict) else {"data": []}, resp_headers


def uw_get(endpoint: str, params: Optional[Dict[str, Any]] = None, cache_policy: Any = None) -> Dict[str, Any]:
    """
    Public UW interface.
    Returns dict (typically with "data").
    Never raises.
    """
    status, data, _hdr = uw_http_get(endpoint, params=params, cache_policy=cache_policy)
    if not isinstance(data, dict):
        return {"data": []}
    # normalize on rate limit block
    if status == 429 and data.get("_blocked"):
        return {"data": [], "_blocked": True, "_reason": data.get("_reason")}
    return data

