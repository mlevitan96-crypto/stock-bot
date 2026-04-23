"""
Persistent cumulative realized PnL (live + V3-shadow lane) for the Command Center chart.

Append-only ``state/continuous_pnl_ledger.jsonl`` — **not** truncated by epoch log resets — one row
per closed trade after ``append_exit_attribution`` succeeds. Dashboard reads this file first and
falls back to reconstructing from ``exit_attribution`` + ``run.jsonl`` tails only when the ledger
is empty (e.g. fresh host).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

TailFn = Callable[[Path, int, int], List[str]]

SCHEMA_V1 = "continuous_pnl_ledger_v1"
_LEDGER_BASENAME = "continuous_pnl_ledger.jsonl"
_V3_CACHE: Dict[str, Any] = {"mtime": None, "map": {}}


def continuous_pnl_ledger_path(root: Optional[Path] = None) -> Path:
    base = root or Path(os.environ.get("STOCK_BOT_ROOT", Path(__file__).resolve().parents[1]))
    p = (base / "state" / _LEDGER_BASENAME).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _default_tail_lines(path: Path, max_lines: int = 80_000, max_chunk_bytes: int = 20_000_000) -> List[str]:
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            size = path.stat().st_size
            chunk = min(max_chunk_bytes, size)
            if size > chunk:
                f.seek(max(0, size - chunk))
                f.readline()
            lines = f.read().splitlines()
            return lines[-max_lines:] if len(lines) > max_lines else lines
    except OSError:
        return []


def exit_trade_dedupe_id(rec: dict) -> Optional[str]:
    from src.telemetry.alpaca_trade_key import build_trade_key

    for k in ("trade_id", "canonical_trade_id", "trade_key"):
        v = rec.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    sym = rec.get("symbol")
    side = rec.get("side") or rec.get("position_side")
    et_ent = rec.get("entry_ts") or rec.get("entry_timestamp")
    try:
        return build_trade_key(sym, side, et_ent)
    except Exception:
        return None


def _v3_shadow_map_from_run_jsonl(root: Path, tail_lines: TailFn) -> Dict[str, Any]:
    run_path = (root / "logs" / "run.jsonl").resolve()
    out: Dict[str, Any] = {}
    for line in tail_lines(run_path, 120_000, 25_000_000):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if str(rec.get("event_type") or "") != "trade_intent":
            continue
        if str(rec.get("decision_outcome") or "").lower() != "entered":
            continue
        v3 = rec.get("ai_approved_v3_shadow")
        for k in ("trade_id", "trade_key", "canonical_trade_id"):
            v = rec.get(k)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                out[s] = v3
    return out


def _cached_v3_map(root: Path, tail_lines: TailFn) -> Dict[str, Any]:
    run_path = (root / "logs" / "run.jsonl").resolve()
    try:
        m = float(run_path.stat().st_mtime)
    except OSError:
        return {}
    if _V3_CACHE.get("mtime") != m:
        _V3_CACHE["map"] = _v3_shadow_map_from_run_jsonl(root, tail_lines)
        _V3_CACHE["mtime"] = m
    return _V3_CACHE.get("map") or {}


def _resolve_v3_hit(rec: dict, trade_key: str, v3_map: Dict[str, Any]) -> bool:
    v3 = None
    if trade_key in v3_map:
        v3 = v3_map.get(trade_key)
    else:
        for alt in ("trade_id", "canonical_trade_id", "trade_key"):
            v = rec.get(alt)
            if v is not None and str(v).strip() in v3_map:
                v3 = v3_map.get(str(v).strip())
                break
    return v3 is True


def _thin_points(points: List[dict], max_points: int) -> List[dict]:
    if max_points <= 0 or len(points) <= max_points:
        return points
    step = max(1, len(points) // max_points)
    thin = points[::step]
    if thin[-1] is not points[-1]:
        thin.append(points[-1])
    return thin


def reconstruct_dual_barrel_cumulative_from_logs(
    root: Path,
    *,
    max_points: int = 600,
    tail_lines: Optional[TailFn] = None,
) -> dict:
    """Rebuild chart series from volatile JSONL tails (fallback when ledger is empty)."""
    from src.governance.canonical_trade_count import _parse_exit_epoch
    from utils.era_cut import learning_excluded_for_exit_record

    tail = tail_lines or _default_tail_lines
    v3_map = _v3_shadow_map_from_run_jsonl(root, tail)
    exit_path = (root / "logs" / "exit_attribution.jsonl").resolve()
    rows: List[Tuple[float, str, float, bool]] = []
    seen: Set[str] = set()
    for line in tail(exit_path, 100_000, 24_000_000):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if learning_excluded_for_exit_record(rec):
            continue
        ex = _parse_exit_epoch(rec)
        if ex is None:
            continue
        tid = exit_trade_dedupe_id(rec)
        if not tid or tid in seen:
            continue
        seen.add(tid)
        raw_pnl = rec.get("pnl_usd")
        if raw_pnl is None:
            raw_pnl = rec.get("pnl")
        try:
            pnl = float(raw_pnl) if raw_pnl is not None else 0.0
        except (TypeError, ValueError):
            pnl = 0.0
        shadow_hit = _resolve_v3_hit(rec, tid, v3_map)
        rows.append((float(ex), tid, pnl, shadow_hit))

    rows.sort(key=lambda x: x[0])
    live_cum = 0.0
    shadow_cum = 0.0
    points: List[dict] = []
    for ts, _tid, pnl, shadow_hit in rows:
        live_cum += pnl
        shadow_cum += pnl if shadow_hit else 0.0
        points.append(
            {
                "t": ts,
                "ts_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "live_cumulative_usd": round(live_cum, 4),
                "shadow_cumulative_usd": round(shadow_cum, 4),
            }
        )
    points = _thin_points(points, max_points)
    return {
        "ok": True,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "points": points,
        "source": "logs/exit_attribution.jsonl + logs/run.jsonl (V3 shadow gate, volatile tail)",
        "ledger_path": f"state/{_LEDGER_BASENAME}",
        "does_not_claim": [
            "shadow_pnl_for_blocked_entries",
            "v3_none_treated_as_zero_shadow_increment",
            "pre_trade_intent_era_alignment",
            "truncated_logs_lose_history",
        ],
    }


def read_dual_barrel_series_from_persistent_ledger(
    root: Path,
    *,
    max_points: int = 600,
    max_ledger_tail_lines: int = 800_000,
    tail_lines: Optional[TailFn] = None,
) -> Tuple[List[dict], Dict[str, Any]]:
    """
    Read chart points from ``state/continuous_pnl_ledger.jsonl``. Deduplicates by ``trade_key``
    (keeps the row with the greatest ``t`` per key). Returns (points, meta).
    """
    tail = tail_lines or _default_tail_lines
    path = continuous_pnl_ledger_path(root)
    if not path.is_file():
        return [], {"source": None, "ledger_path": f"state/{_LEDGER_BASENAME}", "row_count": 0}

    objs: List[dict] = []
    for line in tail(path, max_ledger_tail_lines, 48_000_000):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        if obj.get("schema") != SCHEMA_V1:
            continue
        tk = str(obj.get("trade_key") or "").strip()
        if not tk:
            continue
        objs.append(obj)

    by_key: Dict[str, dict] = {}
    for o in sorted(objs, key=lambda x: float(x.get("t") or 0.0)):
        tk = str(o.get("trade_key") or "").strip()
        if tk:
            by_key[tk] = o

    points: List[dict] = []
    for obj in sorted(by_key.values(), key=lambda x: float(x.get("t") or 0.0)):
        try:
            ts = float(obj.get("t"))
        except (TypeError, ValueError):
            continue
        try:
            points.append(
                {
                    "t": ts,
                    "ts_iso": str(obj.get("ts_iso") or datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()),
                    "live_cumulative_usd": float(obj.get("live_cumulative_usd", 0.0)),
                    "shadow_cumulative_usd": float(obj.get("shadow_cumulative_usd", 0.0)),
                }
            )
        except (TypeError, ValueError):
            continue
    points = _thin_points(points, max_points)
    if not points:
        return [], {"source": None, "ledger_path": f"state/{_LEDGER_BASENAME}", "row_count": 0}
    meta = {
        "source": f"state/{_LEDGER_BASENAME} (persistent)",
        "ledger_path": f"state/{_LEDGER_BASENAME}",
        "row_count": len(by_key),
    }
    return points, meta


def append_continuous_pnl_point_from_exit(rec: Dict[str, Any]) -> None:
    """Append one ledger row after a successful exit attribution write. Never raises."""
    try:
        from src.governance.canonical_trade_count import _parse_exit_epoch
        from utils.era_cut import learning_excluded_for_exit_record

        if not isinstance(rec, dict):
            return
        if learning_excluded_for_exit_record(rec):
            return
        root = Path(__file__).resolve().parents[1]
        trade_key = exit_trade_dedupe_id(rec)
        if not trade_key:
            return
        ex = _parse_exit_epoch(rec)
        if ex is None:
            return
        raw_pnl = rec.get("pnl_usd")
        if raw_pnl is None:
            raw_pnl = rec.get("pnl")
        try:
            pnl = float(raw_pnl) if raw_pnl is not None else 0.0
        except (TypeError, ValueError):
            pnl = 0.0

        tail = _default_tail_lines
        v3_map = _cached_v3_map(root, tail)
        shadow_hit = _resolve_v3_hit(rec, trade_key, v3_map)
        shadow_inc = pnl if shadow_hit else 0.0

        path = continuous_pnl_ledger_path(root)
        recent_keys: Set[str] = set()
        last_live = 0.0
        last_shadow = 0.0
        for line in tail(path, 5000, 4_000_000):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(o, dict) or o.get("schema") != SCHEMA_V1:
                continue
            tk = str(o.get("trade_key") or "").strip()
            if tk:
                recent_keys.add(tk)
            try:
                last_live = float(o.get("live_cumulative_usd", last_live))
                last_shadow = float(o.get("shadow_cumulative_usd", last_shadow))
            except (TypeError, ValueError):
                pass
        if trade_key in recent_keys:
            return

        new_live = last_live + pnl
        new_shadow = last_shadow + shadow_inc
        row = {
            "schema": SCHEMA_V1,
            "t": float(ex),
            "ts_iso": datetime.fromtimestamp(float(ex), tz=timezone.utc).isoformat(),
            "trade_key": trade_key,
            "symbol": str(rec.get("symbol") or "").upper() or None,
            "pnl_usd": round(pnl, 6),
            "shadow_increment_usd": round(shadow_inc, 6),
            "live_cumulative_usd": round(new_live, 6),
            "shadow_cumulative_usd": round(new_shadow, 6),
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except Exception:
        return


def seed_continuous_pnl_ledger_from_logs(
    root: Path,
    *,
    force: bool = False,
    tail_lines: Optional[TailFn] = None,
) -> int:
    """
    One-off: populate ``state/continuous_pnl_ledger.jsonl`` from current exit + run tails.
    Returns number of rows written. Skips if ledger non-empty unless ``force=True``.
    """
    path = continuous_pnl_ledger_path(root)
    if path.is_file() and path.stat().st_size > 0 and not force:
        return 0
    if path.is_file() and force:
        path.unlink(missing_ok=True)

    from src.governance.canonical_trade_count import _parse_exit_epoch
    from utils.era_cut import learning_excluded_for_exit_record

    tail = tail_lines or _default_tail_lines
    v3_map = _v3_shadow_map_from_run_jsonl(root, tail)
    exit_path = (root / "logs" / "exit_attribution.jsonl").resolve()
    rows: List[Tuple[float, str, float, bool]] = []
    seen: Set[str] = set()
    for line in tail(exit_path, 120_000, 28_000_000):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if learning_excluded_for_exit_record(rec):
            continue
        ex = _parse_exit_epoch(rec)
        if ex is None:
            continue
        tid = exit_trade_dedupe_id(rec)
        if not tid or tid in seen:
            continue
        seen.add(tid)
        raw_pnl = rec.get("pnl_usd")
        if raw_pnl is None:
            raw_pnl = rec.get("pnl")
        try:
            pnl = float(raw_pnl) if raw_pnl is not None else 0.0
        except (TypeError, ValueError):
            pnl = 0.0
        shadow_hit = _resolve_v3_hit(rec, tid, v3_map)
        rows.append((float(ex), tid, pnl, shadow_hit))

    rows.sort(key=lambda x: x[0])
    live_cum = 0.0
    shadow_cum = 0.0
    n = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ts, tid, pnl, shadow_hit in rows:
            live_cum += pnl
            inc = pnl if shadow_hit else 0.0
            shadow_cum += inc
            row = {
                "schema": SCHEMA_V1,
                "t": float(ts),
                "ts_iso": datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat(),
                "trade_key": tid,
                "pnl_usd": round(pnl, 6),
                "shadow_increment_usd": round(inc, 6),
                "live_cumulative_usd": round(live_cum, 6),
                "shadow_cumulative_usd": round(shadow_cum, 6),
                "written_at_utc": datetime.now(timezone.utc).isoformat(),
                "seeded": True,
            }
            f.write(json.dumps(row, default=str) + "\n")
            n += 1
    _V3_CACHE["mtime"] = None
    return n
