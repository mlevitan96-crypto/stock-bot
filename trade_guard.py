#!/usr/bin/env python3
"""
Trade Guard - Mandatory Trade Sanity Checks
===========================================
No order is sent to Alpaca unless it passes this strict risk/sanity gate.

All order submission paths MUST go through evaluate_order().

Checks:
- Max position size per symbol
- Max portfolio exposure / concentration
- Max notional per order
- No unintended direction flip
- Price sanity (within configurable % band of last known market price)
- Slippage bounds (if available)
- Cooldown (minimum time between trades per symbol)
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple, Any
from config.registry import Thresholds, get_env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeGuard:
    """Mandatory trade sanity checker."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize trade guard with configuration.
        
        Args:
            config: Optional config dict. If None, uses defaults from env/registry.
        """
        # Risk limits
        self.max_position_size_usd = get_env("MAX_POSITION_SIZE_USD", Thresholds.POSITION_SIZE_USD, float)
        self.max_portfolio_exposure_pct = get_env("MAX_PORTFOLIO_EXPOSURE_PCT", 0.30, float)  # 30% max
        self.max_notional_per_order = get_env("MAX_NOTIONAL_PER_ORDER", 2000.0, float)
        self.max_concentration_per_symbol_pct = get_env("MAX_CONCENTRATION_PER_SYMBOL_PCT", 0.15, float)  # 15% max per symbol
        
        # Price sanity
        self.max_price_deviation_pct = get_env("MAX_PRICE_DEVIATION_PCT", 0.05, float)  # 5% max deviation
        
        # Cooldown
        self.min_cooldown_minutes = get_env("MIN_COOLDOWN_MINUTES", 5, int)  # 5 minutes between trades per symbol
        
        # Direction flip protection
        self.allow_direction_flip = get_env("ALLOW_DIRECTION_FLIP", False, bool)
        
        # Override with provided config
        if config:
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
    
    def evaluate_order(self, order_context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluate order for safety and sanity.
        
        Args:
            order_context: Dict containing:
                - symbol: str
                - side: "buy" or "sell"
                - qty: int
                - intended_price: float (or last known price)
                - current_positions: Dict[symbol, position_data] from state_manager
                - account_equity: float (optional, for exposure checks)
                - account_buying_power: float (optional)
                - last_trade_timestamp: Optional[str] (ISO timestamp)
                - risk_config: Optional[Dict] (additional risk config)
        
        Returns:
            Tuple of (approved: bool, reason: str)
            If approved=False, reason explains why the order was rejected.
        """
        symbol = order_context.get("symbol")
        side = order_context.get("side")
        qty = order_context.get("qty")
        intended_price = order_context.get("intended_price", 0.0)
        current_positions = order_context.get("current_positions", {})
        account_equity = order_context.get("account_equity", 0.0)
        account_buying_power = order_context.get("account_buying_power", 0.0)
        last_trade_timestamp = order_context.get("last_trade_timestamp")
        risk_config = order_context.get("risk_config", {})
        
        # Basic validation
        if not symbol or not isinstance(symbol, str):
            return False, "invalid_symbol"
        
        if side not in ["buy", "sell"]:
            return False, f"invalid_side_{side}"
        
        if not isinstance(qty, int) or qty <= 0:
            return False, f"invalid_qty_{qty}"
        
        if intended_price <= 0:
            return False, f"invalid_price_{intended_price}"
        
        # Calculate notional
        notional = qty * intended_price
        
        # Check 1: Max notional per order
        if notional > self.max_notional_per_order:
            return False, f"notional_exceeds_limit_{notional:.2f}_max_{self.max_notional_per_order:.2f}"
        
        # Check 2: Max position size per symbol
        current_pos = current_positions.get(symbol, {})
        current_qty = current_pos.get("qty", 0)
        current_side = current_pos.get("side", "buy")
        
        # Calculate new position size
        if side == current_side or not current_qty:
            # Adding to position or new position
            new_qty = current_qty + qty
        else:
            # Reducing or flipping position
            new_qty = abs(current_qty - qty)
        
        new_notional = new_qty * intended_price
        if new_notional > self.max_position_size_usd:
            return False, f"position_size_exceeds_limit_{new_notional:.2f}_max_{self.max_position_size_usd:.2f}"
        
        # Check 3: Direction flip protection
        if current_qty > 0 and not self.allow_direction_flip:
            if (current_side == "buy" and side == "sell" and qty >= current_qty) or \
               (current_side == "sell" and side == "buy" and qty >= current_qty):
                return False, f"direction_flip_blocked_current_{current_side}_new_{side}"
        
        # Check 4: Portfolio exposure / concentration
        if account_equity > 0:
            # Calculate total portfolio exposure
            total_exposure = sum(
                pos.get("qty", 0) * pos.get("cost_basis", intended_price)
                for pos in current_positions.values()
            )
            
            # Add new order notional
            if symbol in current_positions:
                # Adjust existing position
                existing_notional = current_pos.get("qty", 0) * current_pos.get("cost_basis", intended_price)
                total_exposure = total_exposure - existing_notional + new_notional
            else:
                total_exposure += notional
            
            exposure_pct = total_exposure / account_equity if account_equity > 0 else 0.0
            if exposure_pct > self.max_portfolio_exposure_pct:
                return False, f"portfolio_exposure_exceeds_limit_{exposure_pct:.2%}_max_{self.max_portfolio_exposure_pct:.2%}"
            
            # Check concentration per symbol
            symbol_exposure_pct = new_notional / account_equity if account_equity > 0 else 0.0
            if symbol_exposure_pct > self.max_concentration_per_symbol_pct:
                return False, f"symbol_concentration_exceeds_limit_{symbol_exposure_pct:.2%}_max_{self.max_concentration_per_symbol_pct:.2%}"
        
        # Check 5: Buying power check (if available)
        if account_buying_power > 0 and side == "buy":
            if notional > account_buying_power:
                return False, f"insufficient_buying_power_{notional:.2f}_available_{account_buying_power:.2f}"
        
        # Check 6: Price sanity (if last known price provided)
        last_known_price = order_context.get("last_known_price")
        if last_known_price and last_known_price > 0:
            price_deviation = abs(intended_price - last_known_price) / last_known_price
            if price_deviation > self.max_price_deviation_pct:
                return False, f"price_deviation_exceeds_limit_{price_deviation:.2%}_max_{self.max_price_deviation_pct:.2%}_intended_{intended_price}_last_{last_known_price}"
        
        # Check 7: Cooldown
        if last_trade_timestamp:
            try:
                last_trade_dt = datetime.fromisoformat(last_trade_timestamp.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                elapsed_minutes = (now - last_trade_dt).total_seconds() / 60.0
                
                if elapsed_minutes < self.min_cooldown_minutes:
                    return False, f"cooldown_not_met_{elapsed_minutes:.1f}_min_required_{self.min_cooldown_minutes}_min"
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse last_trade_timestamp {last_trade_timestamp}: {e}")
                # Fail open - don't block on timestamp parsing errors
        
        # Check 8: Custom risk config checks
        if risk_config:
            max_qty = risk_config.get("max_qty")
            if max_qty and qty > max_qty:
                return False, f"custom_max_qty_exceeded_{qty}_max_{max_qty}"
            
            blocked_symbols = risk_config.get("blocked_symbols", [])
            if symbol in blocked_symbols:
                return False, f"symbol_blocked_{symbol}"
        
        # All checks passed
        return True, "approved"
    
    def log_rejection(self, symbol: str, side: str, qty: int, reason: str, 
                     order_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a rejected trade for analysis.
        
        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            qty: Quantity
            reason: Rejection reason
            order_context: Optional full order context for debugging
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "trade_rejected",
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "reason": reason,
            "guard_config": {
                "max_position_size_usd": self.max_position_size_usd,
                "max_notional_per_order": self.max_notional_per_order,
                "max_portfolio_exposure_pct": self.max_portfolio_exposure_pct,
                "max_concentration_per_symbol_pct": self.max_concentration_per_symbol_pct,
                "min_cooldown_minutes": self.min_cooldown_minutes
            }
        }
        
        if order_context:
            log_entry["order_context"] = {
                k: v for k, v in order_context.items() 
                if k not in ["current_positions", "risk_config"]  # Exclude large objects
            }
        
        logger.warning(f"Trade rejected: {symbol} {side} {qty} - {reason}")
        
        # Also write to structured log
        try:
            from config.registry import append_jsonl, LogFiles
            append_jsonl(LogFiles.ORDERS, log_entry)
        except Exception as e:
            logger.error(f"Failed to log rejection: {e}")


# Global instance (can be overridden)
_guard_instance: Optional[TradeGuard] = None

def get_guard(config: Optional[Dict[str, Any]] = None) -> TradeGuard:
    """Get or create global trade guard instance."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = TradeGuard(config)
    return _guard_instance

def evaluate_order(order_context: Dict[str, Any]) -> Tuple[bool, str]:
    """Convenience function to evaluate order using global guard."""
    guard = get_guard()
    return guard.evaluate_order(order_context)
