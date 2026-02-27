#!/usr/bin/env python3
"""
UW failure diagnostics and governance. No silent failures.
- Classify every UW reject/penalize into exactly one failure class.
- Diagnose data-related vs genuine low signal.
- Auto-repair for data failures; escalate when repair fails or pattern persists.
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# Failure classes (every UW decision that blocks/penalizes emits exactly one)
UW_MISSING_DATA = "UW_MISSING_DATA"
UW_STALE_DATA = "UW_STALE_DATA"
UW_CONTRADICTORY_DATA = "UW_CONTRADICTORY_DATA"
UW_LOW_QUALITY_SIGNAL = "UW_LOW_QUALITY_SIGNAL"  # genuine
UW_INTERNAL_ERROR = "UW_INTERNAL_ERROR"

REPO_ROOT = Path(__file__).resolve().parents[2]
UW_HEALTH_DIR = REPO_ROOT / "reports" / "uw_health"
UW_FAILURE_EVENTS_JSONL = UW_HEALTH_DIR / "uw_failure_events.jsonl"
INCIDENTS_DIR = REPO_ROOT / "reports" / "incidents"

# Escalation: same failure_class > N times in window_minutes, or first_ts to last_ts > persist_minutes
ESCALATION_COUNT_THRESHOLD = int(os.environ.get("UW_ESCALATION_COUNT", "50"))
ESCALATION_WINDOW_MINUTES = int(os.environ.get("UW_ESCALATION_WINDOW_MIN", "60"))
ESCALATION_PERSIST_MINUTES = int(os.environ.get("UW_ESCALATION_PERSIST_MIN", "30"))

# Repair: paper-only by default
UW_REPAIR_ENABLED = os.environ.get("UW_REPAIR_ENABLED", "1").strip().lower() in ("1", "true", "yes")
UW_BOUNDED_PENALTY_AFTER_REPAIR_FAIL = float(os.environ.get("UW_MISSING_INPUT_PENALTY", "0.75"))


def _append_jsonl(path: Path, rec: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        pass


def _uw_root_cause_file_and_date(base: Path) -> tuple[Path | None, str | None]:
    """Return (path to latest uw_root_cause.json, date_str of that file) or (None, None)."""
    out_dir = base / "board" / "eod" / "out"
    if not out_dir.exists():
        return None, None
    best_path = None
    best_date = ""
    for d in out_dir.iterdir():
        if d.is_dir() and len(d.name) == 10 and d.name[4] == "-":
            p = d / "uw_root_cause.json"
            if p.exists() and d.name > best_date:
                best_path = p
                best_date = d.name
    return best_path, best_date if best_date else None


def _bars_status(symbol: str, date_str: str, base: Path) -> dict[str, Any]:
    """Return bars dependency status: has_bars, count, path_exists."""
    if not date_str or not symbol:
        return {"has_bars": False, "count": 0, "path_exists": False, "reason": "no_date_or_symbol"}
    bars_dir = base / "data" / "bars" / date_str
    path = bars_dir / f"{symbol.replace('/', '_')}_1Min.json"
    if not path.exists():
        return {"has_bars": False, "count": 0, "path_exists": False, "reason": "NO_BARS"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        bars = data.get("bars", data) if isinstance(data, dict) else data
        count = len(bars) if isinstance(bars, list) else 0
        return {"has_bars": count > 0, "count": count, "path_exists": True, "reason": "ok" if count else "empty"}
    except Exception as e:
        return {"has_bars": False, "count": 0, "path_exists": True, "reason": str(e)}


# Minimum bar count to consider lookback sufficient (e.g. for signal quality)
LOOKBACK_MIN_BARS = int(os.environ.get("UW_LOOKBACK_MIN_BARS", "10"))
# Staleness: uw root cause file older than this many hours → stale
UW_ROOT_CAUSE_STALE_HOURS = float(os.environ.get("UW_ROOT_CAUSE_STALE_HOURS", "24"))


def detect_missing_data_indicators(
    symbol: str,
    data: dict[str, Any],
    timestamps: dict[str, Any] | None = None,
    base: Path | None = None,
) -> dict[str, Any]:
    """
    Returns a struct of booleans indicating missing/stale data. Used to enforce:
    if ANY is true → never classify as UW_LOW_QUALITY_SIGNAL; use UW_MISSING_DATA or UW_STALE_DATA.
    """
    base = base or REPO_ROOT
    timestamps = timestamps or {}
    eval_ts = timestamps.get("evaluation_ts") or time.time()
    date_str = ""
    try:
        from datetime import datetime as dt_cls
        date_str = dt_cls.fromtimestamp(int(eval_ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        pass
    now_date = timestamps.get("evaluation_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    bars_status = _bars_status(symbol, date_str, base) if symbol and date_str else {"has_bars": False, "count": 0, "path_exists": False}
    no_bars = not bars_status.get("has_bars") and not bars_status.get("path_exists")
    bars_empty = bars_status.get("path_exists") and bars_status.get("count", 0) == 0
    bars_stale = False  # bars are per-day; "stale" here means wrong day or empty
    if date_str and now_date and date_str < now_date:
        bars_stale = True

    uw_path, uw_date = _uw_root_cause_file_and_date(base)
    uw_root_cause_missing = not uw_path or not uw_path.exists()
    uw_root_cause_stale = False
    if uw_date and now_date:
        try:
            from datetime import datetime as dt_parse
            file_dt = dt_parse.strptime(uw_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            now_dt = dt_parse.strptime(now_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            lag_hours = (now_dt - file_dt).total_seconds() / 3600
            uw_root_cause_stale = lag_hours > UW_ROOT_CAUSE_STALE_HOURS
        except Exception:
            pass

    required_fields_missing: list[str] = []
    if not data:
        required_fields_missing.append("uw_root_cause_data")
    else:
        candidates = data.get("candidates") or []
        cand = next((c for c in candidates if c.get("symbol") == symbol), None)
        if cand is None and data.get("uw_signal_quality_score") is None:
            required_fields_missing.append("uw_quality_for_symbol")
        if not candidates and data.get("uw_signal_quality_score") is None:
            required_fields_missing.append("uw_signal_quality_score")

    lookback_insufficient = (bars_status.get("count") or 0) < LOOKBACK_MIN_BARS

    return {
        "no_bars": no_bars,
        "bars_empty": bars_empty,
        "bars_stale": bars_stale,
        "uw_root_cause_missing": uw_root_cause_missing,
        "uw_root_cause_stale": uw_root_cause_stale,
        "required_fields_missing": required_fields_missing,
        "lookback_insufficient": lookback_insufficient,
    }


def diagnose_uw_failure(
    inputs: dict[str, Any],
    symbol: str,
    bars: Any = None,
    timestamps: dict[str, Any] | None = None,
    caches: dict[str, Any] | None = None,
    base: Path | None = None,
) -> dict[str, Any]:
    """
    Determine why UW would reject/penalize. Returns:
    - failure_class: one of UW_* constants
    - missing_inputs: list of missing dependency names
    - upstream_dependency_status: dict
    - decision_taken: reject | penalize | defer (recommended)
    - details: extra for logging
    """
    base = base or REPO_ROOT
    timestamps = timestamps or {}
    caches = caches or {}
    missing_inputs: list[str] = []
    upstream: dict[str, Any] = {}

    try:
        # UW root cause file (only used when inputs are empty or we need staleness)
        uw_path, uw_date = _uw_root_cause_file_and_date(base)
        upstream["uw_root_cause_file"] = str(uw_path) if uw_path else None
        upstream["uw_root_cause_date"] = uw_date
        data = inputs if isinstance(inputs, dict) else {}
        # If no data at all, classify from file presence/staleness
        if not data:
            indicators_empty = detect_missing_data_indicators(symbol, data, timestamps, base)
            if not uw_path or not uw_path.exists():
                missing_inputs.append("uw_root_cause.json")
                return {
                    "failure_class": UW_MISSING_DATA,
                    "missing_inputs": missing_inputs,
                    "upstream_dependency_status": upstream,
                    "decision_taken": os.environ.get("UW_MISSING_DATA_POLICY", "defer").strip().lower() or "defer",
                    "details": {"reason": "no_uw_root_cause_file"},
                    "missing_data_indicators": indicators_empty,
                }
            now_date = (timestamps.get("evaluation_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            if uw_date and now_date and uw_date < now_date:
                try:
                    from datetime import datetime as dt_parse
                    file_dt = dt_parse.strptime(uw_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    now_dt = dt_parse.strptime(now_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    lag_hours = (now_dt - file_dt).total_seconds() / 3600
                    upstream["uw_file_lag_hours"] = round(lag_hours, 2)
                    if lag_hours > 24:
                        missing_inputs.append("uw_root_cause_fresh")
                        return {
                            "failure_class": UW_STALE_DATA,
                            "missing_inputs": missing_inputs,
                            "upstream_dependency_status": upstream,
                            "decision_taken": os.environ.get("UW_MISSING_DATA_POLICY", "defer").strip().lower() or "defer",
                            "details": {"reason": "uw_file_stale", "lag_hours": lag_hours},
                            "missing_data_indicators": indicators_empty,
                        }
                except Exception:
                    pass

        # Inputs: data from load_uw_root_cause_latest
        quality = data.get("uw_signal_quality_score")
        candidates = data.get("candidates") or []
        cand = next((c for c in candidates if c.get("symbol") == symbol), None)
        cand_quality = cand.get("uw_signal_quality_score") if cand else None
        if cand_quality is not None:
            try:
                cand_quality = float(cand_quality)
            except (TypeError, ValueError):
                cand_quality = None
        use_quality = cand_quality if cand_quality is not None else (float(quality) if quality is not None else None)

        # Always compute missing-data indicators for precedence and logging
        indicators = detect_missing_data_indicators(symbol, data, timestamps, base)

        # Missing: symbol not in candidates and no global quality
        if use_quality is None:
            if not candidates:
                missing_inputs.append("uw_candidates")
            else:
                missing_inputs.append("uw_quality_for_symbol")
            eval_ts = timestamps.get("evaluation_ts") or time.time()
            try:
                from datetime import datetime as dt_cls
                dt = dt_cls.fromtimestamp(int(eval_ts), tz=timezone.utc)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                date_str = ""
            bars_status = _bars_status(symbol, date_str, base)
            upstream["bars"] = bars_status
            if not bars_status.get("has_bars"):
                missing_inputs.append("bars")
            _policy = os.environ.get("UW_MISSING_DATA_POLICY", "defer").strip().lower()
            if _policy not in ("defer", "penalize"):
                _policy = "defer"
            return {
                "failure_class": UW_MISSING_DATA,
                "missing_inputs": missing_inputs,
                "upstream_dependency_status": upstream,
                "decision_taken": _policy,
                "details": {"reason": "no_quality_for_symbol", "bars": bars_status},
                "missing_data_indicators": indicators,
            }

        # Quality present but low: allow UW_LOW_QUALITY_SIGNAL ONLY if no missing-data indicators
        threshold = float(os.environ.get("UW_QUALITY_PRE_FILTER_MIN", "0.25"))
        any_missing = (
            indicators.get("no_bars") or indicators.get("bars_empty") or indicators.get("bars_stale")
            or indicators.get("uw_root_cause_missing") or indicators.get("uw_root_cause_stale")
            or len(indicators.get("required_fields_missing") or []) > 0
            or indicators.get("lookback_insufficient")
        )
        if any_missing:
            # Precedence: never classify as low quality when data is missing/stale
            failure_class = UW_STALE_DATA if (indicators.get("uw_root_cause_stale") or indicators.get("bars_stale")) else UW_MISSING_DATA
            decision = os.environ.get("UW_MISSING_DATA_POLICY", "defer").strip().lower()
            if decision not in ("defer", "penalize"):
                decision = "defer"
            return {
                "failure_class": failure_class,
                "missing_inputs": list(indicators.get("required_fields_missing") or []) + (["bars"] if (indicators.get("no_bars") or indicators.get("bars_empty")) else []),
                "upstream_dependency_status": {**upstream, "uw_signal_quality_score": use_quality},
                "decision_taken": decision,
                "details": {"reason": "missing_data_indicator_blocks_low_quality", "quality": use_quality, "indicators": indicators},
                "missing_data_indicators": indicators,
            }
        if use_quality < threshold:
            return {
                "failure_class": UW_LOW_QUALITY_SIGNAL,
                "missing_inputs": [],
                "upstream_dependency_status": {**upstream, "uw_signal_quality_score": use_quality},
                "decision_taken": "reject",
                "details": {"reason": "quality_below_threshold", "quality": use_quality, "threshold": threshold},
                "missing_data_indicators": indicators,
            }

        # Contradictory: e.g. global vs candidate mismatch (optional heuristic)
        if quality is not None and cand_quality is not None and abs(float(quality) - float(cand_quality)) > 0.5:
            return {
                "failure_class": UW_CONTRADICTORY_DATA,
                "missing_inputs": ["uw_consistency"],
                "upstream_dependency_status": {**upstream, "global_quality": quality, "cand_quality": cand_quality},
                "decision_taken": "penalize",
                "details": {"reason": "global_vs_candidate_mismatch"},
                "missing_data_indicators": indicators,
            }

        # Should not reach here for a "failure" path; if we do, treat as internal
        return {
            "failure_class": UW_LOW_QUALITY_SIGNAL,
            "missing_inputs": [],
            "upstream_dependency_status": upstream,
            "decision_taken": "reject",
            "details": {"reason": "unknown"},
            "missing_data_indicators": indicators,
        }
    except Exception as e:
        return {
            "failure_class": UW_INTERNAL_ERROR,
            "missing_inputs": ["diagnostic_error"],
            "upstream_dependency_status": {"error": str(e), "error_type": type(e).__name__},
            "decision_taken": "penalize",
            "details": {"reason": "exception", "error": str(e)},
            "missing_data_indicators": {"no_bars": False, "bars_empty": False, "bars_stale": False, "uw_root_cause_missing": False, "uw_root_cause_stale": False, "required_fields_missing": ["diagnostic_error"], "lookback_insufficient": False},
        }


def attempt_repair(
    failure_class: str,
    symbol: str,
    base: Path | None = None,
) -> dict[str, Any]:
    """
    Safe repair for UW_MISSING_DATA and UW_STALE_DATA. Paper-only.
    Returns: { repair_attempted, repair_action, repair_success, message }.
    """
    base = base or REPO_ROOT
    if failure_class not in (UW_MISSING_DATA, UW_STALE_DATA):
        return {"repair_attempted": False, "repair_action": None, "repair_success": False, "message": "not_data_failure"}
    if not UW_REPAIR_ENABLED:
        return {"repair_attempted": False, "repair_action": "disabled", "repair_success": False, "message": "UW_REPAIR_ENABLED=0"}

    repair_attempted = True
    repair_action = []
    repair_success = False

    # 1) Recompute UW root cause and write to board/eod/out/<date>/uw_root_cause.json
    try:
        from board.eod.root_cause import build_uw_root_cause
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_dir = base / "board" / "eod" / "out" / date_str
        out_dir.mkdir(parents=True, exist_ok=True)
        data = build_uw_root_cause(base, date_str, window_days=7)
        (out_dir / "uw_root_cause.json").write_text(json.dumps(data, default=str), encoding="utf-8")
        repair_action.append("recompute_uw_root_cause")
        repair_success = True
    except Exception as e:
        repair_action.append(f"recompute_uw_root_cause_failed:{e!s}")
    # 2) Bar refresh: trigger bar load for symbol/today (no-op if already present)
    try:
        from data.bars_loader import load_bars
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        bars = load_bars(symbol, date_str, "1Min", use_cache=True, fetch_if_missing=True)
        if bars:
            repair_action.append("bars_refresh")
            repair_success = True
        else:
            repair_action.append("bars_refresh_no_bars")
    except Exception as e:
        repair_action.append(f"bars_refresh_failed:{e!s}")

    return {
        "repair_attempted": repair_attempted,
        "repair_action": repair_action,
        "repair_success": repair_success,
        "message": "ok" if repair_success else "repair_attempted_no_guarantee",
    }


def should_escalate(
    failure_class: str,
    symbol: str,
    event_ts: float,
    events_path: Path | None = None,
) -> bool:
    """True if same failure_class exceeds count in window or persists > T minutes."""
    path = events_path or UW_FAILURE_EVENTS_JSONL
    if not path.exists():
        return False
    window_sec = ESCALATION_WINDOW_MINUTES * 60
    persist_sec = ESCALATION_PERSIST_MINUTES * 60
    cutoff = event_ts - window_sec
    events: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                ts = float(r.get("ts") or r.get("event_ts") or 0)
                if ts >= cutoff:
                    events.append(r)
            except Exception:
                continue
    except Exception:
        return False
    same_class = [r for r in events if r.get("failure_class") == failure_class]
    if len(same_class) >= ESCALATION_COUNT_THRESHOLD:
        return True
    if same_class:
        tss = [float(r.get("ts") or r.get("event_ts") or 0) for r in same_class]
        if max(tss) - min(tss) >= persist_sec:
            return True
    return False


def write_incident(
    failure_class: str,
    affected_symbols: list[str],
    duration_minutes: float,
    attempted_repairs: list[dict],
    impact: str,
    base: Path | None = None,
) -> Path | None:
    """Write reports/incidents/uw_data_incident_<date>.md. Returns path or None."""
    base = base or REPO_ROOT
    inc_dir = base / "reports" / "incidents"
    inc_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = inc_dir / f"uw_data_incident_{date_str}.md"
    lines = [
        "# UW data incident",
        "",
        f"- **failure_class**: {failure_class}",
        f"- **affected_symbols**: {affected_symbols[:50]}{' ...' if len(affected_symbols) > 50 else ''}",
        f"- **duration_minutes**: {duration_minutes:.1f}",
        f"- **attempted_repairs**: {len(attempted_repairs)}",
        "",
        "## Attempted repairs",
        "",
    ]
    for r in attempted_repairs:
        lines.append(f"- {r.get('repair_action')} success={r.get('repair_success')}")
    lines.extend(["", "## Current impact on trading", "", impact, ""])
    try:
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
    except Exception:
        return None


def load_recent_failure_events(path: Path | None = None, limit: int = 5000) -> list[dict]:
    """Last N events from uw_failure_events.jsonl (newest at end)."""
    path = path or UW_FAILURE_EVENTS_JSONL
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
        if len(out) >= limit:
            out = out[-limit:]
    return out[-limit:]
