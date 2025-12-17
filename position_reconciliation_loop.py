#!/usr/bin/env python3
"""
Position Reconciliation Loop V2
Fully autonomous, authoritative, self-remediating position sync with Alpaca.
Investigates, fixes, and resumes trading without human review.
"""

import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from config.registry import CacheFiles, StateFiles, atomic_write_json, append_jsonl


class PositionReconcilerV2:
    """Autonomous position reconciler with self-healing capabilities."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret
        }
        
        # Config
        self.config = {
            "poll_interval_sec": 30,
            "max_retries": 5,
            "retry_backoff_sec": 10,
            "close_orphaned_in_bot": True,
            "reconcile_quantity_mismatch": True,
            "rebalance_min_qty_delta": 1,
            "rebalance_order_limit_usd": 1000,
            "max_degraded_minutes": 120,
            "prefer_broker_truth": True
        }
        
        # State paths (canonical registry)
        self.alpaca_positions_path = StateFiles.ALPACA_POSITIONS
        self.internal_positions_path = StateFiles.INTERNAL_POSITIONS
        self.executor_state_path = StateFiles.EXECUTOR_STATE
        self.portfolio_state_path = StateFiles.PORTFOLIO_STATE
        self.remediation_log_path = CacheFiles.AUDIT_POSITIONS_AUTOFIX
        self.degraded_state_path = StateFiles.DEGRADED_MODE
        
        # Ensure directories exist
        self.alpaca_positions_path.parent.mkdir(exist_ok=True, parents=True)
        self.remediation_log_path.parent.mkdir(exist_ok=True, parents=True)
    
    def fetch_alpaca_positions_with_retry(self) -> Optional[Dict]:
        """Fetch positions with retry logic. Returns None if broker unreachable."""
        retries = 0
        alpaca_data = None
        
        while retries < self.config["max_retries"] and alpaca_data is None:
            try:
                # Get positions
                positions_resp = requests.get(
                    f'{self.base_url}/v2/positions',
                    headers=self.headers,
                    timeout=10
                )
                positions_resp.raise_for_status()
                positions_raw = positions_resp.json()
                
                # Get account
                account_resp = requests.get(
                    f'{self.base_url}/v2/account',
                    headers=self.headers,
                    timeout=10
                )
                account_resp.raise_for_status()
                account = account_resp.json()
                
                # Format positions
                positions = []
                for p in positions_raw:
                    positions.append({
                        "symbol": p.get("symbol"),
                        "qty": float(p.get("qty", 0)),
                        "side": p.get("side"),
                        "market_value": float(p.get("market_value", 0)),
                        "avg_entry_price": float(p.get("avg_entry_price", 0)),
                        "current_price": float(p.get("current_price", 0)),
                        "unrealized_pl": float(p.get("unrealized_pl", 0)),
                        "unrealized_plpc": float(p.get("unrealized_plpc", 0))
                    })
                
                alpaca_data = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "positions": positions,
                    "cash": float(account.get("cash", 0)),
                    "portfolio_value": float(account.get("portfolio_value", 0)),
                    "equity": float(account.get("equity", 0)),
                    "buying_power": float(account.get("buying_power", 0))
                }
                
            except Exception as e:
                retries += 1
                if retries < self.config["max_retries"]:
                    time.sleep(self.config["retry_backoff_sec"])
                else:
                    self.audit_log("broker_unreachable_max_retries", {
                        "retries": retries,
                        "error": str(e)
                    })
        
        return alpaca_data
    
    def enter_degraded_mode(self, reason: str) -> Dict:
        """Enter autonomous degraded mode: use last-known state, reduce-only."""
        degraded_state = {
            "mode": "DEGRADED",
            "since": datetime.utcnow().isoformat() + "Z",
            "reason": reason
        }
        try:
            atomic_write_json(self.degraded_state_path, degraded_state)
        except Exception:
            self.degraded_state_path.write_text(json.dumps(degraded_state, indent=2))
        
        # Load last known Alpaca snapshot
        last_snapshot = {}
        if self.alpaca_positions_path.exists():
            try:
                last_snapshot = json.loads(self.alpaca_positions_path.read_text())
            except:
                pass
        
        self.audit_log("degraded_mode_entered", {
            "reason": reason,
            "using_snapshot": last_snapshot.get("timestamp", "none")
        })
        
        return last_snapshot
    
    def exit_degraded_mode(self):
        """Exit degraded mode and resume normal operations."""
        normal_state = {
            "mode": "NORMAL",
            "since": datetime.utcnow().isoformat() + "Z"
        }
        try:
            atomic_write_json(self.degraded_state_path, normal_state)
        except Exception:
            self.degraded_state_path.write_text(json.dumps(normal_state, indent=2))
        self.audit_log("degraded_mode_exited", {})
    
    def load_internal_positions(self) -> Dict:
        """Load bot's internal position state."""
        if not self.internal_positions_path.exists():
            return {"positions": {}, "timestamp": datetime.utcnow().isoformat() + "Z"}
        
        try:
            return json.loads(self.internal_positions_path.read_text())
        except:
            return {"positions": {}, "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    def compute_diffs(self, alpaca_data: Dict, internal_data: Dict) -> Tuple[List[Dict], Dict]:
        """Compute differences and return (diffs_list, plan_dict)."""
        alpaca_positions = {p["symbol"]: p for p in alpaca_data.get("positions", [])}
        internal_positions = internal_data.get("positions", {})
        
        alpaca_symbols = set(alpaca_positions.keys())
        internal_symbols = set(internal_positions.keys())
        
        plan = {
            "missing_in_bot": [],
            "orphaned_in_bot": [],
            "quantity_mismatch": []
        }
        
        # Missing in bot
        for symbol in (alpaca_symbols - internal_symbols):
            ap = alpaca_positions[symbol]
            diff = {
                "type": "missing_in_bot",
                "symbol": symbol,
                "alpaca_qty": ap["qty"],
                "alpaca_side": ap["side"],
                "alpaca_value": ap["market_value"]
            }
            plan["missing_in_bot"].append(diff)
        
        # Orphaned in bot
        for symbol in (internal_symbols - alpaca_symbols):
            ip = internal_positions[symbol]
            diff = {
                "type": "orphaned_in_bot",
                "symbol": symbol,
                "bot_qty": ip.get("qty", 0),
                "bot_side": ip.get("side", "unknown")
            }
            plan["orphaned_in_bot"].append(diff)
        
        # Quantity mismatch
        for symbol in (alpaca_symbols & internal_symbols):
            ap = alpaca_positions[symbol]
            ip = internal_positions[symbol]
            
            alpaca_qty = abs(ap["qty"])
            bot_qty = abs(ip.get("qty", 0))
            
            if abs(alpaca_qty - bot_qty) > 0.01:
                diff = {
                    "type": "quantity_mismatch",
                    "symbol": symbol,
                    "alpaca_qty": ap["qty"],
                    "alpaca_side": ap["side"],
                    "bot_qty": ip.get("qty", 0),
                    "bot_side": ip.get("side", "unknown"),
                    "delta": alpaca_qty - bot_qty
                }
                plan["quantity_mismatch"].append(diff)
        
        all_diffs = (plan["missing_in_bot"] + 
                     plan["orphaned_in_bot"] + 
                     plan["quantity_mismatch"])
        
        return all_diffs, plan
    
    def authoritative_overwrite(self, alpaca_data: Dict) -> Dict:
        """Authoritative overwrite: internal state = Alpaca truth."""
        reconciled = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "positions": {}
        }
        
        for pos in alpaca_data.get("positions", []):
            symbol = pos["symbol"]
            reconciled["positions"][symbol] = {
                "qty": pos["qty"],
                "side": pos["side"],
                "avg_entry_price": pos["avg_entry_price"],
                "current_price": pos["current_price"],
                "market_value": pos["market_value"],
                "unrealized_pl": pos["unrealized_pl"],
                "unrealized_plpc": pos["unrealized_plpc"],
                "source": "alpaca_authoritative",
                "reconciled_at": datetime.utcnow().isoformat() + "Z"
            }
        
        return reconciled
    
    def audit_log(self, event: str, details: Dict):
        """Append remediation audit event."""
        event_data = {"event": event, "ts": datetime.utcnow().isoformat() + "Z", "details": details}
        try:
            append_jsonl(self.remediation_log_path, event_data)
        except Exception:
            with self.remediation_log_path.open("a") as f:
                f.write(json.dumps(event_data) + "\n")
    
    def reconcile(self, executor_opens: Optional[Dict] = None) -> Dict:
        """
        V2 Autonomous Reconciliation:
        1. Fetch Alpaca with retries
        2. If unreachable → degraded mode (reduce-only, use last snapshot)
        3. Compute diffs and create remediation plan
        4. Apply fixes autonomously:
           - Authoritative overwrite internal state
           - Close orphaned positions
           - Inject missing positions
        5. Sync executor state
        6. Exit degraded mode if broker reachable
        7. Resume trading (NO HALT)
        """
        
        # Step 1: Fetch Alpaca with retries
        alpaca_data = self.fetch_alpaca_positions_with_retry()
        
        # Step 2: Handle broker unreachable
        degraded_mode = False
        if alpaca_data is None:
            alpaca_data = self.enter_degraded_mode("broker_unreachable")
            degraded_mode = True
        
        # Step 3: Load internal and compute diffs
        internal_data = self.load_internal_positions()
        all_diffs, plan = self.compute_diffs(alpaca_data, internal_data)
        
        # Step 4: Apply autonomous fixes
        # 4a: Authoritative overwrite (Alpaca is truth, sync internal to match it)
        internal_fixed = self.authoritative_overwrite(alpaca_data)
        
        # 4b: Orphaned positions - Just purge from internal state (already handled by authoritative_overwrite)
        # DO NOT close at broker - that would create unwanted positions!
        if plan["orphaned_in_bot"]:
            for orphan in plan["orphaned_in_bot"]:
                self.audit_log("orphan_purged", {
                    "symbol": orphan["symbol"],
                    "qty": orphan["bot_qty"],
                    "action": "removed_from_internal_state_only"
                })
        
        # 4c: Missing in bot - already handled by authoritative overwrite
        if plan["missing_in_bot"]:
            self.audit_log("missing_injected", {
                "count": len(plan["missing_in_bot"]),
                "symbols": [m["symbol"] for m in plan["missing_in_bot"]]
            })
        
        # 4d: Quantity mismatches - already handled by authoritative overwrite
        if plan["quantity_mismatch"]:
            self.audit_log("quantity_reconciled", {
                "count": len(plan["quantity_mismatch"]),
                "details": plan["quantity_mismatch"]
            })
        
        # Step 5: Save reconciled state
        try:
            atomic_write_json(self.internal_positions_path, internal_fixed)
        except Exception:
            self.internal_positions_path.write_text(json.dumps(internal_fixed, indent=2))
        try:
            atomic_write_json(self.alpaca_positions_path, alpaca_data)
        except Exception:
            self.alpaca_positions_path.write_text(json.dumps(alpaca_data, indent=2))
        
        # Sync executor.opens if provided
        if executor_opens is not None:
            executor_opens.clear()
            for pos in alpaca_data.get("positions", []):
                symbol = pos["symbol"]
                executor_opens[symbol] = {
                    "entry_price": pos["avg_entry_price"],
                    "qty": abs(pos["qty"]),
                    "side": pos["side"],
                    "ts": datetime.utcnow(),
                    "trail_dist": None,
                    "high_water": pos["current_price"]
                }
        
        # Save executor state
        executor_state = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "opens": {k: {**v, "ts": v["ts"].isoformat() + "Z"} 
                     for k, v in (executor_opens or {}).items()}
        }
        try:
            atomic_write_json(self.executor_state_path, executor_state)
        except Exception:
            self.executor_state_path.write_text(json.dumps(executor_state, indent=2))
        
        # Append portfolio state history
        portfolio_event = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "alpaca": alpaca_data,
            "internal": internal_fixed,
            "diffs": all_diffs
        }
        with self.portfolio_state_path.open("a") as f:
            f.write(json.dumps(portfolio_event) + "\n")
        
        # Step 6: Exit degraded mode if broker reachable
        if not degraded_mode and self.degraded_state_path.exists():
            try:
                current_degraded = json.loads(self.degraded_state_path.read_text())
                if current_degraded.get("mode") == "DEGRADED":
                    self.exit_degraded_mode()
            except:
                pass
        
        # Step 7: Build result (NO HALT - always resume)
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "alpaca_positions_count": len(alpaca_data.get("positions", [])),
            "internal_positions_count": len(internal_data.get("positions", {})),
            "reconciled_positions_count": len(internal_fixed["positions"]),
            "total_diffs": len(all_diffs),
            "plan": plan,
            "alpaca_cash": alpaca_data.get("cash", 0),
            "alpaca_portfolio_value": alpaca_data.get("portfolio_value", 0),
            "degraded_mode": degraded_mode,
            "reconciliation_status": "autonomous_fixed" if len(all_diffs) > 0 else "clean",
            "action": "resume_trading"  # V2: Always resume
        }
        
        # Audit final status
        if len(all_diffs) > 0:
            self.audit_log("autonomous_reconciliation_complete", {
                "total_fixes": len(all_diffs),
                "missing_in_bot": len(plan["missing_in_bot"]),
                "orphaned_in_bot": len(plan["orphaned_in_bot"]),
                "quantity_mismatch": len(plan["quantity_mismatch"])
            })
        else:
            self.audit_log("reconciliation_clean", {
                "positions_count": len(alpaca_data.get("positions", []))
            })
        
        return result


def run_position_reconciliation_loop(api_key: str, api_secret: str, base_url: str, 
                                     executor_opens: Optional[Dict] = None) -> Dict:
    """
    Execute V2 autonomous position reconciliation.
    Fixes issues and resumes trading without human intervention.
    """
    reconciler = PositionReconcilerV2(api_key, api_secret, base_url)
    return reconciler.reconcile(executor_opens)
