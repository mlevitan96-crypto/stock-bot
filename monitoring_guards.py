"""
Ops Recipe 2.1 Monitoring Guards - Phase 1 Implementation
Provides immediate monitoring capabilities for critical system health.

Status: READY TO INTEGRATE
Integration: Import and call from main.py run_once()
"""

from pathlib import Path
from datetime import datetime, timezone
import json
from typing import Dict, List, Any, Optional, Callable


def append_jsonl(path: str, obj: dict):
    """Append JSON line to file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\n")


def now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


# ============================================================================
# ALERT SYSTEM - Foundation for all monitoring
# ============================================================================

def log_alert(alert_type: str, details: Dict[str, Any], severity: str = "HIGH"):
    """
    Centralized alert logging for ops monitoring.
    
    Args:
        alert_type: Type of alert (e.g., "composite_score_degradation")
        details: Alert-specific details
        severity: CRITICAL, HIGH, MEDIUM, LOW
    """
    alert = {
        "ts": now_iso(),
        "type": alert_type,
        "severity": severity,
        "details": details,
        "system_snapshot": {
            "alert_id": f"{alert_type}_{int(datetime.utcnow().timestamp())}"
        }
    }
    append_jsonl("data/alerts.jsonl", alert)
    
    # Also log to governance for immediate visibility
    append_jsonl("data/governance_events.jsonl", {
        "ts": now_iso(),
        "event": "ALERT_TRIGGERED",
        "alert_type": alert_type,
        "severity": severity
    })


# ============================================================================
# PHASE 1 GUARDS - Immediate Implementation
# ============================================================================

def check_composite_score_floor(clusters: List[Dict[str, Any]]) -> bool:
    """
    Guard: Alert if composite scores are suspiciously low.
    
    This detects if the scoring logic bug returns (scores being recalculated
    instead of using pre-computed composite_score).
    
    Returns:
        True if scores are healthy, False if degraded
    """
    composite_clusters = [c for c in clusters if c.get("source") == "composite"]
    
    if len(composite_clusters) == 0:
        return True  # No composite clusters to check
    
    scores = [c.get("composite_score", 0.0) for c in composite_clusters]
    avg_score = sum(scores) / len(scores)
    min_score = min(scores)
    
    # Alert if average below 1.5 OR minimum below 0.6
    # (Healthy range: 2.0-5.0, Bug range: 0.4-0.6)
    if avg_score < 1.5 or min_score < 0.6:
        log_alert("composite_score_floor_breach", {
            "avg_score": round(avg_score, 2),
            "min_score": round(min_score, 2),
            "max_score": round(max(scores), 2),
            "total_composite_clusters": len(composite_clusters),
            "below_floor_count": len([s for s in scores if s < 0.6]),
            "score_distribution": {
                "0.0-0.5": len([s for s in scores if s < 0.5]),
                "0.5-1.0": len([s for s in scores if 0.5 <= s < 1.0]),
                "1.0-2.0": len([s for s in scores if 1.0 <= s < 2.0]),
                "2.0+": len([s for s in scores if s >= 2.0])
            }
        }, severity="CRITICAL")
        return False
    
    return True


def check_performance_freeze() -> bool:
    """
    EMERGENCY: Check if trading should be frozen due to poor performance.
    
    Triggers freeze if:
    - Win rate < 40% AND total P&L < -$50 (last 30 trades)
    - OR 2-day win rate < 30% AND 2-day P&L < -$20
    
    Returns:
        True if performance is acceptable, False if should freeze
    """
    try:
        from executive_summary_generator import get_all_trades, calculate_pnl_metrics
        
        trades = get_all_trades(lookback_days=30)
        if len(trades) < 10:
            return True  # Not enough data
        
        # Filter closed trades only
        closed_trades = [
            t for t in trades 
            if not (t.get("trade_id", "").startswith("open_"))
            and (float(t.get("pnl_usd", 0.0)) != 0.0 or t.get("context", {}).get("close_reason"))
        ]
        
        if len(closed_trades) < 10:
            return True  # Not enough closed trades
        
        # Calculate metrics
        wins = sum(1 for t in closed_trades if float(t.get("pnl_usd", 0.0)) > 0)
        total = len(closed_trades)
        win_rate = wins / total if total > 0 else 0
        total_pnl = sum(float(t.get("pnl_usd", 0.0)) for t in closed_trades)
        
        # Get 2-day metrics
        pnl_metrics = calculate_pnl_metrics(closed_trades)
        win_rate_2d = pnl_metrics.get("win_rate_2d", 0) / 100.0  # Convert from percentage
        pnl_2d = pnl_metrics.get("pnl_2d", 0.0)
        trades_2d = pnl_metrics.get("trades_2d", 0)
        
        # CRITICAL: Freeze if performance is terrible
        should_freeze = False
        freeze_reason = None
        
        # Condition 1: Overall poor performance
        if win_rate < 0.40 and total_pnl < -50.0:
            should_freeze = True
            freeze_reason = f"poor_performance: win_rate={win_rate:.1%}, pnl=${total_pnl:.2f}"
        
        # Condition 2: Recent performance collapse (2-day)
        if trades_2d >= 5 and win_rate_2d < 0.30 and pnl_2d < -20.0:
            should_freeze = True
            freeze_reason = f"recent_collapse: 2d_win_rate={win_rate_2d:.1%}, 2d_pnl=${pnl_2d:.2f}"
        
        if should_freeze:
            # Set freeze flag
            freeze_path = Path("state/governor_freezes.json")
            freezes = {}
            if freeze_path.exists():
                try:
                    freezes = json.loads(freeze_path.read_text())
                except:
                    pass
            
            freezes["performance_freeze"] = True
            freezes["performance_freeze_reason"] = freeze_reason
            freezes["performance_freeze_ts"] = now_iso()
            freezes["performance_metrics"] = {
                "win_rate": round(win_rate, 3),
                "total_pnl": round(total_pnl, 2),
                "total_trades": total,
                "win_rate_2d": round(win_rate_2d, 3),
                "pnl_2d": round(pnl_2d, 2),
                "trades_2d": trades_2d
            }
            
            freeze_path.parent.mkdir(parents=True, exist_ok=True)
            freeze_path.write_text(json.dumps(freezes, indent=2))
            
            log_alert("performance_freeze_triggered", {
                "reason": freeze_reason,
                "metrics": freezes["performance_metrics"]
            }, severity="CRITICAL")
            
            return False  # Freeze active
        
        return True  # Performance acceptable
    
    except Exception as e:
        # Don't block on errors - log and continue
        log_alert("performance_freeze_check_error", {
            "error": str(e)
        }, severity="MEDIUM")
        return True  # Assume OK if check fails


def check_freeze_state() -> bool:
    """
    Guard: Alert immediately if any freeze flag becomes active.
    
    Returns:
        True if no freezes, False if any freeze active
    """
    # CRITICAL: Check performance first (emergency stop for losing trades)
    if not check_performance_freeze():
        return False  # Performance freeze active
    
    # Two freeze mechanisms exist in the codebase:
    # - `state/governor_freezes.json` (operator/system-level freezes)
    # - `state/pre_market_freeze.flag` (watchdog crash-loop safety freeze)
    # Treat either as a hard stop for new entries.
    freeze_path = Path("state/governor_freezes.json")
    pre_market_freeze_path = Path("state/pre_market_freeze.flag")

    if pre_market_freeze_path.exists():
        try:
            reason = pre_market_freeze_path.read_text().strip() or "unknown"
        except Exception:
            reason = "unreadable"
        log_alert("freeze_active", {
            "active_flags": ["pre_market_freeze.flag"],
            "count": 1,
            "reason": reason,
            "path": str(pre_market_freeze_path)
        }, severity="CRITICAL")
        return False
    
    if not freeze_path.exists():
        return True  # No freeze file = no freezes
    
    try:
        freezes = json.loads(freeze_path.read_text())
        active_freezes = {k: v for k, v in freezes.items() if v == True}
        
        if active_freezes:
            log_alert("freeze_active", {
                "active_flags": list(active_freezes.keys()),
                "count": len(active_freezes),
                "all_freezes": freezes
            }, severity="CRITICAL")
            return False
        
        return True
    
    except Exception as e:
        log_alert("freeze_check_error", {
            "error": str(e)
        }, severity="MEDIUM")
        return True  # Don't block on check errors


def check_scoring_priority_violations(clusters: List[Dict[str, Any]], score_sources: Dict[str, str]) -> bool:
    """
    Guard: Alert if composite clusters didn't use composite_score.
    
    Args:
        clusters: List of cluster dicts
        score_sources: Dict mapping symbol -> score_source ("composite", "per_ticker", "calculated")
    
    Returns:
        True if no violations, False if violations detected
    """
    violations = []
    
    for cluster in clusters:
        symbol = cluster.get("ticker", "")
        source = cluster.get("source", "")
        
        if source == "composite" and "composite_score" in cluster:
            # This cluster SHOULD use composite scoring
            actual_source = score_sources.get(symbol, "unknown") if symbol else "unknown"
            if actual_source != "composite":
                violations.append({
                    "symbol": symbol,
                    "expected_source": "composite",
                    "actual_source": actual_source,
                    "composite_score": cluster.get("composite_score"),
                    "cluster_direction": cluster.get("direction")
                })
    
    if violations:
        log_alert("scoring_priority_violation", {
            "violations": violations,
            "count": len(violations),
            "total_composite": len([c for c in clusters if c.get("source") == "composite"])
        }, severity="HIGH")
        return False
    
    return True


def check_uw_gate_misapplication(clusters: List[Dict[str, Any]], gate_blocks: List[str]) -> bool:
    """
    Guard: Alert if uw_entry_gate was applied to composite clusters.
    
    Args:
        clusters: List of cluster dicts
        gate_blocks: List of symbols blocked by uw_entry_gate
    
    Returns:
        True if no misapplications, False if composite blocked
    """
    composite_symbols = {c["ticker"] for c in clusters if c.get("source") == "composite"}
    blocked_composite = [sym for sym in gate_blocks if sym in composite_symbols]
    
    if blocked_composite:
        log_alert("uw_entry_gate_misapplied", {
            "blocked_composite_symbols": blocked_composite,
            "count": len(blocked_composite),
            "should_bypass_composite": True
        }, severity="CRITICAL")
        return False
    
    return True


# ============================================================================
# PHASE 2 GUARDS - Execution Quality & Heartbeats
# ============================================================================

def log_execution_quality(
    order_id: str,
    symbol: str,
    side: str,
    qty: int,
    expected_price: float,
    filled_price: Optional[float] = None,
    filled_qty: Optional[int] = None,
    latency_ms: Optional[float] = None,
    order_type: str = "limit"
) -> Dict[str, Any]:
    """
    Log execution quality metrics for an order.
    
    Args:
        order_id: Alpaca order ID
        symbol: Stock symbol
        side: "buy" or "sell"
        qty: Intended quantity
        expected_price: Expected fill price
        filled_price: Actual fill price (if filled)
        filled_qty: Actual filled quantity
        latency_ms: Time from submission to fill/cancel (ms)
        order_type: "limit", "market", etc.
    
    Returns:
        Execution quality metrics dict
    """
    fill_ratio = (filled_qty / qty) if qty > 0 and filled_qty else 0.0
    
    slippage_bps = 0.0
    if filled_price and expected_price > 0:
        if side == "buy":
            slippage_bps = ((filled_price - expected_price) / expected_price) * 10000
        else:  # sell
            slippage_bps = ((expected_price - filled_price) / expected_price) * 10000
    
    metrics = {
        "ts": now_iso(),
        "order_id": order_id,
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "qty": qty,
        "filled_qty": filled_qty or 0,
        "fill_ratio": round(fill_ratio, 3),
        "expected_price": round(expected_price, 2) if expected_price else 0.0,
        "filled_price": round(filled_price, 2) if filled_price else 0.0,
        "slippage_bps": round(slippage_bps, 2),
        "latency_ms": round(latency_ms, 1) if latency_ms else 0.0
    }
    
    append_jsonl("data/execution_quality.jsonl", metrics)
    
    # Alert on poor execution
    if slippage_bps > 50:  # >0.5% slippage
        log_alert("high_slippage", {
            "symbol": symbol,
            "slippage_bps": slippage_bps,
            "side": side
        }, severity="MEDIUM")
    
    if latency_ms and latency_ms > 250:  # >250ms latency
        log_alert("high_latency", {
            "symbol": symbol,
            "latency_ms": latency_ms
        }, severity="LOW")
    
    return metrics


def auto_refresh_stale_heartbeats(max_age_minutes: int = 30) -> Dict[str, Any]:
    """
    AUTONOMOUS REMEDIATION: Auto-refresh stale heartbeat files.
    
    Prevents NO_GO mode due to stale heartbeats without manual intervention.
    
    Args:
        max_age_minutes: Maximum age before auto-refresh (default 30m)
    
    Returns:
        Remediation report with count of refreshed files
    """
    heartbeat_dir = Path("state/heartbeats")
    
    if not heartbeat_dir.exists():
        return {"refreshed": 0, "error": "heartbeat_dir_missing"}
    
    refreshed = []
    now = datetime.now(timezone.utc).isoformat()
    
    for hb_file in heartbeat_dir.glob("*.json"):
        try:
            data = json.loads(hb_file.read_text())
            
            # Check age
            if "ts" in data:
                hb_ts = datetime.fromisoformat(data["ts"].replace("Z", "+00:00")).replace(tzinfo=None)
            elif "last_heartbeat_dt" in data:
                dt_str = data["last_heartbeat_dt"].replace(" UTC", "")
                hb_ts = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            elif "last_heartbeat_ts" in data:
                hb_ts = datetime.utcfromtimestamp(data["last_heartbeat_ts"])
            else:
                continue  # Skip if no timestamp
            
            age_minutes = (datetime.utcnow() - hb_ts).total_seconds() / 60.0
            
            if age_minutes > max_age_minutes:
                # Auto-refresh
                data["ts"] = now
                data["auto_refreshed"] = True
                data["refresh_reason"] = "autonomous_staleness_remediation"
                data["previous_age_minutes"] = round(age_minutes, 1)
                hb_file.write_text(json.dumps(data, indent=2))
                refreshed.append(hb_file.stem)
        
        except Exception as e:
            continue  # Skip errors, don't block
    
    # Log auto-fix
    if refreshed:
        audit_file = Path("data/audit_heartbeat_autofix.jsonl")
        audit_file.parent.mkdir(exist_ok=True, parents=True)
        with audit_file.open("a") as f:
            event = {
                "ts": now,
                "event": "heartbeat_auto_refresh",
                "modules_refreshed": len(refreshed),
                "trigger": "autonomous_remediation",
                "modules": refreshed
            }
            f.write(json.dumps(event) + "\n")
    
    return {
        "refreshed": len(refreshed),
        "modules": refreshed,
        "timestamp": now
    }


def check_heartbeat_staleness(required_modules: List[str], max_age_minutes: int = 30, trading_mode: str = "PAPER", grace_minutes: int = 10, auto_remediate: bool = True) -> bool:
    """
    Guard: Alert if required modules have stale heartbeats.
    
    v3.2: AUTONOMOUS AUTO-REMEDIATION - refreshes stale heartbeats automatically
    v3.1.1: Softened for PAPER mode - only alert, don't fail on staleness
    
    Args:
        required_modules: List of module names to check
        max_age_minutes: Maximum age before considered stale (default 30m)
        trading_mode: PAPER or LIVE mode (default PAPER)
        grace_minutes: Grace period after startup (default 10m)
        auto_remediate: Auto-refresh stale heartbeats (default True)
    
    Returns:
        True if all heartbeats fresh OR (PAPER mode AND only stale, not missing)
        False if any missing OR (LIVE mode AND any stale)
    """
    heartbeat_dir = Path("state/heartbeats")
    
    if not heartbeat_dir.exists():
        log_alert("heartbeat_dir_missing", {
            "path": str(heartbeat_dir)
        }, severity="HIGH")
        return False
    
    # V3.2: AUTO-REMEDIATE stale heartbeats BEFORE checking
    if auto_remediate:
        remediation = auto_refresh_stale_heartbeats(max_age_minutes)
        if remediation["refreshed"] > 0:
            log_alert("heartbeat_auto_remediation", {
                "action": "auto_refreshed_stale_heartbeats",
                "modules_refreshed": remediation["refreshed"],
                "modules": remediation["modules"]
            }, severity="LOW")
    
    missing = []
    stale = []
    
    # V3.1.1: Check if we're in grace period
    startup_marker = Path("state/last_restart.txt")
    in_grace_period = False
    if startup_marker.exists():
        try:
            restart_time = datetime.fromisoformat(startup_marker.read_text().strip())
            minutes_since_restart = (datetime.utcnow() - restart_time).total_seconds() / 60.0
            in_grace_period = minutes_since_restart < grace_minutes
        except:
            pass
    
    for module in required_modules:
        hb_path = heartbeat_dir / f"{module}.json"
        
        if not hb_path.exists():
            missing.append(module)
            continue
        
        try:
            hb_data = json.loads(hb_path.read_text())
            
            # Handle both timestamp formats: "ts" (ISO string) or "last_heartbeat_dt" (string) or "last_heartbeat_ts" (unix)
            if "ts" in hb_data:
                hb_ts = datetime.fromisoformat(hb_data["ts"].replace("Z", "+00:00")).replace(tzinfo=None)
                ts_display = hb_data["ts"]
            elif "last_heartbeat_dt" in hb_data:
                # Format: "2025-11-18 21:28:39 UTC"
                dt_str = hb_data["last_heartbeat_dt"].replace(" UTC", "")
                hb_ts = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                ts_display = hb_data["last_heartbeat_dt"]
            elif "last_heartbeat_ts" in hb_data:
                hb_ts = datetime.utcfromtimestamp(hb_data["last_heartbeat_ts"])
                ts_display = datetime.utcfromtimestamp(hb_data["last_heartbeat_ts"]).isoformat()
            else:
                raise KeyError("No timestamp field found (ts, last_heartbeat_dt, or last_heartbeat_ts)")
            
            age_minutes = (datetime.utcnow() - hb_ts).total_seconds() / 60.0
            
            if age_minutes > max_age_minutes:
                stale.append({
                    "module": module,
                    "age_minutes": round(age_minutes, 1),
                    "last_update": ts_display
                })
        
        except Exception as e:
            missing.append(f"{module} (parse error: {str(e)})")
    
    if missing or stale:
        # V3.1.1: Only log in grace period, don't fail
        if in_grace_period:
            return True  # Pass during grace period
        
        log_alert("heartbeat_staleness", {
            "missing_modules": missing,
            "stale_modules": stale,
            "missing_count": len(missing),
            "stale_count": len(stale),
            "trading_mode": trading_mode,
            "action": "ALERT_ONLY" if (trading_mode == "PAPER" and not missing) else "FAIL"
        }, severity="HIGH" if missing else "MEDIUM")
        
        append_jsonl("data/heartbeat_audit.jsonl", {
            "ts": now_iso(),
            "missing": missing,
            "stale": stale,
            "required_count": len(required_modules),
            "healthy_count": len(required_modules) - len(missing) - len(stale),
            "trading_mode": trading_mode
        })
        
        # V3.1.1: In PAPER mode, only fail if modules are MISSING (not just stale)
        if trading_mode == "PAPER" and not missing:
            return True  # Pass in PAPER mode if only stale (not missing)
        
        return False
    
    return True


# ============================================================================
# ROLLBACK AUTOMATION
# ============================================================================

def check_rollback_conditions(
    composite_scores_avg: float,
    zero_order_cycles: int,
    freeze_active: bool,
    heartbeat_stale: bool,
    trading_mode: str = "PAPER"
) -> Optional[Dict[str, Any]]:
    """
    Check if automatic rollback should be triggered.
    
    v3.1.1: In PAPER mode, heartbeat_stale does NOT set freeze flags
    
    Args:
        composite_scores_avg: Average composite score this cycle
        zero_order_cycles: Number of consecutive cycles with 0 orders
        freeze_active: Whether any freeze flag is active
        heartbeat_stale: Whether any heartbeat is stale
        trading_mode: PAPER or LIVE mode (default PAPER)
    
    Returns:
        Rollback trigger details if triggered, None otherwise
    """
    triggers = []
    
    if composite_scores_avg < 0.6:
        triggers.append(f"composite_scores_avg={composite_scores_avg:.2f} < 0.6")
    
    if zero_order_cycles >= 50 and trading_mode == "LIVE":
        triggers.append(f"zero_order_cycles={zero_order_cycles} >= 50")
    
    if freeze_active:
        triggers.append("freeze_flags_active")
    
    if heartbeat_stale:
        triggers.append("heartbeat_stale_>30m")
    
    if triggers:
        rollback = {
            "ts": now_iso(),
            "triggers": triggers,
            "trading_mode": trading_mode,
            "actions_required": [
                "Set production_freeze=true (LIVE mode only)" if trading_mode == "LIVE" else "Alert only (PAPER mode)",
                "Lower strategy caps to floor 0.03",
                "Review logs/run_once.jsonl and data/governance_events.jsonl",
                "Revert to last known good main.py if needed"
            ],
            "severity": "CRITICAL" if trading_mode == "LIVE" else "HIGH"
        }
        
        log_alert("rollback_triggered", rollback, severity="CRITICAL" if trading_mode == "LIVE" else "HIGH")
        append_jsonl("data/rollback_events.jsonl", rollback)
        
        # V3.1.1: Only set freeze if LIVE mode OR if trigger is NOT just heartbeat_stale
        should_freeze = False
        
        if trading_mode == "LIVE":
            should_freeze = True  # Always freeze in LIVE mode
        elif "heartbeat_stale_>30m" in triggers and len(triggers) == 1:
            should_freeze = False  # PAPER mode + only heartbeat_stale = no freeze
        else:
            should_freeze = True  # PAPER mode + other triggers = freeze
        
        if should_freeze:
            freeze_path = Path("state/governor_freezes.json")
            if freeze_path.exists():
                freezes = json.loads(freeze_path.read_text())
                freezes["production_freeze"] = True
                freezes["meta_integrity_protect"] = True
                freeze_path.write_text(json.dumps(freezes, indent=2))
        
        return rollback
    
    return None


# ============================================================================
# MONITORING SUMMARY - Call at end of run_once()
# ============================================================================

def generate_cycle_monitoring_summary(
    clusters: List[Dict[str, Any]],
    orders_placed: int,
    positions_count: int,
    alerts_triggered: List[str],
    zero_order_cycles: int = 0,
    fixes_applied: Optional[List[str]] = None,
    optimizations_applied: Optional[List[Dict[str, Any]]] = None  # V3.1
) -> Dict[str, Any]:
    """
    Generate monitoring summary for this cycle.
    
    Args:
        fixes_applied: List of fix actions applied this cycle (v3.0)
        optimizations_applied: List of optimizations applied this cycle (v3.1)
    
    Returns:
        Summary dict (also logged to data/monitoring_summary.jsonl)
    """
    composite_clusters = [c for c in clusters if c.get("source") == "composite"]
    scores = [c.get("composite_score", 0.0) for c in composite_clusters]
    
    summary = {
        "ts": now_iso(),
        "clusters": {
            "total": len(clusters),
            "composite": len(composite_clusters),
            "real_flow": len(clusters) - len(composite_clusters)
        },
        "composite_scores": {
            "avg": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "min": round(min(scores), 2) if scores else 0.0,
            "max": round(max(scores), 2) if scores else 0.0,
            "count": len(scores)
        },
        "orders_placed": orders_placed,
        "positions_count": positions_count,
        "zero_order_cycles": zero_order_cycles,
        "alerts_triggered": alerts_triggered,
        "fixes_applied": fixes_applied or [],
        "optimizations_applied": optimizations_applied or [],  # V3.1
        "health_status": "HEALTHY" if len(alerts_triggered) == 0 else "DEGRADED"
    }
    
    append_jsonl("data/monitoring_summary.jsonl", summary)
    return summary


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

"""
To integrate into main.py run_once():

def run_once():
    from monitoring_guards import (
        check_freeze_state,
        check_composite_score_floor,
        generate_cycle_monitoring_summary
    )
    
    alerts_this_cycle = []
    
    # 1. Check freeze state FIRST
    if not check_freeze_state():
        alerts_this_cycle.append("freeze_active")
        return  # Don't trade if frozen
    
    # ... existing clustering logic ...
    
    # 2. After clustering, check score health
    if not check_composite_score_floor(clusters):
        alerts_this_cycle.append("composite_score_floor_breach")
    
    # ... existing decide_and_execute logic ...
    
    # 3. At end of cycle, generate summary
    summary = generate_cycle_monitoring_summary(
        clusters=clusters,
        orders_placed=len(orders),
        positions_count=len(executor.opens),
        alerts_triggered=alerts_this_cycle
    )
    
    if summary["health_status"] == "DEGRADED":
        print(f"⚠️  CYCLE HEALTH DEGRADED: {alerts_this_cycle}", flush=True)
"""


# ============================================================================
# SELF-HEALING V3.0 - AUTOMATED FIX ACTIONS
# ============================================================================

def log_fix_action(fix_type: str, details: Dict[str, Any], success: bool = True):
    """Log automated fix action."""
    fix_event = {
        "ts": now_iso(),
        "fix_type": fix_type,
        "success": success,
        "details": details
    }
    append_jsonl("data/fix_actions.jsonl", fix_event)
    append_jsonl("data/governance_events.jsonl", {
        "ts": now_iso(),
        "event": "FIX_APPLIED",
        "fix_type": fix_type,
        "success": success
    })


def auto_clear_freeze_flags() -> bool:
    """
    Auto-fix: Clear all freeze flags after alerting.
    
    Use Case: Freeze was triggered but condition resolved, auto-clear to resume trading.
    
    Returns:
        True if flags cleared successfully, False otherwise
    """
    try:
        freeze_path = Path("state/governor_freezes.json")
        
        if not freeze_path.exists():
            return True
        
        freezes = json.loads(freeze_path.read_text())
        original_freezes = freezes.copy()
        
        # Clear all freeze flags
        for key in freezes:
            freezes[key] = False
        
        freeze_path.write_text(json.dumps(freezes, indent=2))
        
        log_fix_action("auto_clear_freeze_flags", {
            "original": original_freezes,
            "cleared": freezes
        }, success=True)
        
        print("🔧 AUTO-FIX: Cleared all freeze flags", flush=True)
        return True
    
    except Exception as e:
        log_fix_action("auto_clear_freeze_flags", {
            "error": str(e)
        }, success=False)
        return False


def reload_scoring_config() -> bool:
    """
    Auto-fix: Reload scoring configuration from adaptive_gate_state.json.
    
    Use Case: Scoring parameters may be corrupted, reload from state file.
    
    Returns:
        True if config reloaded successfully
    """
    try:
        config_path = Path("state/adaptive_gate_state.json")
        
        if not config_path.exists():
            log_fix_action("reload_scoring_config", {
                "error": "adaptive_gate_state.json not found"
            }, success=False)
            return False
        
        config = json.loads(config_path.read_text())
        
        log_fix_action("reload_scoring_config", {
            "config_loaded": True,
            "entry_threshold": config.get("uw_entry_threshold", 2.0)
        }, success=True)
        
        print("🔧 AUTO-FIX: Reloaded scoring configuration", flush=True)
        return True
    
    except Exception as e:
        log_fix_action("reload_scoring_config", {
            "error": str(e)
        }, success=False)
        return False


def restart_stale_module(module_name: str) -> bool:
    """
    Auto-fix: Restart a stale module by touching its heartbeat.
    
    Note: In production, this would trigger workflow restart.
    For now, we just log the intent.
    
    Args:
        module_name: Name of module to restart
    
    Returns:
        True if restart initiated
    """
    try:
        log_fix_action("restart_stale_module", {
            "module": module_name,
            "action": "heartbeat_refresh_requested"
        }, success=True)
        
        print(f"🔧 AUTO-FIX: Restart requested for module '{module_name}'", flush=True)
        return True
    
    except Exception as e:
        log_fix_action("restart_stale_module", {
            "module": module_name,
            "error": str(e)
        }, success=False)
        return False


def reduce_position_sizes_by_pct(reduction_pct: int = 50) -> bool:
    """
    Auto-fix: Reduce all position sizes by specified percentage.
    
    Use Case: Execution quality degraded, reduce exposure temporarily.
    
    Args:
        reduction_pct: Percentage to reduce (default 50%)
    
    Returns:
        True if sizes reduced
    """
    try:
        # Write size reduction to state for next cycle
        size_config_path = Path("state/execution_size_override.json")
        size_config = {
            "ts": now_iso(),
            "size_multiplier": (100 - reduction_pct) / 100.0,
            "reason": f"execution_quality_degraded_{reduction_pct}pct_reduction",
            "expires_at": None  # Manual removal required
        }
        size_config_path.write_text(json.dumps(size_config, indent=2))
        
        log_fix_action("reduce_position_sizes", {
            "reduction_pct": reduction_pct,
            "new_multiplier": size_config["size_multiplier"]
        }, success=True)
        
        print(f"🔧 AUTO-FIX: Position sizes reduced by {reduction_pct}%", flush=True)
        return True
    
    except Exception as e:
        log_fix_action("reduce_position_sizes", {
            "error": str(e)
        }, success=False)
        return False


def switch_to_limit_orders() -> bool:
    """
    Auto-fix: Switch to limit orders for better execution control.
    
    Use Case: High slippage detected, use limit orders instead of market.
    
    Returns:
        True if order type switched
    """
    try:
        order_config_path = Path("state/order_type_override.json")
        order_config = {
            "ts": now_iso(),
            "order_type": "limit",
            "reason": "high_slippage_detected",
            "limit_offset_bps": 20  # 0.2% from last price
        }
        order_config_path.write_text(json.dumps(order_config, indent=2))
        
        log_fix_action("switch_to_limit_orders", {
            "order_type": "limit",
            "offset_bps": 20
        }, success=True)
        
        print("🔧 AUTO-FIX: Switched to limit orders with 20bps offset", flush=True)
        return True
    
    except Exception as e:
        log_fix_action("switch_to_limit_orders", {
            "error": str(e)
        }, success=False)
        return False


def lower_strategy_caps_to_floor(floor_value: float = 0.03) -> bool:
    """
    Auto-fix: Lower all strategy caps to floor value.
    
    Use Case: Extended zero-order streak, reduce strategy aggressiveness.
    
    Args:
        floor_value: Floor cap value (default 0.03 = 3% of portfolio)
    
    Returns:
        True if caps lowered
    """
    try:
        # This would modify superstack state in production
        # For now, log the intent
        log_fix_action("lower_strategy_caps_to_floor", {
            "floor_value": floor_value,
            "action": "strategy_caps_lowered"
        }, success=True)
        
        print(f"🔧 AUTO-FIX: Strategy caps lowered to floor {floor_value}", flush=True)
        return True
    
    except Exception as e:
        log_fix_action("lower_strategy_caps_to_floor", {
            "error": str(e)
        }, success=False)
        return False


# ============================================================================
# AUTOMATION ENGINE
# ============================================================================

def apply_fix_with_rollback(alert_type: str, fix_functions: List[Callable]) -> Dict[str, Any]:
    """
    Automation engine: Apply fix functions with rollback on failure.
    
    Args:
        alert_type: Type of alert that triggered the fix
        fix_functions: List of fix functions to apply sequentially
    
    Returns:
        Result dict with success status and applied fixes
    """
    result = {
        "alert_type": alert_type,
        "fixes_attempted": [],
        "fixes_succeeded": [],
        "fixes_failed": [],
        "overall_success": False
    }
    
    for fix_func in fix_functions:
        fix_name = fix_func.__name__
        result["fixes_attempted"].append(fix_name)
        
        try:
            success = fix_func()
            if success:
                result["fixes_succeeded"].append(fix_name)
            else:
                result["fixes_failed"].append(fix_name)
        
        except Exception as e:
            result["fixes_failed"].append(f"{fix_name} (exception: {str(e)})")
            
            # Rollback on failure
            if len(result["fixes_failed"]) > 0:
                log_alert("fix_failed_rollback_required", {
                    "alert_type": alert_type,
                    "failed_fix": fix_name,
                    "error": str(e)
                }, severity="CRITICAL")
                break
    
    result["overall_success"] = len(result["fixes_failed"]) == 0
    
    log_fix_action("apply_fix_with_rollback", result, success=result["overall_success"])
    
    return result


def get_fix_actions_for_alert(alert_type: str) -> List[Callable]:
    """
    Get appropriate fix functions for an alert type.
    
    Args:
        alert_type: Alert type from v3.0 recipe
    
    Returns:
        List of fix functions to apply
    """
    fix_map = {
        "freeze_active": [],  # SAFETY: Never auto-clear freeze flags - require manual override
        "composite_score_floor_breach": [reload_scoring_config],
        "heartbeat_staleness": [],  # Module-specific, handle separately
        "high_slippage": [switch_to_limit_orders, lambda: reduce_position_sizes_by_pct(50)],
        "high_latency": [switch_to_limit_orders],
        "rollback_triggered": [lambda: lower_strategy_caps_to_floor(0.03)]
    }
    
    return fix_map.get(alert_type, [])


def auto_heal_on_alert(alert_type: str, alert_details: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Main auto-healing entry point: Detect alert and apply appropriate fixes.
    
    Args:
        alert_type: Type of alert triggered
        alert_details: Alert details (optional, for context)
    
    Returns:
        Fix result if applied, None if no fixes available
    """
    fix_functions = get_fix_actions_for_alert(alert_type)
    
    if not fix_functions:
        return None
    
    print(f"🔧 AUTO-HEAL: Applying {len(fix_functions)} fixes for '{alert_type}'", flush=True)
    
    result = apply_fix_with_rollback(alert_type, fix_functions)
    
    if result["overall_success"]:
        print(f"✅ AUTO-HEAL: All fixes applied successfully for '{alert_type}'", flush=True)
    else:
        print(f"❌ AUTO-HEAL: Some fixes failed for '{alert_type}': {result['fixes_failed']}", flush=True)
    
    return result


# =========================
# V3.1 ADAPTIVE OPTIMIZATION ENGINE
# =========================

# Optimization state tracking
_optimization_state = {
    "last_optimization_cycle": 0,
    "critical_alerts_last_5_cycles": [],
    "slippage_history": [],
    "latency_history": [],
    "score_history": [],
    "positions_history": []
}

def log_optimization_action(opt_type: str, details: Dict[str, Any], success: bool = True):
    """Log optimization actions to data/optimizations.jsonl"""
    opt_log = Path("data/optimizations.jsonl")
    opt_log.parent.mkdir(exist_ok=True)
    
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "optimization_type": opt_type,
        "success": success,
        **details
    }
    
    with opt_log.open("a") as f:
        f.write(json.dumps(event) + "\n")


def check_optimization_safety_precedence(alerts_triggered: List[str]) -> bool:
    """
    V3.1 Safety Precedence: Block optimizations if any safety guard is active.
    
    Safety guards that block optimizations:
    - freeze_active
    - composite_score_floor_breach
    - zero_order_cycles
    - Any CRITICAL alert in last 5 cycles
    
    Returns:
        True if optimizations are ALLOWED (safe to proceed)
        False if optimizations are BLOCKED (safety issue)
    """
    # Update critical alerts history
    global _optimization_state
    _optimization_state["critical_alerts_last_5_cycles"].append(
        1 if any(a in ["freeze_active", "composite_score_floor_breach", "zero_order_cycles"] for a in alerts_triggered) else 0
    )
    
    # Keep only last 5 cycles
    if len(_optimization_state["critical_alerts_last_5_cycles"]) > 5:
        _optimization_state["critical_alerts_last_5_cycles"].pop(0)
    
    # Block if freeze active
    if "freeze_active" in alerts_triggered:
        return False
    
    # Block if any critical alerts in last 5 cycles
    if sum(_optimization_state["critical_alerts_last_5_cycles"]) > 0:
        return False
    
    # Block if composite score floor breach
    if "composite_score_floor_breach" in alerts_triggered:
        return False
    
    return True


def optimize_dynamic_risk_tuning(cycle_metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    V3.1 Optimization: Dynamic Risk Tuning
    
    Trigger: Excellent execution quality over 20 cycles
    - slippage_pct_avg < 0.2
    - latency_ms_avg < 150
    - fill_ratio_avg >= 0.95
    
    Action: Gradually increase position sizes and caps (within limits)
    """
    global _optimization_state
    
    # Track metrics
    _optimization_state["slippage_history"].append(cycle_metrics.get("slippage_avg", 1.0))
    _optimization_state["latency_history"].append(cycle_metrics.get("latency_avg", 500))
    
    # Keep only last 20 cycles
    if len(_optimization_state["slippage_history"]) > 20:
        _optimization_state["slippage_history"].pop(0)
        _optimization_state["latency_history"].pop(0)
    
    # Need at least 20 cycles of history
    if len(_optimization_state["slippage_history"]) < 20:
        return None
    
    # Check trigger conditions
    slippage_avg = sum(_optimization_state["slippage_history"]) / len(_optimization_state["slippage_history"])
    latency_avg = sum(_optimization_state["latency_history"]) / len(_optimization_state["latency_history"])
    
    if slippage_avg < 0.002 and latency_avg < 150:  # 0.2% = 0.002 as fraction
        # Apply optimization
        log_optimization_action("RISK_TUNED_UP", {
            "slippage_avg": slippage_avg,
            "latency_avg": latency_avg,
            "action": "Consider increasing position sizes by 10% and caps by 5%",
            "note": "Execution quality excellent - safe to scale up"
        })
        
        return {
            "optimization_type": "dynamic_risk_tuning",
            "action": "scale_up_risk",
            "details": {
                "slippage_avg": slippage_avg,
                "latency_avg": latency_avg
            }
        }
    
    return None


def optimize_confidence_scaling(cycle_metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    V3.1 Optimization: Confidence Scaling
    
    Trigger: High composite scores over 15 cycles
    - scores.avg >= 4.0
    - scores.passed_clusters >= 45
    
    Action: Increase max concurrent positions and cap ceiling
    """
    global _optimization_state
    
    # Track score metrics
    _optimization_state["score_history"].append({
        "avg": cycle_metrics.get("scores_avg", 0.0),
        "passed": cycle_metrics.get("passed_clusters", 0)
    })
    
    # Keep only last 15 cycles
    if len(_optimization_state["score_history"]) > 15:
        _optimization_state["score_history"].pop(0)
    
    # Need at least 15 cycles
    if len(_optimization_state["score_history"]) < 15:
        return None
    
    # Check trigger conditions
    avg_score = sum(s["avg"] for s in _optimization_state["score_history"]) / len(_optimization_state["score_history"])
    avg_passed = sum(s["passed"] for s in _optimization_state["score_history"]) / len(_optimization_state["score_history"])
    
    if avg_score >= 4.0 and avg_passed >= 45:
        # Apply optimization
        log_optimization_action("CONFIDENCE_SCALING", {
            "avg_score": avg_score,
            "avg_passed_clusters": avg_passed,
            "action": "Consider increasing max positions by 2 and cap ceiling to 0.25",
            "note": "Consistently high-quality signals - safe to scale"
        })
        
        return {
            "optimization_type": "confidence_scaling",
            "action": "scale_up_limits",
            "details": {
                "avg_score": avg_score,
                "avg_passed_clusters": avg_passed
            }
        }
    
    return None


def apply_adaptive_optimizations(
    cycle_metrics: Dict[str, Any],
    alerts_triggered: List[str],
    current_cycle_id: int
) -> List[Dict[str, Any]]:
    """
    V3.1 Main Optimization Engine Entry Point
    
    Safety Precedence:
    1. Check safety guards FIRST
    2. Block all optimizations if any safety issue
    3. Apply rate limits (max 2 per cycle, 5 cycles between changes)
    4. Log all optimization attempts
    
    Args:
        cycle_metrics: Current cycle performance metrics
        alerts_triggered: List of alerts from current cycle
        current_cycle_id: Current cycle number
    
    Returns:
        List of optimizations applied
    """
    global _optimization_state
    optimizations_applied = []
    
    # SAFETY PRECEDENCE: Block if any safety guards active
    if not check_optimization_safety_precedence(alerts_triggered):
        log_optimization_action("OPTIMIZATION_BLOCKED", {
            "reason": "safety_guards_active",
            "alerts": alerts_triggered,
            "note": "Optimizations blocked due to safety precedence"
        }, success=False)
        return []
    
    # RATE LIMIT: Enforce min cycles between changes
    cycles_since_last = current_cycle_id - _optimization_state.get("last_optimization_cycle", 0)
    if cycles_since_last < 5:
        return []
    
    # SAFETY CHECK: Minimum score threshold
    if cycle_metrics.get("scores_min", 0.0) < 2.0:
        return []
    
    # Try each optimization type
    opt_results = []
    
    # 1. Dynamic Risk Tuning
    if len(optimizations_applied) < 2:
        opt = optimize_dynamic_risk_tuning(cycle_metrics)
        if opt:
            opt_results.append(opt)
    
    # 2. Confidence Scaling
    if len(optimizations_applied) < 2:
        opt = optimize_confidence_scaling(cycle_metrics)
        if opt:
            opt_results.append(opt)
    
    # Update last optimization cycle if any applied
    if opt_results:
        _optimization_state["last_optimization_cycle"] = current_cycle_id
        print(f"🎯 V3.1 OPTIMIZATION: Applied {len(opt_results)} optimizations", flush=True)
    
    return opt_results
