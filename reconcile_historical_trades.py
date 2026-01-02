#!/usr/bin/env python3
"""
Full Week Data Reconciliation
Searches entire project for trade records and merges them into standardized attribution.jsonl
Authoritative Source: MEMORY_BANK.md
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict

BASE_DIR = Path(__file__).parent

# CRITICAL: Use standardized path from config/registry.py
try:
    from config.registry import LogFiles
    TARGET_ATTRIBUTION_LOG = LogFiles.ATTRIBUTION
except ImportError:
    TARGET_ATTRIBUTION_LOG = BASE_DIR / "logs" / "attribution.jsonl"

# Search directories
SEARCH_DIRS = [BASE_DIR / "logs", BASE_DIR / "data", BASE_DIR / "state", BASE_DIR / "reports"]
SEARCH_PATTERNS = ["*.jsonl", "*.json"]


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


def extract_field(record: Dict, field_name: str, default: Any = None) -> Any:
    """Extract field supporting both flat and nested schemas"""
    # Try top level first (flat schema)
    if field_name in record:
        value = record[field_name]
        if value is not None and value != "":
            return value
    
    # Try context dict (nested schema)
    context = record.get("context", {})
    if isinstance(context, dict) and field_name in context:
        value = context[field_name]
        if value is not None and value != "":
            return value
    
    return default


def normalize_attribution_record(record: Dict, source_file: Path) -> Optional[Dict]:
    """
    Normalize a trade record to the mandatory flat schema.
    Supports multiple input formats.
    """
    # Skip if not a trade/attribution record
    record_type = record.get("type", "").lower()
    
    # Handle different record types
    if record_type == "attribution":
        # Already attribution format - normalize schema
        pass
    elif record_type == "trade_exit":
        # Explainable logs format - convert to attribution
        pass
    elif "pnl_pct" in record or "pnl_usd" in record or extract_field(record, "symbol"):
        # Might be a trade record - check for required fields
        pass
    else:
        # Not a trade record
        return None
    
    # Extract required fields
    symbol = extract_field(record, "symbol")
    if not symbol:
        return None
    
    # Skip test symbols
    if "TEST" in str(symbol).upper():
        return None
    
    # Extract timestamp
    ts_str = record.get("ts") or record.get("timestamp") or record.get("_ts")
    entry_ts_str = extract_field(record, "entry_ts") or extract_field(record, "entry_timestamp")
    
    if not ts_str and not entry_ts_str:
        # Try to infer from timestamp in trade_id
        trade_id = record.get("trade_id", "")
        if trade_id and "T" in trade_id:
            try:
                # Extract timestamp from trade_id like "close_AAPL_2026-01-02T21:30:00Z"
                parts = trade_id.split("_")
                for part in parts:
                    if "T" in part and "-" in part:
                        ts_str = part
                        break
            except:
                pass
    
    ts = parse_timestamp(ts_str) or parse_timestamp(entry_ts_str)
    if not ts:
        return None
    
    # Only include records from past 7 days
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    if ts < week_ago:
        return None
    
    # Extract P&L data
    pnl_usd = float(record.get("pnl_usd", 0.0) or extract_field(record, "pnl_usd", 0.0))
    pnl_pct = float(record.get("pnl_pct", 0.0) or extract_field(record, "pnl_pct", 0.0) or 
                    extract_field(record, "exit_pnl", 0.0))
    
    # Extract entry_score (CRITICAL - required field)
    entry_score = extract_field(record, "entry_score")
    if entry_score is None:
        # Try to extract from components or score
        entry_score = record.get("score") or record.get("composite_score") or extract_field(record, "score")
    
    # Extract market_regime
    market_regime = extract_field(record, "market_regime", "unknown")
    if market_regime == "unknown":
        # Try regime field
        market_regime = extract_field(record, "regime", "unknown")
    
    # Extract stealth_boost_applied
    stealth_boost_applied = extract_field(record, "stealth_boost_applied", False)
    if not stealth_boost_applied:
        # Check flow_magnitude
        flow_magnitude = extract_field(record, "flow_magnitude", "")
        if flow_magnitude == "LOW":
            stealth_boost_applied = True
        else:
            # Check components for low flow conviction
            context = record.get("context", {})
            if isinstance(context, dict):
                components = context.get("components", {})
                if isinstance(components, dict):
                    flow_comp = components.get("flow") or components.get("options_flow")
                    if isinstance(flow_comp, dict):
                        flow_conv = flow_comp.get("conviction", 1.0)
                    elif isinstance(flow_comp, (int, float)):
                        flow_conv = float(flow_comp)
                    else:
                        flow_conv = 1.0
                    
                    if flow_conv < 0.3:
                        stealth_boost_applied = True
    
    # Extract other fields
    hold_minutes = float(extract_field(record, "hold_minutes", 0.0) or 
                        record.get("hold_minutes", 0.0) or 0.0)
    entry_price = float(extract_field(record, "entry_price", 0.0) or 0.0)
    exit_price = float(extract_field(record, "exit_price", 0.0) or 0.0)
    close_reason = extract_field(record, "close_reason", "unknown")
    side = extract_field(record, "side", "buy")
    qty = int(extract_field(record, "qty", 1) or 1)
    direction = extract_field(record, "direction", "unknown")
    
    # Extract components
    components = extract_field(record, "components", {})
    if not components:
        context = record.get("context", {})
        if isinstance(context, dict):
            components = context.get("components", {})
    
    # Build normalized attribution record with mandatory flat schema
    normalized = {
        "type": "attribution",
        "ts": ts.isoformat(),
        "trade_id": record.get("trade_id") or f"close_{symbol}_{ts.isoformat().replace(':', '-')}",
        # MANDATORY FLAT FIELDS
        "symbol": str(symbol).upper(),
        "entry_score": float(entry_score) if entry_score is not None else 0.0,
        "exit_pnl": round(pnl_pct, 4),
        "market_regime": str(market_regime).upper() if market_regime != "unknown" else "unknown",
        "stealth_boost_applied": bool(stealth_boost_applied),
        # Additional fields
        "pnl_usd": round(pnl_usd, 2),
        "pnl_pct": round(pnl_pct, 4),
        "hold_minutes": round(hold_minutes, 1),
        # Full context preserved for backward compatibility
        "context": {
            "close_reason": close_reason,
            "entry_price": round(entry_price, 4) if entry_price > 0 else None,
            "exit_price": round(exit_price, 4) if exit_price > 0 else None,
            "pnl_pct": round(pnl_pct, 4),
            "hold_minutes": round(hold_minutes, 1),
            "side": side,
            "qty": qty,
            "entry_score": float(entry_score) if entry_score is not None else 0.0,
            "components": components if isinstance(components, dict) else {},
            "market_regime": str(market_regime).upper() if market_regime != "unknown" else "unknown",
            "direction": direction,
            "entry_ts": ts.isoformat(),
            "flow_magnitude": extract_field(record, "flow_magnitude", "UNKNOWN")
        },
        "_reconciled_from": str(source_file.relative_to(BASE_DIR)),
        "_reconciled_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Validate required fields
    if normalized["entry_score"] == 0.0:
        print(f"[Reconciliation] WARNING: entry_score is 0.0 for {symbol} from {source_file}", file=sys.stderr)
    
    return normalized


def search_all_trade_records() -> List[Tuple[Dict, Path]]:
    """Search entire project for trade records"""
    found_records = []
    
    print("[Reconciliation] Searching for trade records...", file=sys.stderr)
    
    # Search all directories
    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            continue
        
        for pattern in SEARCH_PATTERNS:
            for file_path in search_dir.rglob(pattern):
                # Skip target file (don't read what we're writing to)
                if file_path == TARGET_ATTRIBUTION_LOG:
                    continue
                
                # Skip very large files
                try:
                    if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                        continue
                except:
                    continue
                
                # Try to read as JSON/JSONL
                try:
                    if pattern == "*.jsonl":
                        # Read JSONL (one JSON per line)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    record = json.loads(line)
                                    normalized = normalize_attribution_record(record, file_path)
                                    if normalized:
                                        found_records.append((normalized, file_path))
                                except json.JSONDecodeError:
                                    continue
                                except Exception as e:
                                    print(f"[Reconciliation] Error parsing line {line_num} in {file_path}: {e}", file=sys.stderr)
                    elif pattern == "*.json":
                        # Read JSON (could be single object or array)
                        try:
                            data = json.loads(file_path.read_text(encoding='utf-8'))
                            
                            # Handle different JSON structures
                            if isinstance(data, dict):
                                # Check if it's a daily report with attribution data
                                if "attribution" in data:
                                    # Daily report format - extract individual trades
                                    attribution_data = data.get("attribution", {})
                                    report_date = data.get("date")
                                    
                                    for symbol, symbol_data in attribution_data.items():
                                        if isinstance(symbol_data, dict) and "trades" in symbol_data:
                                            # Create synthetic attribution records from daily report
                                            trades_count = symbol_data.get("trades", 0)
                                            total_pnl = symbol_data.get("pnl", 0.0)
                                            
                                            # Create one record per trade (distribute P&L)
                                            if trades_count > 0:
                                                avg_pnl = total_pnl / trades_count
                                                for i in range(trades_count):
                                                    synthetic_record = {
                                                        "type": "attribution",
                                                        "symbol": symbol,
                                                        "pnl_usd": round(avg_pnl, 2),
                                                        "pnl_pct": round(avg_pnl / 100.0, 4) if abs(avg_pnl) < 100 else round(avg_pnl / 1000.0, 4),  # Estimate
                                                        "ts": f"{report_date}T16:00:00Z" if report_date else datetime.now(timezone.utc).isoformat(),
                                                        "trade_id": f"reconciled_{symbol}_{report_date}_{i}" if report_date else f"reconciled_{symbol}_{i}",
                                                        "context": {
                                                            "close_reason": "reconciled_from_daily_report",
                                                            "market_regime": "unknown"
                                                        }
                                                    }
                                                    normalized = normalize_attribution_record(synthetic_record, file_path)
                                                    if normalized:
                                                        found_records.append((normalized, file_path))
                                else:
                                    # Single record
                                    normalized = normalize_attribution_record(data, file_path)
                                    if normalized:
                                        found_records.append((normalized, file_path))
                            elif isinstance(data, list):
                                # Array of records
                                for record in data:
                                    normalized = normalize_attribution_record(record, file_path)
                                    if normalized:
                                        found_records.append((normalized, file_path))
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            print(f"[Reconciliation] Error reading {file_path}: {e}", file=sys.stderr)
                except Exception as e:
                    # Skip files that can't be read
                    continue
    
    print(f"[Reconciliation] Found {len(found_records)} trade records", file=sys.stderr)
    return found_records


def deduplicate_records(records: List[Dict]) -> List[Dict]:
    """Deduplicate records by (symbol, timestamp, trade_id)"""
    seen = set()
    deduplicated = []
    
    for record in records:
        # Create unique key
        symbol = record.get("symbol", "")
        ts = record.get("ts", "")
        trade_id = record.get("trade_id", "")
        
        # Try multiple keys for deduplication
        key1 = (symbol, ts, trade_id)
        key2 = (symbol, ts[:16], trade_id)  # Ignore seconds for fuzzy match
        
        if key1 in seen or key2 in seen:
            continue
        
        seen.add(key1)
        seen.add(key2)
        deduplicated.append(record)
    
    print(f"[Reconciliation] Deduplicated: {len(records)} -> {len(deduplicated)} records", file=sys.stderr)
    return deduplicated


def main():
    """Main reconciliation process"""
    print(f"[Reconciliation] Starting full week data reconciliation...", file=sys.stderr)
    print(f"[Reconciliation] Target file: {TARGET_ATTRIBUTION_LOG}", file=sys.stderr)
    
    # Step 1: Search for all trade records
    found_records_with_sources = search_all_trade_records()
    
    if not found_records_with_sources:
        print("[Reconciliation] WARNING: No trade records found in search", file=sys.stderr)
        return
    
    # Extract just the records
    found_records = [r[0] for r in found_records_with_sources]
    
    # Step 2: Deduplicate
    deduplicated_records = deduplicate_records(found_records)
    
    # Step 3: Sort by timestamp
    deduplicated_records.sort(key=lambda x: parse_timestamp(x.get("ts")) or datetime.min.replace(tzinfo=timezone.utc))
    
    # Step 4: Write to standardized path
    TARGET_ATTRIBUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup existing file if it exists
    if TARGET_ATTRIBUTION_LOG.exists():
        backup_path = TARGET_ATTRIBUTION_LOG.with_suffix(".jsonl.backup")
        try:
            import shutil
            shutil.copy2(TARGET_ATTRIBUTION_LOG, backup_path)
            print(f"[Reconciliation] Backed up existing file to {backup_path}", file=sys.stderr)
        except Exception as e:
            print(f"[Reconciliation] WARNING: Could not backup existing file: {e}", file=sys.stderr)
    
    # Write all records
    with open(TARGET_ATTRIBUTION_LOG, 'w', encoding='utf-8') as f:
        for record in deduplicated_records:
            f.write(json.dumps(record) + "\n")
    
    print(f"[Reconciliation] ✅ Wrote {len(deduplicated_records)} records to {TARGET_ATTRIBUTION_LOG}", file=sys.stderr)
    
    # Step 5: Verify
    if TARGET_ATTRIBUTION_LOG.exists():
        file_size = TARGET_ATTRIBUTION_LOG.stat().st_size
        print(f"[Reconciliation] ✅ File size: {file_size} bytes", file=sys.stderr)
        
        # Count records
        with open(TARGET_ATTRIBUTION_LOG, 'r', encoding='utf-8') as f:
            line_count = sum(1 for line in f if line.strip())
        print(f"[Reconciliation] ✅ Record count: {line_count}", file=sys.stderr)
        
        # Count by source
        sources = defaultdict(int)
        for record in deduplicated_records:
            source = record.get("_reconciled_from", "unknown")
            sources[source] += 1
        
        print(f"[Reconciliation] Records by source:", file=sys.stderr)
        for source, count in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"  - {source}: {count} records", file=sys.stderr)
    else:
        print(f"[Reconciliation] ERROR: File was not created!", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
