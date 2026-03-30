"""Telegram message bodies — safe with missing optional fields."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from telemetry.alpaca_telegram_integrity.milestone import MilestoneSnapshot
from telemetry.alpaca_telegram_integrity.warehouse_summary import CoverageSummary


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
