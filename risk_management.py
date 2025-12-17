#!/usr/bin/env python3
"""
Risk Management Module
======================
Comprehensive risk management for real money trading.

Features:
- Daily loss limits (both $ and %)
- Account equity floor protection
- Maximum drawdown circuit breaker
- Position sizing with dynamic limits
- Exposure limits (symbol and sector)
- Order validation
- Idempotency key generation
"""

import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

# Import existing utilities
try:
    from main import Config, log_event, atomic_write_json
except ImportError:
    # For testing
    class Config:
        TRADING_MODE = os.getenv("TRADING_MODE", "PAPER")
    def log_event(*args, **kwargs):
        print(f"LOG: {args} {kwargs}")
    def atomic_write_json(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

# Directories
STATE_DIR = Path("state")
DATA_DIR = Path("data")

# State files
PEAK_EQUITY_FILE = STATE_DIR / "peak_equity.json"
DAILY_START_EQUITY_FILE = STATE_DIR / "daily_start_equity.json"
RISK_STATE_FILE = STATE_DIR / "risk_management_state.json"
FREEZE_FILE = STATE_DIR / "governor_freezes.json"

# ============================================================
# CONFIGURATION (Mode-based)
# ============================================================

def is_paper_mode() -> bool:
    """Check if running in paper mode"""
    return Config.TRADING_MODE.upper() == "PAPER"

def get_starting_equity() -> float:
    """Get starting equity based on mode"""
    if is_paper_mode():
        return float(os.getenv("STARTING_EQUITY", "55000"))
    else:
        return float(os.getenv("STARTING_EQUITY", "10000"))

def get_risk_limits() -> Dict[str, float]:
    """Get risk limits based on mode"""
    starting_equity = get_starting_equity()
    is_paper = is_paper_mode()
    
    if is_paper:
        daily_loss_pct = 0.04  # 4%
        daily_loss_dollar = 2200  # 4% of 55k
        min_account_equity = starting_equity * 0.85  # 85% of 55k = 46,750
        risk_per_trade_pct = 0.015  # 1.5%
        max_position_dollar = 825  # 1.5% of 55k
        max_symbol_exposure = starting_equity * 0.10  # 10%
        max_sector_exposure = starting_equity * 0.30  # 30%
    else:
        daily_loss_pct = 0.04  # 4%
        daily_loss_dollar = 400  # Hard cap for 10k account
        min_account_equity = starting_equity * 0.85  # 85% of 10k = 8,500
        risk_per_trade_pct = 0.015  # 1.5%
        max_position_dollar = 300  # Hard cap for 10k
        max_symbol_exposure = starting_equity * 0.10  # 10% of 10k = 1,000
        max_sector_exposure = starting_equity * 0.30  # 30% of 10k = 3,000
    
    return {
        "starting_equity": starting_equity,
        "daily_loss_pct": daily_loss_pct,
        "daily_loss_dollar": daily_loss_dollar,
        "min_account_equity": min_account_equity,
        "max_drawdown_pct": 0.20,  # 20% drawdown allowed
        "risk_per_trade_pct": risk_per_trade_pct,
        "max_position_dollar": max_position_dollar,
        "min_position_dollar": 50.0,
        "max_symbol_exposure": max_symbol_exposure,
        "max_sector_exposure": max_sector_exposure,
    }

# ============================================================
# PEAK EQUITY TRACKING
# ============================================================

def load_peak_equity() -> float:
    """Load peak equity from persistent storage"""
    starting_equity = get_starting_equity()
    
    # Try to use existing telemetry logger if available
    try:
        from telemetry.logger import TelemetryLogger
        telemetry = TelemetryLogger()
        peak_data = telemetry.get_peak_equity()
        return float(peak_data.get("peak_equity", starting_equity))
    except Exception:
        pass
    
    # Fallback to direct file read
    if PEAK_EQUITY_FILE.exists():
        try:
            data = json.loads(PEAK_EQUITY_FILE.read_text())
            return float(data.get("peak_equity", starting_equity))
        except Exception:
            pass
    
    return starting_equity

def update_peak_equity(current_equity: float) -> float:
    """Update peak equity if current is higher"""
    peak = load_peak_equity()
    
    if current_equity > peak:
        # Use telemetry logger if available
        try:
            from telemetry.logger import TelemetryLogger
            telemetry = TelemetryLogger()
            telemetry.update_peak_equity(current_equity)
        except Exception:
            # Fallback to direct write
            atomic_write_json(PEAK_EQUITY_FILE, {
                "peak_equity": current_equity,
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
        return current_equity
    return peak

# ============================================================
# DAILY P&L TRACKING
# ============================================================

def get_daily_start_equity() -> Optional[float]:
    """Get equity at start of trading day"""
    if DAILY_START_EQUITY_FILE.exists():
        try:
            data = json.loads(DAILY_START_EQUITY_FILE.read_text())
            date = data.get("date")
            today = datetime.now(timezone.utc).date().isoformat()
            if date == today:
                return float(data.get("equity"))
        except Exception:
            pass
    return None

def set_daily_start_equity(equity: float):
    """Set equity at start of trading day"""
    atomic_write_json(DAILY_START_EQUITY_FILE, {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "equity": equity,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

def calculate_daily_pnl(current_equity: float) -> float:
    """Calculate today's P&L"""
    start_equity = get_daily_start_equity()
    if start_equity is None:
        # First check today - use current as baseline
        set_daily_start_equity(current_equity)
        return 0.0
    return current_equity - start_equity

# ============================================================
# FREEZE MECHANISM
# ============================================================

def freeze_trading(reason: str, **details):
    """Freeze trading immediately"""
    freeze_path = FREEZE_FILE
    
    # Load existing freezes
    if freeze_path.exists():
        try:
            freezes = json.loads(freeze_path.read_text())
        except Exception:
            freezes = {}
    else:
        freezes = {}
    
    # Add new freeze
    freeze_key = reason.replace(" ", "_").lower()
    freezes[freeze_key] = {
        "active": True,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details
    }
    
    # Write atomically
    atomic_write_json(freeze_path, freezes)
    
    # Log and alert
    log_event("freeze", "activated", reason=reason, **details)
    
    # Send webhook if configured
    try:
        from main import send_webhook
        send_webhook({
            "event": "FREEZE_ACTIVATED",
            "reason": reason,
            **details
        })
    except Exception:
        pass

# ============================================================
# RISK CHECKS
# ============================================================

def check_daily_loss_limit(daily_pnl: float, account_equity: float) -> Tuple[bool, Optional[str]]:
    """
    Check if daily loss limit is exceeded.
    Returns (is_safe, freeze_reason_if_breached)
    """
    limits = get_risk_limits()
    
    # Check dollar limit
    if daily_pnl <= -limits["daily_loss_dollar"]:
        freeze_trading(
            "daily_loss_dollar_limit",
            daily_pnl=daily_pnl,
            limit=limits["daily_loss_dollar"],
            account_equity=account_equity
        )
        return False, "daily_loss_dollar_limit"
    
    # Check percentage limit
    loss_pct = abs(daily_pnl) / account_equity if account_equity > 0 else 0
    if daily_pnl < 0 and loss_pct >= limits["daily_loss_pct"]:
        freeze_trading(
            "daily_loss_pct_limit",
            daily_pnl=daily_pnl,
            loss_pct=loss_pct,
            limit_pct=limits["daily_loss_pct"],
            account_equity=account_equity
        )
        return False, "daily_loss_pct_limit"
    
    return True, None

def check_account_equity_floor(current_equity: float) -> Tuple[bool, Optional[str]]:
    """Check if account equity is above floor"""
    limits = get_risk_limits()
    
    if current_equity < limits["min_account_equity"]:
        freeze_trading(
            "account_equity_floor_breached",
            current_equity=current_equity,
            floor=limits["min_account_equity"],
            shortfall=limits["min_account_equity"] - current_equity
        )
        return False, "account_equity_floor_breached"
    
    return True, None

def check_drawdown(current_equity: float, peak_equity: float) -> Tuple[bool, Optional[str]]:
    """Check if maximum drawdown is exceeded"""
    limits = get_risk_limits()
    
    if peak_equity <= 0:
        return True, None
    
    drawdown_pct = (peak_equity - current_equity) / peak_equity
    
    if drawdown_pct >= limits["max_drawdown_pct"]:
        freeze_trading(
            "max_drawdown_exceeded",
            current_equity=current_equity,
            peak_equity=peak_equity,
            drawdown_pct=drawdown_pct,
            limit_pct=limits["max_drawdown_pct"]
        )
        return False, "max_drawdown_exceeded"
    
    return True, None

# ============================================================
# POSITION SIZING
# ============================================================

def calculate_position_size(account_equity: float) -> float:
    """Calculate position size based on account equity"""
    limits = get_risk_limits()
    
    dynamic_size = account_equity * limits["risk_per_trade_pct"]
    
    # Clamp between min and max
    return max(
        limits["min_position_dollar"],
        min(dynamic_size, limits["max_position_dollar"])
    )

# ============================================================
# EXPOSURE LIMITS
# ============================================================

# Sector mapping for common symbols
SECTOR_MAP = {
    # Technology
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "GOOG": "Technology", "META": "Technology", "NVDA": "Technology",
    "AMD": "Technology", "INTC": "Technology", "NFLX": "Technology",
    "TSLA": "Technology",
    
    # Financial
    "JPM": "Financial", "BAC": "Financial", "GS": "Financial",
    "MS": "Financial", "C": "Financial", "WFC": "Financial",
    "BLK": "Financial", "V": "Financial", "MA": "Financial",
    
    # Energy
    "XOM": "Energy", "CVX": "Energy", "COP": "Energy", "SLB": "Energy",
    
    # Healthcare
    "JNJ": "Healthcare", "PFE": "Healthcare", "MRNA": "Healthcare",
    "UNH": "Healthcare",
    
    # Consumer
    "WMT": "Consumer", "TGT": "Consumer", "COST": "Consumer",
    "HD": "Consumer", "LOW": "Consumer",
    
    # ETFs
    "SPY": "ETF", "QQQ": "ETF", "IWM": "ETF", "DIA": "ETF",
    "XLF": "ETF", "XLE": "ETF", "XLK": "ETF", "XLV": "ETF",
    "XLI": "ETF", "XLP": "ETF",
    
    # Crypto/FinTech
    "COIN": "Financial", "SOFI": "Financial", "HOOD": "Financial",
    
    # Auto
    "F": "Consumer", "GM": "Consumer", "NIO": "Consumer", "RIVN": "Consumer",
    "LCID": "Consumer",
    
    # Aerospace
    "BA": "Industrial",
    
    # Industrial
    "CAT": "Industrial",
    
    # Other
    "PLTR": "Technology",
}

def get_sector(symbol: str) -> str:
    """Get sector for symbol"""
    # Try hard-coded map first
    if symbol in SECTOR_MAP:
        return SECTOR_MAP[symbol]
    
    # Default to Unknown
    return "Unknown"

def check_symbol_exposure(symbol: str, positions: list, account_equity: float) -> Tuple[bool, Optional[str]]:
    """
    Check if symbol exposure is within limits.
    positions: list of position objects with .symbol and .market_value attributes
    """
    limits = get_risk_limits()
    
    # Calculate current exposure for this symbol
    symbol_exposure = sum(
        float(getattr(p, "market_value", 0) or 0)
        for p in positions
        if getattr(p, "symbol", "") == symbol
    )
    
    if symbol_exposure > limits["max_symbol_exposure"]:
        return False, f"Symbol {symbol} exposure ${symbol_exposure:.2f} exceeds limit ${limits['max_symbol_exposure']:.2f}"
    
    return True, None

def check_sector_exposure(positions: list, account_equity: float) -> Tuple[bool, Optional[str]]:
    """
    Check if sector exposure is within limits.
    positions: list of position objects with .symbol and .market_value attributes
    """
    limits = get_risk_limits()
    
    # Calculate exposure by sector
    sector_exposure = {}
    for p in positions:
        symbol = getattr(p, "symbol", "")
        market_value = float(getattr(p, "market_value", 0) or 0)
        sector = get_sector(symbol)
        sector_exposure[sector] = sector_exposure.get(sector, 0.0) + market_value
    
    # Check each sector
    for sector, exposure in sector_exposure.items():
        if exposure > limits["max_sector_exposure"]:
            return False, f"Sector {sector} exposure ${exposure:.2f} exceeds limit ${limits['max_sector_exposure']:.2f}"
    
    return True, None

# ============================================================
# ORDER VALIDATION
# ============================================================

def validate_order_size(symbol: str, qty: int, side: str, current_price: float, buying_power: float) -> Tuple[bool, Optional[str]]:
    """Validate order size against buying power and limits"""
    limits = get_risk_limits()
    
    order_value = qty * current_price
    
    # Check against buying power (95% safety margin)
    if side == "buy" and order_value > buying_power * 0.95:
        return False, f"Order ${order_value:.2f} exceeds 95% of buying power ${buying_power:.2f}"
    
    # Check against max position size
    if order_value > limits["max_position_dollar"]:
        return False, f"Order ${order_value:.2f} exceeds max position size ${limits['max_position_dollar']:.2f}"
    
    # Check against min position size
    if order_value < limits["min_position_dollar"]:
        return False, f"Order ${order_value:.2f} below min position size ${limits['min_position_dollar']:.2f}"
    
    return True, None

def generate_idempotency_key(symbol: str, side: str, qty: int) -> str:
    """Generate unique order ID for idempotency"""
    timestamp_ms = int(time.time() * 1000)
    unique_id = uuid.uuid4().hex[:8]
    return f"{symbol}_{side}_{qty}_{timestamp_ms}_{unique_id}"

# ============================================================
# MAIN RISK CHECK FUNCTION
# ============================================================

def run_risk_checks(
    api,  # Alpaca API object
    current_equity: Optional[float] = None,
    positions: Optional[list] = None
) -> Dict[str, Any]:
    """
    Run all risk checks and return results.
    
    Returns:
        {
            "safe_to_trade": bool,
            "freeze_reason": Optional[str],
            "checks": {
                "daily_loss": {"passed": bool, "daily_pnl": float, ...},
                "equity_floor": {"passed": bool, ...},
                "drawdown": {"passed": bool, "drawdown_pct": float, ...},
                ...
            }
        }
    """
    results = {
        "safe_to_trade": True,
        "freeze_reason": None,
        "checks": {}
    }
    
    # Get current account info
    try:
        account = api.get_account()
        if current_equity is None:
            current_equity = float(account.equity)
        if positions is None:
            positions = api.list_positions()
    except Exception as e:
        log_event("risk_check", "api_error", error=str(e))
        results["safe_to_trade"] = False
        results["freeze_reason"] = "api_error"
        return results
    
    # Update peak equity
    peak_equity = update_peak_equity(current_equity)
    
    # 1. Check account equity floor
    equity_safe, equity_reason = check_account_equity_floor(current_equity)
    results["checks"]["equity_floor"] = {
        "passed": equity_safe,
        "current_equity": current_equity,
        "floor": get_risk_limits()["min_account_equity"]
    }
    if not equity_safe:
        results["safe_to_trade"] = False
        results["freeze_reason"] = equity_reason
        return results
    
    # 2. Check drawdown
    drawdown_safe, drawdown_reason = check_drawdown(current_equity, peak_equity)
    drawdown_pct = (peak_equity - current_equity) / peak_equity if peak_equity > 0 else 0
    results["checks"]["drawdown"] = {
        "passed": drawdown_safe,
        "current_equity": current_equity,
        "peak_equity": peak_equity,
        "drawdown_pct": drawdown_pct,
        "limit_pct": get_risk_limits()["max_drawdown_pct"]
    }
    if not drawdown_safe:
        results["safe_to_trade"] = False
        results["freeze_reason"] = drawdown_reason
        return results
    
    # 3. Check daily loss limit
    daily_pnl = calculate_daily_pnl(current_equity)
    daily_loss_safe, daily_loss_reason = check_daily_loss_limit(daily_pnl, current_equity)
    results["checks"]["daily_loss"] = {
        "passed": daily_loss_safe,
        "daily_pnl": daily_pnl,
        "limit_dollar": get_risk_limits()["daily_loss_dollar"],
        "limit_pct": get_risk_limits()["daily_loss_pct"]
    }
    if not daily_loss_safe:
        results["safe_to_trade"] = False
        results["freeze_reason"] = daily_loss_reason
        return results
    
    # 4. Check exposure limits (if positions provided)
    if positions:
        # Check sector exposure
        sector_safe, sector_reason = check_sector_exposure(positions, current_equity)
        results["checks"]["sector_exposure"] = {
            "passed": sector_safe,
            "reason": sector_reason
        }
        # Don't freeze on exposure limits, just log (these are checked per-order)
    
    results["checks"]["summary"] = {
        "current_equity": current_equity,
        "peak_equity": peak_equity,
        "daily_pnl": daily_pnl,
        "starting_equity": get_starting_equity(),
        "mode": "PAPER" if is_paper_mode() else "LIVE"
    }
    
    return results
