"""
Runtime SPI visibility for Alpaca entries.

Requires a row in the signal intelligence SPI CSV for the symbol with
timestamp_utc within the configured freshness window (default 15 minutes).
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

# Exact line requested for operator grep / journald filters.
SPI_VISIBILITY_VETO_LOG_LINE = (
    "[VETO] Trade denied: SPI Visibility Gap (Signal missing or stale)."
)

_SPI_CACHE: Dict[str, Tuple[float, Dict[str, float]]] = {}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _spi_csv_paths() -> list[Path]:
    paths: list[Path] = []
    env = os.environ.get("ALPACA_SPI_CSV", "").strip()
    if env:
        paths.append(Path(env))
    root = _repo_root()
    for rel in (
        "reports/Gemini/signal_intelligence_spi.csv",
        "reports/Gemini/signal_intelligence_spi_droplet.csv",
    ):
        paths.append(root / rel)
    # De-dupe while preserving order
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        k = str(p.resolve())
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def _parse_ts(s: str) -> Optional[float]:
    if not s:
        return None
    try:
        t = str(s).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _load_spi_latest_by_symbol(path: Path) -> Optional[Dict[str, float]]:
    """Return map symbol_upper -> unix timestamp of latest SPI row, or None if file missing."""
    if not path.is_file():
        return None
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    key = str(path.resolve())
    cached = _SPI_CACHE.get(key)
    if cached and cached[0] == mtime:
        return cached[1]

    sym_to_ts: Dict[str, float] = {}
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                _SPI_CACHE[key] = (mtime, sym_to_ts)
                return sym_to_ts
            fields = {str(n).lower().strip(): n for n in reader.fieldnames if n}
            sym_col = None
            for candidate in ("symbol", "ticker", "sym"):
                if candidate in fields:
                    sym_col = fields[candidate]
                    break
            ts_col = None
            for candidate in ("timestamp_utc", "timestamp", "utc", "ts_utc"):
                if candidate in fields:
                    ts_col = fields[candidate]
                    break
            if not sym_col or not ts_col:
                _SPI_CACHE[key] = (mtime, sym_to_ts)
                return sym_to_ts
            for row in reader:
                sym = str(row.get(sym_col) or "").strip().upper()
                if not sym:
                    continue
                ts = _parse_ts(str(row.get(ts_col) or ""))
                if ts is None:
                    continue
                prev = sym_to_ts.get(sym)
                if prev is None or ts > prev:
                    sym_to_ts[sym] = ts
    except OSError:
        return None

    _SPI_CACHE[key] = (mtime, sym_to_ts)
    return sym_to_ts


def _max_age_minutes() -> float:
    raw = os.environ.get("ALPACA_SPI_MAX_AGE_MINUTES", "15").strip()
    try:
        return max(0.5, float(raw))
    except (TypeError, ValueError):
        return 15.0


def spi_visibility_ok(symbol: str, max_age_minutes: Optional[float] = None) -> Tuple[bool, str]:
    """
    True if the freshest SPI row for symbol across configured CSV paths is within max_age_minutes.
    """
    sym_u = str(symbol).strip().upper()
    lim = float(max_age_minutes) if max_age_minutes is not None else _max_age_minutes()
    best_ts: Optional[float] = None
    best_src = ""
    for p in _spi_csv_paths():
        latest = _load_spi_latest_by_symbol(p)
        if not latest:
            continue
        ts = latest.get(sym_u)
        if ts is None:
            continue
        if best_ts is None or ts > best_ts:
            best_ts = ts
            best_src = str(p)
    if best_ts is None:
        return False, "no_spi_row"
    now = datetime.now(timezone.utc).timestamp()
    age_min = (now - best_ts) / 60.0
    if age_min <= lim:
        return True, f"spi_ok path={best_src} age_min={round(age_min, 3)}"
    return False, f"stale_spi path={best_src} age_min={round(age_min, 3)} max={lim}"


def should_allow_entry_with_spi_visibility(symbol: str) -> Tuple[bool, str]:
    """
    ALPACA_SPI_VISIBILITY_GATE=0|false|no|off — disables the check (emergency / drills only).
    """
    v = os.environ.get("ALPACA_SPI_VISIBILITY_GATE", "1").strip().lower()
    if v in ("0", "false", "no", "off"):
        return True, "spi_visibility_gate_disabled"
    return spi_visibility_ok(symbol)
