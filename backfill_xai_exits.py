#!/usr/bin/env python3
"""
Backfill XAI exit logs from attribution.jsonl
Ensures all exits have XAI explanations for dashboard display
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict

LOGS_DIR = Path("logs")
DATA_DIR = Path("data")
ATTRIBUTION_FILE = LOGS_DIR / "attribution.jsonl"
XAI_FILE = DATA_DIR / "explainable_logs.jsonl"

def load_jsonl(file_path: Path) -> List[Dict]:
    """Load JSONL file"""
    if not file_path.exists():
        return []
    records = []
    try:
        with file_path.open('r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except:
                        continue
    except Exception as e:
        print(f"[ERROR] Failed to load {file_path}: {e}")
    return records

def get_existing_xai_exits() -> set:
    """Get set of existing XAI exit records (by symbol+timestamp)"""
    existing = set()
    for record in load_jsonl(XAI_FILE):
        if record.get("type") == "trade_exit":
            symbol = record.get("symbol", "")
            timestamp = record.get("timestamp", "")
            if symbol and timestamp:
                existing.add(f"{symbol}_{timestamp[:19]}")
    return existing

def backfill_exits():
    """Backfill XAI exit logs from attribution.jsonl"""
    from xai.explainable_logger import get_explainable_logger
    
    explainable = get_explainable_logger()
    existing = get_existing_xai_exits()
    
    # Get all attribution exits
    attribution_exits = []
    for record in load_jsonl(ATTRIBUTION_FILE):
        if record.get("type") != "attribution":
            continue
        
        # Skip open trades
        trade_id = record.get("trade_id", "")
        if trade_id.startswith("open_"):
            continue
        
        # Must have close_reason (actual exit)
        context = record.get("context", {})
        close_reason = context.get("close_reason", "")
        if not close_reason or close_reason == "unknown":
            continue
        
        attribution_exits.append(record)
    
    # Sort by timestamp
    attribution_exits.sort(key=lambda x: x.get("ts", ""), reverse=True)
    
    backfilled = 0
    skipped = 0
    
    for exit_record in attribution_exits:
        symbol = exit_record.get("symbol", "")
        if not symbol or "TEST" in symbol.upper():
            continue
        
        context = exit_record.get("context", {})
        entry_price = context.get("entry_price", 0.0)
        exit_price = context.get("exit_price", 0.0)
        pnl_pct = exit_record.get("pnl_pct", 0.0)
        hold_minutes = context.get("hold_minutes", 0.0)
        close_reason = context.get("close_reason", "unknown")
        regime = context.get("market_regime", "unknown")
        ts = exit_record.get("ts", "")
        
        if not ts:
            continue
        
        # Check if already logged
        try:
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            else:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            ts_key = f"{symbol}_{dt.isoformat()[:19]}"
        except:
            continue
        
        if ts_key in existing:
            skipped += 1
            continue
        
        # Backfill this exit
        try:
            explainable.log_trade_exit(
                symbol=symbol,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl_pct=pnl_pct,
                hold_minutes=hold_minutes,
                exit_reason=close_reason,
                regime=regime,
                gamma_walls=None
            )
            backfilled += 1
            print(f"[OK] Backfilled exit: {symbol} - {close_reason[:50]}")
        except Exception as e:
            print(f"[ERROR] Failed to backfill {symbol}: {e}")
    
    print(f"\n[SUMMARY] Backfilled: {backfilled}, Skipped (already exists): {skipped}")
    return backfilled

if __name__ == "__main__":
    print("=" * 80)
    print("BACKFILLING XAI EXIT LOGS")
    print("=" * 80)
    backfilled = backfill_exits()
    print(f"\n[COMPLETE] Backfilled {backfilled} exit(s) to XAI logs")

