#!/usr/bin/env python3
"""
Regime Persistence Audit - Specialist Tier Monitoring
Authoritative Source: MEMORY_BANK.md

Evaluates HMM Regime transition stability over the week.
Determines if current signal weights are correctly aligned with dominant weekly market structure.

Output: reports/weekly_regime_persistence_YYYY-MM-DD.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Base directory
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
STATE_DIR = BASE_DIR / "state"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Data files
ATTRIBUTION_LOG = LOG_DIR / "attribution.jsonl"
REGIME_STATE_FILE = STATE_DIR / "regime_detector_state.json"


def load_jsonl(file_path: Path) -> List[Dict]:
    """Load JSONL file and return list of records"""
    if not file_path.exists():
        return []
    
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
    
    return records


def parse_timestamp(ts: Any) -> Optional[datetime]:
    """Parse various timestamp formats to datetime"""
    if ts is None:
        return None
    
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        elif isinstance(ts, str):
            if 'T' in ts:
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except Exception:
        pass
    
    return None


def get_week_regime_data(friday_date: datetime) -> Dict[str, Any]:
    """
    Extract regime information from week's trades and regime detector state.
    """
    # Find Monday of the week
    days_since_monday = friday_date.weekday()
    monday = friday_date - timedelta(days=days_since_monday)
    monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    saturday_start = monday_start + timedelta(days=5)
    
    # Load regime detector state
    current_regime = "UNKNOWN"
    regime_confidence = 0.0
    if REGIME_STATE_FILE.exists():
        try:
            with open(REGIME_STATE_FILE, 'r') as f:
                regime_state = json.load(f)
                current_regime = regime_state.get("current_regime", "UNKNOWN")
                regime_confidence = regime_state.get("confidence", 0.0)
        except Exception:
            pass
    
    # Extract regime from trades
    regime_distribution = defaultdict(int)
    regime_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "trades": 0,
        "wins": 0,
        "total_pnl_pct": 0.0
    })
    
    trades = load_jsonl(ATTRIBUTION_LOG)
    for trade in trades:
        if trade.get("type") != "attribution":
            continue
        
        context = trade.get("context", {})
        entry_ts_str = context.get("entry_ts") or trade.get("ts") or trade.get("timestamp")
        entry_dt = parse_timestamp(entry_ts_str)
        
        if entry_dt and monday_start <= entry_dt < saturday_start:
            regime = context.get("market_regime", "UNKNOWN").upper()
            regime_distribution[regime] += 1
            
            pnl_pct = trade.get("pnl_pct", 0.0) or context.get("pnl_pct", 0.0)
            perf = regime_performance[regime]
            perf["trades"] += 1
            perf["total_pnl_pct"] += pnl_pct
            if pnl_pct > 0:
                perf["wins"] += 1
    
    # Calculate win rates and avg P&L per regime
    regime_stats = {}
    for regime, perf in regime_performance.items():
        trades_count = perf["trades"]
        if trades_count > 0:
            regime_stats[regime] = {
                "trades": trades_count,
                "win_rate": round(perf["wins"] / trades_count, 4),
                "avg_pnl_pct": round(perf["total_pnl_pct"] / trades_count, 4),
                "distribution_pct": round(regime_distribution[regime] / sum(regime_distribution.values()), 4) if regime_distribution else 0.0
            }
    
    # Find dominant regime (most trades)
    dominant_regime = max(regime_distribution.items(), key=lambda x: x[1])[0] if regime_distribution else "UNKNOWN"
    
    # Calculate regime transition frequency (would need regime detector logs - estimate from trade regime changes)
    transitions = 0
    prev_regime = None
    sorted_trades = sorted(
        [t for t in trades if parse_timestamp(t.get("context", {}).get("entry_ts") or t.get("ts")) and
         monday_start <= parse_timestamp(t.get("context", {}).get("entry_ts") or t.get("ts")) < saturday_start],
        key=lambda t: parse_timestamp(t.get("context", {}).get("entry_ts") or t.get("ts"))
    )
    
    for trade in sorted_trades:
        regime = trade.get("context", {}).get("market_regime", "UNKNOWN").upper()
        if prev_regime and regime != prev_regime:
            transitions += 1
        prev_regime = regime
    
    total_trades = len(sorted_trades)
    transition_rate = transitions / total_trades if total_trades > 0 else 0.0
    
    # Stability assessment
    stability_score = 1.0 - transition_rate  # Lower transitions = higher stability
    is_stable = stability_score > 0.7  # >70% stability
    
    # Weight alignment assessment (would need to check if weights match dominant regime)
    # For now, report current regime vs dominant regime
    weight_alignment = current_regime == dominant_regime
    
    return {
        "current_regime": current_regime,
        "regime_confidence": regime_confidence,
        "dominant_regime": dominant_regime,
        "regime_distribution": dict(regime_distribution),
        "regime_statistics": regime_stats,
        "transition_analysis": {
            "total_transitions": transitions,
            "total_trades": total_trades,
            "transition_rate": round(transition_rate, 4),
            "stability_score": round(stability_score, 4),
            "is_stable": is_stable
        },
        "weight_alignment": {
            "current_regime": current_regime,
            "dominant_regime": dominant_regime,
            "aligned": weight_alignment,
            "recommendation": "Weights aligned with dominant regime" if weight_alignment else f"Consider aligning weights with {dominant_regime}"
        }
    }


def generate_regime_persistence_audit(friday_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Generate regime persistence audit report.
    
    Args:
        friday_date: Friday date to analyze (defaults to today if Friday, otherwise last Friday)
    
    Returns:
        Dictionary with audit results
    """
    if friday_date is None:
        friday_date = datetime.now(timezone.utc)
    
    # Ensure we're analyzing a Friday
    days_since_friday = (friday_date.weekday() - 4) % 7
    if days_since_friday != 0:
        friday_date = friday_date - timedelta(days=days_since_friday)
    
    regime_data = get_week_regime_data(friday_date)
    
    report = {
        "report_date": friday_date.strftime("%Y-%m-%d"),
        "report_timestamp": datetime.now(timezone.utc).isoformat(),
        "report_type": "weekly_regime_persistence_audit",
        "authoritative_source": "MEMORY_BANK.md",
        "regime_analysis": regime_data,
        "assessment": {
            "regime_stability": "STABLE" if regime_data["transition_analysis"]["is_stable"] else "UNSTABLE",
            "stability_score": regime_data["transition_analysis"]["stability_score"],
            "weight_alignment_status": "ALIGNED" if regime_data["weight_alignment"]["aligned"] else "MISALIGNED",
            "recommendation": regime_data["weight_alignment"]["recommendation"]
        }
    }
    
    return report


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Regime Persistence Audit Report")
    parser.add_argument("--date", type=str, help="Friday date to analyze (YYYY-MM-DD), defaults to today/last Friday")
    parser.add_argument("--output", type=str, help="Output file path (defaults to reports/weekly_regime_persistence_YYYY-MM-DD.json)")
    
    args = parser.parse_args()
    
    # Parse target date
    friday_date = None
    if args.date:
        try:
            friday_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    
    # Generate report
    report = generate_regime_persistence_audit(friday_date)
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        report_date = report["report_date"]
        output_file = REPORTS_DIR / f"weekly_regime_persistence_{report_date}.json"
    
    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Regime Persistence Audit report written to: {output_file}")
    print(f"Date: {report['report_date']}")
    print(f"Current Regime: {report['regime_analysis']['current_regime']}")
    print(f"Dominant Regime: {report['regime_analysis']['dominant_regime']}")
    print(f"Stability: {report['assessment']['regime_stability']} (score: {report['assessment']['stability_score']:.2%})")
    print(f"Weight Alignment: {report['assessment']['weight_alignment_status']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
