#!/usr/bin/env python3
"""
Telemetry Logger - Institutional-grade observability and monitoring

Provides structured logging for:
- Daily postmortems (P&L, win rate, slippage)
- Live order events
- Ops errors and incidents
- Learning events (adaptive weights, per-ticker updates)
- Portfolio events (position changes, theme exposure)
- Risk dashboard metrics
- Governance events (mode changes, capital ramp)
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


# Directory structure
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
STATE_DIR = BASE_DIR / "state"

# Telemetry files
OPERATOR_DASHBOARD = DATA_DIR / "operator_dashboard.json"
DAILY_POSTMORTEM = DATA_DIR / "daily_postmortem.jsonl"
LIVE_ORDERS = DATA_DIR / "live_orders.jsonl"
OPS_ERRORS = DATA_DIR / "ops_errors.jsonl"
LEARNING_EVENTS = DATA_DIR / "learning_events.jsonl"
PORTFOLIO_EVENTS = DATA_DIR / "portfolio_events.jsonl"
RISK_DASHBOARD = DATA_DIR / "risk_dashboard.jsonl"
GOV_EVENTS = DATA_DIR / "governance_events.jsonl"
UW_FLOW_CACHE = DATA_DIR / "uw_flow_cache.json"

# State files
TRADING_MODE = STATE_DIR / "trading_mode.json"
CAPITAL_RAMP = STATE_DIR / "capital_ramp.json"
PEAK_EQUITY = STATE_DIR / "peak_equity.json"


def append_jsonl(file: Path, rec: Dict):
    """Append a record to a JSONL file with automatic timestamp."""
    file.parent.mkdir(exist_ok=True, parents=True)
    rec["_ts"] = int(time.time())
    rec["_dt"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with file.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def read_json(path: Path, default=None):
    """Read a JSON file, returning default if not found or invalid."""
    if not path.exists():
        return default
    try:
        with path.open() as f:
            return json.load(f)
    except Exception:
        return default


def read_jsonl_tail(path: Path, max_lines: int = 500) -> List[Dict[str, Any]]:
    """Read the last N lines from a JSONL file."""
    if not path.exists():
        return []
    out = []
    try:
        lines = path.read_text().strip().splitlines()[-max_lines:]
        for line in lines:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out
    except Exception:
        return []


def write_json(path: Path, data: Dict):
    """Write a JSON file atomically."""
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def safe_float(val, default=0.0):
    """Convert value to float, returning default on failure."""
    try:
        return float(val)
    except Exception:
        return default


def timestamp_to_iso(ts: Optional[int]) -> str:
    """Convert Unix timestamp to ISO format string."""
    try:
        if ts is None:
            return ""
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ""


class TelemetryLogger:
    """
    Centralized telemetry logger for institutional monitoring.
    
    Provides methods for logging:
    - Daily postmortems
    - Live orders
    - Ops errors
    - Learning events
    - Portfolio events
    - Risk metrics
    - Governance events
    """
    
    def __init__(self):
        """Initialize telemetry logger with lazy file handles."""
        # Ensure directories exist
        DATA_DIR.mkdir(exist_ok=True, parents=True)
        STATE_DIR.mkdir(exist_ok=True, parents=True)
    
    # Daily Postmortem
    def log_daily_postmortem(self, pnl_total: float, trades: int, win_rate: float, 
                            avg_slippage_cents: float, max_drawdown_pct: float):
        """Log end-of-day summary statistics."""
        append_jsonl(DAILY_POSTMORTEM, {
            "event": "DAILY_POSTMORTEM",
            "pnl_total": pnl_total,
            "trades": trades,
            "win_rate": win_rate,
            "avg_slippage_cents": avg_slippage_cents,
            "max_drawdown_pct": max_drawdown_pct
        })
    
    # Live Orders
    def log_order_event(self, event_type: str, symbol: str, side: str, qty: int, 
                       price: float = None, **kwargs):
        """Log real-time order events."""
        rec = {
            "event": event_type,
            "symbol": symbol,
            "side": side,
            "qty": qty
        }
        if price is not None:
            rec["price"] = price
        rec.update(kwargs)
        append_jsonl(LIVE_ORDERS, rec)
    
    def log_slippage_block(self, spread: float, slippage_cents: float, 
                          latency_ms: int, depth_ok: bool):
        """Log execution quality metrics."""
        append_jsonl(LIVE_ORDERS, {
            "event": "SLIPPAGE_BLOCK",
            "spread": spread,
            "slippage_cents": slippage_cents,
            "latency_ms": latency_ms,
            "depth_ok": depth_ok
        })
    
    # Ops Errors
    def log_ops_error(self, error_type: str, message: str, symbol: str = None, **kwargs):
        """Log operational errors and incidents."""
        rec = {
            "event": error_type,
            "message": message
        }
        if symbol:
            rec["symbol"] = symbol
        rec.update(kwargs)
        append_jsonl(OPS_ERRORS, rec)
    
    # Learning Events
    def log_learning_event(self, event_type: str, symbol: str = None, **kwargs):
        """Log adaptive learning updates."""
        rec = {"event": event_type}
        if symbol:
            rec["symbol"] = symbol
        rec.update(kwargs)
        append_jsonl(LEARNING_EVENTS, rec)
    
    # Portfolio Events
    def log_portfolio_event(self, event_type: str, symbol: str, **kwargs):
        """Log position changes and portfolio updates."""
        rec = {
            "event": event_type,
            "symbol": symbol
        }
        rec.update(kwargs)
        append_jsonl(PORTFOLIO_EVENTS, rec)
    
    # Risk Dashboard
    def log_risk_metrics(self, total_exposure: float, theme_concentration: Dict[str, float],
                        net_delta: float = 0.0, max_symbol_exposure: float = 0.0, **kwargs):
        """Log risk metrics snapshot."""
        rec = {
            "event": "RISK_SNAPSHOT",
            "total_exposure": total_exposure,
            "theme_concentration": theme_concentration,
            "net_delta": net_delta,
            "max_symbol_exposure": max_symbol_exposure
        }
        rec.update(kwargs)
        append_jsonl(RISK_DASHBOARD, rec)
    
    # Governance Events
    def log_governance_event(self, event_type: str, **kwargs):
        """Log mode changes, capital ramp updates, kill-switch triggers."""
        rec = {"event": event_type}
        rec.update(kwargs)
        append_jsonl(GOV_EVENTS, rec)
    
    # UW Flow Cache
    def update_uw_flow_cache(self, cache: Dict[str, Any]):
        """Update the Unusual Whales flow cache, preserving computed signals."""
        # Preserve computed signals when updating cache
        if UW_FLOW_CACHE.exists():
            try:
                existing_cache = read_json(UW_FLOW_CACHE, default={})
                # For each symbol, preserve computed signals if they exist
                for symbol, new_data in cache.items():
                    if symbol.startswith("_"):
                        continue  # Skip metadata
                    if symbol in existing_cache and isinstance(existing_cache[symbol], dict):
                        existing_symbol_data = existing_cache[symbol]
                        # Preserve computed signals
                        for computed_signal in ["iv_term_skew", "smile_slope"]:
                            if computed_signal in existing_symbol_data and existing_symbol_data[computed_signal] is not None:
                                if symbol not in cache or not isinstance(cache[symbol], dict):
                                    cache[symbol] = {}
                                cache[symbol][computed_signal] = existing_symbol_data[computed_signal]
                        # Preserve insider if it exists
                        if "insider" in existing_symbol_data and existing_symbol_data["insider"]:
                            if symbol not in cache or not isinstance(cache[symbol], dict):
                                cache[symbol] = {}
                            cache[symbol]["insider"] = existing_symbol_data["insider"]
            except Exception:
                pass  # If merge fails, just write the new cache
        
        write_json(UW_FLOW_CACHE, cache)
    
    def get_uw_flow_cache(self) -> Dict[str, Any]:
        """Read the current UW flow cache."""
        return read_json(UW_FLOW_CACHE, default={})
    
    # State management
    def get_trading_mode(self) -> Dict[str, Any]:
        """Get current trading mode (PAPER/LIVE)."""
        return read_json(TRADING_MODE, default={"mode": "PAPER", "last_flip": 0, "flip_history": []})
    
    def set_trading_mode(self, mode: str):
        """Update trading mode."""
        current = self.get_trading_mode()
        current["mode"] = mode
        current["last_flip"] = int(time.time())
        if "flip_history" not in current:
            current["flip_history"] = []
        current["flip_history"].append({"mode": mode, "ts": int(time.time())})
        write_json(TRADING_MODE, current)
        self.log_governance_event("MODE_CHANGE", new_mode=mode)
    
    def get_capital_ramp(self) -> Dict[str, Any]:
        """Get current capital ramp state."""
        return read_json(CAPITAL_RAMP, default={
            "phase": 0,
            "live_frac": 0.0,
            "target_equity": 100000.0,
            "go_streak": 0,
            "min_days_ok": 10
        })
    
    def update_capital_ramp(self, phase: int = None, live_frac: float = None, 
                           go_streak: int = None, **kwargs):
        """Update capital ramp state."""
        current = self.get_capital_ramp()
        if phase is not None:
            current["phase"] = phase
        if live_frac is not None:
            current["live_frac"] = live_frac
        if go_streak is not None:
            current["go_streak"] = go_streak
        current.update(kwargs)
        write_json(CAPITAL_RAMP, current)
        self.log_governance_event("CAPITAL_RAMP_UPDATE", **current)
    
    def get_peak_equity(self) -> Dict[str, Any]:
        """Get peak equity for drawdown calculation."""
        return read_json(PEAK_EQUITY, default={"peak_equity": 100000.0, "peak_timestamp": 0})
    
    def update_peak_equity(self, equity: float):
        """Update peak equity if new high."""
        current = self.get_peak_equity()
        if equity > current.get("peak_equity", 0):
            current["peak_equity"] = equity
            current["peak_timestamp"] = int(time.time())
            write_json(PEAK_EQUITY, current)
    
    # Cockpit data access
    def get_operator_dashboard(self) -> Dict[str, Any]:
        """Get operator dashboard KPIs."""
        return read_json(OPERATOR_DASHBOARD, default={})
    
    def update_operator_dashboard(self, kpis: Dict[str, Any]):
        """Update operator dashboard KPIs."""
        write_json(OPERATOR_DASHBOARD, kpis)
    
    def get_recent_postmortems(self, max_lines: int = 250) -> List[Dict[str, Any]]:
        """Get recent daily postmortems."""
        return read_jsonl_tail(DAILY_POSTMORTEM, max_lines)
    
    def get_recent_orders(self, max_lines: int = 500) -> List[Dict[str, Any]]:
        """Get recent order events."""
        return read_jsonl_tail(LIVE_ORDERS, max_lines)
    
    def get_recent_errors(self, max_lines: int = 250) -> List[Dict[str, Any]]:
        """Get recent ops errors."""
        return read_jsonl_tail(OPS_ERRORS, max_lines)
    
    def get_recent_learning_events(self, max_lines: int = 250) -> List[Dict[str, Any]]:
        """Get recent learning events."""
        return read_jsonl_tail(LEARNING_EVENTS, max_lines)
    
    def get_recent_portfolio_events(self, max_lines: int = 250) -> List[Dict[str, Any]]:
        """Get recent portfolio events."""
        return read_jsonl_tail(PORTFOLIO_EVENTS, max_lines)
    
    def get_recent_risk_snapshots(self, max_lines: int = 250) -> List[Dict[str, Any]]:
        """Get recent risk dashboard snapshots."""
        return read_jsonl_tail(RISK_DASHBOARD, max_lines)
    
    def get_recent_governance_events(self, max_lines: int = 250) -> List[Dict[str, Any]]:
        """Get recent governance events."""
        return read_jsonl_tail(GOV_EVENTS, max_lines)
