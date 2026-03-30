"""Telegram message bodies — safe with missing optional fields."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from telemetry.alpaca_telegram_integrity.milestone import MilestoneSnapshot
from telemetry.alpaca_telegram_integrity.warehouse_summary import CoverageSummary


def _fmt_pct(x: Any) -> str:
    if x is None:
        return "n/a"
    try:
        return f"{float(x):.2f}%"
    except (TypeError, ValueError):
        return str(x)


def format_100trade_checkpoint(
    *,
    test: bool,
    snap: MilestoneSnapshot,
    cov: CoverageSummary,
    data_ready: Optional[str],
    strict_status: Optional[str],
    exit_probe_ok: bool,
    utc_iso: str,
) -> str:
    """Informational only; no operator action."""
    prefix = "[TEST] " if test else ""
    lines = [
        f"{prefix}[ALPACA] 100-TRADE CHECKPOINT",
        "Informational only — no operator action required.",
        f"Trade count (canonical trade_key since session open): {snap.unique_closed_trades}",
        f"Session open (UTC): {snap.session_open_utc_iso}",
        f"Session baseline (ET date): {snap.session_anchor_et}",
        f"Timestamp (UTC): {utc_iso}",
        "",
        "Pre-send integrity (snapshot):",
        f"  DATA_READY: {data_ready or 'unknown'}",
        f"  Execution join coverage: {_fmt_pct(cov.execution_join_pct)}",
        f"  Fee coverage: {_fmt_pct(cov.fee_pct)}",
        f"  Slippage coverage: {_fmt_pct(cov.slippage_pct)}",
        f"  Signal snapshot (near exit): {_fmt_pct(cov.signal_snap_pct)}",
        f"  Coverage artifact: {cov.path.name if cov.path else 'none'} (age_h={cov.age_hours})",
        f"  Strict LEARNING_STATUS: {strict_status or 'unknown'}",
        f"  Exit attribution tail probe OK: {exit_probe_ok}",
        "",
        "System is on track for 250-trade milestone (same session baseline and counters).",
    ]
    return "\n".join(lines)


def format_100trade_checkpoint_deferred(
    *,
    test: bool,
    degradation_reasons: List[str],
    snap: MilestoneSnapshot,
    utc_iso: str,
) -> str:
    """Sent instead of checkpoint when pre-send integrity fails."""
    prefix = "[TEST] " if test else ""
    body = [
        f"{prefix}ALPACA DATA INTEGRITY ALERT (100-trade checkpoint deferred)",
        "The 100-trade informational checkpoint was not sent because integrity pre-checks failed.",
        f"Session baseline (ET): {snap.session_anchor_et} | trades_since_open={snap.unique_closed_trades} | {utc_iso}",
        "Degradation:",
    ]
    for r in degradation_reasons:
        body.append(f"  - {r}")
    body.append(
        "Operator: resolve DATA_READY / coverage / strict completeness / exit schema; next cycle may send checkpoint if green."
    )
    return "\n".join(body)


def format_milestone_250(
    *,
    test: bool,
    snap: MilestoneSnapshot,
    data_ready: Optional[str],
    strict_status: Optional[str],
    spi_rel: Optional[str],
    reports_hint: str,
) -> str:
    prefix = "[TEST] " if test else ""
    lines = [
        f"{prefix}ALPACA 250-TRADE MILESTONE",
        f"Session open (UTC): {snap.session_open_utc_iso}",
        f"Session anchor (ET date): {snap.session_anchor_et}",
        f"Unique closed trades (canonical keys): {snap.unique_closed_trades}",
        f"Realized PnL sum since session open (USD): {snap.realized_pnl_sum_usd}",
        f"DATA_READY: {data_ready or 'unknown (run warehouse)'}",
        f"Strict LEARNING_STATUS: {strict_status or 'unknown'}",
    ]
    if spi_rel:
        lines.append(f"SPI snapshot (latest): {spi_rel}")
    else:
        lines.append("SPI snapshot: none found under reports/")
    lines.append(f"Reports: {reports_hint}")
    if snap.sample_trade_keys:
        lines.append("Sample trade_keys: " + ", ".join(snap.sample_trade_keys))
    return "\n".join(lines)


def format_integrity_alert(
    *,
    test: bool,
    reasons: List[str],
    last_good: Optional[Dict[str, Any]],
    action: str,
) -> str:
    prefix = "[TEST] " if test else ""
    body = [
        f"{prefix}ALPACA DATA INTEGRITY ALERT",
        "Issues:",
    ]
    for r in reasons:
        body.append(f"- {r}")
    if last_good:
        body.append("Last known good (snapshot):")
        for k, v in sorted(last_good.items())[:12]:
            body.append(f"  {k}: {v}")
    else:
        body.append("Last known good: not recorded yet")
    body.append(f"Operator action: {action}")
    return "\n".join(body)
