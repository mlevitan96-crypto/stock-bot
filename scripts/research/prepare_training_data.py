#!/usr/bin/env python3
"""
Alpha-10 prep: strict-cohort binary labels (+1.3% TP before -0.65% SL) + ultra-dense feature merge.

Labels use the same 1m bar first-touch semantics as ``optimize_tp_sl.py`` (same-bar TP+SL → SL first).
Features: ``entry_snapshots`` (components) joined like ``alpaca_ml_flattener``, plus flattened
``entry_uw`` / optional blobs from ``exit_attribution`` (numeric leaves only for JSONL size).

Does not write live logs. Requires Alpaca keys in env for bar fetch unless ``--skip-bars``
(all labels 0 with ``label_reason=skip_bars``).

Usage (repo root, after bell / DATA settled):
  PYTHONPATH=. python scripts/research/prepare_training_data.py --root /root/stock-bot \\
    --out-jsonl reports/research/alpha10_labeled_cohort.jsonl
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv

    _env = _ROOT / ".env"
    if _env.is_file():
        load_dotenv(_env, override=False)
except Exception:
    pass

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)
from src.telemetry.alpaca_trade_key import normalize_side  # noqa: E402


def _load_flattener():
    path = _ROOT / "scripts" / "telemetry" / "alpaca_ml_flattener.py"
    spec = importlib.util.spec_from_file_location("alpaca_ml_flattener", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _iter_exit_jsonl(path: Path) -> Iterator[dict]:
    if not path.is_file():
        return
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _load_strict_cohort_exits(root: Path, open_ts_epoch: float) -> Tuple[List[str], Dict[str, dict]]:
    r = evaluate_completeness(
        root,
        open_ts_epoch=open_ts_epoch,
        audit=False,
        collect_strict_cohort_trade_ids=True,
    )
    ids = list(r.get("strict_cohort_trade_ids") or [])
    want = set(ids)
    by_tid: Dict[str, dict] = {}
    for rec in _iter_exit_jsonl(root / "logs" / "exit_attribution.jsonl"):
        tid = str(rec.get("trade_id") or "")
        if tid in want:
            by_tid[tid] = rec
    return ids, by_tid


def _trade_fields(rec: dict) -> Optional[Tuple[str, datetime, datetime, float, float, str]]:
    sym = str(rec.get("symbol") or "").upper().strip()
    if not sym or sym == "?":
        return None
    raw_side = rec.get("position_side") or rec.get("side") or "long"
    side = normalize_side(raw_side)
    ent = _parse_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
    ex = _parse_ts(rec.get("exit_ts") or rec.get("timestamp"))
    if ent is None or ex is None or ex <= ent:
        return None
    try:
        ep = float(rec.get("entry_price") or 0.0)
        xp = float(rec.get("exit_price") or 0.0)
    except (TypeError, ValueError):
        return None
    if ep <= 0 or xp <= 0:
        return None
    return sym, ent, ex, ep, xp, side


def _bars_from_df(resp: Any) -> List[Dict[str, Any]]:
    df = getattr(resp, "df", None)
    if df is None or len(df) == 0:
        return []
    out: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        t = idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
        out.append(
            {
                "t": t,
                "o": float(row.get("open", row.get("o", 0))),
                "h": float(row.get("high", row.get("h", 0))),
                "l": float(row.get("low", row.get("l", 0))),
                "c": float(row.get("close", row.get("c", 0))),
            }
        )
    return out


def _filter_window(bars: List[Dict[str, Any]], t0: datetime, t1: datetime) -> List[Dict[str, Any]]:
    out = []
    for b in bars:
        dt = _parse_ts(b.get("t"))
        if dt is None:
            continue
        if dt < t0 - timedelta(minutes=1):
            continue
        if dt > t1 + timedelta(minutes=1):
            continue
        out.append(b)
    out.sort(key=lambda x: (_parse_ts(x["t"]) or datetime.min.replace(tzinfo=timezone.utc)))
    return out


def _label_tp_before_sl(
    bars: List[Dict[str, Any]],
    side: str,
    entry_px: float,
    exit_px: float,
    tp_pct: float,
    sl_pct: float,
) -> Tuple[int, str]:
    """
    1 = TP (+tp_pct) touched strictly before SL (sl_pct negative); same bar → SL first.
    0 = SL first, or neither before hold end (neither → failure per mandate).
    """
    p = entry_px
    sl_mag = abs(sl_pct)

    if side == "LONG":

        def outcome(b: Dict[str, Any]) -> Optional[str]:
            low_pct = (b["l"] - p) / p * 100.0
            high_pct = (b["h"] - p) / p * 100.0
            hit_sl = low_pct <= sl_pct
            hit_tp = high_pct >= tp_pct
            if hit_sl and hit_tp:
                return "SL"
            if hit_sl:
                return "SL"
            if hit_tp:
                return "TP"
            return None

    else:

        def outcome(b: Dict[str, Any]) -> Optional[str]:
            adv = (b["h"] - p) / p * 100.0
            fav = (p - b["l"]) / p * 100.0
            hit_sl = adv >= sl_mag
            hit_tp = fav >= tp_pct
            if hit_sl and hit_tp:
                return "SL"
            if hit_sl:
                return "SL"
            if hit_tp:
                return "TP"
            return None

    for b in bars:
        o = outcome(b)
        if o == "TP":
            return 1, "tp_first"
        if o == "SL":
            return 0, "sl_first_or_samebar"
    return 0, "neither_timeout_actual_path_unused"


def _alpaca_rest():
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    if not key or not secret:
        return None
    try:
        from alpaca_trade_api import REST

        return REST(key, secret, base_url=base)
    except Exception:
        return None


async def _fetch_symbol_bars(
    sym: str,
    t_min: datetime,
    t_max: datetime,
    api: Any,
    cache_dir: Path,
    sem: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    ck = cache_dir / f"{sym}_{t_min.date()}_{t_max.date()}_1m.json"
    if ck.is_file():
        try:
            raw = json.loads(ck.read_text(encoding="utf-8"))
            if isinstance(raw, list) and raw:
                return raw
        except Exception:
            pass
    start_s = _iso_z(t_min - timedelta(minutes=2))
    end_s = _iso_z(t_max + timedelta(minutes=2))
    async with sem:

        def _call():
            return api.get_bars(sym, "1Min", start=start_s, end=end_s, limit=10000)

        try:
            resp = await asyncio.to_thread(_call)
        except Exception as e:
            print(f"[warn] get_bars {sym}: {e}", file=sys.stderr)
            return []
    bars = _bars_from_df(resp)
    try:
        ck.write_text(json.dumps(bars), encoding="utf-8")
    except Exception:
        pass
    return bars


async def _load_all_bars(
    grouped: Dict[str, List[Tuple[datetime, datetime]]],
    cache_dir: Path,
    concurrency: int,
) -> Dict[str, List[Dict[str, Any]]]:
    api = _alpaca_rest()
    if api is None:
        return {}
    sem = asyncio.Semaphore(max(1, concurrency))
    tasks = []
    syms = []
    for sym, spans in grouped.items():
        t0 = min(s[0] for s in spans)
        t1 = max(s[1] for s in spans)
        syms.append(sym)
        tasks.append(_fetch_symbol_bars(sym, t0, t1, api, cache_dir, sem))
    results = await asyncio.gather(*tasks)
    return dict(zip(syms, results))


def _numeric_flat_from_nested(flatten_fn, obj: Any, prefix: str) -> Dict[str, float]:
    raw = flatten_fn(obj, prefix) if isinstance(obj, dict) and obj else {}
    out: Dict[str, float] = {}
    for k, v in raw.items():
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if not math.isfinite(float(v)):
                continue
            out[str(k)] = float(v)
        elif v is not None and str(v).strip() != "":
            try:
                x = float(v)
                if math.isfinite(x):
                    out[str(k)] = x
            except (TypeError, ValueError):
                continue
    return out


def _resolve_snapshot(
    mlf: Any,
    snap_idx: Dict[str, Dict[str, dict]],
    exit_rec: dict,
) -> Tuple[Optional[dict], str]:
    by_order = snap_idx.get("by_order") or {}
    by_tk = snap_idx.get("by_trade_key") or {}
    keys = mlf._exit_row_snapshot_lookup_keys(exit_rec)
    for k in keys:
        if k in by_tk:
            return by_tk[k], f"trade_key:{k[:48]}"
        if k in by_order:
            return by_order[k], f"order_id:{k[:24]}"
    return None, "none"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=_ROOT)
    ap.add_argument("--open-ts-epoch", type=float, default=float(STRICT_EPOCH_START))
    ap.add_argument("--out-jsonl", type=Path, default=_ROOT / "reports" / "research" / "alpha10_labeled_cohort.jsonl")
    ap.add_argument("--cache-dir", type=Path, default=_ROOT / "data" / "bars_mfe_cache")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--tp-pct", type=float, default=1.3)
    ap.add_argument("--sl-pct", type=float, default=-0.65)
    ap.add_argument(
        "--skip-bars",
        action="store_true",
        help="Do not call Alpaca; emit label=0 and label_reason=skip_bars (features still merged).",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    args.out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    mlf = _load_flattener()
    snap_path = root / "logs" / "entry_snapshots.jsonl"
    snap_idx = mlf._load_entry_snapshot_indexes(snap_path) if snap_path.is_file() else {"by_order": {}, "by_trade_key": {}}

    ids, by_tid = _load_strict_cohort_exits(root, float(args.open_ts_epoch))
    trades: List[dict] = []
    grouped: Dict[str, List[Tuple[datetime, datetime]]] = defaultdict(list)
    for tid in ids:
        rec = by_tid.get(tid)
        if not rec:
            continue
        tf = _trade_fields(rec)
        if not tf:
            continue
        sym, ent, ex, ep, xp, side = tf
        trades.append({"trade_id": tid, "symbol": sym, "t_entry": ent, "t_exit": ex, "entry_px": ep, "exit_px": xp, "side": side, "exit_rec": rec})
        grouped[sym].append((ent, ex))

    bars_by_sym: Dict[str, List[Dict[str, Any]]] = {}
    if not args.skip_bars:
        bars_by_sym = asyncio.run(_load_all_bars(grouped, args.cache_dir.resolve(), int(args.concurrency)))

    n_out = 0
    with args.out_jsonl.open("w", encoding="utf-8") as fout:
        for row in trades:
            rec = row["exit_rec"]
            snap, snap_tier = _resolve_snapshot(mlf, snap_idx, rec)
            feats: Dict[str, float] = {}
            if snap and isinstance(snap.get("components"), dict):
                comp = _numeric_flat_from_nested(mlf._flatten_leaves, snap["components"], "snap")
                feats.update(comp)
            for blob_key in ("entry_uw", "exit_uw"):
                blob = rec.get(blob_key)
                if isinstance(blob, dict):
                    pref = "euw" if blob_key == "entry_uw" else "xuw"
                    feats.update(_numeric_flat_from_nested(mlf._flatten_leaves, blob, pref))

            tid = row["trade_id"]
            sym = row["symbol"]
            bars: List[Dict[str, Any]] = []
            if not args.skip_bars:
                bars = _filter_window(bars_by_sym.get(sym) or [], row["t_entry"], row["t_exit"])
            if args.skip_bars or not bars:
                y, why = (0, "skip_bars" if args.skip_bars else "no_bars")
            else:
                y, why = _label_tp_before_sl(
                    bars,
                    row["side"],
                    row["entry_px"],
                    row["exit_px"],
                    float(args.tp_pct),
                    float(args.sl_pct),
                )

            out = {
                "trade_id": tid,
                "symbol": sym,
                "side": row["side"],
                "label": int(y),
                "label_reason": why,
                "tp_pct": float(args.tp_pct),
                "sl_pct": float(args.sl_pct),
                "bars_n": len(bars),
                "snapshot_join": snap_tier,
                "features": feats,
            }
            fout.write(json.dumps(out, default=str) + "\n")
            n_out += 1

    print(f"Wrote {n_out} rows -> {args.out_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
