"""
Audit Guard: Hard safety interlock to prevent live orders during audit mode.

This module provides a single authoritative source for audit mode detection
and enforcement. All order submission paths MUST check this guard before
making network calls to the broker.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path


def is_audit_mode() -> bool:
    """
    Check if AUDIT_MODE is enabled.
    
    Reads from os.environ with strict normalization:
    - "1", "true", "yes" (case-insensitive) -> True
    - "0", "false", "no" (case-insensitive) -> False
    - Missing or empty -> False
    
    Returns:
        True if audit mode is enabled, False otherwise
    """
    val = os.getenv("AUDIT_MODE", "").strip().lower()
    return val in ("1", "true", "yes")


def is_audit_dry_run() -> bool:
    """
    Check if AUDIT_DRY_RUN is enabled.
    
    Reads from os.environ with strict normalization:
    - "1", "true", "yes" (case-insensitive) -> True
    - "0", "false", "no" (case-insensitive) -> False
    - Missing or empty -> False
    
    Returns:
        True if audit dry-run is enabled, False otherwise
    """
    val = os.getenv("AUDIT_DRY_RUN", "").strip().lower()
    return val in ("1", "true", "yes")


def assert_no_live_orders(context: Dict[str, Any]) -> None:
    """
    Assert that no live orders can be submitted.
    
    If AUDIT_MODE is enabled, raises RuntimeError to prevent order submission.
    Logs CRITICAL event to system_events.jsonl.
    
    Args:
        context: Dictionary with order details:
            - op: Operation name (e.g., "submit_order", "close_position")
            - symbol: Stock symbol
            - side: "buy" or "sell" (optional)
            - qty: Quantity (optional)
            - order_type: Order type (optional)
            - caller: Caller function/module (optional)
    
    Raises:
        RuntimeError: If AUDIT_MODE is enabled
    """
    if is_audit_mode():
        # Log CRITICAL event
        try:
            from utils.system_events import log_system_event
            log_system_event(
                subsystem="audit",
                event_type="live_order_blocked",
                severity="CRITICAL",
                details=context
            )
        except Exception:
            # Fallback if logging fails
            pass
        
        # Raise to prevent order submission
        raise RuntimeError(
            f"AUDIT_MODE=1: Live order submission blocked. "
            f"Operation: {context.get('op', 'unknown')}, "
            f"Symbol: {context.get('symbol', 'unknown')}, "
            f"Caller: {context.get('caller', 'unknown')}"
        )


def should_use_dry_run() -> bool:
    """
    Check if dry-run mode should be used.
    
    Returns True if either AUDIT_MODE or AUDIT_DRY_RUN is enabled.
    
    Returns:
        True if dry-run should be used, False otherwise
    """
    return is_audit_mode() or is_audit_dry_run()


def create_mock_order(order_id: str, symbol: str, qty: int, side: str, 
                     order_type: str = "limit", limit_price: Optional[float] = None) -> Any:
    """
    Create a mock Order object compatible with Alpaca Order schema.
    
    Args:
        order_id: Mock order ID
        symbol: Stock symbol
        qty: Quantity
        side: "buy" or "sell"
        order_type: Order type
        limit_price: Limit price (optional)
    
    Returns:
        Mock Order object with minimal required attributes
    """
    class MockOrder:
        def __init__(self, order_id, symbol, qty, side, order_type, limit_price):
            self.id = order_id
            self.symbol = symbol
            self.qty = qty
            self.side = side
            self.type = order_type
            self.limit_price = limit_price
            self.status = "new"
            self.filled_qty = 0
            self.filled_avg_price = None
            self.created_at = None
            self.updated_at = None
            self.client_order_id = None
            self.asset_class = "us_equity"
            self.asset_id = None
            self.canceled_at = None
            self.expired_at = None
            self.expires_at = None
            self.time_in_force = "day"
            self.order_class = None
            self.legs = None
            self.trail_percent = None
            self.trail_price = None
            self.hwm = None
    
    return MockOrder(order_id, symbol, qty, side, order_type, limit_price)
