#!/usr/bin/env python3
"""
Score Pipeline Diagnostic Tool
===============================
Traces a signal through the complete pipeline and identifies where scores are lost.

Usage:
    python3 diagnose_score_pipeline.py --symbol AAPL
    python3 diagnose_score_pipeline.py --symbol all
    python3 diagnose_score_pipeline.py --trace-full
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.registry import CacheFiles, read_json


class ScorePipelineDiagnostic:
    """Diagnostic tool for tracing signal → score pipeline."""
    
    def __init__(self):
        self.results = []
        
    def trace_symbol(self, symbol: str) -> Dict:
        """Trace a single symbol through the pipeline."""
        print(f"\n{'='*60}")
        print(f"TRACING SYMBOL: {symbol}")
        print(f"{'='*60}\n")
        
        trace = {
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stages": {}
        }
        
        # Stage 1: Raw cache data
        print("Stage 1: Raw Cache Data")
        print("-" * 60)
        cache_data = self._get_cache_data(symbol)
        trace["stages"]["raw_cache"] = {
            "exists": cache_data is not None,
            "keys": list(cache_data.keys()) if cache_data else [],
            "sentiment": cache_data.get("sentiment") if cache_data else None,
            "conviction": cache_data.get("conviction") if cache_data else None,
            "dark_pool": bool(cache_data.get("dark_pool")) if cache_data else False,
            "insider": bool(cache_data.get("insider")) if cache_data else False,
            "iv_term_skew": cache_data.get("iv_term_skew") if cache_data else None,
            "smile_slope": cache_data.get("smile_slope") if cache_data else None,
            "freshness": cache_data.get("freshness") if cache_data else None,
            "last_update": cache_data.get("_last_update") if cache_data else None
        }
        self._print_stage(trace["stages"]["raw_cache"])
        
        # Stage 2: Enriched data
        print("\nStage 2: Enriched Data")
        print("-" * 60)
        enriched_data = self._get_enriched_data(symbol, cache_data)
        trace["stages"]["enriched"] = {
            "exists": enriched_data is not None,
            "keys": list(enriched_data.keys()) if enriched_data else [],
            "sentiment": enriched_data.get("sentiment") if enriched_data else None,
            "conviction": enriched_data.get("conviction") if enriched_data else None,
            "iv_term_skew": enriched_data.get("iv_term_skew") if enriched_data else None,
            "smile_slope": enriched_data.get("smile_slope") if enriched_data else None,
            "event_alignment": enriched_data.get("event_alignment") if enriched_data else None,
            "toxicity": enriched_data.get("toxicity") if enriched_data else None,
            "freshness": enriched_data.get("freshness") if enriched_data else None,
            "missing_features": self._check_missing_features(enriched_data)
        }
        self._print_stage(trace["stages"]["enriched"])
        
        # Stage 3: Composite score calculation
        print("\nStage 3: Composite Score Calculation")
        print("-" * 60)
        composite_result = self._calculate_composite(symbol, enriched_data)
        trace["stages"]["composite"] = composite_result
        self._print_stage(composite_result)
        
        # Stage 4: Component breakdown
        print("\nStage 4: Component Breakdown")
        print("-" * 60)
        components = composite_result.get("components", {}) if composite_result else {}
        trace["stages"]["components"] = {
            "total_components": len(components),
            "zero_components": [k for k, v in components.items() if v == 0.0],
            "non_zero_components": {k: v for k, v in components.items() if v != 0.0},
            "component_sum": sum(components.values()) if components else 0.0,
            "freshness_factor": composite_result.get("components", {}).get("freshness_factor") if composite_result else None,
            "final_score": composite_result.get("score") if composite_result else None
        }
        self._print_component_breakdown(trace["stages"]["components"])
        
        # Stage 5: Score adjustments
        print("\nStage 5: Score Adjustments")
        print("-" * 60)
        adjustments = self._check_adjustments(composite_result)
        trace["stages"]["adjustments"] = adjustments
        self._print_stage(adjustments)
        
        # Stage 6: Gate check
        print("\nStage 6: Gate Check")
        print("-" * 60)
        gate_result = self._check_gate(composite_result)
        trace["stages"]["gate"] = gate_result
        self._print_stage(gate_result)
        
        # Summary
        print("\n" + "="*60)
        print("DIAGNOSIS SUMMARY")
        print("="*60)
        diagnosis = self._diagnose_issues(trace)
        trace["diagnosis"] = diagnosis
        self._print_diagnosis(diagnosis)
        
        self.results.append(trace)
        return trace
    
    def _get_cache_data(self, symbol: str) -> Optional[Dict]:
        """Get raw cache data for symbol."""
        try:
            cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})
            return cache.get(symbol)
        except Exception as e:
            print(f"ERROR: Failed to load cache: {e}")
            return None
    
    def _get_enriched_data(self, symbol: str, cache_data: Optional[Dict]) -> Optional[Dict]:
        """Get enriched data for symbol."""
        try:
            import uw_enrichment_v2 as uw_enrich
            if cache_data is None:
                cache_data = self._get_cache_data(symbol)
            if cache_data:
                enriched = uw_enrich.enrich_signal(symbol, {symbol: cache_data}, "mixed")
                return enriched
        except Exception as e:
            print(f"ERROR: Failed to enrich signal: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def _calculate_composite(self, symbol: str, enriched_data: Optional[Dict]) -> Optional[Dict]:
        """Calculate composite score."""
        try:
            import uw_composite_v2 as uw_v2
            if enriched_data is None:
                enriched_data = self._get_enriched_data(symbol, None)
            if enriched_data:
                composite = uw_v2.compute_composite_score_v3(symbol, enriched_data, "mixed")
                return composite
        except Exception as e:
            print(f"ERROR: Failed to calculate composite: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def _check_missing_features(self, enriched_data: Optional[Dict]) -> List[str]:
        """Check which features are missing."""
        if not enriched_data:
            return ["ALL"]
        
        required = ["iv_term_skew", "smile_slope", "event_alignment", "toxicity", "freshness"]
        missing = [f for f in required if enriched_data.get(f) is None or enriched_data.get(f) == 0.0]
        return missing
    
    def _check_adjustments(self, composite_result: Optional[Dict]) -> Dict:
        """Check what adjustments were applied to score."""
        if not composite_result:
            return {"error": "No composite result"}
        
        adjustments = {
            "whale_conviction_boost": composite_result.get("whale_conviction_boost", 0.0),
            "persistence_boost": composite_result.get("persistence_boost", 0.0),
            "sector_tide_boost": composite_result.get("sector_tide_boost", 0.0),
            "alpha_signature_boost": composite_result.get("alpha_signature_boost", 0.0),
            "cross_asset_adjustment": composite_result.get("cross_asset_adjustment", 0.0),
            "total_adjustments": 0.0
        }
        
        adjustments["total_adjustments"] = sum([
            adjustments["whale_conviction_boost"],
            adjustments["persistence_boost"],
            adjustments["sector_tide_boost"],
            adjustments["alpha_signature_boost"],
            adjustments["cross_asset_adjustment"]
        ])
        
        return adjustments
    
    def _check_gate(self, composite_result: Optional[Dict]) -> Dict:
        """Check gate conditions."""
        if not composite_result:
            return {"error": "No composite result"}
        
        try:
            import uw_composite_v2 as uw_v2
            score = composite_result.get("score", 0.0)
            threshold = uw_v2.get_threshold(composite_result.get("symbol", ""), "base")
            freshness = composite_result.get("freshness", 1.0)
            toxicity = composite_result.get("toxicity", 0.0)
            
            gate_result = uw_v2.should_enter_v2(composite_result, composite_result.get("symbol", ""), "base")
            
            return {
                "score": score,
                "threshold": threshold,
                "score_meets_threshold": score >= threshold,
                "freshness": freshness,
                "freshness_meets_minimum": freshness >= 0.30,
                "toxicity": toxicity,
                "toxicity_below_maximum": toxicity < 0.90,
                "gate_passed": gate_result,
                "rejection_reasons": self._get_rejection_reasons(score, threshold, freshness, toxicity, gate_result)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_rejection_reasons(self, score: float, threshold: float, freshness: float, toxicity: float, gate_passed: bool) -> List[str]:
        """Get reasons why gate failed."""
        reasons = []
        if not gate_passed:
            if score < threshold:
                reasons.append(f"score_too_low ({score:.2f} < {threshold:.2f})")
            if freshness < 0.30:
                reasons.append(f"freshness_too_low ({freshness:.3f} < 0.30)")
            if toxicity >= 0.90:
                reasons.append(f"toxicity_too_high ({toxicity:.3f} >= 0.90)")
        return reasons
    
    def _diagnose_issues(self, trace: Dict) -> Dict:
        """Diagnose issues from trace."""
        issues = []
        recommendations = []
        
        # Check cache data
        raw_cache = trace["stages"].get("raw_cache", {})
        if not raw_cache.get("exists"):
            issues.append("CRITICAL: No cache data for symbol")
            recommendations.append("Check if uw_flow_daemon is running and has polled this symbol")
        else:
            if raw_cache.get("conviction") is None or raw_cache.get("conviction") == 0.0:
                issues.append("HIGH: Flow conviction missing or zero")
                recommendations.append("Default conviction to 0.5 instead of 0.0")
            
            if not raw_cache.get("dark_pool"):
                issues.append("MEDIUM: Dark pool data missing")
            
            if not raw_cache.get("insider"):
                issues.append("MEDIUM: Insider data missing")
            
            if raw_cache.get("iv_term_skew") is None:
                issues.append("HIGH: IV term skew missing")
                recommendations.append("Ensure enrichment computes iv_term_skew")
            
            if raw_cache.get("smile_slope") is None:
                issues.append("HIGH: Smile slope missing")
                recommendations.append("Ensure enrichment computes smile_slope")
        
        # Check enriched data
        enriched = trace["stages"].get("enriched", {})
        missing_features = enriched.get("missing_features", [])
        if missing_features:
            issues.append(f"HIGH: Missing features: {', '.join(missing_features)}")
            recommendations.append("Ensure all features are computed during enrichment")
        
        freshness = enriched.get("freshness")
        if freshness and freshness < 0.5:
            issues.append(f"CRITICAL: Freshness too low ({freshness:.3f})")
            recommendations.append("Increase decay_min from 45 to 180 minutes, or adjust freshness calculation")
        
        # Check composite score
        composite = trace["stages"].get("composite", {})
        if not composite:
            issues.append("CRITICAL: Composite score calculation failed")
            recommendations.append("Check composite scoring function for errors")
        else:
            score = composite.get("score", 0.0)
            if score == 0.0:
                issues.append("CRITICAL: Composite score is zero")
                recommendations.append("Check component calculations - all may be returning 0.0")
            elif score < 1.0:
                issues.append("HIGH: Composite score very low")
                recommendations.append("Check which components are contributing 0.0")
            elif score < 2.0:
                issues.append("MEDIUM: Composite score below threshold")
                recommendations.append("Check if missing data is causing low scores")
        
        # Check components
        components = trace["stages"].get("components", {})
        zero_components = components.get("zero_components", [])
        if len(zero_components) > 10:
            issues.append(f"HIGH: {len(zero_components)} components are zero")
            recommendations.append("Check if expanded intel data is missing")
        
        component_sum = components.get("component_sum", 0.0)
        final_score = components.get("final_score", 0.0)
        if component_sum > 0 and final_score < component_sum * 0.5:
            issues.append("CRITICAL: Final score much lower than component sum (freshness decay?)")
            recommendations.append("Check freshness factor - may be too aggressive")
        
        # Check gate
        gate = trace["stages"].get("gate", {})
        if not gate.get("gate_passed", False):
            rejection_reasons = gate.get("rejection_reasons", [])
            if rejection_reasons:
                issues.append(f"MEDIUM: Gate failed: {', '.join(rejection_reasons)}")
        
        return {
            "issues": issues,
            "recommendations": recommendations,
            "severity": "CRITICAL" if any("CRITICAL" in i for i in issues) else "HIGH" if any("HIGH" in i for i in issues) else "MEDIUM"
        }
    
    def _print_stage(self, stage_data: Dict):
        """Print stage data."""
        for key, value in stage_data.items():
            if isinstance(value, (dict, list)):
                print(f"  {key}:")
                if isinstance(value, dict):
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    for item in value:
                        print(f"    - {item}")
            else:
                print(f"  {key}: {value}")
    
    def _print_component_breakdown(self, components: Dict):
        """Print component breakdown."""
        print(f"  Total components: {components.get('total_components', 0)}")
        print(f"  Zero components: {len(components.get('zero_components', []))}")
        print(f"  Component sum: {components.get('component_sum', 0.0):.3f}")
        print(f"  Freshness factor: {components.get('freshness_factor', 1.0):.3f}")
        print(f"  Final score: {components.get('final_score', 0.0):.3f}")
        
        if components.get('zero_components'):
            print(f"\n  Zero components: {', '.join(components['zero_components'])}")
        
        if components.get('non_zero_components'):
            print(f"\n  Non-zero components:")
            for k, v in sorted(components['non_zero_components'].items(), key=lambda x: abs(x[1]), reverse=True):
                print(f"    {k}: {v:.3f}")
    
    def _print_diagnosis(self, diagnosis: Dict):
        """Print diagnosis."""
        print(f"Severity: {diagnosis.get('severity', 'UNKNOWN')}")
        print(f"\nIssues Found: {len(diagnosis.get('issues', []))}")
        for issue in diagnosis.get('issues', []):
            print(f"  - {issue}")
        
        print(f"\nRecommendations: {len(diagnosis.get('recommendations', []))}")
        for rec in diagnosis.get('recommendations', []):
            print(f"  - {rec}")
    
    def generate_report(self) -> Path:
        """Generate diagnostic report."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_file = Path("diagnostic_score_pipeline_report.json")
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "traces": self.results,
            "summary": {
                "total_symbols": len(self.results),
                "symbols_with_zero_scores": sum(1 for r in self.results if r["stages"].get("composite", {}).get("score", 0.0) == 0.0),
                "symbols_below_threshold": sum(1 for r in self.results if r["stages"].get("gate", {}).get("score", 0.0) < r["stages"].get("gate", {}).get("threshold", 2.7))
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Report saved: {report_file}")
        print(f"{'='*60}\n")
        
        return report_file


def main():
    parser = argparse.ArgumentParser(description="Diagnose score pipeline")
    parser.add_argument("--symbol", type=str, default="AAPL", help="Symbol to trace (or 'all' for all symbols in cache)")
    parser.add_argument("--trace-full", action="store_true", help="Trace full pipeline with detailed output")
    
    args = parser.parse_args()
    
    diagnostic = ScorePipelineDiagnostic()
    
    if args.symbol.lower() == "all":
        # Get all symbols from cache
        try:
            cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})
            symbols = [k for k in cache.keys() if not k.startswith("_")][:10]  # Limit to 10 for testing
            print(f"Tracing {len(symbols)} symbols: {', '.join(symbols)}")
            for symbol in symbols:
                diagnostic.trace_symbol(symbol)
        except Exception as e:
            print(f"ERROR: Failed to load cache: {e}")
            sys.exit(1)
    else:
        diagnostic.trace_symbol(args.symbol.upper())
    
    # Generate report
    report_file = diagnostic.generate_report()
    
    print(f"\nDiagnostic complete. Report: {report_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
