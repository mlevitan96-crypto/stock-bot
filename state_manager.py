#!/usr/bin/env python3
"""
State Manager - Trading State Persistence
=========================================
Manages persistent trading state across restarts to prevent unsafe re-entry.

State Schema (versioned):
- open_positions: per symbol (qty, side, cost_basis, entry_time)
- realized_pnl
- unrealized_pnl (if tracked)
- last_trade_per_symbol: timestamps
- last_order_ids (if used)
- regime / risk posture flags (if already modeled)
- last_heartbeat_time
- state_version: schema version for migration

Self-healing behavior:
- Detects corrupted state files
- Attempts one-time self-heal by moving corrupt file and reconciling with Alpaca
- Refuses to start trading if reconciliation fails
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import alpaca_trade_api as tradeapi
from config.registry import Directories, StateFiles, atomic_write_json, read_json

# Ensure state directory exists
Directories.STATE.mkdir(parents=True, exist_ok=True)

STATE_FILE = Directories.STATE / "trading_state.json"
STATE_VERSION = 1  # Increment when schema changes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateManager:
    """Manages persistent trading state with reconciliation."""
    
    def __init__(self, alpaca_api: Optional[tradeapi.REST] = None):
        """
        Initialize state manager.
        
        Args:
            alpaca_api: Optional Alpaca API client for reconciliation.
                       If None, reconciliation will be skipped.
        """
        self.state_file = STATE_FILE
        self.alpaca_api = alpaca_api
        self._state: Dict[str, Any] = {}
        self._reconciled = False
        
    def _empty_state(self) -> Dict[str, Any]:
        """Return a well-defined empty state structure."""
        return {
            "state_version": STATE_VERSION,
            "open_positions": {},
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "last_trade_per_symbol": {},
            "last_order_ids": {},
            "regime": "neutral",
            "risk_posture": "normal",
            "last_heartbeat_time": None,
            "last_updated": None,
            "reconciliation_status": "pending"
        }
    
    def load_state(self) -> Dict[str, Any]:
        """
        Load state from disk.
        
        Returns:
            State dictionary. If file is missing or corrupted, returns empty state.
            
        Raises:
            Exception: If state is corrupted and self-heal fails.
        """
        if not self.state_file.exists():
            logger.info(f"State file not found at {self.state_file}, starting with empty state")
            self._state = self._empty_state()
            return self._state
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            
            # Validate required keys
            required_keys = ["state_version", "open_positions", "realized_pnl", 
                            "last_trade_per_symbol", "last_heartbeat_time"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                raise ValueError(f"State file missing required keys: {missing_keys}")
            
            # Version migration (future-proofing)
            if data.get("state_version", 0) != STATE_VERSION:
                logger.warning(f"State version mismatch: {data.get('state_version')} vs {STATE_VERSION}")
                # For now, just log - future versions can implement migration logic
            
            self._state = data
            logger.info(f"State loaded successfully: {len(data.get('open_positions', {}))} positions")
            return self._state
            
        except (json.JSONDecodeError, IOError, ValueError) as e:
            logger.critical(f"State file corruption detected: {e}")
            return self._self_heal_corrupt_state(e)
    
    def _self_heal_corrupt_state(self, error: Exception) -> Dict[str, Any]:
        """
        Attempt one-time self-heal of corrupted state.
        
        Moves corrupt file to backup and starts with empty state + reconciliation.
        
        Returns:
            Empty state dictionary (reconciled with Alpaca if possible).
            
        Raises:
            Exception: If reconciliation fails and trading should be halted.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = self.state_file.with_suffix(f".corrupt.{timestamp}.json")
        
        try:
            # Move corrupt file to backup
            if self.state_file.exists():
                import shutil
                shutil.move(str(self.state_file), str(backup_path))
                logger.critical(f"Moved corrupt state file to {backup_path}")
        except Exception as move_err:
            logger.error(f"Failed to move corrupt file: {move_err}")
        
        # Start with empty state
        self._state = self._empty_state()
        logger.info("Starting with empty state after corruption recovery")
        
        # Attempt reconciliation
        if self.alpaca_api:
            try:
                reconciled = self.reconcile_with_alpaca(self._state)
                if not reconciled:
                    raise Exception("Reconciliation failed after state corruption")
                logger.info("State self-healed: reconciled with Alpaca successfully")
            except Exception as recon_err:
                logger.critical(f"Reconciliation failed after corruption: {recon_err}")
                # Mark state as requiring manual intervention
                self._state["reconciliation_status"] = "failed"
                self._state["reconciliation_error"] = str(recon_err)
                self._state["requires_manual_intervention"] = True
                # Save the failed state so it's visible
                self.save_state(self._state)
                raise Exception(f"Cannot proceed: state corruption + reconciliation failure: {recon_err}")
        else:
            logger.warning("No Alpaca API available for reconciliation after corruption")
            self._state["reconciliation_status"] = "skipped_no_api"
        
        return self._state
    
    def reconcile_with_alpaca(self, state: Optional[Dict[str, Any]] = None) -> bool:
        """
        Reconcile local state with Alpaca (ground truth).
        
        Alpaca is authoritative for open positions. Local state is updated to match.
        
        Args:
            state: Optional state dict. If None, uses internal state.
            
        Returns:
            True if reconciliation succeeded, False otherwise.
        """
        if not self.alpaca_api:
            logger.warning("Cannot reconcile: no Alpaca API provided")
            return False
        
        if state is None:
            state = self._state
        
        try:
            # Fetch current positions from Alpaca
            alpaca_positions = self.alpaca_api.list_positions()
            
            # Build reconciled positions dict
            reconciled_positions = {}
            for pos in alpaca_positions:
                symbol = pos.symbol
                qty = float(pos.qty)
                side = "buy" if qty > 0 else "sell"
                cost_basis = float(pos.avg_entry_price) if hasattr(pos, 'avg_entry_price') else 0.0
                
                # Try to preserve entry_time from local state if available
                local_pos = state.get("open_positions", {}).get(symbol, {})
                entry_time = local_pos.get("entry_time")
                if not entry_time:
                    # Use current time as fallback
                    entry_time = datetime.now(timezone.utc).isoformat()
                
                reconciled_positions[symbol] = {
                    "qty": abs(qty),
                    "side": side,
                    "cost_basis": cost_basis,
                    "entry_time": entry_time,
                    "current_price": float(pos.current_price) if hasattr(pos, 'current_price') else cost_basis,
                    "market_value": float(pos.market_value) if hasattr(pos, 'market_value') else 0.0,
                    "unrealized_pl": float(pos.unrealized_pl) if hasattr(pos, 'unrealized_pl') else 0.0,
                    "reconciled_at": datetime.now(timezone.utc).isoformat()
                }
            
            # Check for discrepancies
            local_positions = state.get("open_positions", {})
            local_symbols = set(local_positions.keys())
            alpaca_symbols = set(reconciled_positions.keys())
            
            if local_symbols != alpaca_symbols:
                missing_in_alpaca = local_symbols - alpaca_symbols
                missing_in_local = alpaca_symbols - local_symbols
                
                if missing_in_alpaca:
                    logger.warning(f"Positions in local state but not in Alpaca: {missing_in_alpaca}")
                if missing_in_local:
                    logger.warning(f"Positions in Alpaca but not in local state: {missing_in_local}")
            
            # Update state with reconciled positions
            state["open_positions"] = reconciled_positions
            state["reconciliation_status"] = "success"
            state["last_reconciled"] = datetime.now(timezone.utc).isoformat()
            state["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            # Update unrealized PnL from Alpaca positions
            total_unrealized = sum(pos.get("unrealized_pl", 0.0) for pos in reconciled_positions.values())
            state["unrealized_pnl"] = total_unrealized
            
            self._state = state
            self._reconciled = True
            
            logger.info(f"Reconciliation complete: {len(reconciled_positions)} positions from Alpaca")
            return True
            
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}", exc_info=True)
            state["reconciliation_status"] = "failed"
            state["reconciliation_error"] = str(e)
            return False
    
    def save_state(self, state: Optional[Dict[str, Any]] = None) -> None:
        """
        Save state to disk using atomic write.
        
        Args:
            state: Optional state dict. If None, uses internal state.
        """
        if state is None:
            state = self._state
        
        # Update metadata
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        state["state_version"] = STATE_VERSION
        
        try:
            atomic_write_json(self.state_file, state)
            self._state = state
        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)
            raise
    
    def update_position(self, symbol: str, qty: int, side: str, cost_basis: float, 
                       entry_time: Optional[str] = None) -> None:
        """
        Update position in state and persist.
        
        Args:
            symbol: Stock symbol
            qty: Quantity (always positive)
            side: "buy" or "sell"
            cost_basis: Entry price
            entry_time: Optional ISO timestamp. If None, uses current time.
        """
        if entry_time is None:
            entry_time = datetime.now(timezone.utc).isoformat()
        
        if qty == 0:
            # Remove position
            self._state.get("open_positions", {}).pop(symbol, None)
        else:
            # Update or add position
            if "open_positions" not in self._state:
                self._state["open_positions"] = {}
            
            self._state["open_positions"][symbol] = {
                "qty": qty,
                "side": side,
                "cost_basis": cost_basis,
                "entry_time": entry_time,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        
        # Update last trade timestamp
        if "last_trade_per_symbol" not in self._state:
            self._state["last_trade_per_symbol"] = {}
        self._state["last_trade_per_symbol"][symbol] = datetime.now(timezone.utc).isoformat()
        
        # Persist
        self.save_state()
    
    def record_order_id(self, symbol: str, order_id: str) -> None:
        """Record order ID for a symbol."""
        if "last_order_ids" not in self._state:
            self._state["last_order_ids"] = {}
        self._state["last_order_ids"][symbol] = order_id
        self.save_state()
    
    def update_pnl(self, realized_delta: float = 0.0, unrealized: Optional[float] = None) -> None:
        """
        Update PnL values.
        
        Args:
            realized_delta: Change in realized PnL (can be negative)
            unrealized: New unrealized PnL value (if provided)
        """
        self._state["realized_pnl"] = self._state.get("realized_pnl", 0.0) + realized_delta
        
        if unrealized is not None:
            self._state["unrealized_pnl"] = unrealized
        
        self.save_state()
    
    def update_heartbeat(self) -> None:
        """Update last heartbeat time."""
        self._state["last_heartbeat_time"] = datetime.now(timezone.utc).isoformat()
        self.save_state()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state (read-only copy)."""
        return self._state.copy()
    
    def is_reconciled(self) -> bool:
        """Check if state has been reconciled with Alpaca."""
        return self._reconciled and self._state.get("reconciliation_status") == "success"


# Convenience functions for backward compatibility
def load_state(alpaca_api: Optional[tradeapi.REST] = None) -> Dict[str, Any]:
    """Load state from disk."""
    manager = StateManager(alpaca_api)
    return manager.load_state()

def save_state(state: Dict[str, Any]) -> None:
    """Save state to disk."""
    manager = StateManager()
    manager.save_state(state)

def reconcile_with_alpaca(state: Dict[str, Any], alpaca_api: tradeapi.REST) -> Dict[str, Any]:
    """Reconcile state with Alpaca."""
    manager = StateManager(alpaca_api)
    manager.load_state()  # Load existing state
    manager.reconcile_with_alpaca(state)
    return manager.get_state()
