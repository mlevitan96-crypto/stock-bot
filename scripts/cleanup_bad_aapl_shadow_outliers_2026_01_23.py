#!/usr/bin/env python3
"""
Cleanup: remove a specific known-bad AAPL shadow PnL outlier cluster (2026-01-23 UTC)
==================================================================================

Why:
- A regression smoke-test (or similar) created impossible shadow exits:
  entry_price=100, exit_price=1000, qty=5 => pnl=4500, pnl_pct=9.0
- These 3 exits sum to 13,500 and distort the dashboard "Live vs Shadow PnL".

Scope:
- Removes ONLY records matching this exact outlier signature.
- Does NOT remove all AAPL trades.
- Creates .bak backups once before overwriting.
- Idempotent.

Targets (if they exist):
- logs/exit_attribution.jsonl
- logs/shadow_trades.jsonl
- logs/master_trade_log.jsonl
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TARGET_DAY = "2026-01-23"
SYMBOL = "AAPL"


def _backup_once(path: Path) -> None:
    try:
        if not path.exists():
            return
        bak = path.with_suffix(path.suffix + ".bak")
        if bak.exists():
            return
        shutil.copy2(path, bak)
    except Exception:
        return


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _iter_jsonl_lines(path: Path) -> Iterable[Tuple[str, Optional[Dict[str, Any]]]]:
    for ln in _read_text(path).splitlines():
        raw = ln
        s = ln.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                yield raw, obj
            else:
                yield raw, None
        except Exception:
            yield raw, None


def _write_jsonl(path: Path, lines: List[str]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    tmp.replace(path)


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _is_target_day(ts: Any) -> bool:
    try:
        return str(ts or "").startswith(TARGET_DAY)
    except Exception:
        return False


def _matches_outlier_exit(rec: Dict[str, Any]) -> bool:
    # Exact signature for the known-bad cluster.
    if str(rec.get("symbol", "")).upper() != SYMBOL:
        return False
    ts = rec.get("timestamp") or rec.get("ts") or rec.get("exit_ts")
    if not _is_target_day(ts):
        return False
    ep = _safe_float(rec.get("entry_price"))
    xp = _safe_float(rec.get("exit_price"))
    qty = _safe_float(rec.get("qty") or rec.get("size"))
    pnl = _safe_float(rec.get("pnl") or rec.get("realized_pnl_usd"))
    pnl_pct = _safe_float(rec.get("pnl_pct"))
    return (
        ep is not None
        and xp is not None
        and qty is not None
        and pnl is not None
        and pnl_pct is not None
        and abs(ep - 100.0) < 1e-9
        and abs(xp - 1000.0) < 1e-6
        and abs(qty - 5.0) < 1e-9
        and abs(pnl - 4500.0) < 1e-6
        and abs(pnl_pct - 9.0) < 1e-9
    )


def _clean_jsonl(path: Path, *, predicate, note: str) -> Tuple[int, int]:
    if not path.exists():
        return 0, 0
    _backup_once(path)
    kept: List[str] = []
    removed = 0
    total = 0
    for raw, rec in _iter_jsonl_lines(path):
        if rec is None:
            kept.append(raw)
            continue
        total += 1
        if predicate(rec):
            removed += 1
            continue
        kept.append(raw)
    if removed > 0:
        _write_jsonl(path, kept)
    print(f"- {path.as_posix()}: removed={removed} total_records={total} ({note})")
    return removed, total


def main() -> int:
    print("AAPL_SHADOW_OUTLIER_CLEANUP")
    print(f"- target_day={TARGET_DAY} symbol={SYMBOL}")

    removed_total = 0

    # 1) exit_attribution: remove the 3 pnl=4500 exits
    r, _ = _clean_jsonl(Path("logs/exit_attribution.jsonl"), predicate=_matches_outlier_exit, note="exit_attribution outlier exits")
    removed_total += r

    # 2) shadow_trades: remove matching shadow_exit rows (same signature)
    def _shadow_trade_pred(rec: Dict[str, Any]) -> bool:
        if str(rec.get("symbol", "")).upper() != SYMBOL:
            return False
        ts = rec.get("ts") or rec.get("timestamp") or rec.get("exit_ts") or rec.get("entry_ts")
        if not _is_target_day(ts):
            return False
        et = str(rec.get("event_type", "") or "")
        if et not in ("shadow_exit", "shadow_entry_opened"):
            return False
        # For shadow_exit the fields match exit_attribution closely:
        if et == "shadow_exit":
            return _matches_outlier_exit(rec)
        # For shadow_entry_opened, match the corresponding impossible entry setup:
        ep = _safe_float(rec.get("entry_price"))
        qty = _safe_float(rec.get("qty"))
        return (ep is not None and abs(ep - 100.0) < 1e-9 and qty is not None and abs(qty - 5.0) < 1e-9)

    r, _ = _clean_jsonl(Path("logs/shadow_trades.jsonl"), predicate=_shadow_trade_pred, note="shadow_trades outlier entry/exit rows")
    removed_total += r

    # 3) master_trade_log: remove both entry record and full close record if they match the signature
    def _mtl_pred(rec: Dict[str, Any]) -> bool:
        if str(rec.get("symbol", "")).upper() != SYMBOL:
            return False
        if not bool(rec.get("is_shadow")):
            return False
        ts = rec.get("timestamp") or rec.get("exit_ts") or rec.get("entry_ts")
        if not _is_target_day(ts):
            return False
        return _matches_outlier_exit(rec) or (
            _safe_float(rec.get("entry_price")) is not None
            and abs(float(rec.get("entry_price") or 0.0) - 100.0) < 1e-9
            and _safe_float(rec.get("size")) is not None
            and abs(float(rec.get("size") or 0.0) - 5.0) < 1e-9
            and (rec.get("exit_ts") in (None, "", "null"))
        )

    r, _ = _clean_jsonl(Path("logs/master_trade_log.jsonl"), predicate=_mtl_pred, note="master_trade_log outlier records")
    removed_total += r

    print(f"- removed_total_lines={removed_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

