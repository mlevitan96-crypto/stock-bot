#!/usr/bin/env python3
"""
Report Data Validator - Validates data before generating reports

This module prevents committing reports with obviously bad data (e.g., 0 trades when trades exist).

Usage:
    from report_data_validator import validate_report_data
    
    try:
        validate_report_data(trades, blocked, signals, date="2026-01-08")
    except ValidationError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class ValidationError(Exception):
    """Raised when data validation fails"""
    pass


def validate_report_data(
    executed_trades: List[Dict],
    blocked_trades: List[Dict],
    signals: List[Dict],
    date: Optional[str] = None,
    allow_zero_trades: bool = False,
    min_trades_threshold: int = 0
) -> Dict[str, Any]:
    """
    Validate report data before generating report.
    
    Args:
        executed_trades: List of executed trades
        blocked_trades: List of blocked trades
        signals: List of signals generated
        date: Date being analyzed (YYYY-MM-DD)
        allow_zero_trades: If True, allow 0 trades (e.g., market closed)
        min_trades_threshold: Minimum expected trades (default: 0)
    
    Returns:
        Validation report with warnings and errors
    
    Raises:
        ValidationError: If critical validation fails
    """
    validation_report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "stats": {
            "executed_trades": len(executed_trades),
            "blocked_trades": len(blocked_trades),
            "signals": len(signals),
        }
    }
    
    # Critical Validation: Executed Trades
    if len(executed_trades) == 0 and not allow_zero_trades:
        error_msg = (
            f"CRITICAL: Found 0 executed trades for {date or 'target date'}. "
            "This usually means:\n"
            "1. Data was not fetched from Droplet (used local files instead)\n"
            "2. Market was closed (set allow_zero_trades=True if this is the case)\n"
            "3. No trading occurred (very rare for active bot)\n\n"
            "SOLUTION: Verify data source is Droplet, not local files. "
            "Use ReportDataFetcher to get data from production server."
        )
        validation_report["errors"].append(error_msg)
        validation_report["valid"] = False
    
    # Warning: Low trade count
    if len(executed_trades) > 0 and len(executed_trades) < min_trades_threshold:
        validation_report["warnings"].append(
            f"Low trade count: {len(executed_trades)} trades (expected at least {min_trades_threshold})"
        )
    
    # Warning: More trades than signals (timing issue)
    if len(executed_trades) > len(signals) * 1.1:  # Allow 10% margin
        validation_report["warnings"].append(
            f"More trades ({len(executed_trades)}) than signals ({len(signals)}). "
            "This may indicate data timing issues or trades from previous day."
        )
    
    # Warning: Very low execution rate
    if len(signals) > 0:
        execution_rate = len(executed_trades) / len(signals) * 100
        if execution_rate < 1.0:
            validation_report["warnings"].append(
                f"Very low execution rate: {execution_rate:.1f}% "
                f"({len(executed_trades)} trades / {len(signals)} signals). "
                "May indicate over-filtering or data issues."
            )
    
    # Warning: All trades have same timestamp or no timestamps
    if executed_trades:
        timestamps = []
        for trade in executed_trades:
            ts = trade.get("ts") or trade.get("timestamp")
            if ts:
                timestamps.append(str(ts))
        
        if len(set(timestamps)) < len(executed_trades) * 0.5:
            validation_report["warnings"].append(
                "Many trades have duplicate timestamps. May indicate data quality issue."
            )
        
        if len(timestamps) < len(executed_trades) * 0.8:
            validation_report["warnings"].append(
                f"Many trades missing timestamps ({len(timestamps)}/{len(executed_trades)}). "
                "Data quality may be compromised."
            )
    
    # Check data age (if timestamps present)
    if executed_trades:
        dates_found = set()
        for trade in executed_trades:
            ts = trade.get("ts") or trade.get("timestamp")
            if ts:
                try:
                    if isinstance(ts, str):
                        if "T" in ts:
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            dates_found.add(dt.date())
                except:
                    pass
        
        if date and dates_found:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            if target_date not in dates_found:
                validation_report["warnings"].append(
                    f"Target date {date} not found in trade timestamps. "
                    f"Found dates: {sorted(dates_found)}"
                )
    
    # If critical errors, raise exception
    if not validation_report["valid"]:
        error_summary = "\n".join(validation_report["errors"])
        raise ValidationError(f"Data validation failed:\n\n{error_summary}")
    
    return validation_report


def validate_data_source(data_source_info: Dict[str, Any]) -> bool:
    """
    Validate that data source is Droplet, not local files.
    
    Args:
        data_source_info: Dictionary with 'source' key from ReportDataFetcher.get_data_source_info()
    
    Returns:
        True if data source is valid (Droplet), False otherwise
    
    Raises:
        ValidationError: If data source is not Droplet
    """
    source = data_source_info.get("source", "").lower()
    
    valid_sources = ["droplet", "production server", "production"]
    
    if not any(valid in source for valid in valid_sources):
        raise ValidationError(
            f"INVALID DATA SOURCE: '{data_source_info.get('source')}'\n\n"
            "Reports MUST use data from Droplet production server.\n"
            "Local files may be outdated, empty, or non-existent.\n\n"
            "SOLUTION: Use ReportDataFetcher to fetch data from Droplet.\n"
            "Example:\n"
            "  from report_data_fetcher import ReportDataFetcher\n"
            "  fetcher = ReportDataFetcher(date='2026-01-08')\n"
            "  trades = fetcher.get_executed_trades()  # From Droplet"
        )
    
    return True
