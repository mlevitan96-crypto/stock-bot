"""
Permanent system event logging + global failure wrapper.

Contract:
- All events are appended to logs/system_events.jsonl (never overwritten).
- Logging MUST NOT raise (never blocks trading).
- global_failure_wrapper() MUST log any exception and apply safe fallbacks/retries.
"""

from __future__ import annotations

import json
import time
import traceback as _traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, cast

T = TypeVar("T")

SYSTEM_EVENTS_PATH = Path("logs/system_events.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_system_events_file() -> None:
    try:
        SYSTEM_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Touch (append open creates if missing)
        with SYSTEM_EVENTS_PATH.open("a", encoding="utf-8"):
            pass
    except Exception:
        # Never block execution on logging infrastructure
        pass


def log_system_event(
    subsystem: str,
    event_type: str,
    severity: str,
    **fields: Any,
) -> None:
    """
    Append a structured system event to logs/system_events.jsonl.

    Required fields:
    - timestamp (UTC ISO)
    - subsystem
    - event_type
    - severity: INFO|WARN|ERROR|CRITICAL
    - symbol (optional)
    - details (dict)
    """
    try:
        _ensure_system_events_file()

        symbol = fields.pop("symbol", None)
        details = fields.pop("details", None)
        if details is None:
            details_dict: Dict[str, Any] = {}
        elif isinstance(details, dict):
            details_dict = dict(details)
        else:
            details_dict = {"details": details}
        # Remaining fields are merged into details
        details_dict.update(fields)

        rec: Dict[str, Any] = {
            "timestamp": _now_iso(),
            "subsystem": str(subsystem),
            "event_type": str(event_type),
            "severity": str(severity).upper(),
            "details": details_dict,
        }
        if symbol is not None and str(symbol).strip():
            rec["symbol"] = str(symbol)

        with SYSTEM_EVENTS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        # Never block execution on logging failures
        pass


def _infer_default_fallback(subsystem: str, fn_name: str) -> Any:
    s = (subsystem or "").lower()
    n = (fn_name or "").lower()

    # Gate evaluation must fail closed (do not trade) on errors.
    if s in ("gate", "gating"):
        return False

    # Decision engine/orchestrator should fail open to "do nothing this cycle".
    if s in ("decision", "decision_engine", "engine"):
        # Common decision functions return list[orders] or dict[metrics]; infer from name.
        if any(k in n for k in ("decide", "execute", "orders")):
            return []
        return {}

    # Read-only/data/cache layers: safe empty/None.
    # Note: "bar_fetch" returns None by contract (stale/no bars => None).
    if s in ("bar_fetch", "bars"):
        return None
    if s in ("data", "market_data"):
        return {}
    if s in ("uw_cache", "cache", "uw_daemon", "uw_poll"):
        return {}

    # Scoring: safe neutral score (prevents unintended trades).
    if s in ("scoring", "signals", "composite", "score"):
        return {"score": 0.0, "components": {}, "notes": "fallback_score_due_to_exception"}

    # Orders/exits: return None to signal failure upstream (but logged).
    if s in ("order", "orders", "execution", "order_submission", "exit"):
        return None

    # Heuristic based on function naming.
    if "read" in n or "load" in n or "cache" in n:
        return {}
    if "score" in n or "composite" in n:
        return {"score": 0.0, "components": {}, "notes": "fallback_score_due_to_exception"}
    return None


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    base_delay_sec: float = 0.5
    backoff_mult: float = 2.0
    max_delay_sec: float = 5.0


def _retry_policy_for(subsystem: str) -> RetryPolicy:
    s = (subsystem or "").lower()
    if s in ("order", "orders", "execution", "order_submission"):
        return RetryPolicy(max_attempts=3, base_delay_sec=0.5, backoff_mult=2.0, max_delay_sec=5.0)
    if s in ("exit",):
        return RetryPolicy(max_attempts=3, base_delay_sec=0.5, backoff_mult=2.0, max_delay_sec=5.0)
    return RetryPolicy(max_attempts=1)


def global_failure_wrapper(subsystem: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that:
    - logs ANY exception as a CRITICAL system event (with traceback)
    - retries safely for order/exit subsystems
    - returns a safe fallback value so failures are never silent
    """

    def _decorator(fn: Callable[..., T]) -> Callable[..., T]:
        fn_name = getattr(fn, "__name__", "unknown")
        policy = _retry_policy_for(subsystem)

        def _wrapped(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            delay = float(policy.base_delay_sec)
            last_err: Optional[BaseException] = None
            last_tb: Optional[str] = None

            while attempt < int(policy.max_attempts):
                attempt += 1
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    last_tb = _traceback.format_exc()

                    # Order/exit retries get ERROR per-attempt; final gets CRITICAL.
                    sev = "ERROR" if attempt < int(policy.max_attempts) else "CRITICAL"
                    log_system_event(
                        subsystem=subsystem,
                        event_type="exception",
                        severity=sev,
                        function=fn_name,
                        attempt=attempt,
                        max_attempts=int(policy.max_attempts),
                        error=str(e),
                        traceback=last_tb,
                    )

                    if attempt < int(policy.max_attempts):
                        try:
                            time.sleep(min(delay, float(policy.max_delay_sec)))
                        except Exception:
                            pass
                        delay = min(float(policy.max_delay_sec), delay * float(policy.backoff_mult))
                        continue

            # Fallback (never propagate silently).
            fb = _infer_default_fallback(subsystem, fn_name)
            # Include context as a WARN so downstream can spot fallback activations.
            try:
                log_system_event(
                    subsystem=subsystem,
                    event_type="fallback_returned",
                    severity="WARN",
                    function=fn_name,
                    error=str(last_err) if last_err else None,
                )
            except Exception:
                pass
            return cast(T, fb)

        return _wrapped

    return _decorator


def read_last_system_events(
    limit: int = 500,
    *,
    subsystem: Optional[str] = None,
    severity: Optional[str] = None,
    symbol: Optional[str] = None,
) -> list[dict]:
    """
    Best-effort tail reader for the dashboard (no dependencies).
    Reads from end of file to avoid loading huge files (perf fix).
    """
    try:
        _ensure_system_events_file()
        if not SYSTEM_EVENTS_PATH.exists():
            return []

        # Read last ~200KB max to avoid loading huge files (typical line ~200 bytes → ~1000 lines)
        file_size = SYSTEM_EVENTS_PATH.stat().st_size
        read_size = min(200000, file_size)
        with SYSTEM_EVENTS_PATH.open("r", encoding="utf-8", errors="ignore") as f:
            if file_size > read_size:
                f.seek(max(0, file_size - read_size))
                f.readline()  # Skip partial line
            lines = f.read().splitlines()
        rows = []
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if subsystem and str(rec.get("subsystem", "")).lower() != subsystem.lower():
                continue
            if severity and str(rec.get("severity", "")).upper() != severity.upper():
                continue
            if symbol and str(rec.get("symbol", "")).upper() != symbol.upper():
                continue
            rows.append(rec)
            if len(rows) >= int(limit):
                break
        return list(reversed(rows))
    except Exception:
        return []

