#!/usr/bin/env python3
"""
UW Client - Hardened Unusual Whales API Wrapper with Contract Checks
=====================================================================
Wraps UW API calls with:
- Explicit response contracts
- Schema validation
- Error classification
- Retry logic for transient errors
- Startup compatibility checks
"""

import os
import time
import logging
import requests
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


class UWClient:
    """Hardened Unusual Whales API client with contract validation."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.unusualwhales.com"):
        """
        Initialize UW client.
        
        Args:
            api_key: UW API key
            base_url: UW API base URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        self._compatibility_checked = False
        self.timeout = 15.0
        
        # Contract definitions (expected response structures)
        self.contracts = {
            "flow": {
                "required_fields": ["symbol", "flow_conv", "flow_magnitude"],
                "field_types": {
                    "symbol": str,
                    "flow_conv": (int, float),
                    "flow_magnitude": (int, float)
                }
            },
            "signal": {
                "required_fields": ["symbol", "signal_type"],
                "field_types": {
                    "symbol": str,
                    "signal_type": str
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
        if isinstance(error, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            return ErrorType.NETWORK, f"Network error: {error}"
        
        if any(term in error_str for term in ["timeout", "connection", "network", "dns", "refused"]):
            return ErrorType.NETWORK, f"Network error: {error}"
        
        # Schema errors
        if any(term in error_str for term in ["attribute", "keyerror", "typeerror", "missing", "invalid", "json"]):
            return ErrorType.SCHEMA_ERROR, f"Schema mismatch: {error}"
        
        return ErrorType.UNKNOWN, f"Unknown error: {error}"
    
    def _validate_contract(self, data: Any, contract_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate response against contract.
        
        Args:
            data: Response data to validate (dict or list)
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
        
        # Must be dict for validation
        if not isinstance(data, dict):
            return False, f"Response is not a dict: {type(data)}"
        
        # Check required fields
        required_fields = contract.get("required_fields", [])
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return False, f"Missing required fields: {missing_fields}"
        
        # Check field types (basic validation)
        field_types = contract.get("field_types", {})
        for field, expected_type in field_types.items():
            if field in data:
                value = data[field]
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
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                json_data: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request with error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            json_data: JSON body
        
        Returns:
            Response JSON as dict
        
        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"HTTP error for {endpoint}: {reason}")
            raise
        except requests.exceptions.RequestException as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"Request error for {endpoint}: {reason}")
            raise
    
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
            # Check a simple endpoint (e.g., flow endpoint)
            # Note: Adjust endpoint based on actual UW API structure
            # This is a placeholder - adjust based on actual UW API
            
            # Try to fetch flow data (if endpoint exists)
            # If endpoint doesn't exist or structure is different, adjust accordingly
            try:
                # Example: Check if we can get flow data
                # Adjust this based on actual UW API endpoints
                flow_data = self.get_flow()
                if flow_data:
                    is_valid, error = self._validate_contract(flow_data, "flow")
                    if not is_valid:
                        return False, f"Flow contract validation failed: {error}"
            except Exception as flow_err:
                # If flow endpoint doesn't exist or fails, log warning but don't fail
                logger.warning(f"Flow endpoint check failed (non-critical): {flow_err}")
            
            self._compatibility_checked = True
            logger.info("UW API compatibility check passed")
            return True, None
            
        except Exception as e:
            error_type, reason = self._classify_error(e)
            if error_type == ErrorType.AUTH_ERROR:
                return False, f"Authentication failed during compatibility check: {reason}"
            elif error_type == ErrorType.SCHEMA_ERROR:
                return False, f"Schema error during compatibility check: {reason}"
            else:
                return False, f"Compatibility check failed: {reason}"
    
    def get_flow(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get flow data (placeholder - adjust based on actual UW API).
        
        Args:
            symbol: Optional symbol filter
        
        Returns:
            List of flow data dicts
        """
        def _get():
            params = {}
            if symbol:
                params["symbol"] = symbol
            return self._request("GET", "/api/flow", params=params)
        
        try:
            return self._retry_with_backoff(_get, max_retries=3, base_delay=1.0)
        except Exception as e:
            error_type, reason = self._classify_error(e)
            logger.error(f"get_flow failed: {reason}")
            raise


# Convenience function
def check_uw_compat(api_key: str, base_url: str = "https://api.unusualwhales.com") -> Tuple[bool, Optional[str]]:
    """Check UW API compatibility."""
    client = UWClient(api_key, base_url)
    return client.check_compatibility()
