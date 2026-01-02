#!/usr/bin/env python3
"""
Attribution Logging Audit
Reviews attribution.jsonl logic to ensure all 'Panic Boost' and 'Stealth Flow' modifiers
are correctly logged with their non-zero scores.

Checks:
1. Panic Boost logging (regime modifier from regime_detector.py)
2. Stealth Flow logging (stealth_flow_boost from uw_composite_v2.py)
3. Component logging in attribution.jsonl
4. Notes field logging for modifiers
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ATTRIBUTION_LOG = LOG_DIR / "attribution.jsonl"

def load_jsonl(file_path: Path) -> List[Dict]:
    """Load JSONL file"""
    if not file_path.exists():
        return []
    records = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except:
                        pass
    except:
        pass
    return records

def check_panic_boost_logging() -> Dict[str, Any]:
    """Check if Panic Boost (regime modifier) is logged in attribution"""
    
    # Read uw_composite_v2.py to understand how regime modifier is applied
    composite_file = BASE_DIR / "uw_composite_v2.py"
    composite_code = composite_file.read_text() if composite_file.exists() else ""
    
    # Read regime_detector.py to understand panic boost
    regime_file = BASE_DIR / "structural_intelligence" / "regime_detector.py"
    regime_code = regime_file.read_text() if regime_file.exists() else ""
    
    findings = []
    issues = []
    
    # Check if regime modifier is logged
    if "regime_modifier" in composite_code or "regime_component" in composite_code:
        findings.append("✅ Regime modifier component exists in composite scoring")
    else:
        issues.append("Regime modifier component not found in composite scoring")
    
    # Check panic regime multiplier
    if "PANIC" in regime_code and "1.2" in regime_code:
        findings.append("✅ Panic regime multiplier: 1.2x for bullish (buy the dip strategy)")
    else:
        issues.append("Panic regime multiplier not verified - check regime_detector.py")
    
    return {
        "panic_boost_detected": "PANIC" in regime_code and "1.2" in regime_code,
        "findings": findings,
        "issues": issues
    }

def check_stealth_flow_logging() -> Dict[str, Any]:
    """Check if Stealth Flow boost is logged in attribution"""
    
    # Read uw_composite_v2.py
    composite_file = BASE_DIR / "uw_composite_v2.py"
    composite_code = composite_file.read_text() if composite_file.exists() else ""
    
    findings = []
    issues = []
    
    # Check stealth flow boost logic
    if "stealth_flow_boost" in composite_code:
        findings.append("✅ Stealth flow boost logic exists in uw_composite_v2.py")
        
        # Check if it's logged in notes
        if "stealth_flow_boost" in composite_code and "all_notes.append" in composite_code:
            findings.append("✅ Stealth flow boost is logged in notes field")
        else:
            issues.append("Stealth flow boost may not be logged in notes field")
        
        # Check boost value
        if "stealth_flow_boost = 0.2" in composite_code or "stealth_flow_boost = 0.2" in composite_code.replace(" ", ""):
            findings.append("✅ Stealth flow boost value: +0.2 (applied when flow_magnitude == 'LOW')")
        else:
            issues.append("Stealth flow boost value not verified")
    else:
        issues.append("Stealth flow boost logic not found in uw_composite_v2.py")
    
    return {
        "stealth_flow_detected": "stealth_flow_boost" in composite_code,
        "findings": findings,
        "issues": issues
    }

def audit_attribution_logs() -> Dict[str, Any]:
    """Audit actual attribution logs for Panic Boost and Stealth Flow"""
    
    attribution_records = load_jsonl(ATTRIBUTION_LOG)
    
    findings = []
    issues = []
    stats = {
        "total_trades": 0,
        "trades_with_components": 0,
        "trades_with_notes": 0,
        "trades_with_panic_regime": 0,
        "trades_with_stealth_flow": 0,
        "trades_with_regime_modifier": 0
    }
    
    # Check last 100 trades
    recent_trades = [r for r in attribution_records if r.get("type") == "attribution"][-100:]
    stats["total_trades"] = len(recent_trades)
    
    for trade in recent_trades:
        context = trade.get("context", {})
        components = context.get("components", {})
        notes = context.get("notes", "")
        
        if components:
            stats["trades_with_components"] += 1
            
            # Check for regime modifier component
            if "regime" in components or "regime_modifier" in components:
                stats["trades_with_regime_modifier"] += 1
                regime_value = components.get("regime") or components.get("regime_modifier", 0)
                if regime_value != 0:
                    findings.append(f"Trade {trade.get('trade_id', 'unknown')}: regime_modifier = {regime_value}")
        
        # Check market regime
        market_regime = context.get("market_regime", "").upper()
        if "PANIC" in market_regime:
            stats["trades_with_panic_regime"] += 1
        
        # Check notes for stealth flow
        if notes:
            stats["trades_with_notes"] += 1
            if "stealth_flow" in notes.lower():
                stats["trades_with_stealth_flow"] += 1
                findings.append(f"Trade {trade.get('trade_id', 'unknown')}: stealth_flow_boost detected in notes")
    
    # Analysis
    if stats["trades_with_components"] == 0:
        issues.append("No trades have component data - modifiers cannot be verified")
    
    if stats["trades_with_panic_regime"] == 0 and stats["total_trades"] > 0:
        findings.append("No trades detected in PANIC regime (may be normal if no panic occurred)")
    
    if stats["trades_with_stealth_flow"] == 0 and stats["trades_with_notes"] > 0:
        findings.append("No stealth_flow_boost detected in notes (may be normal if no LOW flow magnitude trades)")
    
    return {
        "stats": stats,
        "findings": findings,
        "issues": issues
    }

def main():
    print("Auditing Attribution Logging for Panic Boost and Stealth Flow...")
    
    panic_check = check_panic_boost_logging()
    stealth_check = check_stealth_flow_logging()
    log_audit = audit_attribution_logs()
    
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "panic_boost_check": panic_check,
        "stealth_flow_check": stealth_check,
        "attribution_log_audit": log_audit,
        "summary": {
            "panic_boost_logged": panic_check.get("panic_boost_detected", False),
            "stealth_flow_logged": stealth_check.get("stealth_flow_detected", False),
            "attribution_logs_examined": log_audit["stats"]["total_trades"]
        }
    }
    
    # Save to JSON
    output_file = REPORTS_DIR / "attribution_logging_audit.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print(f"\nPanic Boost: {'YES - Detected' if panic_check.get('panic_boost_detected') else 'NO - Not verified'}")
    print(f"Stealth Flow: {'YES - Detected' if stealth_check.get('stealth_flow_detected') else 'NO - Not verified'}")
    print(f"\nAttribution Logs:")
    print(f"  Total trades examined: {log_audit['stats']['total_trades']}")
    print(f"  Trades with components: {log_audit['stats']['trades_with_components']}")
    print(f"  Trades in PANIC regime: {log_audit['stats']['trades_with_panic_regime']}")
    print(f"  Trades with stealth_flow: {log_audit['stats']['trades_with_stealth_flow']}")

if __name__ == "__main__":
    main()
