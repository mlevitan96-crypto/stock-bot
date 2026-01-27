"""
Orders Log: Canonical logging for order events (real and dry-run).

This module provides a single source for writing order events to logs/orders.jsonl.
Used by both real order submission and audit dry-run paths to ensure consistent formatting.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


def append_order_event(event: Dict[str, Any], repo_root: Optional[Path] = None) -> None:
    """
    Append an order event to logs/orders.jsonl.
    
    This is the canonical path for logging order events. Both real orders
    and audit dry-run orders should use this function to ensure consistent
    formatting and schema.
    
    Args:
        event: Dictionary with order event data. Required fields:
            - action: Action type (e.g., "submit", "audit_dry_run", "close")
            - symbol: Stock symbol
        repo_root: Repository root path (defaults to detecting from __file__)
    
    Raises:
        Exception: If logging fails (caller should handle gracefully)
    """
    if repo_root is None:
        # Detect repo root from this file's location
        this_file = Path(__file__).resolve()
        repo_root = this_file.parents[1]
    
    log_path = repo_root / "logs" / "orders.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure timestamp is present
    if "ts" not in event and "_ts" not in event:
        event["ts"] = datetime.now(timezone.utc).isoformat()
    
    # Write as JSON line
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")
        f.flush()
