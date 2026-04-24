#!/usr/bin/env python3
"""
Unusual Whales API synthetic health probe (cron-friendly).

- Calls live UW endpoints for a liquid symbol (default SPY).
- Validates **raw** JSON shapes and critical keys/types (no Data Armor / coercion).
- On failure: ``utils.system_events.log_system_event`` → ``logs/system_events.jsonl``
  with severity ERROR or CRITICAL.

Run:
  cd /path/to/stock-bot && PYTHONPATH=. python3 src/telemetry/uw_api_health_probe.py

Cron (example, do not install without approval):
  */5 * * * * cd /root/stock-bot && PYTHONPATH=/root/stock-bot /root/stock-bot/venv/bin/python3 -u src/telemetry/uw_api_health_probe.py >>/root/stock-bot/logs/uw_health_probe.cron.log 2>&1
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _repo_root() -> Path:
    env = (os.environ.get("STOCK_BOT_ROOT") or os.environ.get("STOCKBOT_ROOT") or "").strip()
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    for p in (here.parents[2], here.parents[1], Path.cwd()):
        if (p / "config" / "registry.py").exists():
            return p
    return Path.cwd()


def _fail(
    *,
    reason: str,
    endpoint: str,
    severity: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        from utils.system_events import log_system_event

        details: Dict[str, Any] = {"reason": reason, "endpoint": str(endpoint)}
        if extra:
            details.update(extra)
        log_system_event(
            subsystem="uw_health_probe",
            event_type="uw_api_schema_or_transport_failure",
            severity=severity,
            symbol="SPY",
            details=details,
        )
    except Exception:
        pass


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _numeric_like(x: Any) -> bool:
    """True if ``x`` is a real number or a string that parses to a finite float (raw UW quirk)."""
    if _is_number(x):
        return True
    if isinstance(x, str) and x.strip():
        try:
            float(x.strip())
            return True
        except ValueError:
            return False
    return False


def _validate_flow_first_row(row: Dict[str, Any]) -> Optional[str]:
    """
    Raw flow-alert row: UW often omits ``flow_conv`` on the wire; require tape primitives
    (ticker + premium + size) **or** explicit conviction fields. String numerics allowed (parse check only).
    """
    conv_keys = ("flow_conv", "flow_conviction", "conviction")
    has_conv = False
    for k in conv_keys:
        if k not in row:
            continue
        v = row.get(k)
        if v is None:
            continue
        if _numeric_like(v):
            has_conv = True
            break
        return f"non_numeric_like_{k}:{type(v).__name__}"

    prem = row.get("total_premium", row.get("premium"))
    vol = row.get("volume", row.get("total_size"))
    ticker = row.get("ticker", row.get("symbol"))
    if not has_conv:
        if not ticker:
            return "missing_ticker"
        if prem is None or not _numeric_like(prem):
            return "missing_or_non_numeric_total_premium"
        if vol is None or not _numeric_like(vol):
            return "missing_or_non_numeric_volume"

    mag = row.get("flow_magnitude", row.get("magnitude"))
    if mag is not None and not isinstance(mag, str):
        return f"flow_magnitude_wrong_type:{type(mag).__name__}"

    if prem is not None and not _numeric_like(prem):
        return f"total_premium_non_numeric_like:{type(prem).__name__}"
    if vol is not None and not _numeric_like(vol):
        return f"volume_non_numeric_like:{type(vol).__name__}"
    return None


def _validate_dp_first_row(row: Dict[str, Any]) -> Optional[str]:
    if "price" not in row:
        return "missing_price"
    if not _numeric_like(row.get("price")):
        return f"price_non_numeric_like:{type(row.get('price')).__name__}"
    vol_keys = ("off_lit_volume", "total_volume", "dark_volume", "size", "volume")
    if not any(k in row for k in vol_keys):
        return "missing_volume_fields"
    for k in vol_keys:
        if k in row and row[k] is not None and not _numeric_like(row[k]):
            return f"{k}_non_numeric_like:{type(row[k]).__name__}"
    return None


def _validate_iv_rank_payload(data: Dict[str, Any]) -> Optional[str]:
    """IV / skew lane: UW ``/api/stock/{sym}/iv-rank`` — expect iv_rank-like numeric in ``data``."""
    d = data.get("data")
    if isinstance(d, dict):
        cand = d.get("iv_rank", d.get("iv_rank_1y", d.get("rank")))
        if cand is None:
            return "iv_rank_data_dict_missing_scalar"
        if not _numeric_like(cand):
            return f"iv_rank_non_numeric_like:{type(cand).__name__}"
        return None
    if isinstance(d, list) and d:
        first = d[0]
        if not isinstance(first, dict):
            return "iv_rank_data_list_first_not_object"
        cand = first.get("iv_rank", first.get("iv_rank_1y"))
        if cand is None:
            return "iv_rank_row_missing_scalar"
        if not _numeric_like(cand):
            return f"iv_rank_non_numeric_like:{type(cand).__name__}"
        return None
    return "iv_rank_unexpected_data_shape"


def _check_endpoint(
    path: str,
    params: Optional[Dict[str, Any]],
) -> bool:
    from src.uw.uw_client import uw_http_get

    policy = {
        "ttl_seconds": 45,
        "endpoint_name": f"uw_health_probe:{path}",
        "max_calls_per_day": 50000,
        # Unique prefix so each probe run hits the wire (avoids stale 45s cache masking regressions).
        "key_prefix": f"probe_{int(time.time())}_{hash(path) % 1_000_000}",
    }
    try:
        status, body, _hdr = uw_http_get(path, params=params, cache_policy=policy, timeout_s=15.0)
    except Exception as ex:
        _fail(
            reason="request_exception",
            endpoint=path,
            severity="CRITICAL",
            extra={"error": str(ex)[:500]},
        )
        return False

    if status == 0 or status >= 500:
        _fail(
            reason="http_transport_or_timeout",
            endpoint=path,
            severity="CRITICAL",
            extra={"http_status": status, "body_type": type(body).__name__},
        )
        return False

    if status == 401 or status == 403:
        _fail(
            reason="http_auth_forbidden",
            endpoint=path,
            severity="CRITICAL",
            extra={"http_status": status},
        )
        return False

    if status == 404 or status == 400:
        _fail(
            reason="http_client_error_deprecated_or_bad_request",
            endpoint=path,
            severity="CRITICAL",
            extra={"http_status": status},
        )
        return False

    if status != 200:
        _fail(
            reason="http_non_success",
            endpoint=path,
            severity="ERROR",
            extra={"http_status": status},
        )
        return False

    if not isinstance(body, dict):
        _fail(
            reason="body_not_json_object",
            endpoint=path,
            severity="CRITICAL",
            extra={"body_type": type(body).__name__},
        )
        return False

    if path.endswith("/iv-rank"):
        err = _validate_iv_rank_payload(body)
        if err:
            _fail(
                reason=err,
                endpoint=path,
                severity="ERROR",
                extra={"validation": "iv_rank"},
            )
            return False
        return True

    if "data" not in body:
        _fail(
            reason="missing_top_level_data_key",
            endpoint=path,
            severity="CRITICAL",
            extra={"keys": sorted(body.keys())[:40]},
        )
        return False

    raw_data = body.get("data")
    if not isinstance(raw_data, list):
        _fail(
            reason="data_not_list",
            endpoint=path,
            severity="CRITICAL",
            extra={"data_type": type(raw_data).__name__},
        )
        return False

    if not raw_data:
        # Schema is valid (200 + list); empty tape is not a key-drop — WARN only, pass probe.
        try:
            from utils.system_events import log_system_event

            log_system_event(
                subsystem="uw_health_probe",
                event_type="uw_api_probe_empty_data",
                severity="WARN",
                symbol=params.get("symbol") if isinstance(params, dict) else None,
                details={"endpoint": path, "note": "data_array_empty"},
            )
        except Exception:
            pass
        return True

    first = raw_data[0]
    if not isinstance(first, dict):
        _fail(
            reason="first_row_not_object",
            endpoint=path,
            severity="CRITICAL",
            extra={"first_type": type(first).__name__},
        )
        return False

    if "/option-trades/flow-alerts" in path:
        err = _validate_flow_first_row(first)
    else:
        err = _validate_dp_first_row(first)

    if err:
        _fail(
            reason=err,
            endpoint=path,
            severity="ERROR",
            extra={"sample_keys": sorted(first.keys())[:48]},
        )
        return False

    return True


def main() -> int:
    root = _repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # Cron / manual SSH: load repo .env so ``APIConfig.get_uw_headers()`` resolves the UW token.
    try:
        from dotenv import load_dotenv

        load_dotenv(root / ".env")
    except Exception:
        pass
    os.chdir(root)

    symbol = (os.environ.get("UW_HEALTH_PROBE_SYMBOL") or "SPY").strip().upper() or "SPY"

    flow_path = "/api/option-trades/flow-alerts"
    dp_path = f"/api/darkpool/{symbol}"
    iv_path = f"/api/stock/{symbol}/iv-rank"

    ok = True
    ok &= _check_endpoint(flow_path, {"symbol": symbol, "limit": 10})
    ok &= _check_endpoint(dp_path, None)
    ok &= _check_endpoint(iv_path, None)

    if ok:
        try:
            from utils.system_events import log_system_event

            log_system_event(
                subsystem="uw_health_probe",
                event_type="uw_api_probe_ok",
                severity="INFO",
                symbol=symbol,
                details={"endpoints": [flow_path, dp_path, iv_path]},
            )
        except Exception:
            pass
        print(f"uw_api_health_probe_ok symbol={symbol}")
        return 0

    print(f"uw_api_health_probe_failed symbol={symbol}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
