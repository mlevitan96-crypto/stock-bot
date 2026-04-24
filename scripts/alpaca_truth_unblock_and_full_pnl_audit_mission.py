#!/usr/bin/env python3
"""
ALPACA TRUTH + PNL AUDIT — consolidated reports only (≤5 markdown files under reports/).

Read-only on logs; optional broker/API reads. Does not modify strategy or rewrite logs.

Outputs:
  reports/ALPACA_TRUTH_WAREHOUSE_<TS>.md
  reports/ALPACA_EXECUTION_COVERAGE_<TS>.md
  reports/ALPACA_SIGNAL_CONTRIBUTION_<TS>.md
  reports/ALPACA_PNL_AUDIT_<TS>.md          (if DATA_READY)
  reports/ALPACA_BOARD_PACKET_<TS>.md       (if DATA_READY)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# ---------------------------------------------------------------------------
def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", "").strip()
    if r:
        return Path(r).resolve()
    for p in (Path("/root/trading-bot-current"), Path.cwd()):
        if (p / "logs").is_dir():
            return p.resolve()
    return Path.cwd().resolve()


def _tag() -> str:
    e = os.environ.get("ALPACA_REPORT_TAG", "").strip()
    if e:
        return e
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _parse_ts(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _stream_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(r, dict):
                    yield r
    except OSError:
        return


def _git_head(root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, timeout=8
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def _alpaca_headers() -> Optional[Dict[str, str]]:
    key = (
        os.getenv("APCA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY")
        or os.getenv("ALPACA_KEY")
    )
    sec = (
        os.getenv("APCA_API_SECRET_KEY")
        or os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("ALPACA_SECRET")
    )
    if not key or not sec:
        return None
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec}


def _alpaca_data_headers() -> Optional[Dict[str, str]]:
    # Same keys for SIP/data in most setups
    return _alpaca_headers()


def _http_get_json(url: str, headers: Dict[str, str]) -> Tuple[Any, str]:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        return json.loads(body), "OK"
    except urllib.error.HTTPError as e:
        return None, f"HTTP_{e.code}"
    except Exception as e:
        return None, str(e)


def fetch_account_activities(
    base_url: str,
    headers: Dict[str, str],
    start_date: str,
    end_date: str,
    activity_types: str,
    *,
    max_days: int = 120,
    max_pages_per_day: int = 50,
) -> List[dict]:
    """Fetch FILL (etc.) activities day-by-day — Alpaca API is most reliable with `date=YYYY-MM-DD`."""
    out: List[dict] = []
    try:
        d0 = datetime.fromisoformat(start_date[:10]).date()
        d1 = datetime.fromisoformat(end_date[:10]).date()
    except Exception:
        return out
    n_days = 0
    while d0 <= d1 and n_days < max_days:
        ds = d0.isoformat()
        page_token: Optional[str] = None
        for _ in range(max_pages_per_day):
            q: Dict[str, str] = {
                "activity_types": activity_types,
                "date": ds,
                "direction": "asc",
                "page_size": "100",
            }
            if page_token:
                q["page_token"] = page_token
            url = f"{base_url.rstrip('/')}/v2/account/activities?" + urllib.parse.urlencode(q)
            data, st = _http_get_json(url, headers)
            if st != "OK" or not isinstance(data, list):
                break
            out.extend([x for x in data if isinstance(x, dict)])
            if len(data) < 100:
                break
            page_token = data[-1].get("id")
            if not page_token:
                break
        d0 += timedelta(days=1)
        n_days += 1
    return out


def fetch_orders_rest(after_iso: str, until_iso: str, max_rows: int = 8000) -> List[dict]:
    headers = _alpaca_headers()
    if not headers:
        return []
    base = os.getenv("APCA_API_BASE_URL") or os.getenv("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets"
    try:
        from alpaca_trade_api.rest import REST  # type: ignore

        api = REST(
            key_id=headers["APCA-API-KEY-ID"],
            secret_key=headers["APCA-API-SECRET-KEY"],
            base_url=base,
            api_version="v2",
        )
        acc: List[dict] = []
        end_dt = until_iso
        while len(acc) < max_rows:
            batch = api.list_orders(status="all", after=after_iso, until=end_dt, limit=500, nested=True)
            if not batch:
                break
            for o in batch:
                if isinstance(o, dict):
                    acc.append(o)
                elif hasattr(o, "_raw"):
                    acc.append(dict(o._raw))
                else:
                    acc.append(
                        {
                            "id": getattr(o, "id", None),
                            "symbol": getattr(o, "symbol", None),
                            "filled_avg_price": getattr(o, "filled_avg_price", None),
                            "filled_qty": getattr(o, "filled_qty", None),
                            "status": getattr(o, "status", None),
                            "submitted_at": getattr(o, "submitted_at", None),
                            "filled_at": getattr(o, "filled_at", None),
                        }
                    )
            if len(batch) < 500:
                break
            last = batch[-1]
            sub = getattr(last, "submitted_at", None) or getattr(last, "created_at", None)
            if not sub:
                break
            end_dt = str(sub)
        return acc[:max_rows]
    except Exception:
        return []


def fetch_corporate_announcements(symbols: List[str], start: str, end: str) -> Tuple[List[dict], str]:
    h = _alpaca_data_headers()
    if not h:
        return [], "NO_API_KEYS"
    syms = ",".join(sorted(set(s.upper() for s in symbols if s)))[:2000]
    url = (
        "https://data.alpaca.markets/v1beta1/corporate-actions/announcements?"
        + urllib.parse.urlencode({"symbols": syms, "start": start, "end": end})
    )
    data, st = _http_get_json(url, h)
    if st != "OK":
        return [], st
    if isinstance(data, dict) and "announcements" in data:
        return list(data.get("announcements") or []), "OK"
    if isinstance(data, list):
        return data, "OK"
    return [], "UNEXPECTED_SHAPE"


def load_exits(root: Path, t0: float, t1: float) -> List[dict]:
    paths = [root / "logs" / "exit_attribution.jsonl", root / "logs" / "alpaca_exit_attribution.jsonl"]
    seen: set[str] = set()
    rows: List[dict] = []
    for p in paths:
        for r in _stream_jsonl(p):
            ts = _parse_ts(r.get("timestamp") or r.get("ts"))
            if ts is None or ts < t0 or ts > t1:
                continue
            k = f"{r.get('trade_id')}|{r.get('timestamp')}"
            if k in seen:
                continue
            seen.add(k)
            rows.append(r)
    return rows


def index_exit_snapshots(root: Path, t0: float, t1: float, cap: int = 250000) -> Tuple[Dict[Tuple[str, str], List[dict]], set]:
    """Entry-key index + set of (symbol, exit_5m_epoch) for proximity joins."""
    idx: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
    by_exit_min: set = set()
    p = root / "logs" / "signal_snapshots.jsonl"
    n = 0
    for r in _stream_jsonl(p):
        ev = (r.get("lifecycle_event") or "").upper()
        if ev not in ("EXIT_FILL", "EXIT_DECISION"):
            continue
        ts = _parse_ts(r.get("timestamp_utc") or r.get("timestamp"))
        if ts is not None and (ts < t0 or ts > t1):
            continue
        sym = (r.get("symbol") or "").upper()
        if sym and ts is not None:
            b5 = int(ts // 300) * 300
            by_exit_min.add((sym, b5))
            for k in (-1, 1, -2, 2):
                by_exit_min.add((sym, b5 + k * 300))
        ets = r.get("entry_timestamp_utc") or (r.get("exit_join_key_fields") or {}).get("entry_timestamp_utc")
        ek = norm_ts19(ets)
        if sym and ek:
            idx[(sym, ek)].append(r)
        n += 1
        if n >= cap:
            break
    return idx, by_exit_min


def index_master_trade_exit_buckets(root: Path, t0: float, t1: float, cap: int = 200000) -> set:
    """(symbol, exit_5m_epoch) from master_trade_log rows whose lifecycle mentions EXIT."""
    out: set = set()
    n = 0
    for r in _stream_jsonl(root / "logs" / "master_trade_log.jsonl"):
        ev = str(r.get("lifecycle_event") or r.get("event") or "").upper()
        if "EXIT" not in ev:
            continue
        ts = _parse_ts(r.get("timestamp_utc") or r.get("timestamp") or r.get("ts"))
        if ts is None or ts < t0 or ts > t1:
            continue
        sym = (r.get("symbol") or "").upper()
        if sym and ts is not None:
            b5 = int(ts // 300) * 300
            for k in (0, -1, 1, -2, 2):
                out.add((sym, b5 + k * 300))
        n += 1
        if n >= cap:
            break
    return out


def index_signal_context_exit(root: Path, t0: float, t1: float, cap: int = 250000) -> Dict[Tuple[str, int], List[dict]]:
    """Key (symbol, exit_ts_bucket_300s) -> rows."""
    idx: Dict[Tuple[str, int], List[dict]] = defaultdict(list)
    n = 0
    for r in _stream_jsonl(root / "logs" / "signal_context.jsonl"):
        if (r.get("decision") or "").lower() != "exit":
            continue
        ts = _parse_ts(r.get("timestamp") or r.get("ts"))
        if ts is None or ts < t0 or ts > t1:
            continue
        sym = (r.get("symbol") or "").upper()
        b = int(ts // 300) * 300
        idx[(sym, b)].append(r)
        n += 1
        if n >= cap:
            break
    return idx


def norm_ts19(v: Any) -> str:
    if not v:
        return ""
    s = str(v).strip().replace("Z", "").replace("+00:00", "").replace(" ", "T")
    if len(s) >= 19:
        return s[:19]
    return s


def entry_ts_key19(ex: dict) -> str:
    return norm_ts19(ex.get("entry_timestamp") or ex.get("entry_ts") or "")


def exit_has_side_snapshot(
    ex: dict,
    snap_idx: Dict[Tuple[str, str], List[dict]],
    snap_exit_min: set,
    master_exit_min: set,
    ctx_idx: Dict[Tuple[str, int], List[dict]],
) -> bool:
    sym = (ex.get("symbol") or "").upper()
    ek = entry_ts_key19(ex)
    if sym and ek and (sym, ek) in snap_idx:
        return True
    ts = _parse_ts(ex.get("timestamp") or ex.get("ts"))
    if ts is None:
        return False
    b5 = int(ts // 300) * 300
    if sym:
        for k in (0, -1, 1, -2, 2, -3, 3):
            sk = b5 + k * 300
            if (sym, sk) in snap_exit_min or (sym, sk) in master_exit_min:
                return True
    b = int(ts // 300) * 300
    return bool(ctx_idx.get((sym, b)))


def ref_price_exit(ex: dict) -> Optional[float]:
    fs = ex.get("feature_snapshot_at_exit")
    if isinstance(fs, dict):
        for k in ("mid", "last", "mark"):
            if fs.get(k) is not None:
                try:
                    return float(fs[k])
                except (TypeError, ValueError):
                    pass
        q = fs.get("quote")
        if isinstance(q, dict):
            try:
                b, a = float(q.get("bid") or 0), float(q.get("ask") or 0)
                if b > 0 and a > 0:
                    return (b + a) / 2.0
            except (TypeError, ValueError):
                pass
    return None


def load_orders_local(root: Path, t0: float, t1: float, cap: int = 120000) -> List[dict]:
    o: List[dict] = []
    for r in _stream_jsonl(root / "logs" / "orders.jsonl"):
        if r.get("type") != "order" and "order_id" not in r and "symbol" not in r:
            continue
        ts = _parse_ts(r.get("ts") or r.get("timestamp"))
        if ts is not None and (ts < t0 or ts > t1):
            continue
        o.append(r)
        if len(o) >= cap:
            break
    return o


def blocked_bucket_coverage(
    root: Path, t0: float, t1: float, max_compute: bool
) -> Tuple[float, int, int]:
    cap = 200000 if max_compute else 40000
    snapshots: List[dict] = []
    intents: List[dict] = []
    blocked: List[dict] = []
    for r in _stream_jsonl(root / "logs" / "score_snapshot.jsonl"):
        ts = _parse_ts(r.get("ts") or r.get("ts_iso"))
        if ts is None or ts < t0 or ts > t1:
            continue
        snapshots.append(r)
        if len(snapshots) >= cap:
            break
    for r in _stream_jsonl(root / "logs" / "run.jsonl"):
        if (r.get("event_type") or "") != "trade_intent":
            continue
        ts = _parse_ts(r.get("ts") or r.get("timestamp"))
        if ts is None or ts < t0 or ts > t1:
            continue
        intents.append(r)
        if len(intents) >= cap:
            break
    for r in _stream_jsonl(root / "state" / "blocked_trades.jsonl"):
        ts = _parse_ts(r.get("timestamp") or r.get("ts"))
        if ts is None or ts < t0 or ts > t1:
            continue
        blocked.append(r)
        if len(blocked) >= cap:
            break

    def bucket(sym: str, ts: float) -> Tuple[str, int]:
        return (sym.upper(), int(ts // 300) * 300)

    eval_b: set[Tuple[str, int]] = set()
    for s in snapshots:
        ts = _parse_ts(s.get("ts") or s.get("ts_iso"))
        sym = (s.get("symbol") or "").upper()
        if ts and sym:
            eval_b.add(bucket(sym, ts))
    for it in intents:
        ts = _parse_ts(it.get("ts") or it.get("timestamp"))
        sym = (it.get("symbol") or "").upper()
        if ts and sym:
            eval_b.add(bucket(sym, ts))

    blocked_b: set[Tuple[str, int]] = set()
    for b in blocked:
        ts = _parse_ts(b.get("timestamp") or b.get("ts"))
        sym = (b.get("symbol") or "").upper()
        if ts and sym:
            blocked_b.add(bucket(sym, ts))
    for it in intents:
        if (it.get("decision_outcome") or "").lower() != "blocked":
            continue
        ts = _parse_ts(it.get("ts") or it.get("timestamp"))
        sym = (it.get("symbol") or "").upper()
        if ts and sym:
            blocked_b.add(bucket(sym, ts))
    for s in snapshots:
        g = s.get("gates") or {}
        gated = s.get("block_reason") or any(
            not (v.get("pass") if isinstance(v, dict) else True) for v in (g.values() if isinstance(g, dict) else [])
        )
        if not gated:
            continue
        ts = _parse_ts(s.get("ts") or s.get("ts_iso"))
        sym = (s.get("symbol") or "").upper()
        if ts and sym:
            blocked_b.add(bucket(sym, ts))

    inter = len(blocked_b & eval_b)
    denom = len(eval_b)
    pct = 100.0 * inter / max(denom, 1) if denom else 0.0
    return pct, inter, denom


def uw_configured(root: Path) -> bool:
    if os.getenv("UW_FORCE_CONFIGURED", "").strip().lower() in ("1", "true", "yes"):
        return True
    p = root / "logs" / "uw_daemon.jsonl"
    return p.exists() and p.stat().st_size > 40


def _record_ts(rec: dict) -> Optional[float]:
    t = rec.get("ts")
    if isinstance(t, (int, float)):
        return float(t)
    return _parse_ts(rec.get("timestamp") or rec.get("dt"))


def uw_visible_recent(root: Path, minutes: int = 30) -> Tuple[bool, str, int, Optional[float]]:
    """
    True if at least one UW event in the last `minutes` in canonical sinks.
    Scans tail of logs/uw_daemon.jsonl and data/uw_flow_cache.log.jsonl.
    """
    cut = time.time() - minutes * 60
    paths = [root / "logs" / "uw_daemon.jsonl", root / "data" / "uw_flow_cache.log.jsonl"]
    last_any: Optional[float] = None
    count_window = 0

    def scan_file(p: Path) -> None:
        nonlocal last_any, count_window
        if not p.exists() or p.stat().st_size == 0:
            return
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return
        for line in lines[-3000:]:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(r, dict):
                continue
            tsf = _record_ts(r)
            if tsf is None:
                continue
            if tsf > (last_any or 0):
                last_any = tsf
            if tsf >= cut:
                count_window += 1

    for p in paths:
        scan_file(p)

    ok = last_any is not None and last_any >= cut and count_window >= 1
    detail = (
        f"last_event_epoch={last_any}, events_in_{minutes}m_window={count_window}, "
        f"paths_scanned={[str(p) for p in paths if p.exists()]}"
    )
    return ok, detail, count_window, last_any


def uw_coverage_pct(root: Path, t0: float, t1: float, max_compute: bool) -> float:
    cap = 100000 if max_compute else 20000
    snaps: List[dict] = []
    intents: List[dict] = []
    for r in _stream_jsonl(root / "logs" / "score_snapshot.jsonl"):
        ts = _parse_ts(r.get("ts") or r.get("ts_iso"))
        if ts is None or ts < t0 or ts > t1:
            continue
        snaps.append(r)
        if len(snaps) >= cap:
            break
    for r in _stream_jsonl(root / "logs" / "run.jsonl"):
        if (r.get("event_type") or "") != "trade_intent":
            continue
        ts = _parse_ts(r.get("ts") or r.get("timestamp"))
        if ts is None or ts < t0 or ts > t1:
            continue
        intents.append(r)
        if len(intents) >= cap:
            break
    rows = snaps + intents
    if not rows:
        return 100.0
    ok = 0
    for s in rows:
        if (
            s.get("uw_deferred") is not None
            or s.get("uw_flow_strength") is not None
            or (s.get("feature_snapshot") or {}).get("uw_flow_strength") is not None
        ):
            ok += 1
    return 100.0 * ok / len(rows)


def execution_join_pct(
    exits: List[dict],
    orders_rest: List[dict],
    activities: List[dict],
    local_orders: List[dict],
) -> Tuple[float, Counter]:
    if not exits:
        return 0.0, Counter({"no_exits": 1})
    by_oid: set[str] = set()
    for o in orders_rest:
        oid = o.get("id") or o.get("order_id")
        if oid:
            by_oid.add(str(oid))
    for a in activities:
        oid = a.get("order_id")
        if oid:
            by_oid.add(str(oid))
    # local order_id
    for r in local_orders:
        oid = r.get("order_id")
        if oid:
            by_oid.add(str(oid))
    reasons: Counter = Counter()
    ok = 0
    for ex in exits:
        md = ex.get("metadata")
        md_eid = md.get("exit_order_id") if isinstance(md, dict) else None
        eid = ex.get("exit_order_id") or ex.get("exit_orderId") or md_eid
        if eid and str(eid) in by_oid:
            ok += 1
            reasons["exit_order_id"] += 1
            continue
        sym = (ex.get("symbol") or "").upper()
        xts = _parse_ts(ex.get("timestamp") or ex.get("ts"))
        matched = False
        if xts and sym:
            for a in activities:
                if (a.get("symbol") or "").upper() != sym:
                    continue
                ats = _parse_ts(a.get("transaction_time") or a.get("date"))
                if ats and abs(ats - xts) < 900:
                    matched = True
                    break
        if matched:
            ok += 1
            reasons["activity_time_proximity"] += 1
            continue
        if xts and sym:
            for r in local_orders:
                if (r.get("symbol") or "").upper() != sym:
                    continue
                rts = _parse_ts(r.get("ts") or r.get("timestamp"))
                if rts and abs(rts - xts) < 900 and "fill" in str(r.get("action", "")).lower():
                    matched = True
                    break
        if matched:
            ok += 1
            reasons["local_order_proximity"] += 1
        else:
            reasons["no_join"] += 1
    return 100.0 * ok / len(exits), reasons


def fee_coverage_pct(orders_rest: List[dict], activities: List[dict]) -> float:
    by_oid: Dict[str, dict] = {}
    for a in activities:
        oid = a.get("order_id")
        if oid:
            by_oid[str(oid)] = a
    n = 0
    ok = 0
    for o in orders_rest:
        st = str(o.get("status") or "").lower()
        try:
            fpx = float(o.get("filled_avg_price") or 0)
        except (TypeError, ValueError):
            fpx = 0.0
        if st != "filled" and fpx <= 0:
            continue
        n += 1
        oid = str(o.get("id") or o.get("order_id") or "")
        if "commission" in o or "fees" in o:
            ok += 1
        elif o.get("legs"):
            legs = o.get("legs") or []
            if legs and all("commission" in leg for leg in legs if isinstance(leg, dict)):
                ok += 1
        elif oid and oid in by_oid:
            a = by_oid[oid]
            if a.get("commission") is not None or a.get("fee") is not None or a.get("net_amount") is not None:
                ok += 1
    if n == 0 and activities:
        for a in activities:
            if (a.get("activity_type") or a.get("type") or "").upper() != "FILL":
                continue
            n += 1
            if a.get("commission") is not None or a.get("net_amount") is not None:
                ok += 1
    return 100.0 * ok / max(n, 1) if n else 0.0


def slippage_coverage_pct(
    exits: List[dict], ctx_idx: Optional[Dict[Tuple[str, int], List[dict]]] = None
) -> float:
    if not exits:
        return 0.0
    ok = 0
    for ex in exits:
        ref = ref_price_exit(ex)
        if ref is None and ctx_idx:
            xts = _parse_ts(ex.get("timestamp") or ex.get("ts"))
            sym = (ex.get("symbol") or "").upper()
            if xts and sym:
                for delta in (0, 150, -150, 300, -300, 600, -600):
                    b = int((xts + delta) // 300) * 300
                    rows = ctx_idx.get((sym, b))
                    if rows:
                        ref = rows[0].get("mid")
                        if ref is None and isinstance(rows[0].get("signals"), dict):
                            q = rows[0]["signals"].get("quote")
                            if isinstance(q, dict):
                                try:
                                    bb, aa = float(q.get("bid") or 0), float(q.get("ask") or 0)
                                    if bb > 0 and aa > 0:
                                        ref = (bb + aa) / 2.0
                                except (TypeError, ValueError):
                                    pass
                        if ref is not None:
                            break
        ep = ex.get("exit_price")
        try:
            epf = float(ep) if ep is not None else None
        except (TypeError, ValueError):
            epf = None
        if ref is not None and epf is not None and epf > 0:
            ok += 1
    return 100.0 * ok / len(exits)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--max-compute", action="store_true")
    args = ap.parse_args()

    root = _root()
    tag = _tag()
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    t1 = time.time()
    t0 = t1 - float(args.days) * 86400.0
    start_d = datetime.fromtimestamp(t0, tz=timezone.utc).date().isoformat()
    end_d = datetime.fromtimestamp(t1, tz=timezone.utc).date().isoformat()
    after_iso = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    until_iso = datetime.fromtimestamp(t1, tz=timezone.utc).isoformat()

    paths = {
        "truth": reports / f"ALPACA_TRUTH_WAREHOUSE_{tag}.md",
        "exec": reports / f"ALPACA_EXECUTION_COVERAGE_{tag}.md",
        "sig": reports / f"ALPACA_SIGNAL_CONTRIBUTION_{tag}.md",
        "pnl": reports / f"ALPACA_PNL_AUDIT_{tag}.md",
        "board": reports / f"ALPACA_BOARD_PACKET_{tag}.md",
    }

    exits = load_exits(root, t0, t1)
    symbols = sorted({(e.get("symbol") or "").upper() for e in exits if e.get("symbol")})

    snap_idx, snap_exit_min = index_exit_snapshots(root, t0, t1, 400000 if args.max_compute else 80000)
    master_exit_min = index_master_trade_exit_buckets(root, t0, t1, 200000 if args.max_compute else 40000)
    ctx_idx = index_signal_context_exit(root, t0, t1, 400000 if args.max_compute else 80000)
    exit_snap_ok = sum(
        1 for e in exits if exit_has_side_snapshot(e, snap_idx, snap_exit_min, master_exit_min, ctx_idx)
    )
    exit_snap_pct = 100.0 * exit_snap_ok / max(len(exits), 1) if exits else 0.0

    local_orders = load_orders_local(root, t0, t1, 200000 if args.max_compute else 60000)
    orders_rest: List[dict] = []
    if os.getenv("ALPACA_TRUTH_FETCH_REST", "1").strip().lower() not in ("0", "false", "no"):
        orders_rest = fetch_orders_rest(after_iso, until_iso, 12000 if args.max_compute else 4000)

    activities: List[dict] = []
    hdrs = _alpaca_headers()
    base = os.getenv("APCA_API_BASE_URL") or os.getenv("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets"
    if hdrs and os.getenv("ALPACA_TRUTH_FETCH_ACTIVITIES", "1").strip().lower() not in ("0", "false", "no"):
        max_d = 180 if args.max_compute else 60
        activities = fetch_account_activities(
            base, hdrs, start_d, end_d, "FILL", max_days=max_d, max_pages_per_day=50
        )

    join_pct, join_reasons = execution_join_pct(exits, orders_rest, activities, local_orders)
    fee_pct = fee_coverage_pct(orders_rest, activities)
    slip_pct = slippage_coverage_pct(exits, ctx_idx)
    blocked_pct, blocked_inter, blocked_denom = blocked_bucket_coverage(root, t0, t1, args.max_compute)

    corp_ann, corp_st = fetch_corporate_announcements(symbols, start_d, end_d)
    if corp_st == "OK":
        corp_line = f"CERTIFIED: Alpaca data API returned {len(corp_ann)} announcement(s) for window {start_d}..{end_d}; symbols queried: {len(symbols)}."
        if len(corp_ann) == 0 and symbols:
            corp_status = "EXCLUDED_WITH_PROOF"
            corp_detail = (
                "EXCLUDED_WITH_PROOF: Broker corporate-actions feed returned **zero** announcements for all traded "
                f"symbols in window ({start_d}..{end_d}). Traded symbols: {', '.join(symbols[:80])}"
                + (" …" if len(symbols) > 80 else "")
                + ". PnL series treated as unadjusted for splits/dividends per this feed."
            )
        else:
            corp_status = "CERTIFIED"
            corp_detail = corp_line
    elif corp_st == "NO_API_KEYS":
        corp_status = "NOT_CERTIFIED"
        corp_detail = (
            "NOT_CERTIFIED: APCA_API_KEY_ID / APCA_API_SECRET_KEY not available to this process. "
            "Export keys (same as trading API) for data.alpaca.markets corporate-actions call, or provide manual proof."
        )
    else:
        corp_status = "NOT_CERTIFIED"
        corp_detail = f"NOT_CERTIFIED: API error `{corp_st}`."

    uw_conf = uw_configured(root)
    uw_pct = uw_coverage_pct(root, t0, t1, args.max_compute) if uw_conf else 100.0
    uw_note = (
        f"UW configured (heuristic): **{uw_conf}**. Coverage on score_snapshot+trade_intent: **{uw_pct:.2f}%**."
        if uw_conf
        else "**NOT_APPLICABLE**: uw_daemon log empty/unused for snapshot gate; see UW_VISIBLE hard gate."
    )
    uw_vis_ok, uw_vis_detail, uw_vis_n, uw_vis_last = uw_visible_recent(root, 30)

    # Root causes (concrete)
    root_causes: List[str] = []
    if join_pct < 98.0:
        root_causes.append(
            f"Execution join {join_pct:.2f}% < 98%: missing exit_order_id on exits and/or sparse FILL activities vs exit timestamps ({join_reasons})."
        )
    if fee_pct < 95.0:
        root_causes.append(
            f"Fee coverage {fee_pct:.2f}% < 95%: REST order objects often omit explicit commission field for paper; need activities+order detail join."
        )
    if slip_pct < 95.0:
        root_causes.append(
            f"Slippage coverage {slip_pct:.2f}% < 95%: feature_snapshot_at_exit.mid/quote missing on most exit_attribution rows."
        )
    if exit_snap_pct < 95.0:
        root_causes.append(
            f"Exit-side snapshot coverage {exit_snap_pct:.2f}% < 95%: signal_snapshots EXIT_FILL and/or signal_context exit rows not aligned to exits (module was missing until restored; historical gap)."
        )
    if corp_status != "CERTIFIED" and corp_status != "EXCLUDED_WITH_PROOF":
        root_causes.append(f"Corporate actions: {corp_detail}")
    if blocked_pct < 70.0:
        root_causes.append(
            f"Blocked bucket coverage {blocked_pct:.2f}% < 70%: blocked_trades + gated snapshots + blocked intents vs eval buckets ({blocked_inter}/{blocked_denom})."
        )
    if uw_conf and uw_pct < 95.0:
        root_causes.append(f"UW field coverage {uw_pct:.2f}% < 95% on evaluated rows.")
    if not uw_vis_ok:
        root_causes.append(f"UW_VISIBLE FAIL: {uw_vis_detail}")

    if not root_causes:
        root_causes.append("All hard gates satisfied; no failure root causes.")

    data_ready = (
        uw_vis_ok
        and join_pct >= 98.0
        and fee_pct >= 95.0
        and slip_pct >= 95.0
        and exit_snap_pct >= 95.0
        and corp_status in ("CERTIFIED", "EXCLUDED_WITH_PROOF")
        and blocked_pct >= 70.0
    )

    # --- ALPACA_TRUTH_WAREHOUSE ---
    tw: List[str] = [
        f"# ALPACA Truth Warehouse — `{tag}`",
        "",
        "## Metadata",
        f"- **TRADING_ROOT:** `{root}`",
        f"- **Window:** {args.days}d (UTC dates {start_d} .. {end_d})",
        f"- **git HEAD:** `{_git_head(root)}`",
        f"- **DATA_READY:** **{'YES' if data_ready else 'NO'}**",
        "",
        "## Data Surfaces (inventory)",
        f"- `logs/exit_attribution.jsonl` — exits in window: **{len(exits)}**",
        f"- `logs/signal_snapshots.jsonl` — EXIT_* entry-keys: **{sum(len(v) for v in snap_idx.values())}**; exit 5m-buckets: **{len(snap_exit_min)}**",
        f"- `logs/master_trade_log.jsonl` — EXIT* 5m-buckets (mission join aid): **{len(master_exit_min)}**",
        f"- `logs/signal_context.jsonl` — exit decisions indexed: **{sum(len(v) for v in ctx_idx.values())}** buckets",
        f"- `logs/orders.jsonl` — local rows scanned: **{len(local_orders)}**",
        f"- Alpaca REST `list_orders`: **{len(orders_rest)}** (if keys present)",
        f"- Alpaca REST activities FILL: **{len(activities)}**",
        f"- `logs/score_snapshot.jsonl`, `logs/run.jsonl`, `state/blocked_trades.jsonl` — used for blocked/UW metrics",
        "",
        "## Join Keys",
        "- **Execution:** `exit_order_id` on exit row ↔ order `id`; else FILL `activity` `transaction_time`+`symbol` ↔ exit `timestamp`; else local `orders.jsonl` fill proximity.",
        "- **Exit snapshot:** `(symbol, entry_timestamp[:19])` ↔ `signal_snapshots` `entry_timestamp_utc`; or `signal_context` exit `(symbol, 5m bucket of exit ts)`.",
        "- **Attribution:** `trade_id` / `entry_timestamp` per `src.telemetry.alpaca_trade_key` (used upstream).",
        "",
        "## Retention",
        "- JSONL append-only; mission does not trim. Window filter applied in memory only.",
        "",
        "## Root Causes of Current Failures",
        *[f"- {c}" for c in root_causes],
        "",
        "## Decision Ledger Coverage",
        f"- Executed closes in window: **{len(exits)}**",
        f"- Blocked/eval overlap buckets: **{blocked_inter}** / **{blocked_denom}** ({blocked_pct:.2f}%)",
        "- CI / gate reasons: from `trade_intent` `blocked_reason_code`, `gate_summary`, `score_snapshot.gates` (see execution report).",
        "",
        "## Blocked vs Executed Ratios",
        f"- Blocked bucket coverage vs eval universe: **{blocked_pct:.2f}%** (gate ≥70%).",
        f"- Executed exits (window): **{len(exits)}**.",
        "",
        "## Counterfactual Availability",
        "- `exit_attribution` may include shadow/paper fields in metadata; full counterfactual families still require replay harness.",
        "- MFE/MAE often in `exit_quality_metrics` / emitter snapshot when present.",
        "",
        "## STOP / Gate Status (embedded)",
        ("**ALL GATES PASS.**" if data_ready else "**FAIL-CLOSED:** one or more hard gates failed — see table below."),
        "",
        "| Gate | Value | Threshold | Pass |",
        "|------|-------|-----------|------|",
        f"| execution_join_coverage | {join_pct:.2f}% | 98% | {'YES' if join_pct >= 98 else 'NO'} |",
        f"| fee_coverage | {fee_pct:.2f}% | 95% | {'YES' if fee_pct >= 95 else 'NO'} |",
        f"| slippage_coverage | {slip_pct:.2f}% | 95% | {'YES' if slip_pct >= 95 else 'NO'} |",
        f"| exit_side_signal_snapshot | {exit_snap_pct:.2f}% | 95% | {'YES' if exit_snap_pct >= 95 else 'NO'} |",
        f"| corporate_actions | {corp_status} | CERTIFIED or EXCLUDED_WITH_PROOF | {'YES' if corp_status in ('CERTIFIED','EXCLUDED_WITH_PROOF') else 'NO'} |",
        f"| blocked_candidate_coverage | {blocked_pct:.2f}% | 70% | {'YES' if blocked_pct >= 70 else 'NO'} |",
        f"| UW_VISIBLE (30m) | {'YES' if uw_vis_ok else 'NO'} | fresh ts + ≥1 event | {'YES' if uw_vis_ok else 'NO'} |",
        f"| uw_snapshot_fields (info) | {uw_pct:.2f}% | — | — |",
        "",
        "## Manifest / reproducibility (embedded)",
        f"- Command: `python3 scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py --days {args.days} {'--max-compute' if args.max_compute else ''}`",
        f"- Env toggles: `ALPACA_TRUTH_FETCH_REST`, `ALPACA_TRUTH_FETCH_ACTIVITIES`, `ALPACA_SIGNAL_CONTEXT_EMIT`",
        "",
    ]
    paths["truth"].write_text("\n".join(tw) + "\n", encoding="utf-8")

    # --- ALPACA_EXECUTION_COVERAGE ---
    exl: List[str] = [
        f"# ALPACA Execution Coverage — `{tag}`",
        "",
        "## Chosen Approach (SRE)",
        "**Hybrid:** (1) local `logs/orders.jsonl` for proximity joins, (2) Alpaca REST `list_orders` for broker-native ids/prices/commission when keys exist, (3) `account/activities` type FILL for fill-time alignment. No strategy changes; read-only API.",
        "",
        "## Fields Captured",
        "- Orders: id, symbol, status, filled_avg_price, filled_qty, filled_at, commission (when present), legs[]",
        "- Activities FILL: symbol, qty, price, transaction_time, order_id, net_amount / commission when present",
        "",
        "## Join Coverage (overall / by symbol)",
        f"- **Overall:** {join_pct:.2f}%",
        f"- **Reasons:** `{join_reasons}`",
        "",
        "### By symbol (execution join hit rate)",
    ]
    by_sym: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for e in exits:
        sym = (e.get("symbol") or "?").upper()
        by_sym[sym][1] += 1
        jone, _ = execution_join_pct(
            [e], orders_rest, activities, local_orders
        )
        if jone >= 99.9:
            by_sym[sym][0] += 1
    for sym, (hit, tot) in sorted(by_sym.items(), key=lambda x: -x[1][1])[:40]:
        pct = 100.0 * hit / max(tot, 1)
        exl.append(f"- **{sym}:** {pct:.1f}% ({hit}/{tot})")
    exl.extend(
        [
            "",
            "## Fee Coverage",
            f"- **{fee_pct:.2f}%** of filled REST orders expose commission/fees fields (or FILL activities expose net_amount/commission).",
            "",
            "## Slippage Coverage",
            f"- **{slip_pct:.2f}%** of exits have `feature_snapshot_at_exit` ref price and `exit_price`.",
            "",
            "## Corporate Actions Status",
            corp_detail,
            "",
            "## Embedded blockers (if any)",
            ("None." if data_ready else "\n".join(f"- {c}" for c in root_causes)),
            "",
        ]
    )
    paths["exec"].write_text("\n".join(exl) + "\n", encoding="utf-8")

    # --- SIGNAL CONTRIBUTION ---
    ci_blocked = 0
    ci_ok = 0
    for r in _stream_jsonl(root / "logs" / "run.jsonl"):
        if (r.get("event_type") or "") != "trade_intent":
            continue
        ts = _parse_ts(r.get("ts") or r.get("timestamp"))
        if ts is None or ts < t0 or ts > t1:
            continue
        if (r.get("decision_outcome") or "").lower() == "blocked":
            ci_blocked += 1
            if r.get("blocked_reason_code") or r.get("gate_summary") or r.get("final_decision_primary_reason"):
                ci_ok += 1
    ci_pct = 100.0 * ci_ok / max(ci_blocked, 1) if ci_blocked else 100.0

    sig_lines: List[str] = [
        f"# ALPACA Signal + UW Contribution — `{tag}`",
        "",
        "## Signal Coverage Table",
        f"| Surface | Role | Notes |",
        f"|---------|------|-------|",
        f"| score_snapshot.jsonl | per-eval scores/gates | window-scoped |",
        f"| signal_snapshots.jsonl EXIT_* | exit-side components | join via entry_timestamp_utc |",
        f"| signal_context.jsonl | enter/exit/blocked vectors | `decision=exit` for exit gate |",
        f"| exit_attribution.jsonl | PnL + v2 exit components | signal contribution from v2_exit_components |",
        "",
        "## UW Presence & Joinability",
        uw_note,
        f"- Example: correlate `score_snapshot.uw_flow_strength` with `logs/uw_daemon.jsonl` by symbol+time (manual / follow-on script).",
        "",
        "## Contribution Analysis (Quant)",
        "- Dominant loss/profit drivers: use `v2_exit_components` and entry scores in exit rows (aggregate offline).",
        f"- Blocked intent CI code coverage (blocked outcomes): **{ci_pct:.2f}%** ({ci_ok}/{ci_blocked}).",
        "",
        "## CSA Invalidation Notes",
        "- **Lookahead:** verify `feature_snapshot_at_exit` timestamps ≤ exit fill time on a sample.",
        "- **Double-count:** activities + list_orders may overlap; joins prefer explicit order_id.",
        "- **Survivorship:** live paper universe — document selection bias when comparing to indices.",
        "- **UW staleness:** compare uw_daemon ts to decision ts (not auto-computed here).",
        "",
        "## STOP (Phase 3)",
        "**UW gate:** "
        + ("PASS (not applicable or ≥95%)." if (not uw_conf or uw_pct >= 95) else f"FAIL ({uw_pct:.2f}% < 95%)."),
        "",
    ]
    paths["sig"].write_text("\n".join(sig_lines) + "\n", encoding="utf-8")

    if data_ready:
        pnl_by: Dict[str, List[float]] = defaultdict(list)
        for ex in exits:
            sym = (ex.get("symbol") or "?").upper()
            try:
                pnl_by[sym].append(float(ex.get("pnl") or ex.get("realized_pnl_usd") or 0))
            except (TypeError, ValueError):
                pnl_by[sym].append(0.0)
        ranked = sorted(((s, sum(v), len(v)) for s, v in pnl_by.items()), key=lambda x: x[1])
        losers = ranked[:10]
        winners = ranked[-10:][::-1]
        total_pnl = sum(sum(pnl_by[s]) for s in pnl_by)

        pnl_body = [
            f"# ALPACA PnL Audit — `{tag}`",
            "",
            "## PnL Decomposition",
            f"- **Total realized (sum exit pnl fields):** {total_pnl:.4f} USD",
            "- **Gross vs net:** use broker statements for definitive net; here exit_attribution pnl is pre-broker-fee unless enriched.",
            f"- **Fees:** REST fee coverage was {fee_pct:.2f}% for this run.",
            f"- **Slippage:** computable on {slip_pct:.2f}% of exits (feature_snapshot_at_exit vs exit_price).",
            "",
            "## Profit Leakage Map",
            "- Fee drag, slippage, adverse selection on entry, exit pressure in chop — quantify with gated data above.",
            "",
            "## Top Loss Drivers (symbol)",
            "```json",
            json.dumps(losers, indent=2),
            "```",
            "",
            "## Top Profit Drivers (symbol)",
            "```json",
            json.dumps(winners, indent=2),
            "```",
            "",
            "## MFE / MAE / Giveback",
            "- Use `exit_quality_metrics` / snapshot mfe/mae when present per exit row.",
            "",
            "## Regime slices",
            "- Slice by `entry_regime` / `exit_regime` on exit rows (counts in follow-on pivot).",
            "",
            "## CI / gate counterfactuals",
            f"- Blocked intents with reason codes: {ci_blocked} in window; code coverage {ci_pct:.2f}%.",
            "",
            "## CSA Invalidation Checklist",
            "| Risk | Status |",
            "|------|--------|",
            "| Join leakage | CHECK sample order_id ↔ exit |",
            "| Lookahead ref price | CHECK timestamps |",
            "| Corp actions | " + corp_status + " |",
            "| Fee under-reporting | VERIFY broker statement |",
            "",
        ]
        paths["pnl"].write_text("\n".join(pnl_body) + "\n", encoding="utf-8")

        board_body = [
            f"# ALPACA Board Packet — `{tag}`",
            "",
            "## DATA_READY Evidence",
            f"- Join {join_pct:.2f}% | Fee {fee_pct:.2f}% | Slippage {slip_pct:.2f}% | Exit snapshot {exit_snap_pct:.2f}% | Corp {corp_status} | Blocked {blocked_pct:.2f}% | UW {uw_note}",
            "",
            "## Kill List (symbols net drag, top 10)",
            *[f"- {s}: {p:.4f} USD over {n} exits" for s, p, n in losers[:10]],
            "",
            "## Promotion Candidates (max 5)",
            *[f"- {s}: {p:.4f} USD over {n} exits" for s, p, n in winners[:5]],
            "",
            "## 7-Day Experiment Plan",
            "- Hold out top kill-list symbols paper-only.",
            "- Re-run this mission after telemetry backfill; gates must stay green 3 runs.",
            "- Ablation: exit pressure thresholds on single regime bucket.",
            "",
            "## Capital Allocation Guidance",
            "- Paper-only until sustained DATA_READY YES; no ramp while fee/slippage gates fail intermittently.",
            "",
        ]
        paths["board"].write_text("\n".join(board_body) + "\n", encoding="utf-8")

    # Mandatory end print
    print("DATA_READY:", "YES" if data_ready else "NO")
    print(f"execution_join_coverage: {join_pct:.2f}%")
    print(f"fee_coverage: {fee_pct:.2f}%")
    print(f"slippage_coverage: {slip_pct:.2f}%")
    print(f"corporate_actions_status: {corp_status}")
    print(f"blocked_candidate_coverage: {blocked_pct:.2f}%")
    print(f"uw_coverage: {uw_pct:.2f}% (configured={uw_conf})")
    print(f"exit_side_signal_snapshot_coverage: {exit_snap_pct:.2f}%")
    print("ALPACA_TRUTH_WAREHOUSE:", paths["truth"])
    print("ALPACA_EXECUTION_COVERAGE:", paths["exec"])
    print("ALPACA_SIGNAL_CONTRIBUTION:", paths["sig"])
    if data_ready:
        print("ALPACA_PNL_AUDIT:", paths["pnl"])
        print("ALPACA_BOARD_PACKET:", paths["board"])
    return 0 if data_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
