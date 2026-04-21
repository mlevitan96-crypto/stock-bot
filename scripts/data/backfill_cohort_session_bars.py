#!/usr/bin/env python3
"""
Backfill full RTH 1-minute Alpaca bars for the strict learning cohort (+ SPY/QQQ).

Reads strict cohort trade ids (``evaluate_completeness`` + ``exit_attribution.jsonl``), builds
unique ``(symbol, ET session date)`` keys from entry/exit timestamps, fetches each full session
via Alpaca REST ``get_bars``, merges/dedupes into ``artifacts/market_data/alpaca_bars.jsonl``.

Rate limiting: ``--sleep-sec`` between REST calls (default 0.35).

Usage:
  PYTHONPATH=. python3 scripts/data/backfill_cohort_session_bars.py --root /root/stock-bot
  PYTHONPATH=. python3 scripts/data/backfill_cohort_session_bars.py --root . --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Load .env.research first, then .env (same pattern as scripts/fetch_alpaca_bars.py)
_env_research = REPO / ".env.research"
_env_path = REPO / ".env"
for path, override in [(_env_research, True), (_env_path, False)]:
    if not path.exists():
        continue
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=override)
    except Exception:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and (override or k not in os.environ):
                os.environ[k] = v

from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START  # noqa: E402

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    _ET = None


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(float(v), tz=timezone.utc)
    s = str(v).strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _et_day_str(ts: datetime) -> str:
    if _ET is None:
        return ts.astimezone(timezone.utc).strftime("%Y-%m-%d")
    return ts.astimezone(_ET).strftime("%Y-%m-%d")


def _session_utc_bounds_for_et_day(et_day: str) -> Tuple[datetime, datetime]:
    y, m, d = (int(x) for x in et_day.split("-"))
    if _ET is None:
        start = datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc)
        end = start + timedelta(days=1) - timedelta(seconds=1)
        return start, end
    open_local = datetime(y, m, d, 9, 30, 0, tzinfo=_ET)
    close_local = datetime(y, m, d, 16, 0, 0, tzinfo=_ET)
    return open_local.astimezone(timezone.utc), close_local.astimezone(timezone.utc)


def _iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _iter_exit_jsonl(path: Path) -> Iterable[dict]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                yield o


def _strict_cohort_trade_ids(root: Path, open_ts_epoch: float) -> Set[str]:
    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    r = evaluate_completeness(
        root,
        open_ts_epoch=float(open_ts_epoch),
        audit=False,
        collect_strict_cohort_trade_ids=True,
    )
    return set(str(x) for x in (r.get("strict_cohort_trade_ids") or []) if x)


def _cohort_pairs_from_jsonl(
    root: Path,
    want: Set[str],
    cohort_jsonl: Optional[Path],
) -> Set[Tuple[str, str]]:
    pairs: Set[Tuple[str, str]] = set()
    paths: List[Path] = []
    if cohort_jsonl is not None:
        paths.append(cohort_jsonl)
    else:
        paths.append(root / "logs" / "exit_attribution.jsonl")

    for path in paths:
        if not path.is_file():
            continue
        for rec in _iter_exit_jsonl(path):
            tid = str(rec.get("trade_id") or "")
            if want and tid not in want:
                continue
            sym = str(rec.get("symbol") or "").upper().strip()
            if not sym or sym == "?":
                continue
            for key in ("entry_ts", "entry_timestamp", "exit_ts", "timestamp"):
                dt = _parse_ts(rec.get(key))
                if dt is not None:
                    pairs.add((sym, _et_day_str(dt)))
    return pairs


def _alpaca_rest_client() -> Any:
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


def _bars_from_get_bars_df(resp: Any) -> List[Dict[str, Any]]:
    df = getattr(resp, "df", None)
    if df is None or len(df) == 0:
        return []
    out: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        if hasattr(idx, "to_pydatetime"):
            tdt = idx.to_pydatetime()
            if tdt.tzinfo is None:
                tdt = tdt.replace(tzinfo=timezone.utc)
            else:
                tdt = tdt.astimezone(timezone.utc)
            t = _iso_utc(tdt)
        elif hasattr(idx, "isoformat"):
            t = idx.isoformat()
            if isinstance(t, str) and t.endswith("+00:00"):
                t = t.replace("+00:00", "Z")
        else:
            t = str(idx)
        out.append(
            {
                "t": t,
                "o": float(row.get("open", row.get("o", 0))),
                "h": float(row.get("high", row.get("h", 0))),
                "l": float(row.get("low", row.get("l", 0))),
                "c": float(row.get("close", row.get("c", 0))),
                "v": int(row.get("volume", row.get("v", 0)) or 0),
            }
        )
    out.sort(key=lambda b: b.get("t") or "")
    return out


def _load_existing_merged(path: Path) -> Dict[Tuple[str, str], Dict[str, Dict[str, Any]]]:
    """
    (symbol, et_day) -> { iso_minute_key -> bar dict } for dedupe across JSONL lines.
    """
    merged: Dict[Tuple[str, str], Dict[str, Dict[str, Any]]] = defaultdict(dict)
    if not path.is_file():
        return merged
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = payload.get("data") or {}
            bars = data.get("bars") or {}
            day = str(payload.get("session_date") or "")
            for sym, arr in bars.items():
                if not isinstance(arr, list):
                    continue
                su = str(sym).upper()
                for bar in arr:
                    if not isinstance(bar, dict):
                        continue
                    t = bar.get("t")
                    if not t:
                        continue
                    dt = _parse_ts(t)
                    if dt is None:
                        continue
                    dkey = day or _et_day_str(dt)
                    k = (su, dkey)
                    iso = str(t)
                    cur = merged[k].get(iso)
                    if cur is None or int(bar.get("v", 0) or 0) >= int(cur.get("v", 0) or 0):
                        merged[k][iso] = bar
    return merged


def _write_merged(path: Path, merged: Dict[Tuple[str, str], Dict[str, Dict[str, Any]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    keys = sorted(merged.keys(), key=lambda x: (x[1], x[0]))
    with tmp.open("w", encoding="utf-8") as w:
        for sym, et_day in keys:
            bars_map = merged.get((sym, et_day)) or {}
            if not bars_map:
                continue
            bars_sorted = [bars_map[k] for k in sorted(bars_map.keys())]
            rec = {
                "type": "cohort_session_1m_backfill",
                "session_date": et_day,
                "data": {"bars": {sym: bars_sorted}},
            }
            w.write(json.dumps(rec, default=str) + "\n")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Default: <root>/artifacts/market_data/alpaca_bars.jsonl",
    )
    ap.add_argument("--open-ts-epoch", type=float, default=float(STRICT_EPOCH_START))
    ap.add_argument(
        "--cohort-jsonl",
        type=Path,
        default=None,
        help="Optional JSONL of cohort rows (must include trade_id + symbol + timestamps). "
        "Default: logs/exit_attribution.jsonl filtered to strict cohort ids.",
    )
    ap.add_argument("--sleep-sec", type=float, default=0.35, help="Pause between Alpaca REST calls.")
    ap.add_argument("--dry-run", action="store_true", help="Print keys only; do not call API or write.")
    args = ap.parse_args()
    root = args.root.resolve()
    out_path = args.out or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")

    want = _strict_cohort_trade_ids(root, float(args.open_ts_epoch))
    if not want:
        print(
            "WARN: strict_cohort_trade_ids empty; backfilling from all rows in cohort JSONL / exit_attribution.",
            file=sys.stderr,
        )
    pairs = _cohort_pairs_from_jsonl(root, want, args.cohort_jsonl)
    et_days = {d for _, d in pairs}
    for bench in ("SPY", "QQQ"):
        for d in et_days:
            pairs.add((bench, d))

    pairs = {(s.upper(), d) for s, d in pairs if s and d}
    print(f"unique_symbol_session_pairs={len(pairs)} out={out_path}", flush=True)

    if args.dry_run:
        for sym, day in sorted(pairs, key=lambda x: (x[1], x[0]))[:50]:
            print(f"  {sym} {day}")
        if len(pairs) > 50:
            print(f"  ... ({len(pairs) - 50} more)", flush=True)
        return 0

    api = _alpaca_rest_client()
    if not api:
        print("ERROR: Alpaca REST credentials missing (ALPACA_API_KEY / ALPACA_SECRET_KEY).", file=sys.stderr)
        return 1

    merged = _load_existing_merged(out_path)
    fetched = 0
    for sym, et_day in sorted(pairs, key=lambda x: (x[1], x[0])):
        start_utc, end_utc = _session_utc_bounds_for_et_day(et_day)
        key = (sym, et_day)
        try:
            resp = api.get_bars(
                sym,
                "1Min",
                start=_iso_utc(start_utc),
                end=_iso_utc(end_utc + timedelta(minutes=1)),
                limit=10000,
            )
            bars = _bars_from_get_bars_df(resp)
        except Exception as e:
            print(f"WARN: get_bars failed {sym} {et_day}: {e}", file=sys.stderr)
            bars = []
        bucket = merged.setdefault(key, {})
        for b in bars:
            t = b.get("t")
            if not t:
                continue
            iso = str(t)
            prev = bucket.get(iso)
            if prev is None or int(b.get("v", 0) or 0) >= int(prev.get("v", 0) or 0):
                bucket[iso] = b
        fetched += 1
        if args.sleep_sec > 0:
            time.sleep(float(args.sleep_sec))
        if fetched % 25 == 0:
            print(f"progress fetched_keys={fetched}/{len(pairs)}", flush=True)

    _write_merged(out_path, merged)
    print(f"OK wrote merged bars to {out_path} lines~={len(merged)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
