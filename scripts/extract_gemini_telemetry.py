#!/usr/bin/env python3
"""
Extract last 48h of telemetry into flat CSVs under reports/Gemini/.
Fail-safe JSONL parsing; no secrets or raw IPs in output columns.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
OUT_DIR = REPO_ROOT / "reports" / "Gemini"
LOGS = REPO_ROOT / "logs"
DATA = REPO_ROOT / "data"

try:
    from src.governance.canonical_trade_count import (
        _parse_exit_epoch,
        iter_harvester_era_exit_records_for_csv,
    )
    from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START
except Exception:  # pragma: no cover
    iter_harvester_era_exit_records_for_csv = None  # type: ignore
    _parse_exit_epoch = None  # type: ignore
    STRICT_EPOCH_START = 1777075199.0  # fallback; sync with alpaca_strict_completeness_gate

# IPv4 quick redact (for any string fields we serialize)
_IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def window_48h(now: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    end = now or utc_now()
    start = end - timedelta(hours=48)
    return start, end


def parse_ts(rec: Dict[str, Any]) -> Optional[datetime]:
    """Best-effort extract event time as timezone-aware UTC."""
    for key in ("timestamp", "ts", "entry_ts", "exit_ts", "time"):
        v = rec.get(key)
        if v is None:
            continue
        if isinstance(v, (int, float)):
            x = float(v)
            if x > 1e12:  # ms
                x = x / 1000.0
            if x > 1e9:
                try:
                    return datetime.fromtimestamp(x, tz=timezone.utc)
                except (OSError, ValueError, OverflowError):
                    continue
        if isinstance(v, str) and v.strip():
            s = v.strip().replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                continue
    ts = rec.get("_ts")
    if isinstance(ts, (int, float)) and ts > 1e9:
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            pass
    return None


def in_window(dt: Optional[datetime], start: datetime, end: datetime) -> bool:
    if dt is None:
        return False
    return start <= dt <= end


def redact_text(s: str) -> str:
    if not s:
        return s
    return _IP_RE.sub("[REDACTED_IP]", s)


def safe_str(x: Any, max_len: int = 2000) -> str:
    if x is None:
        return ""
    if isinstance(x, (dict, list)):
        try:
            t = json.dumps(x, default=str, ensure_ascii=False)
        except Exception:
            t = str(x)
    else:
        t = str(x)
    t = redact_text(t)
    if len(t) > max_len:
        t = t[: max_len - 3] + "..."
    return t


def iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    if not path.is_file():
        return
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def write_csv(path: Path, headers: List[str], rows: List[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})
    return len(rows)


# --- row builders ---

ENTRIES_HEADERS = [
    "timestamp_utc",
    "source_file",
    "event_kind",
    "symbol",
    "side",
    "requested_qty",
    "filled_qty",
    "limit_or_intended_price",
    "fill_price",
    "slippage_bps",
    "realized_pnl_usd",
    "trade_id",
    "notes",
]


def rows_from_live_orders(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        ev = str(rec.get("event") or "")
        if rec.get("fill_price") is None and "fill" not in ev.lower() and "FILLED" not in ev:
            continue
        side = rec.get("side") or rec.get("position_side") or ""
        row = {
            "timestamp_utc": dt.isoformat() if dt else "",
            "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "event_kind": ev or "order_event",
            "symbol": rec.get("symbol") or "",
            "side": safe_str(side),
            "requested_qty": rec.get("qty") if rec.get("qty") is not None else "",
            "filled_qty": rec.get("filled_qty") if rec.get("filled_qty") is not None else rec.get("qty") or "",
            "limit_or_intended_price": rec.get("limit_price") if rec.get("limit_price") is not None else "",
            "fill_price": rec.get("fill_price") if rec.get("fill_price") is not None else rec.get("price") or "",
            "slippage_bps": rec.get("slippage_bps") if rec.get("slippage_bps") is not None else "",
            "realized_pnl_usd": "",
            "trade_id": rec.get("order_id") or rec.get("client_order_id") or "",
            "notes": safe_str(rec.get("order_type") or rec.get("status") or ""),
        }
        out.append(row)
    return out


def rows_from_orders_jsonl(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        if rec.get("type") != "order":
            continue
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        action = str(rec.get("action") or "")
        if "filled" not in action.lower() and action != "submit_market_fallback":
            continue
        row = {
            "timestamp_utc": dt.isoformat() if dt else "",
            "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "event_kind": action,
            "symbol": rec.get("symbol") or "",
            "side": rec.get("side") or "",
            "requested_qty": rec.get("qty") if rec.get("qty") is not None else "",
            "filled_qty": rec.get("filled_qty") if rec.get("filled_qty") is not None else rec.get("qty") or "",
            "limit_or_intended_price": rec.get("limit_price") if rec.get("limit_price") is not None else "",
            "fill_price": rec.get("filled_price") if rec.get("filled_price") is not None else "",
            "slippage_bps": "",
            "realized_pnl_usd": "",
            "trade_id": rec.get("order_id") or "",
            "notes": safe_str(rec.get("attempt") or rec.get("error") or ""),
        }
        if row["slippage_bps"] == "" and row["limit_or_intended_price"] and row["fill_price"]:
            try:
                lp = float(row["limit_or_intended_price"])
                fp = float(row["fill_price"])
                if lp > 0:
                    row["slippage_bps"] = round(abs(fp - lp) / lp * 10000, 4)
            except (TypeError, ValueError):
                pass
        out.append(row)
    return out


def rows_from_master_trade_log(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        pnl = rec.get("realized_pnl_usd")
        is_exit = rec.get("exit_ts") is not None or pnl is not None
        kind = "shadow_exit" if rec.get("is_shadow") else ("live_exit" if is_exit else "trade_update")
        row = {
            "timestamp_utc": dt.isoformat() if dt else "",
            "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "event_kind": kind,
            "symbol": rec.get("symbol") or "",
            "side": rec.get("side") or "",
            "requested_qty": rec.get("size") if rec.get("size") is not None else "",
            "filled_qty": rec.get("size") if rec.get("size") is not None else "",
            "limit_or_intended_price": rec.get("entry_price") if rec.get("entry_price") is not None else "",
            "fill_price": rec.get("exit_price") if rec.get("exit_price") is not None else "",
            "slippage_bps": "",
            "realized_pnl_usd": pnl if pnl is not None else "",
            "trade_id": rec.get("trade_id") or "",
            "notes": safe_str(rec.get("exit_reason") or rec.get("source") or ""),
        }
        out.append(row)
    return out


def rows_from_attribution(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        if rec.get("type") != "attribution":
            continue
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        row = {
            "timestamp_utc": dt.isoformat() if dt else "",
            "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "event_kind": "attribution_close",
            "symbol": rec.get("symbol") or "",
            "side": (rec.get("context") or {}).get("side") if isinstance(rec.get("context"), dict) else "",
            "requested_qty": (rec.get("context") or {}).get("qty") if isinstance(rec.get("context"), dict) else "",
            "filled_qty": (rec.get("context") or {}).get("qty") if isinstance(rec.get("context"), dict) else "",
            "limit_or_intended_price": (rec.get("context") or {}).get("entry_price") or "",
            "fill_price": (rec.get("context") or {}).get("exit_price") or "",
            "slippage_bps": "",
            "realized_pnl_usd": rec.get("pnl_usd") if rec.get("pnl_usd") is not None else "",
            "trade_id": rec.get("trade_id") or "",
            "notes": safe_str((rec.get("context") or {}).get("close_reason") or ""),
        }
        out.append(row)
    return out


def exit_attribution_rec_to_entry_row(rec: Dict[str, Any], path: Path) -> Dict[str, Any]:
    """Build ENTRIES_HEADERS row; timestamp_utc is exit time (canonical harvester semantics)."""
    ex = _parse_exit_epoch(rec) if _parse_exit_epoch else None
    dt = datetime.fromtimestamp(ex, tz=timezone.utc) if ex is not None else None
    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
    pnl = snap.get("pnl")
    return {
        "timestamp_utc": dt.isoformat() if dt else "",
        "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "event_kind": "exit_attribution",
        "symbol": rec.get("symbol") or "",
        "side": "",
        "requested_qty": snap.get("qty") or "",
        "filled_qty": snap.get("qty") or "",
        "limit_or_intended_price": snap.get("entry_price") or "",
        "fill_price": snap.get("exit_price") or "",
        "slippage_bps": "",
        "realized_pnl_usd": pnl if pnl is not None else "",
        "trade_id": rec.get("trade_id") or "",
        "notes": safe_str(rec.get("exit_reason") or rec.get("winner") or ""),
    }


def rows_from_exit_attribution(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
        pnl = snap.get("pnl")
        row = {
            "timestamp_utc": dt.isoformat() if dt else "",
            "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "event_kind": "exit_attribution",
            "symbol": rec.get("symbol") or "",
            "side": "",
            "requested_qty": snap.get("qty") or "",
            "filled_qty": snap.get("qty") or "",
            "limit_or_intended_price": snap.get("entry_price") or "",
            "fill_price": snap.get("exit_price") or "",
            "slippage_bps": "",
            "realized_pnl_usd": pnl if pnl is not None else "",
            "trade_id": rec.get("trade_id") or "",
            "notes": safe_str(rec.get("exit_reason") or rec.get("winner") or ""),
        }
        out.append(row)
    return out


def rows_from_alpaca_unified(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        et = str(rec.get("event_type") or "")
        if et == "alpaca_exit_attribution":
            dt = parse_ts(rec)
            if not in_window(dt, start, end):
                continue
            snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
            pnl = snap.get("pnl")
            row = {
                "timestamp_utc": dt.isoformat() if dt else "",
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "event_kind": "alpaca_exit_attribution",
                "symbol": rec.get("symbol") or "",
                "side": "",
                "requested_qty": "",
                "filled_qty": "",
                "limit_or_intended_price": "",
                "fill_price": "",
                "slippage_bps": "",
                "realized_pnl_usd": pnl if pnl is not None else "",
                "trade_id": rec.get("trade_id") or "",
                "notes": safe_str(rec.get("winner_explanation") or rec.get("winner") or ""),
            }
            out.append(row)
    return out


BLOCKED_HEADERS = [
    "timestamp_utc",
    "source_file",
    "category",
    "symbol",
    "score",
    "rejection_reason",
    "detail",
]


def rows_blocked_orders(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    blocked_actions = (
        "trade_guard_blocked",
        "spread_watchdog_blocked",
        "min_notional_blocked",
        "insufficient_buying_power",
        "market_fail",
        "limit_retry_failed",
        "limit_final_failed",
        "price_exceeds_cap",
        "asset_not_shortable_blocked",
    )
    for rec in iter_jsonl(path):
        if rec.get("type") != "order":
            continue
        action = str(rec.get("action") or "")
        if action not in blocked_actions and "blocked" not in action.lower() and "fail" not in action.lower():
            continue
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        cat = "trade_guard"
        if "spread" in action:
            cat = "spread_watchdog"
        elif "notional" in action or "buying_power" in action or "margin" in action:
            cat = "margin"
        elif "market_fail" in action or "fail" in action:
            cat = "api_or_execution"
        reason = rec.get("reason") or rec.get("error") or action
        out.append(
            {
                "timestamp_utc": dt.isoformat() if dt else "",
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "category": cat,
                "symbol": rec.get("symbol") or "",
                "score": "",
                "rejection_reason": safe_str(reason),
                "detail": safe_str(rec.get("error_details") or rec.get("spread_bps") or ""),
            }
        )
    return out


def rows_gate_diagnostic(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        if str(rec.get("decision") or "").lower() not in ("blocked", "reject", "rejected"):
            if "gate" not in str(rec.get("gate_name") or "").lower() and rec.get("status") != "rejected":
                continue
        details = rec.get("details") if isinstance(rec.get("details"), dict) else {}
        score = details.get("score") or details.get("signal_score") or rec.get("score")
        out.append(
            {
                "timestamp_utc": dt.isoformat() if dt else "",
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "category": "score_or_entry_gate",
                "symbol": rec.get("symbol") or "",
                "score": score if score is not None else "",
                "rejection_reason": safe_str(rec.get("gate_name") or rec.get("reason") or rec.get("msg") or ""),
                "detail": safe_str(details),
            }
        )
    return out


def rows_run_trade_intent_blocked(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        if str(rec.get("event_type") or "") != "trade_intent":
            continue
        br = rec.get("blocked_reason")
        if br is None or str(br).strip() == "" or str(br).lower() in ("null", "none"):
            continue
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        out.append(
            {
                "timestamp_utc": dt.isoformat() if dt else "",
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "category": "trade_intent_blocked",
                "symbol": rec.get("symbol") or "",
                "score": rec.get("score") if rec.get("score") is not None else "",
                "rejection_reason": safe_str(br),
                "detail": safe_str(rec.get("decision_outcome") or ""),
            }
        )
    return out


def rows_critical_api_log(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.is_file():
        return out
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|", 2)]
        if len(parts) < 2:
            continue
        iso = parts[0]
        tag = parts[1] if len(parts) > 1 else ""
        rest = parts[2] if len(parts) > 2 else ""
        try:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(timezone.utc)
        except ValueError:
            continue
        if not in_window(dt, start, end):
            continue
        sym = ""
        score = ""
        try:
            jd = json.loads(rest) if rest.startswith("{") else {}
            sym = jd.get("symbol") or ""
        except json.JSONDecodeError:
            jd = {}
        out.append(
            {
                "timestamp_utc": dt.isoformat(),
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "category": "critical_api_failure",
                "symbol": sym,
                "score": score,
                "rejection_reason": safe_str(tag),
                "detail": safe_str(rest[:1500]),
            }
        )
    return out


def rows_system_events_blocked(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        et = str(rec.get("event_type") or "").lower()
        if "block" not in et and "reject" not in et and "denied" not in et:
            continue
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        details = rec.get("details") if isinstance(rec.get("details"), dict) else {}
        out.append(
            {
                "timestamp_utc": dt.isoformat() if dt else "",
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "category": "system_event",
                "symbol": rec.get("symbol") or details.get("symbol") or "",
                "score": details.get("score") or "",
                "rejection_reason": safe_str(rec.get("event_type") or rec.get("reason") or ""),
                "detail": safe_str(details),
            }
        )
    return out


SHADOW_HEADERS = [
    "timestamp_utc",
    "source_file",
    "record_type",
    "symbol",
    "side",
    "variant_or_promo",
    "score_or_metric",
    "would_enter",
    "blocked_reason",
    "extra",
]


def rows_shadow_jsonl(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        et = str(rec.get("event_type") or "")
        out.append(
            {
                "timestamp_utc": dt.isoformat() if dt else "",
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "record_type": et or "shadow",
                "symbol": rec.get("symbol") or "",
                "side": rec.get("side") or "",
                "variant_or_promo": rec.get("variant_name") or "",
                "score_or_metric": rec.get("v2_score_variant") if rec.get("v2_score_variant") is not None else "",
                "would_enter": rec.get("would_enter") if rec.get("would_enter") is not None else "",
                "blocked_reason": safe_str(rec.get("blocked_reason") or ""),
                "extra": safe_str({k: v for k, v in rec.items() if k not in ("feature_snapshot", "thesis_tags")}),
            }
        )
    return out


def rows_paper_exec_decisions(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        out.append(
            {
                "timestamp_utc": dt.isoformat() if dt else "",
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "record_type": str(rec.get("event") or rec.get("action") or "paper_exec"),
                "symbol": rec.get("symbol") or "",
                "side": rec.get("side") or "",
                "variant_or_promo": rec.get("arm") or rec.get("mode") or "paper_exec_promo",
                "score_or_metric": rec.get("entry_score") or rec.get("score") or "",
                "would_enter": "",
                "blocked_reason": safe_str(rec.get("blocked_reason") or rec.get("reason") or ""),
                "extra": safe_str(rec),
            }
        )
    return out


SPI_HEADERS = [
    "timestamp_utc",
    "source_file",
    "symbol",
    "total_score",
    "freshness",
    "component_options_flow",
    "component_dark_pool",
    "component_greeks_gamma",
    "component_ftd_pressure",
    "component_iv_skew",
    "component_oi_change",
    "component_toxicity_penalty",
    "decision",
    "source_tag",
    # Passive / shadow features for ML (not used in streamlined entry weights)
    "shadow_congress",
    "shadow_etf_flow",
    "shadow_market_tide",
    "shadow_insider",
    "shadow_squeeze_score",
    "shadow_calendar",
]


def component_get(comps: Any, *names: str) -> str:
    if not isinstance(comps, dict):
        return ""
    for n in names:
        if n in comps and comps[n] is not None:
            return safe_str(comps[n])
    return ""


SPI_CORE_KEYS = (
    "component_options_flow",
    "component_dark_pool",
    "component_greeks_gamma",
    "component_ftd_pressure",
    "component_iv_skew",
    "component_oi_change",
    "component_toxicity_penalty",
)


def _parse_float_loose(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, str) and not x.strip():
        return None
    if isinstance(x, str) and x.strip().lower() in ("null", "none", "nan"):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v


def _first_present_float(ctr: Dict[str, Any], raw: Dict[str, Any], *keys: str) -> Optional[float]:
    for k in keys:
        for src in (ctr, raw):
            v = _parse_float_loose(src.get(k))
            if v is not None:
                return v
    return None


def _uw_feature_float(uf: Dict[str, Any], *keys: str) -> Optional[float]:
    for k in keys:
        v = _parse_float_loose(uf.get(k))
        if v is not None:
            return v
    return None


def spi_row_components(comps: Any) -> Dict[str, str]:
    """
    Map ``uw_composite_v2`` ``components`` (and merged snapshot blobs) to SPI columns.

    Canonical keys: ``iv_skew``, ``oi_change``, ``toxicity_penalty``. Older rows may only
    have ``iv_term_skew`` for skew; ``component_get`` tries aliases in order. Missing
    keys resolve to ``0.0`` in ``spi_row_components_resolved``.
    """
    if not isinstance(comps, dict):
        comps = {}
    core = {
        "component_options_flow": component_get(comps, "flow", "options_flow", "uw"),
        "component_dark_pool": component_get(comps, "dark_pool", "darkpool"),
        "component_greeks_gamma": component_get(comps, "greeks_gamma"),
        "component_ftd_pressure": component_get(comps, "ftd_pressure"),
        "component_iv_skew": component_get(comps, "iv_skew", "iv_term_skew"),
        "component_oi_change": component_get(comps, "oi_change"),
        "component_toxicity_penalty": component_get(comps, "toxicity_penalty"),
    }
    # Shadow: sidelined components still emitted by uw_composite_v2 for offline analysis
    shadow = {
        "shadow_congress": component_get(comps, "congress"),
        "shadow_etf_flow": component_get(comps, "etf_flow"),
        "shadow_market_tide": component_get(comps, "market_tide"),
        "shadow_insider": component_get(comps, "insider"),
        "shadow_squeeze_score": component_get(comps, "squeeze_score"),
        "shadow_calendar": component_get(comps, "calendar"),
    }
    for k, v in shadow.items():
        if v == "":
            shadow[k] = "0.0"
    return {**core, **shadow}


def spi_row_components_resolved(
    comps: Any,
    *,
    contributions: Optional[Dict[str, Any]] = None,
    raw_signals: Optional[Dict[str, Any]] = None,
    uw_features: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Same as spi_row_components plus fallbacks: Alpaca `contributions` / `raw_signals`, then `uw_features`.
    All seven core component_* columns are emitted as finite float strings (default 0.0).
    """
    base = spi_row_components(comps if isinstance(comps, dict) else {})
    ctr = contributions if isinstance(contributions, dict) else {}
    raw = raw_signals if isinstance(raw_signals, dict) else {}
    uf = uw_features if isinstance(uw_features, dict) else {}
    out = dict(base)

    picks: Dict[str, float] = {}
    for col in SPI_CORE_KEYS:
        v0 = _parse_float_loose(out.get(col))
        if v0 is not None:
            picks[col] = v0
            continue
        alt: Optional[float] = None
        if col == "component_options_flow":
            alt = _first_present_float(ctr, raw, "flow_deterioration", "flow", "options_flow")
            if alt is None:
                alt = _uw_feature_float(uf, "flow_strength", "flow_score", "net_premium_flow", "options_flow")
        elif col == "component_dark_pool":
            alt = _first_present_float(ctr, raw, "darkpool_deterioration", "dark_pool", "darkpool")
            if alt is None:
                alt = _uw_feature_float(uf, "darkpool_bias", "dark_pool_strength", "darkpool")
        elif col == "component_greeks_gamma":
            alt = _first_present_float(ctr, raw, "vol_expansion", "greeks_gamma", "gamma")
            if alt is None:
                alt = _uw_feature_float(uf, "greeks_gamma", "gamma_exposure", "gamma", "vol_regime_score")
        elif col == "component_ftd_pressure":
            alt = _first_present_float(ctr, raw, "regime_shift", "ftd_pressure", "settlement_pressure")
            if alt is None:
                alt = _uw_feature_float(uf, "ftd_pressure", "ftd", "settlement_risk")
        elif col == "component_iv_skew":
            alt = _first_present_float(ctr, raw, "sector_shift", "iv_skew", "iv_term_skew")
            if alt is None:
                alt = _uw_feature_float(uf, "iv_skew", "skew", "iv_rank")
        elif col == "component_oi_change":
            alt = _first_present_float(
                ctr,
                raw,
                "sentiment_deterioration",
                "overnight_flow_risk",
                "oi_change",
                "thesis_invalidated",
            )
            if alt is None:
                alt = _uw_feature_float(uf, "oi_change", "open_interest_change", "oi_delta")
        elif col == "component_toxicity_penalty":
            sd = _first_present_float(ctr, raw, "score_deterioration")
            if sd is not None:
                alt = -sd
            else:
                alt = _first_present_float(ctr, raw, "toxicity_penalty", "earnings_risk")
            if alt is None:
                alt = _uw_feature_float(uf, "toxicity_penalty", "toxicity")
        picks[col] = 0.0 if alt is None else alt

    for col in SPI_CORE_KEYS:
        v = picks[col]
        if not math.isfinite(v):
            v = 0.0
        out[col] = str(float(v))

    return out


def rows_uw_attribution_main(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    """Main.py V3 attribution stream (decision signal/rejected + components)."""
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        if "ts" in rec and isinstance(rec.get("ts"), (int, float)):
            try:
                dt = datetime.fromtimestamp(int(rec["ts"]), tz=timezone.utc)
            except (OSError, ValueError, OverflowError):
                dt = parse_ts(rec)
        else:
            dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        comps = rec.get("components") if isinstance(rec.get("components"), dict) else {}
        row = {
            "timestamp_utc": dt.isoformat() if dt else "",
            "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "symbol": rec.get("symbol") or "",
            "total_score": rec.get("score") if rec.get("score") is not None else "",
            "freshness": rec.get("freshness") if rec.get("freshness") is not None else "",
            "decision": rec.get("decision") or "",
            "source_tag": rec.get("source") or rec.get("version") or "",
        }
        contrib = rec.get("contributions") if isinstance(rec.get("contributions"), dict) else {}
        raw_sig = rec.get("raw_signals") if isinstance(rec.get("raw_signals"), dict) else {}
        uf = rec.get("uw_features") if isinstance(rec.get("uw_features"), dict) else {}
        row.update(
            spi_row_components_resolved(
                comps,
                contributions=contrib,
                raw_signals=raw_sig,
                uw_features=uf,
            )
        )
        out.append(row)
    return out


def rows_score_snapshot(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        w = rec.get("weighted_contributions") if isinstance(rec.get("weighted_contributions"), dict) else {}
        gs = rec.get("signal_group_scores") if isinstance(rec.get("signal_group_scores"), dict) else {}
        comps = rec.get("components") if isinstance(rec.get("components"), dict) else {}
        merged = {**comps, **w, **gs}
        row = {
            "timestamp_utc": dt.isoformat() if dt else "",
            "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "symbol": rec.get("symbol") or "",
            "total_score": rec.get("composite_score") if rec.get("composite_score") is not None else "",
            "freshness": "",
            "decision": rec.get("candidate_status") or rec.get("block_reason") or "",
            "source_tag": "score_snapshot",
        }
        row.update(spi_row_components_resolved(merged))
        out.append(row)
    return out


def rows_emit_uw_intel(path: Path, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    """logs/uw_attribution.jsonl from emit_uw_attribution (different schema)."""
    out: List[Dict[str, Any]] = []
    for rec in iter_jsonl(path):
        dt = parse_ts(rec)
        if not in_window(dt, start, end):
            continue
        comps = rec.get("components") if isinstance(rec.get("components"), dict) else {}
        uf = rec.get("uw_features") if isinstance(rec.get("uw_features"), dict) else {}
        sc = spi_row_components_resolved(comps, uw_features=uf)
        out.append(
            {
                "timestamp_utc": dt.isoformat() if dt else "",
                "source_file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "symbol": rec.get("symbol") or "",
                "total_score": rec.get("score") if rec.get("score") is not None else "",
                "freshness": rec.get("freshness") if rec.get("freshness") is not None else "",
                "decision": rec.get("direction") or rec.get("decision") or "",
                "source_tag": rec.get("composite_version") or "uw_intel_emit",
                **sc,
            }
        )
    return out


def summarize_pnl(rows: List[Dict[str, Any]]) -> Tuple[int, int, int, int, Optional[float]]:
    """Returns wins, losses, breakeven, total_with_pnl, sum_pnl."""
    wins = losses = flat = 0
    total = 0
    pnl_sum = 0.0
    for r in rows:
        p = r.get("realized_pnl_usd")
        if p is None or p == "":
            continue
        try:
            v = float(p)
        except (TypeError, ValueError):
            continue
        total += 1
        pnl_sum += v
        if v > 0:
            wins += 1
        elif v < 0:
            losses += 1
        else:
            flat += 1
    return wins, losses, flat, total, (pnl_sum if total else None)


def main() -> int:
    start, end = window_48h()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # entries_and_exits.csv: canonical Harvester-era unique closed trades only (STRICT_EPOCH_START
    # exit floor + era cut + trade_key dedupe). Matches compute_canonical_trade_count row cardinality.
    entries: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []
    exit_path = LOGS / "exit_attribution.jsonl"
    if iter_harvester_era_exit_records_for_csv is not None and exit_path.is_file():
        try:
            for rec in iter_harvester_era_exit_records_for_csv(
                REPO_ROOT,
                floor_epoch=float(STRICT_EPOCH_START),
                as_of_utc=end,
            ):
                entries.append(exit_attribution_rec_to_entry_row(rec, exit_path))
        except Exception:
            entries = []
    if not entries and exit_path.is_file():
        # Fallback if imports fail: legacy 48h merge (avoid empty CSV on broken env)
        try:
            entries.extend(rows_from_exit_attribution(exit_path, start, end))
        except Exception:
            pass

    ord_path = LOGS / "orders.jsonl"
    if ord_path.is_file():
        try:
            blocked.extend(rows_blocked_orders(ord_path, start, end))
        except Exception:
            pass

    gd = LOGS / "gate_diagnostic.jsonl"
    if gd.is_file():
        blocked.extend(rows_gate_diagnostic(gd, start, end))
    runp = LOGS / "run.jsonl"
    if runp.is_file():
        blocked.extend(rows_run_trade_intent_blocked(runp, start, end))
    crit = LOGS / "critical_api_failure.log"
    blocked.extend(rows_critical_api_log(crit, start, end))
    se = LOGS / "system_events.jsonl"
    if se.is_file():
        blocked.extend(rows_system_events_blocked(se, start, end))

    shadow_rows: List[Dict[str, Any]] = []
    for p in (LOGS / "shadow.jsonl", LOGS / "shadow_trades.jsonl", LOGS / "master_trade_log.jsonl"):
        if p.is_file():
            if p.name == "shadow.jsonl":
                shadow_rows.extend(rows_shadow_jsonl(p, start, end))
            else:
                for rec in iter_jsonl(p):
                    dt = parse_ts(rec)
                    if not in_window(dt, start, end):
                        continue
                    if rec.get("is_shadow"):
                        shadow_rows.append(
                            {
                                "timestamp_utc": dt.isoformat() if dt else "",
                                "source_file": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                                "record_type": "shadow_trade",
                                "symbol": rec.get("symbol") or "",
                                "side": rec.get("side") or "",
                                "variant_or_promo": rec.get("source") or "shadow",
                                "score_or_metric": rec.get("realized_pnl_usd") if rec.get("realized_pnl_usd") is not None else "",
                                "would_enter": "",
                                "blocked_reason": "",
                                "extra": safe_str(rec.get("trade_id") or ""),
                            }
                        )
    pep = LOGS / "paper_exec_mode_decisions.jsonl"
    if pep.is_file():
        shadow_rows.extend(rows_paper_exec_decisions(pep, start, end))

    spi: List[Dict[str, Any]] = []
    for p in (
        DATA / "uw_attribution.jsonl",
        LOGS / "uw_attribution.jsonl",
        LOGS / "score_snapshot.jsonl",
        REPO_ROOT / "telemetry" / "score_snapshot.jsonl",
    ):
        if p.is_file():
            if p.name == "uw_attribution.jsonl":
                if "logs" in p.parts:
                    spi.extend(rows_emit_uw_intel(p, start, end))
                else:
                    spi.extend(rows_uw_attribution_main(p, start, end))
            elif "score_snapshot" in p.name:
                spi.extend(rows_score_snapshot(p, start, end))

    for p in (LOGS / "alpaca_entry_attribution.jsonl",):
        if p.is_file():
            for rec in iter_jsonl(p):
                if str(rec.get("event_type") or "") != "alpaca_entry_attribution":
                    continue
                dt = parse_ts(rec)
                if not in_window(dt, start, end):
                    continue
                contrib = rec.get("contributions") if isinstance(rec.get("contributions"), dict) else {}
                raw_sig = rec.get("raw_signals") if isinstance(rec.get("raw_signals"), dict) else {}
                row = {
                    "timestamp_utc": dt.isoformat() if dt else "",
                    "source_file": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "symbol": rec.get("symbol") or "",
                    "total_score": rec.get("composite_score") if rec.get("composite_score") is not None else "",
                    "freshness": "",
                    "decision": rec.get("decision") or "",
                    "source_tag": "alpaca_entry_attribution",
                }
                row.update(spi_row_components_resolved({}, contributions=contrib, raw_signals=raw_sig))
                spi.append(row)

    n_ent = write_csv(OUT_DIR / "entries_and_exits.csv", ENTRIES_HEADERS, entries)
    n_blk = write_csv(OUT_DIR / "blocked_and_rejected.csv", BLOCKED_HEADERS, blocked)
    n_sh = write_csv(OUT_DIR / "shadow_and_ab_testing.csv", SHADOW_HEADERS, shadow_rows)
    n_spi = write_csv(OUT_DIR / "signal_intelligence_spi.csv", SPI_HEADERS, spi)

    wins, losses, flat, pnl_n, pnl_sum = summarize_pnl(entries)

    # Timestamp coverage from all written rows
    all_ts: List[datetime] = []
    for coll in (entries, blocked, shadow_rows, spi):
        for r in coll:
            try:
                if r.get("timestamp_utc"):
                    all_ts.append(datetime.fromisoformat(str(r["timestamp_utc"]).replace("Z", "+00:00")))
            except ValueError:
                pass
    tmin = min(all_ts) if all_ts else None
    tmax = max(all_ts) if all_ts else None

    wl = wins + losses
    win_rate = f"{(wins / wl):.4f}" if wl > 0 else "n/a"

    overview = f"""# Telemetry extract overview (Gemini)

## Extraction window

- **Script window (UTC):** `{start.isoformat()}` → `{end.isoformat()}` (last 48 hours from run time)
- **Run executed at (UTC):** `{utc_now().isoformat()}`
- **Earliest event in extracted rows:** `{tmin.isoformat() if tmin else "(no rows)"}`
- **Latest event in extracted rows:** `{tmax.isoformat() if tmax else "(no rows)"}`

## Output files (under `reports/Gemini/`)

| File | Rows written |
|------|----------------|
| `entries_and_exits.csv` | {n_ent} |
| `blocked_and_rejected.csv` | {n_blk} |
| `shadow_and_ab_testing.csv` | {n_sh} |
| `signal_intelligence_spi.csv` | {n_spi} |

## High-level counts (this batch)

- **Harvester-era unique exit rows (`entries_and_exits.csv`):** {n_ent}
- **Blocked / rejected rows:** {n_blk}
- **Rows with numeric realized P&L:** {pnl_n}
- **Wins (P&L > 0):** {wins}
- **Losses (P&L < 0):** {losses}
- **Breakeven (P&L = 0):** {flat}
- **Win rate (wins / (wins+losses)):** `{win_rate}`
- **Sum realized P&L (where present):** `{pnl_sum if pnl_sum is not None else "n/a"}`

## Data sources consulted (non-exhaustive)

- **`entries_and_exits.csv`:** unique closed trades from `logs/exit_attribution.jsonl` only — same rules as `compute_canonical_trade_count` (`STRICT_EPOCH_START` exit floor, era cut, `trade_key` dedupe). No merged fills/orders.
- **Blocked / other CSVs:** `logs/orders.jsonl` (blocked actions), `logs/gate_diagnostic.jsonl`, `logs/run.jsonl` (trade_intent blocked_reason), `logs/critical_api_failure.log`, `logs/system_events.jsonl`
- `logs/shadow.jsonl`, `logs/paper_exec_mode_decisions.jsonl`
- `data/uw_attribution.jsonl`, `logs/uw_attribution.jsonl`, `logs/alpaca_entry_attribution.jsonl`, `logs/score_snapshot.jsonl`, `telemetry/score_snapshot.jsonl`

## Notes

- Parsing is **best-effort**; malformed JSONL lines are skipped.
- **IPs** in free-text fields are replaced with `[REDACTED_IP]` where string redaction applies.
- No API keys are emitted as dedicated columns; avoid copying raw `error_details` blobs into external systems without review.

"""
    (OUT_DIR / "telemetry_overview.md").write_text(overview, encoding="utf-8")
    print(f"Wrote {OUT_DIR} — entries={n_ent} blocked={n_blk} shadow={n_sh} spi={n_spi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
