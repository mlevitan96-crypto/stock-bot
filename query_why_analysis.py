#!/usr/bin/env python3
"""
Query WHY Analysis - Interactive tool to answer "why did X lose/win?"

Usage:
    python3 query_why_analysis.py --component options_flow --question why_underperforming
    python3 query_why_analysis.py --component dark_pool --question when_works_best
    python3 query_why_analysis.py --all
"""

import argparse
import json
from pathlib import Path
from causal_analysis_engine import CausalAnalysisEngine

def main():
    parser = argparse.ArgumentParser(description="Query WHY signals win or lose")
    parser.add_argument("--component", help="Component to analyze (e.g., options_flow, dark_pool)")
    parser.add_argument("--question", choices=["why_underperforming", "when_works_best", "what_conditions_fail"], 
                       default="why_underperforming", help="Question to answer")
    parser.add_argument("--all", action="store_true", help="Analyze all components")
    parser.add_argument("--process", action="store_true", help="Process all trades first")
    
    args = parser.parse_args()
    
    engine = CausalAnalysisEngine()
    
    if args.process:
        print("Processing all historical trades...")
        result = engine.process_all_trades()
        print(f"Processed: {result.get('processed', 0)} trades")
        engine._save_state()
    
    if args.all:
        from adaptive_signal_optimizer import SIGNAL_COMPONENTS
        print("\n" + "="*80)
        print("COMPREHENSIVE WHY ANALYSIS - ALL COMPONENTS")
        print("="*80)
        
        for component in SIGNAL_COMPONENTS[:10]:  # Top 10
            print(f"\n{'='*80}")
            print(f"COMPONENT: {component.upper()}")
            print("="*80)
            
            # Why underperforming?
            why = engine.answer_why(component, "why_underperforming")
            if "answer" in why:
                print(f"\nWHY UNDERPERFORMING:")
                print(why["answer"])
            
            # When works best?
            when = engine.answer_why(component, "when_works_best")
            if "answer" in when:
                print(f"\nWHEN WORKS BEST:")
                print(when["answer"])
    
    elif args.component:
        print("\n" + "="*80)
        print(f"WHY ANALYSIS: {args.component.upper()}")
        print("="*80)
        
        answer = engine.answer_why(args.component, args.question)
        
        if "error" in answer:
            print(f"ERROR: {answer['error']}")
        elif "answer" in answer:
            print(f"\n{answer['answer']}")
            if "recommendation" in answer:
                print(f"\nRECOMMENDATION: {answer['recommendation']}")
        else:
            print(json.dumps(answer, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
