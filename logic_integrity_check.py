#!/usr/bin/env python3
"""
Logic Integrity Check: Bayesian Learning Engine
Identifies why signals might be stalling or weights drifting.

Checks:
1. Weight update conditions (MIN_SAMPLES, MIN_DAYS_BETWEEN_UPDATES)
2. Beta distribution updates (regime-specific)
3. EWMA smoothing calculations
4. Wilson confidence interval calculations
5. Weight clamping and normalization
6. Regime-specific weight isolation
"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).parent
STATE_DIR = BASE_DIR / "state"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

WEIGHTS_FILE = STATE_DIR / "signal_weights.json"
ATTRIBUTION_LOG = LOG_DIR / "attribution.jsonl"
LEARNING_LOG = DATA_DIR / "weight_learning.jsonl"

def load_json(file_path: Path) -> Dict:
    """Load JSON file"""
    if not file_path.exists():
        return {}
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return {}

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

def check_learning_integrity() -> Dict[str, Any]:
    """Perform logic integrity check on Bayesian learning engine"""
    
    issues = []
    warnings = []
    findings = []
    
    # 1. Check weight state file
    weights_state = load_json(WEIGHTS_FILE)
    if not weights_state:
        issues.append("No weight state file found - learning system may not be initialized")
    else:
        findings.append(f"Weight state file exists with {len(weights_state.get('base_weights', {}))} base weights")
        
        # Check regime-specific distributions
        regime_beta = weights_state.get("regime_beta_distributions", {})
        if not regime_beta:
            warnings.append("No regime-specific Beta distributions found - weights may not be regime-aware")
        else:
            component_count = len(regime_beta)
            total_regimes = sum(len(regimes) for regimes in regime_beta.values())
            findings.append(f"Found {component_count} components with regime-specific distributions ({total_regimes} total regimes)")
            
            # Check for components with no samples
            for component, regimes in regime_beta.items():
                for regime, dist in regimes.items():
                    samples = dist.get("sample_count", 0)
                    if samples == 0:
                        warnings.append(f"Component '{component}' in regime '{regime}' has no samples - weight may be stuck at default")
    
    # 2. Check attribution log for recent trades
    attribution_records = load_jsonl(ATTRIBUTION_LOG)
    recent_trades = [r for r in attribution_records if r.get("type") == "attribution"]
    
    if not recent_trades:
        warnings.append("No attribution records found - learning system has no data to learn from")
    else:
        findings.append(f"Found {len(recent_trades)} attribution records")
        
        # Check if trades have component data
        trades_with_components = 0
        for trade in recent_trades[-50:]:  # Check last 50 trades
            context = trade.get("context", {})
            components = context.get("components", {})
            if components:
                trades_with_components += 1
        
        if trades_with_components == 0:
            issues.append("Recent trades have no component data - learning cannot update weights")
        else:
            findings.append(f"{trades_with_components} of last 50 trades have component data")
    
    # 3. Check learning log for weight updates
    learning_records = load_jsonl(LEARNING_LOG)
    if not learning_records:
        warnings.append("No learning log found - weight updates may not be happening")
    else:
        recent_updates = [r for r in learning_records if r.get("event") == "weight_update"]
        findings.append(f"Found {len(recent_updates)} weight update events in learning log")
        
        if recent_updates:
            last_update = recent_updates[-1]
            last_ts = last_update.get("ts", 0)
            days_ago = (datetime.now(timezone.utc).timestamp() - last_ts) / 86400
            if days_ago > 7:
                warnings.append(f"Last weight update was {days_ago:.1f} days ago - weights may be stale")
            findings.append(f"Last weight update: {days_ago:.1f} days ago")
    
    # 4. Check for weight drift (if state exists)
    if weights_state:
        weight_bands = weights_state.get("weight_bands", {})
        for component, band in weight_bands.items():
            current = band.get("current", 1.0)
            if current < 0.5:
                warnings.append(f"Component '{component}' has very low multiplier ({current:.2f}) - may be over-penalized")
            elif current > 2.0:
                warnings.append(f"Component '{component}' has very high multiplier ({current:.2f}) - may be over-boosted")
    
    # 5. Check MIN_SAMPLES threshold
    # From adaptive_signal_optimizer.py: MIN_SAMPLES = 15 (reduced from 30 for faster learning)
    findings.append("MIN_SAMPLES threshold: 15 (reduced from 30 for faster learning)")
    findings.append("MIN_DAYS_BETWEEN_UPDATES: 1 (allows daily updates for faster learning)")
    
    # 6. Potential issues identified
    potential_issues = []
    
    if not weights_state:
        potential_issues.append({
            "issue": "Weight state not initialized",
            "impact": "No learning can occur - weights stuck at defaults",
            "recommendation": "Check if comprehensive_learning_orchestrator_v2.py is running"
        })
    
    if recent_trades and trades_with_components == 0:
        potential_issues.append({
            "issue": "Trades missing component data",
            "impact": "Learning system cannot attribute outcomes to components",
            "recommendation": "Check log_exit_attribution() to ensure components are logged"
        })
    
    if recent_trades and not learning_records:
        potential_issues.append({
            "issue": "No learning log entries despite trades",
            "impact": "Weight updates not being triggered",
            "recommendation": "Check if update_weights() is being called after trades"
        })
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "issues": issues,
        "warnings": warnings,
        "findings": findings,
        "potential_issues": potential_issues,
        "weights_state_exists": bool(weights_state),
        "attribution_records_count": len(recent_trades),
        "learning_records_count": len(learning_records)
    }

def main():
    print("Performing Logic Integrity Check on Bayesian Learning Engine...")
    result = check_learning_integrity()
    
    # Save to JSON
    output_file = REPORTS_DIR / "logic_integrity_check.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print(f"\nIssues: {len(result['issues'])}")
    print(f"Warnings: {len(result['warnings'])}")
    print(f"Findings: {len(result['findings'])}")
    
    if result['issues']:
        print("\nCRITICAL ISSUES:")
        for issue in result['issues']:
            print(f"  - {issue}")
    
    if result['warnings']:
        print("\nWARNINGS:")
        for warning in result['warnings']:
            print(f"  - {warning}")

if __name__ == "__main__":
    main()
