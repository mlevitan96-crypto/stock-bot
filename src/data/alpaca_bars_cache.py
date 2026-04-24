"""
Disk cache for Alpaca bars keyed by symbol + date + resolution.
Used by the 2000-trade pipeline to avoid rate limits and ensure reproducibility.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = REPO / "data" / "bars_cache"


def cache_path(
    symbol: str,
    date_str: str,
    resolution: str,
    cache_dir: Optional[Path] = None,
) -> Path:
    """Path to cached bars file: cache_dir/SYMBOL/YYYY-MM-DD_resolution.json."""
    root = Path(cache_dir or DEFAULT_CACHE_DIR)
    safe = resolution.replace("/", "_").strip() or "1m"
    return root / symbol.upper().strip() / f"{date_str}_{safe}.json"


def get_cached_bars(
    symbol: str,
    date_str: str,
    resolution: str,
    cache_dir: Optional[Path] = None,
) -> Optional[List[dict]]:
    """Return list of bar dicts if cached, else None. Bars have t, o, h, l, c, v."""
    path = cache_path(symbol, date_str, resolution, cache_dir)
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return data if isinstance(data, list) else data.get("bars", data)
    except Exception:
        return None


def set_cached_bars(
    symbol: str,
    date_str: str,
    resolution: str,
    bars: List[dict],
    cache_dir: Optional[Path] = None,
) -> None:
    """Write bars to cache. Creates parent dirs."""
    path = cache_path(symbol, date_str, resolution, cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(bars, default=str), encoding="utf-8")
    except Exception:
        pass
