#!/usr/bin/env python3
"""
Generate Missing Shadow Artifacts
=================================
Generates the 4 missing shadow artifacts that aren't created by telemetry extraction:
- entry_parity_details.json
- feature_family_summary.json
- live_vs_shadow_pnl.json
- shadow_vs_live_parity.json
"""

import sys
import json
from pathlib import Path

# Inline script to run on droplet (use TELEMETRY_DATE=YYYY-MM-DD to target a specific bundle)
GENERATE_SCRIPT = '''python3 << 'GENERATE_EOF'
import json
import os
import time
from pathlib import Path
from datetime import datetime, timezone

def generate_missing_artifacts():
    """Generate missing shadow artifacts"""
    today = os.environ.get("TELEMETRY_DATE") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    telemetry_dir = Path(f"telemetry/{today}/computed")
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "artifacts_generated": {},
        "issues": []
    }
    
    # 1. entry_parity_details.json - Entry score parity between shadow and live
    try:
        # This would compare entry scores between shadow and live trades
        # For now, create a placeholder structure
        entry_parity = {
            "as_of_ts": datetime.now(timezone.utc).isoformat(),
            "date": today,
            "parity_available": False,
            "note": "Entry parity requires shadow trading data comparison",
            "classification_counts": {},
            "mean_entry_ts_delta_seconds": None,
            "mean_score_delta": None,
            "mean_price_delta_usd": None
        }
        
        entry_parity_path = telemetry_dir / "entry_parity_details.json"
        with open(entry_parity_path, 'w') as f:
            json.dump(entry_parity, f, indent=2)
        results["artifacts_generated"]["entry_parity_details"] = True
    except Exception as e:
        results["artifacts_generated"]["entry_parity_details"] = False
        results["issues"].append(f"entry_parity_details: {str(e)}")
    
    # 2. feature_family_summary.json - Summary of feature families
    try:
        # Generate from signal performance if available
        signal_perf_path = telemetry_dir / "signal_performance.json"
        feature_family_summary = {
            "as_of_ts": datetime.now(timezone.utc).isoformat(),
            "date": today,
            "families": {}
        }
        
        if signal_perf_path.exists():
            try:
                with open(signal_perf_path, 'r') as f:
                    signal_perf = json.load(f)
                
                # Extract feature families from signal performance
                signals = signal_perf.get("signals", [])
                for sig in signals:
                    name = sig.get("name", "unknown")
                    feature_family_summary["families"][name] = {
                        "trade_count": sig.get("trade_count", 0),
                        "win_rate": sig.get("win_rate", 0.0),
                        "expectancy_usd": sig.get("expectancy_usd", 0.0),
                        "contribution_to_total_pnl": sig.get("contribution_to_total_pnl", 0.0)
                    }
            except:
                pass
        
        feature_family_path = telemetry_dir / "feature_family_summary.json"
        with open(feature_family_path, 'w') as f:
            json.dump(feature_family_summary, f, indent=2)
        results["artifacts_generated"]["feature_family_summary"] = True
    except Exception as e:
        results["artifacts_generated"]["feature_family_summary"] = False
        results["issues"].append(f"feature_family_summary: {str(e)}")
    
    # 3. live_vs_shadow_pnl.json - PnL comparison between live and shadow
    # Dashboard expects windows["24h"].delta.pnl_usd, per_symbol[{symbol,window,live_pnl_usd,shadow_pnl_usd,delta_pnl_usd,...}]
    try:
        live_vs_shadow = {
            "as_of_ts": datetime.now(timezone.utc).isoformat(),
            "date": today,
            "comparison_available": False,
            "note": "Live vs shadow PnL comparison requires shadow trading data",
            "windows": {
                "24h": {"delta": {"pnl_usd": 0.0}, "pnl_usd": 0.0, "trade_count": 0},
                "48h": {"delta": {"pnl_usd": 0.0}, "pnl_usd": 0.0, "trade_count": 0},
                "5d": {"delta": {"pnl_usd": 0.0}, "pnl_usd": 0.0, "trade_count": 0},
            },
            "per_symbol": [],
        }
        
        # Optional: merge from pnl_windows.json (full extract) for live-only stats; delta remains 0 without shadow
        try:
            pnl_path = telemetry_dir / "pnl_windows.json"
            if pnl_path.exists():
                pnl_w = json.loads(pnl_path.read_text())
                w = pnl_w.get("windows") or {}
                for k in ("24h", "48h", "5d"):
                    if k in w and isinstance(w[k], dict):
                        pnl = float(w[k].get("pnl_usd") or 0.0)
                        live_vs_shadow["windows"][k]["pnl_usd"] = pnl
                        live_vs_shadow["windows"][k]["trade_count"] = int(w[k].get("trade_count") or 0)
                rows = pnl_w.get("per_symbol") or []
                for r in rows:
                    if isinstance(r, dict) and r.get("symbol"):
                        live_vs_shadow["per_symbol"].append({
                            "symbol": str(r["symbol"]),
                            "window": str(r.get("window") or "24h"),
                            "live_pnl_usd": float(r.get("pnl_usd") or 0.0),
                            "shadow_pnl_usd": 0.0,
                            "delta_pnl_usd": 0.0,
                            "live_trade_count": int(r.get("trade_count") or 0),
                            "shadow_trade_count": 0,
                        })
        except Exception:
            pass
        
        # Fallback: live totals from master_trade_log (today only)
        if not live_vs_shadow["per_symbol"]:
            try:
                master_log = Path("logs/master_trade_log.jsonl")
                if master_log.exists():
                    live_pnl = 0.0
                    live_count = 0
                    with open(master_log, 'r') as f:
                        for line in f:
                            try:
                                trade = json.loads(line)
                                ts = trade.get("entry_ts") or trade.get("ts") or trade.get("timestamp")
                                if ts and str(ts).startswith(today):
                                    pnl = float(trade.get("pnl_usd") or trade.get("realized_pnl_usd") or trade.get("final_pnl_usd") or 0.0)
                                    live_pnl += pnl
                                    live_count += 1
                            except Exception:
                                continue
                    for k in ("24h", "48h", "5d"):
                        live_vs_shadow["windows"][k]["pnl_usd"] = live_pnl
                        live_vs_shadow["windows"][k]["trade_count"] = live_count
            except Exception:
                pass
        
        live_vs_shadow_path = telemetry_dir / "live_vs_shadow_pnl.json"
        with open(live_vs_shadow_path, 'w') as f:
            json.dump(live_vs_shadow, f, indent=2)
        results["artifacts_generated"]["live_vs_shadow_pnl"] = True
    except Exception as e:
        results["artifacts_generated"]["live_vs_shadow_pnl"] = False
        results["issues"].append(f"live_vs_shadow_pnl: {str(e)}")
    
    # 4. shadow_vs_live_parity.json - Overall parity between shadow and live
    try:
        # This is the main parity artifact
        shadow_parity = {
            "as_of_ts": datetime.now(timezone.utc).isoformat(),
            "date": today,
            "parity_available": False,
            "note": "Shadow vs live parity requires shadow trading data",
            "aggregate_metrics": {
                "match_rate": None,
                "mean_entry_ts_delta_seconds": None,
                "mean_score_delta": None,
                "mean_price_delta_usd": None
            },
            "entry_parity": {
                "classification_counts": {}
            },
            "notes": {
                "parity_available": False
            }
        }
        
        shadow_parity_path = telemetry_dir / "shadow_vs_live_parity.json"
        with open(shadow_parity_path, 'w') as f:
            json.dump(shadow_parity, f, indent=2)
        results["artifacts_generated"]["shadow_vs_live_parity"] = True
    except Exception as e:
        results["artifacts_generated"]["shadow_vs_live_parity"] = False
        results["issues"].append(f"shadow_vs_live_parity: {str(e)}")
    
    return results

results = generate_missing_artifacts()
print(json.dumps(results, indent=2))
GENERATE_EOF
'''

def main():
    """Generate missing shadow artifacts on droplet. Use --date YYYY-MM-DD to target a bundle (default: today on droplet)."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate missing shadow artifacts on droplet")
    parser.add_argument("--date", default=None, help="Telemetry bundle date (YYYY-MM-DD). Default: today on droplet.")
    args = parser.parse_args()
    
    print("=" * 80)
    print("GENERATING MISSING SHADOW ARTIFACTS ON DROPLET")
    print("=" * 80)
    if args.date:
        print(f"Target date: {args.date}")
    print()
    
    try:
        from droplet_client import DropletClient
        
        client = DropletClient()
        
        print("Connecting to droplet...")
        print("Generating missing artifacts...")
        print()
        
        script = f"export TELEMETRY_DATE={args.date} && " + GENERATE_SCRIPT if args.date else GENERATE_SCRIPT
        stdout, stderr, exit_code = client._execute_with_cd(script, timeout=60)
        
        print("=" * 80)
        print("GENERATION OUTPUT")
        print("=" * 80)
        print(stdout)
        if stderr:
            print("\nSTDERR:")
            print(stderr)
        
        # Parse results
        if stdout:
            try:
                lines = stdout.split('\n')
                json_start = None
                for i, line in enumerate(lines):
                    if line.strip().startswith('{'):
                        json_start = i
                        break
                
                if json_start is not None:
                    json_text = '\n'.join(lines[json_start:])
                    results = json.loads(json_text)
                    
                    print("\n" + "=" * 80)
                    print("GENERATION SUMMARY")
                    print("=" * 80)
                    
                    artifacts = results.get("artifacts_generated", {})
                    print(f"Artifacts Generated: {sum(1 for v in artifacts.values() if v)}/4")
                    for name, success in artifacts.items():
                        status = "SUCCESS" if success else "FAILED"
                        print(f"  {name}: {status}")
                    
                    if results.get("issues"):
                        print(f"\nIssues: {len(results['issues'])}")
                        for issue in results["issues"]:
                            print(f"  - {issue}")
                    else:
                        print("\n[SUCCESS] All artifacts generated")
                    
                    # Save results
                    local_path = Path("reports/shadow_artifacts_generation_results.json")
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(local_path, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"\nResults saved to: {local_path}")
                    
            except json.JSONDecodeError as e:
                print(f"\nCould not parse JSON: {e}")
        
        client.close()
        return exit_code
        
    except ImportError:
        print("ERROR: droplet_client not available")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
