#!/usr/bin/env python3
"""
Alpaca Client - Hardened API Wrapper with Contract Checks
==========================================================
Wraps Alpaca API calls with:
- Explicit response contracts
- Schema validation
- Error classification (AUTH_ERROR, RATE_LIMIT, NETWORK, SCHEMA_ERROR, UNKNOWN)
- Retry logic for transient errors
- Startup compatibility checks

Self-healing behavior:
- TRANSIENT errors: retry with backoff
- AUTH_ERROR / SCHEMA_ERROR: fail fast, mark system as FAILED_API_SCHEMA
"""

import os
import time
import logging
import alpaca_trade_api as tradeapi
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error classification for API failures."""
    AUTH_ERROR = "auth_error"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    SCHEMA_ERROR = "schema_error"
    UNKNOWN = "unknown"


class AlpacaClient:
    """Hardened Alpaca API client with contract validation."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        """
        Initialize Alpaca client.
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: Alpaca API base URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.api = tradeapi.REST(api_key, api_secret, base_url)
        self._compatibility_checked = False
        
        # Contract definitions (expected response structures)
        self.contracts = {
            "account": {
                "required_fields": ["equity", "buying_power", "cash", "portfolio_value"],
                "field_types": {
                    "equity": (int, float),
                    "buying_power": (int, float),
                    "cash": (int, float),
                    "portfolio_value": (int, float)
                }
            },
            "position": {
                "required_fields": ["symbol", "qty", "side"],
                "field_types": {
                    "symbol": str,
                    "qty": (int, float),
                    "side": str
                }
            },
            "order": {
                "required_fields": ["id", "symbol", "qty", "side", "status"],
                "field_types": {
                    "id": (str, int),
                    "symbol": str,
                    "qty": (int, float),
                    "side": str,
                    "status": str
                }
            }
        }
    
    def _classify_error(self, error: Exception) -> Tuple[ErrorType, str]:
        """
        Classify API error into category.
        
        Returns:
            Tuple of (ErrorType, reason_string)
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Auth errors
        if "401" in error_str or "unauthorized" in error_str or "authentication" in error_str:
            return ErrorType.AUTH_ERROR, f"Authentication failed: {error}"
        
        # Rate limit
        if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
            return ErrorType.RATE_LIMIT, f"Rate limit exceeded: {error}"
        
        # Network/connectivity
        if any(term in error_str for term in ["timeout", "connection", "network", "dns", "refused"]):
            return ErrorType.NETWORK, f"Network error: {error}"
        
        # Schema errors (unexpected response structure)
        if any(term in error_str for term in ["attribute", "keyerror", "typeerror", "missing", "invalid"]):
            return ErrorType.SCHEMA_ERROR, f"Schema mismatch: {error}"
        
        return ErrorType.UNKNOWN, f"Unknown error: {error}"
    
    def _validate_contract(self, data: Any, contract_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate response against contract.
        
        Args:
            data: Response data to validate
            contract_name: Name of contract to validate against
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if contract_name not in self.contracts:
            return True, None  # No contract defined, skip validation
        
        contract = self.contracts[contract_name]
        
        # For list responses, validate first item
        if isinstance(data, list):
            if len(data) == 0:
                return True, None  # Empty list is valid
            data = data[0]
        
        # Check required fields
        required_fields = contract.get("required_fields", [])
        missing_fields = []
        
        for field in required_fields:
            if not hasattr(data, field):
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {missing_fields}"
        
        # Check field types (basic validation)
        field_types = contract.get("field_types", {})
        for field, expected_type in field_types.items():
            if hasattr(data, field):
                value = getattr(data, field)
                if not isinstance(value, expected_type):
                    return False, f"Field {field} has wrong type: {type(value)} expected {expected_type}"
        
        return True, None
    
    def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0, 
                           max_delay: float = 30.0, retry_on: List[ErrorType] = None) -> Any:
        """
        Execute function with exponential backoff retry for transient errors.
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            retry_on: List of error types to retry on. Default: [RATE_LIMIT, NETWORK]
        
        Returns:
            Function result
        
        Raises:
            Exception: If all retries fail or error is non-retryable
        """
        if retry_on is None:
            retry_on = [ErrorType.RATE_LIMIT, ErrorType.NETWORK]
        
        last_error = None
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                error_type, reason = self._classify_error(e)
                last_error = e
                
                # Don't retry on non-transient errors
                if error_type not in retry_on:
                    logger.error(f"Non-retryable error: {reason}")
                    raise
                
                # Don't retry on last attempt
                if attempt == max_retries - 1:
                    break
                
                # Calculate backoff delay
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"Retryable error (attempt {attempt + 1}/{max_retries}): {reason}. Retrying in {delay:.1f}s")
                time.sleep(delay)
        
        # All retries failed
        raise last_error
    
    def check_compatibility(self) -> Tuple[bool, Optional[str]]:
        """
        Check API compatibility on startup.
        
        Validates that required endpoints return expected structure.
        
        Returns:
            Tuple of (is_compatible, error_message)
        """
        if self._compatibility_checked:
            return True, None
        
        try:
            # Check account endpoint
            account = self.get_account()
            is_valid, error = self._validate_contract(account, "account")
            if not is_valid:
                return False, f"Account contract validation failed: {error}"
            
            # Check positions endpoint
            positions = self.list_positions()
            if positions:
                is_valid, error = self._validate_contract(positions, "position")
                if not is_valid:
                    return False, f"Position contract validation failed: {error}"
            
            # Check clock endpoint (if available)
            try:
                clock = self.api.get_clock()
                if not hasattr(clock, "is_open"):
                    return False, "Clock response missing 'is_open' attribute"
            except Exception as clock_err:
                logger.warning(f"Clock endpoint check failed (non-critical): {clock_err}")
            
            self._compatibility_checked = True
            logger.info("Alpaca API compatibility check passed")
            return True, None
            
        except Exception as e:
            error_type, reason = self._classify_error(e)
            if error_type == ErrorType.AUTH_ERROR:
                return False, f"Authentication failed during compatibility check: {reason}"
            elif error_type == ErrorType.SCHEMA_ERROR:
                return False, f"Schema error during compatibility check: {reason}"
            else:
                return False, f"Compatibility check failed: {reason}"
    
    def get_account(self) -> Any:
        """Get account information with error handling."""
        try:
            account = self.api.get_account()
            return account
        except Exception as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"get_account failed: {reason}")
            raise
    
    def list_positions(self) -> List[Any]:
        """List positions with error handling."""
        try:
            positions = self.api.list_positions()
            return positions
        except Exception as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"list_positions failed: {reason}")
            raise
    
    def submit_order(self, symbol: str, qty: int, side: str, order_type: str = "market",
                    time_in_force: str = "day", limit_price: Optional[float] = None,
                    client_order_id: Optional[str] = None, **kwargs) -> Any:
        """
        Submit order with retry logic for transient errors.
        
        Args:
            symbol: Stock symbol
            qty: Quantity
            side: "buy" or "sell"
            order_type: "market" or "limit"
            time_in_force: "day", "gtc", etc.
            limit_price: Limit price (required for limit orders)
            client_order_id: Optional client order ID
            **kwargs: Additional order parameters
        
        Returns:
            Order object
        
        Raises:
            Exception: If order submission fails after retries
        """
        def _submit():
            return self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                client_order_id=client_order_id,
                **kwargs
            )
        
        try:
            return self._retry_with_backoff(_submit, max_retries=3, base_delay=1.0)
        except Exception as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"submit_order failed: {reason}")
            raise
    
    def close_position(self, symbol: str) -> Any:
        """Close position with error handling."""
        try:
            return self.api.close_position(symbol)
        except Exception as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"close_position failed: {reason}")
            raise
    
    def get_quote(self, symbol: str) -> Any:
        """Get quote with error handling."""
        try:
            return self.api.get_quote(symbol)
        except Exception as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"get_quote failed: {reason}")
            raise
    
    def get_bars(self, symbol: str, timeframe: str = "1Min", limit: int = 100) -> Any:
        """Get bars with error handling."""
        try:
            return self.api.get_bars(symbol, timeframe, limit=limit)
        except Exception as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"get_bars failed: {reason}")
            raise


# Convenience function
def check_alpaca_compat(api_key: str, api_secret: str, base_url: str) -> Tuple[bool, Optional[str]]:
    """Check Alpaca API compatibility."""
    client = AlpacaClient(api_key, api_secret, base_url)
    return client.check_compatibility()
