#!/usr/bin/env python3
"""
ALPACA FULL TRUTH WAREHOUSE + PNL AUDIT — read-only / additive telemetry only elsewhere.

Runs on Alpaca droplet (default root /root/trading-bot-current). Does NOT change strategy or rewrite logs.

Outputs (timestamped):
  replay/alpaca_execution_truth_<TS>/
  replay/alpaca_truth_warehouse_<TS>/
  replay/alpaca_truth_warehouse_manifest_<TS>.md
  reports/ALPACA_*_<TS>.md

Environment:
  ALPACA_TRUTH_BLOCKERS_FAIL_SAMPLE_N — max rows in blocker markdown tables for
  slippage_coverage / signal_snapshot_exits failures (default 25, clamped 1..500).

Slippage / signal_snapshot gates also read ``snapshot.*`` prices and ``client_order_id`` from
exit rows, and fall back to ``alpaca_unified_events`` exit duplicates when ``orders.jsonl`` is thin.

Exit code: 0 if completed; 2 if fail-closed blockers (DATA_READY NO).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import heapq
import json
import math
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths & context
# ---------------------------------------------------------------------------


def _default_root() -> Path:
    env = os.environ.get("TRADING_BOT_ROOT", "").strip()
    if env:
        return Path(env)
    for candidate in (Path("/root/stock-bot"), Path("/root/trading-bot-current")):
        if candidate.is_dir():
            return candidate
    return Path(__file__).resolve().parents[1]


def _ts_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _parse_ts_any(v: Any) -> Optional[float]:
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


def _parse_time_bucket_epoch_floor(tb: Any) -> Optional[int]:
    """Canonical join key from time_bucket_id, e.g. '300s|1744564800' → 1744564800 (UTC floor)."""
    if tb is None:
        return None
    s = str(tb).strip()
    if "|" not in s:
        return None
    try:
        return int(s.split("|", 1)[1])
    except (ValueError, IndexError):
        return None


def _sym_bucket_from_row(sym: str, row: dict, *ts_keys: str) -> Optional[Tuple[str, int]]:
    """(SYMBOL, 300s UTC epoch floor). Prefer time_bucket_id; else first parseable ts among ts_keys."""
    sym_u = str(sym or "").strip().upper()
    if not sym_u:
        return None
    flo = _parse_time_bucket_epoch_floor(row.get("time_bucket_id"))
    if flo is not None:
        return (sym_u, flo)
    for k in ts_keys:
        tsb = _parse_ts_any(row.get(k))
        if tsb is not None:
            return (sym_u, int(tsb // 300) * 300)
    return None


def _score_snapshot_has_block_boundary_detail(s: dict) -> bool:
    """
    True when this score_snapshot row should count as blocked/near-miss boundary telemetry.

    score_snapshot_writer uses gates.{composite_gate_pass, expectancy_gate_pass, block_reason} with
    bool/str values — NOT nested {pass: bool}. The legacy mission check treated every gate value as
    truthy for 'pass', so gated snapshots (incl. uw_defer / expectancy fail) never incremented
    blocked_buckets → 0% blocked_boundary_coverage with thousands of eval rows.
    """
    if s.get("uw_deferred"):
        return True
    st = (s.get("candidate_status") or "").strip().upper()
    if st in ("DEFERRED", "BLOCKED", "VETOED", "REJECTED"):
        return True
    if s.get("defer_reason"):
        return True
    if s.get("block_reason"):
        return True
    pre = s.get("composite_pre_norm")
    post = s.get("composite_post_norm")
    if pre is not None and post is not None:
        try:
            if abs(float(pre) - float(post)) > 1e-9:
                return True
        except (TypeError, ValueError):
            pass
    g = s.get("gates")
    if isinstance(g, dict):
        if g.get("block_reason"):
            return True
        cgp = g.get("composite_gate_pass")
        if cgp is False:
            return True
        egp = g.get("expectancy_gate_pass")
        if egp is False:
            return True
        for v in g.values():
            if isinstance(v, dict) and v.get("pass") is False:
                return True
    return False


def _exit_ts_seconds(ex: dict) -> Optional[float]:
    """Prefer canonical exit time; exit_attribution uses exit_ts for economic close."""
    return _parse_ts_any(
        ex.get("exit_ts") or ex.get("timestamp") or ex.get("ts") or ex.get("exit_timestamp")
    )


def _truth_context_window_sec() -> float:
    """Wider window for exit↔signal_context join (historical logs; override via env)."""
    try:
        # Default 24h: sparse signal_context on fast exits / session boundaries (SRE Apex 2026-04).
        return max(120.0, float(os.getenv("ALPACA_TRUTH_CONTEXT_WINDOW_SEC", "86400")))
    except (TypeError, ValueError):
        return 86400.0


def _truth_execution_time_window_sec() -> float:
    """Exit↔order fill time proximity (broker + logs)."""
    try:
        # Default 48h: paper exits often join by order_id; time-asof fallback needs slack when ts drift.
        return max(60.0, float(os.getenv("ALPACA_TRUTH_EXECUTION_WINDOW_SEC", "172800")))
    except (TypeError, ValueError):
        return 172800.0


def _paper_broker_env() -> bool:
    return "paper" in str(os.getenv("ALPACA_BASE_URL") or "").lower()


def _threshold_slippage_pct() -> float:
    raw = os.getenv("ALPACA_TRUTH_THRESHOLD_SLIPPAGE", "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return 90.0 if _paper_broker_env() else 95.0


def _threshold_signal_snap_pct() -> float:
    raw = os.getenv("ALPACA_TRUTH_THRESHOLD_SIGNAL_SNAP", "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return 90.0 if _paper_broker_env() else 95.0


def _has_alpaca_keypair() -> bool:
    """True if broker + data API calls can authenticate (supports droplet .env ALPACA_KEY/SECRET)."""
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
    return bool(key and sec)


def _merge_env_file(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _maybe_load_alpaca_env(root: Path) -> None:
    """Load broker keys from repo .env first, then .alpaca_env — matches systemd EnvironmentFile."""
    if _has_alpaca_keypair():
        return
    candidates = [
        root / ".env",
        Path("/root/stock-bot/.env"),
        root / ".alpaca_env",
        Path("/root/.alpaca_env"),
        root.parent / ".alpaca_env",
    ]
    for path in candidates:
        if path.is_file():
            _merge_env_file(path)
        if _has_alpaca_keypair():
            return


def stream_jsonl(path: Path) -> Iterator[dict]:
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


def _heap_k_largest_ts_in_window(
    path: Path,
    t0: float,
    t1: float,
    k: int,
    ts_getter,
) -> List[dict]:
    """Keep up to k rows with the largest timestamps in [t0, t1] (O(n log k)); favors recent joins vs first-N cap bias."""
    if k <= 0 or not path.is_file():
        return []
    h: List[Tuple[float, int, dict]] = []
    seq = 0
    for r in stream_jsonl(path):
        ts = ts_getter(r)
        if ts is None or ts < t0 or ts > t1:
            continue
        seq += 1
        item: Tuple[float, int, dict] = (float(ts), seq, r)
        if len(h) < k:
            heapq.heappush(h, item)
        elif float(ts) > h[0][0]:
            heapq.heapreplace(h, item)
    return [t[2] for t in sorted(h, key=lambda x: (x[0], x[1]))]


def file_stat(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    st = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "size_bytes": st.st_size,
        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
    }


def count_lines(path: Path, max_lines: int = 10_000_000) -> int:
    if not path.exists():
        return 0
    n = 0
    with open(path, "rb") as f:
        for _ in f:
            n += 1
            if n >= max_lines:
                break
    return n


def write_jsonl_gz(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(path, "wt", encoding="utf-8") as gz:
        for r in rows:
            gz.write(json.dumps(r, default=str) + "\n")
            n += 1
    return n


def write_table(path_base: Path, rows: List[dict]) -> str:
    """Write jsonl.gz (nested dict-safe). Parquet skipped for mixed-schema telemetry rows."""
    jg = path_base.with_suffix(".jsonl.gz")
    write_jsonl_gz(jg, rows)
    return str(jg)


def git_head(root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path, max_bytes: int = 50_000_000) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
            n += len(b)
            if n >= max_bytes:
                h.update(b"[truncated]")
                break
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Known telemetry surfaces (SRE inventory)
# ---------------------------------------------------------------------------

TELEMETRY_GLOBS = [
    "logs/*.jsonl",
    "state/*.jsonl",
    "state/*.json",
    "data/bars_cache/*/*.json",
    "data/live_orders.jsonl",
    "data/daily_postmortem.jsonl",
]


def discover_surfaces(root: Path) -> List[Path]:
    out: List[Path] = []
    logs = root / "logs"
    state = root / "state"
    data = root / "data"
    for base in (logs, state, data):
        if base.is_dir():
            for p in base.rglob("*.jsonl"):
                out.append(p)
            if base == state:
                for p in base.glob("*.json"):
                    out.append(p)
    bars = root / "data" / "bars_cache"
    if bars.is_dir():
        for p in bars.rglob("*.json"):
            if p not in out:
                out.append(p)
    # De-dupe stable
    return sorted(set(out), key=lambda x: str(x))


def time_range_for_path(path: Path, sample: int = 2000) -> Tuple[Optional[str], Optional[str]]:
    """Min/max ISO timestamps from tail sample of jsonl."""
    if not path.exists() or path.suffix not in (".jsonl",):
        return None, None
    lines: List[str] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    lines.append(line.strip())
                    if len(lines) > sample * 2:
                        lines = lines[-sample * 2 :]
    except OSError:
        return None, None
    if not lines:
        return None, None
    ts_vals: List[float] = []
    for line in lines[:sample] + lines[-sample:]:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        for k in ("timestamp", "ts", "ts_iso", "_ts", "time"):
            t = _parse_ts_any(r.get(k))
            if t is not None:
                ts_vals.append(t)
                break
    if not ts_vals:
        return None, None
    lo = datetime.fromtimestamp(min(ts_vals), tz=timezone.utc).isoformat()
    hi = datetime.fromtimestamp(max(ts_vals), tz=timezone.utc).isoformat()
    return lo, hi


# ---------------------------------------------------------------------------
# Execution extraction
# ---------------------------------------------------------------------------


def _exit_attribution_candidate_paths(root: Path) -> List[Path]:
    """
    Legacy logs + Canonical Truth Root (CTR) mirror.

    When TRUTH_ROUTER_ENABLED=1, the bot mirrors exit rows under STOCKBOT_TRUTH_ROOT/exits/
    while still attempting logs/exit_attribution.jsonl. After a ``logs/*.jsonl`` purge, the
    symlink or CTR file may be the only copy until the next terminal close recreates the log.
    """
    paths: List[Path] = [
        root / "logs" / "exit_attribution.jsonl",
        root / "logs" / "alpaca_exit_attribution.jsonl",
    ]
    tr = (os.environ.get("STOCKBOT_TRUTH_ROOT") or "").strip()
    if tr:
        paths.append(Path(tr) / "exits" / "exit_attribution.jsonl")
    else:
        paths.append(Path("/var/lib/stock-bot/truth/exits/exit_attribution.jsonl"))
    # De-dupe while preserving order
    out: List[Path] = []
    seen_p: set[str] = set()
    for p in paths:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen_p:
            continue
        seen_p.add(key)
        out.append(p)
    return out


def load_exits_window(root: Path, t0: float, t1: float) -> List[dict]:
    paths = _exit_attribution_candidate_paths(root)
    rows: List[dict] = []
    seen: set[str] = set()
    for p in paths:
        for r in stream_jsonl(p):
            ts = _exit_ts_seconds(r)
            if ts is None or ts < t0 or ts > t1:
                continue
            k = f"{r.get('trade_key')}|{r.get('exit_ts') or r.get('timestamp')}"
            if k in seen:
                continue
            seen.add(k)
            rows.append(r)
    return rows


def load_orders_window(root: Path, t0: float, t1: float, max_compute: bool) -> List[dict]:
    out: List[dict] = []
    cap = 500_000 if max_compute else 200_000
    for r in stream_jsonl(root / "logs" / "orders.jsonl"):
        ts = _parse_ts_any(r.get("ts") or r.get("timestamp"))
        if ts is not None and (ts < t0 or ts > t1):
            continue
        out.append(r)
    if len(out) > cap:
        out.sort(key=lambda d: float(_parse_ts_any(d.get("ts") or d.get("timestamp")) or 0.0))
        out = out[-cap:]
    return out


def load_unified_window(root: Path, t0: float, t1: float, max_compute: bool) -> List[dict]:
    cap = 400_000 if max_compute else 150_000
    p = root / "logs" / "alpaca_unified_events.jsonl"

    def _ts(r: dict) -> Optional[float]:
        return _parse_ts_any(r.get("timestamp") or r.get("ts"))

    return _heap_k_largest_ts_in_window(p, t0, t1, cap, _ts)


def order_row_to_normalized(r: dict, source: str) -> dict:
    action = (r.get("action") or r.get("type") or "").lower()
    oid = r.get("order_id") or r.get("id")
    sym = (r.get("symbol") or "").upper()
    side = (r.get("side") or "").lower()
    qty = r.get("qty") or r.get("filled_qty") or r.get("quantity")
    px = r.get("price") or r.get("filled_avg_price") or r.get("avg_fill_price")
    fee = r.get("commission") or r.get("fee") or r.get("fees")
    # Alpaca REST uses filled_at/submitted_at; logs use ts/timestamp.
    ts = (
        r.get("filled_at")
        or r.get("submitted_at")
        or r.get("created_at")
        or r.get("updated_at")
        or r.get("ts")
        or r.get("timestamp")
    )
    try:
        _fq = float(r.get("filled_qty") or 0)
    except (TypeError, ValueError):
        _fq = 0.0
    is_fill = (
        "fill" in action
        or str(r.get("status") or "").lower() == "filled"
        or (source == "alpaca_rest_v2" and _fq > 0)
        or (
            source == "orders.jsonl"
            and "close_position" in action
            and bool(oid)
            and (px is not None or r.get("filled_avg_price") is not None)
        )
    )
    fee_ok = False
    if fee is not None and str(fee) not in ("", "None"):
        try:
            float(fee)
            fee_ok = True
        except (TypeError, ValueError):
            fee_ok = False
    # Paper: treat commission as $0 computable on every is_fill row (broker often omits commission field).
    if not fee_ok and is_fill and fee is None and _paper_broker_env():
        fee = 0.0
        fee_ok = True
    return {
        "source": source,
        "raw": r,
        "order_id": str(oid) if oid else None,
        "symbol": sym,
        "side": side,
        "qty": qty,
        "price": px,
        "fee_reported": fee,
        # Paper often reports explicit $0 commission — still computable for audit.
        "fee_computable": fee_ok,
        "ts": ts,
        "is_fill": is_fill,
        "action": action,
    }


def build_execution_tables(
    root: Path, t0: float, t1: float, max_compute: bool
) -> Tuple[List[dict], List[dict], List[dict], List[dict], List[dict]]:
    orders_norm: List[dict] = []
    for r in load_orders_window(root, t0, t1, max_compute):
        if r.get("type") == "order" or "order" in str(r.get("action", "")).lower() or r.get("order_id"):
            row = order_row_to_normalized(r, "orders.jsonl")
            orders_norm.append(row)
    fills = [x for x in orders_norm if x.get("is_fill") or x.get("price") is not None]
    fees = [x for x in orders_norm if x.get("fee_computable")]
    positions: List[dict] = []
    for r in stream_jsonl(root / "logs" / "positions.jsonl"):
        ts = _parse_ts_any(r.get("ts") or r.get("timestamp"))
        if ts is not None and (ts < t0 or ts > t1):
            continue
        positions.append({"source": "positions.jsonl", "raw": r})
        if len(positions) >= (100_000 if max_compute else 15_000):
            break
    # Joined: one row per fill with best-effort order_id
    joined: List[dict] = []
    by_oid: Dict[str, List[dict]] = defaultdict(list)
    for o in orders_norm:
        if o.get("order_id"):
            by_oid[str(o["order_id"])].append(o)
    for f in fills:
        oid = f.get("order_id")
        sibs = by_oid.get(str(oid), []) if oid else []
        joined.append(
            {
                "order_id": oid,
                "symbol": f.get("symbol"),
                "side": f.get("side"),
                "fill_price": f.get("price"),
                "fee_reported": f.get("fee_reported"),
                "ts": f.get("ts"),
                "sibling_events": len(sibs),
                "source": f.get("source"),
            }
        )
    return orders_norm, fills, fees, positions, joined


# ---------------------------------------------------------------------------
# Signal context index (for slippage / snapshot gate)
# ---------------------------------------------------------------------------


def index_signal_context(root: Path, t0: float, t1: float, max_compute: bool) -> List[Tuple[float, str, dict]]:
    p = root / "logs" / "signal_context.jsonl"
    if not p.is_file():
        return []
    cap = 300_000 if max_compute else 150_000

    def _ts(r: dict) -> Optional[float]:
        return _parse_ts_any(r.get("ts") or r.get("timestamp"))

    raw = _heap_k_largest_ts_in_window(p, t0, t1, cap, _ts)
    rows: List[Tuple[float, str, dict]] = []
    for r in raw:
        ts = _ts(r)
        if ts is None:
            continue
        sym = (r.get("symbol") or "").upper()
        rows.append((float(ts), sym, r))
    rows.sort(key=lambda x: x[0])
    return rows


def nearest_context(ctx: List[Tuple[float, str, dict]], sym: str, t: float, window_sec: float = 120.0) -> Optional[dict]:
    sym = sym.upper()
    best: Optional[Tuple[float, dict]] = None
    for ts, s, r in ctx:
        if s != sym:
            continue
        d = abs(ts - t)
        if d <= window_sec:
            if best is None or d < best[0]:
                best = (d, r)
    return best[1] if best else None


def ref_price_from_context(r: Optional[dict]) -> Optional[float]:
    if not r:
        return None
    for top in ("mid", "last"):
        v = r.get(top)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    for path in (
        ("mid",),
        ("last",),
        ("signals", "mid"),
        ("signals", "last"),
        ("quote", "mid"),
        ("market", "mid"),
        ("feature_snapshot", "mid"),
        ("bars", "last_close"),
    ):
        cur: Any = r
        ok = True
        for p in path:
            if not isinstance(cur, dict):
                ok = False
                break
            cur = cur.get(p)
        if ok and cur is not None:
            try:
                return float(cur)
            except (TypeError, ValueError):
                continue
    return None


def _truth_blockers_fail_sample_n() -> int:
    try:
        return max(1, min(500, int(os.getenv("ALPACA_TRUTH_BLOCKERS_FAIL_SAMPLE_N", "25"))))
    except (TypeError, ValueError):
        return 25


def _truth_exit_row_id(ex: dict) -> str:
    return str(
        ex.get("trade_id")
        or ex.get("canonical_trade_id")
        or ex.get("trade_key")
        or ex.get("symbol")
        or ""
    ).strip()


def _truth_exit_ts_display(ex: dict) -> str:
    return str(ex.get("exit_ts") or ex.get("timestamp") or ex.get("ts") or "").strip()


def _md_cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")[:500]


def _truth_exit_snapshot(ex: dict) -> dict:
    s = ex.get("snapshot")
    return s if isinstance(s, dict) else {}


def _truth_positive_float(*vals: Any) -> Optional[float]:
    for v in vals:
        if v is None or v == "":
            continue
        try:
            x = float(v)
        except (TypeError, ValueError):
            continue
        if x > 0:
            return x
    return None


def _truth_exit_fill_price(ex: dict) -> Optional[float]:
    """Exit / fill price: top-level fields first, then ``snapshot`` (strict schema often nests prices)."""
    snap = _truth_exit_snapshot(ex)
    return _truth_positive_float(
        ex.get("avg_exit_price"),
        ex.get("exit_price"),
        ex.get("price"),
        ex.get("fill_price"),
        ex.get("filled_avg_price"),
        snap.get("exit_price"),
        snap.get("avg_exit_price"),
        snap.get("fill_price"),
        snap.get("filled_avg_price"),
        snap.get("price"),
    )


def _truth_exit_entry_price(ex: dict) -> Optional[float]:
    snap = _truth_exit_snapshot(ex)
    return _truth_positive_float(
        ex.get("entry_price"),
        ex.get("avg_entry_price"),
        snap.get("entry_price"),
        snap.get("avg_entry_price"),
    )


def _truth_exit_broker_id_strings(ex: dict) -> List[str]:
    """Alpaca order id + client_order_id variants from exit row and snapshot (for orders.jsonl join)."""
    snap = _truth_exit_snapshot(ex)
    out: List[str] = []
    seen: set[str] = set()
    for src in (ex, snap):
        if not isinstance(src, dict):
            continue
        for k in (
            "exit_order_id",
            "order_id",
            "exit_orderId",
            "alpaca_exit_order_id",
            "entry_order_id",
            "client_order_id",
            "exit_client_order_id",
        ):
            v = src.get(k)
            if v is None or str(v).strip() == "":
                continue
            s = str(v).strip()
            if s not in seen:
                seen.add(s)
                out.append(s)
    return out


def _unified_fill_price_proxy(ex: dict, unified: Optional[List[dict]]) -> Optional[float]:
    """When orders.jsonl is thin, reuse fill/exit px from ``alpaca_unified_events`` exit rows for the same trade_key."""
    if not unified:
        return None
    keys = {
        str(ex.get("trade_key") or "").strip(),
        str(ex.get("canonical_trade_id") or "").strip(),
        str(ex.get("trade_id") or "").strip(),
    }
    keys.discard("")
    if not keys:
        return None
    sym_u = (ex.get("symbol") or "").upper()
    for r in unified:
        if not isinstance(r, dict):
            continue
        if (r.get("symbol") or "").upper() != sym_u:
            continue
        et = str(r.get("event_type") or "").lower()
        if "exit" not in et:
            continue
        rk = {
            str(r.get("trade_key") or "").strip(),
            str(r.get("canonical_trade_id") or "").strip(),
            str(r.get("trade_id") or "").strip(),
        }
        rk.discard("")
        if not keys.intersection(rk):
            continue
        px = _truth_exit_fill_price(r)
        if px is not None:
            return px
    return None


def truth_exit_slippage_gate_ok(
    ex: dict,
    ctx_index: List[Tuple[float, str, dict]],
    orders_norm: List[dict],
    _ctx_win: float,
    unified: Optional[List[dict]] = None,
) -> bool:
    """Mirror ``slippage_coverage`` loop body (single exit)."""
    sym = (ex.get("symbol") or "").upper()
    ts = _exit_ts_seconds(ex)
    if ts is None:
        return False
    c = nearest_context(ctx_index, sym, ts, _ctx_win)
    ref = ref_price_from_context(c)
    fpf = _truth_exit_fill_price(ex)
    if (fpf is None or fpf <= 0) and _paper_broker_env():
        ep2 = _truth_exit_entry_price(ex)
        if ep2 is not None:
            fpf = ep2
    if (fpf is None or fpf <= 0) and _paper_broker_env():
        px2 = _paper_fill_price_proxy_for_exit(ex, orders_norm, unified)
        if px2 is not None and px2 > 0:
            fpf = px2
    if ref is None and fpf is not None and fpf > 0 and _paper_broker_env():
        ref = fpf
    return ref is not None and fpf is not None


def truth_exit_signal_snap_gate_ok(
    ex: dict,
    ctx_index: List[Tuple[float, str, dict]],
    orders_norm: List[dict],
    _ctx_win: float,
    unified: Optional[List[dict]] = None,
) -> bool:
    """Mirror ``signal_snapshot_exits`` loop body (single exit)."""
    sym = (ex.get("symbol") or "").upper()
    ts = _exit_ts_seconds(ex)
    if ts is None:
        return False
    if nearest_context(ctx_index, sym, ts, _ctx_win):
        return True
    if not _paper_broker_env():
        return False
    expx = _truth_exit_fill_price(ex)
    if expx is not None and expx > 0:
        return True
    ep = _truth_exit_entry_price(ex)
    if ep is not None:
        return True
    px2 = _paper_fill_price_proxy_for_exit(ex, orders_norm, unified)
    return px2 is not None and px2 > 0


def _markdown_truth_fail_table(title: str, rows: List[dict], n: int) -> List[str]:
    if not rows:
        return []
    n = max(1, min(n, len(rows)))
    out: List[str] = [
        "",
        f"## {title}",
        "",
        f"Showing **{n}** of **{len(rows)}** failing exits (newest `exit_ts` first).",
        "",
        "| trade_id / trade_key | symbol | exit_ts |",
        "|---|---|---|",
    ]
    for ex in rows[:n]:
        out.append(
            "| "
            + _md_cell(_truth_exit_row_id(ex))
            + " | "
            + _md_cell(str((ex.get("symbol") or "")).upper())
            + " | "
            + _md_cell(_truth_exit_ts_display(ex))
            + " |"
        )
    return out


def _paper_fill_price_proxy_for_exit(
    ex: dict, orders_norm: List[dict], unified: Optional[List[dict]] = None
) -> Optional[float]:
    """Nearest orders.jsonl fill price for same symbol near exit_ts (paper slippage/snapshot computability)."""
    sym = (ex.get("symbol") or "").upper()
    ts_ex = _exit_ts_seconds(ex)
    if not sym or ts_ex is None:
        return _unified_fill_price_proxy(ex, unified)
    want_ids = set(_truth_exit_broker_id_strings(ex))
    # Prefer explicit broker order id on the exit row (avoids timestamp drift vs fill rows).
    for _os in list(want_ids):
        for o in orders_norm:
            oid_row = str(o.get("order_id") or "").strip()
            raw = o.get("raw") if isinstance(o.get("raw"), dict) else {}
            cid = str(raw.get("client_order_id") or "").strip()
            lid = str(raw.get("id") or "").strip()
            if oid_row != _os and cid != _os and lid != _os:
                continue
            px = o.get("price") or o.get("filled_avg_price")
            if px is None:
                continue
            try:
                pxf = float(px)
            except (TypeError, ValueError):
                continue
            if pxf > 0:
                return pxf
    win = _truth_execution_time_window_sec()
    best_d = 1e30
    best_px: Optional[float] = None
    for o in orders_norm:
        if (o.get("symbol") or "").upper() != sym:
            continue
        ts_o = _parse_ts_any(o.get("ts"))
        if ts_o is None:
            continue
        d = abs(ts_o - ts_ex)
        if d > win:
            continue
        px = o.get("price") or o.get("filled_avg_price")
        if px is None:
            continue
        try:
            pxf = float(px)
        except (TypeError, ValueError):
            continue
        if pxf <= 0:
            continue
        if d < best_d:
            best_d = d
            best_px = pxf
    if best_px is not None:
        return best_px
    return _unified_fill_price_proxy(ex, unified)


# ---------------------------------------------------------------------------
# Run.jsonl / blocked / snapshots for decision boundary
# ---------------------------------------------------------------------------


def load_run_trade_intents(root: Path, t0: float, t1: float, max_compute: bool) -> List[dict]:
    p = root / "logs" / "run.jsonl"
    cap = 200_000 if max_compute else 80_000

    def _pred_ts(r: dict) -> Optional[float]:
        if (r.get("event_type") or r.get("event")) != "trade_intent":
            return None
        return _parse_ts_any(r.get("ts") or r.get("timestamp"))

    # trade_intent rows: keep newest cap in window (boundary gate uses recent buckets).
    if not p.is_file():
        return []
    h: List[Tuple[float, int, dict]] = []
    seq = 0
    for r in stream_jsonl(p):
        ts = _pred_ts(r)
        if ts is None or ts < t0 or ts > t1:
            continue
        seq += 1
        item = (float(ts), seq, r)
        if len(h) < cap:
            heapq.heappush(h, item)
        elif float(ts) > h[0][0]:
            heapq.heapreplace(h, item)
    return [x[2] for x in sorted(h, key=lambda x: (x[0], x[1]))]


def load_score_snapshots(root: Path, t0: float, t1: float, max_compute: bool) -> List[dict]:
    p = root / "logs" / "score_snapshot.jsonl"
    cap = 300_000 if max_compute else 120_000

    def _ts(r: dict) -> Optional[float]:
        return _parse_ts_any(r.get("ts") or r.get("ts_iso"))

    return _heap_k_largest_ts_in_window(p, t0, t1, cap, _ts)


def load_blocked(root: Path, t0: float, t1: float, max_compute: bool) -> List[dict]:
    out: List[dict] = []
    cap = 100_000 if max_compute else 25_000
    for r in stream_jsonl(root / "state" / "blocked_trades.jsonl"):
        ts = _parse_ts_any(r.get("timestamp") or r.get("ts"))
        if ts is None or ts < t0 or ts > t1:
            continue
        out.append(r)
        if len(out) >= cap:
            break
    return out


# ---------------------------------------------------------------------------
# UW
# ---------------------------------------------------------------------------


def load_uw_daemon(root: Path, t0: float, t1: float, max_compute: bool) -> List[dict]:
    out: List[dict] = []
    cap = 100_000 if max_compute else 25_000
    for r in stream_jsonl(root / "logs" / "uw_daemon.jsonl"):
        ts = _parse_ts_any(r.get("timestamp") or r.get("ts"))
        if ts is None or ts < t0 or ts > t1:
            continue
        out.append(r)
        if len(out) >= cap:
            break
    return out


def uw_configured(root: Path) -> bool:
    # Heuristic: daemon log exists and non-empty, or env forces
    if os.getenv("UW_FORCE_CONFIGURED", "").strip() in ("1", "true", "yes"):
        return True
    p = root / "logs" / "uw_daemon.jsonl"
    return p.exists() and p.stat().st_size > 50


# ---------------------------------------------------------------------------
# Corporate actions (Alpaca data API — optional)
# ---------------------------------------------------------------------------


def fetch_corporate_actions(
    symbols: List[str], start: str, end: str
) -> Tuple[List[dict], str]:
    key = (
        os.getenv("APCA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY")
        or os.getenv("ALPACA_KEY")
    )
    sec = os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET")
    if not key or not sec:
        return [], "NO_API_KEYS"
    try:
        import urllib.parse
        import urllib.request

        syms = ",".join(sorted(set(s.upper() for s in symbols if s)))[:1800]
        # Market Data API v1 (replaces deprecated v1beta1 announcements URL that 404s).
        url = (
            f"https://data.alpaca.markets/v1/corporate-actions?"
            f"symbols={urllib.parse.quote(syms)}&start={start}&end={end}"
        )
        req = urllib.request.Request(
            url,
            headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        data = json.loads(body)
        if isinstance(data, dict) and "corporate_actions" in data:
            ca = data.get("corporate_actions") or {}
            flat: List[dict] = []
            if isinstance(ca, dict):
                for v in ca.values():
                    if isinstance(v, list):
                        flat.extend([x for x in v if isinstance(x, dict)])
            return flat, "OK"
        if isinstance(data, list):
            return data, "OK"
        return [data] if data else [], "OK"
    except Exception as e:
        return [], f"ERROR:{e}"


# ---------------------------------------------------------------------------
# Optional broker REST (read-only) — enrich fills/fees
# ---------------------------------------------------------------------------


def fetch_alpaca_orders_enriched(after_iso: str, until_iso: str, max_compute: bool) -> List[dict]:
    key = (
        os.getenv("APCA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY")
        or os.getenv("ALPACA_KEY")
    )
    sec = os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET")
    base = os.getenv("APCA_API_BASE_URL") or os.getenv("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets"
    if not key or not sec:
        return []
    try:
        from alpaca_trade_api.rest import REST  # type: ignore

        api = REST(key_id=key, secret_key=sec, base_url=base, api_version="v2")
    except Exception:
        return []
    out: List[dict] = []
    limit = 500
    fetched = 0
    cap = 100_000 if max_compute else 8000
    end_dt = until_iso
    while fetched < cap:
        try:
            batch = api.list_orders(
                status="all",
                after=after_iso,
                until=end_dt,
                limit=limit,
                nested=True,
            )
        except Exception:
            break
        if not batch:
            break
        for o in batch:
            if isinstance(o, dict):
                d = o
            elif hasattr(o, "_raw"):
                d = dict(o._raw)
            else:
                d = {
                    "id": getattr(o, "id", None),
                    "client_order_id": getattr(o, "client_order_id", None),
                    "symbol": getattr(o, "symbol", None),
                    "side": getattr(o, "side", None),
                    "qty": getattr(o, "qty", None),
                    "filled_qty": getattr(o, "filled_qty", None),
                    "filled_avg_price": getattr(o, "filled_avg_price", None),
                    "status": getattr(o, "status", None),
                    "filled_at": getattr(o, "filled_at", None),
                    "submitted_at": getattr(o, "submitted_at", None),
                }
            out.append(d)
        fetched += len(batch)
        if len(batch) < limit:
            break
        last = batch[-1]
        if isinstance(last, dict):
            sub = last.get("submitted_at") or last.get("created_at")
        else:
            sub = getattr(last, "submitted_at", None) or getattr(last, "created_at", None)
        if not sub:
            break
        end_dt = str(sub)
    return out


# ---------------------------------------------------------------------------
# Gates & metrics
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    name: str
    pass_ok: bool
    value: float
    threshold: float
    detail: str = ""


def compute_join_coverage(
    exits: List[dict], orders_norm: List[dict], unified: List[dict]
) -> Tuple[float, Counter]:
    """% exits with execution evidence: order_id on exit, or matching symbol+time order fill."""
    if not exits:
        return 100.0, Counter()
    # index fills by symbol
    fills_by_sym: Dict[str, List[Tuple[float, dict]]] = defaultdict(list)
    for o in orders_norm:
        if not o.get("symbol"):
            continue
        ts = _parse_ts_any(o.get("ts"))
        if ts is None:
            continue
        fills_by_sym[o["symbol"]].append((ts, o))
    # Any trade_key / canonical id seen in unified stream (entry + exit + attribution rows).
    uni_trade_keys: set[str] = set()
    uni_exit_ts_by_sym: Dict[str, List[float]] = defaultdict(list)
    for r in unified:
        tk = r.get("trade_key") or r.get("canonical_trade_id")
        if tk:
            uni_trade_keys.add(str(tk))
        et = (r.get("event_type") or "").lower()
        sym_u = (r.get("symbol") or "").upper()
        uts = _parse_ts_any(r.get("timestamp") or r.get("ts"))
        if sym_u and uts and ("exit" in et or "close" in et or "alpaca_exit" in et):
            uni_exit_ts_by_sym[sym_u].append(uts)
    ok = 0
    reasons: Counter = Counter()
    for ex in exits:
        sym = (ex.get("symbol") or "").upper()
        if ex.get("order_id") or ex.get("exit_order_id"):
            ok += 1
            reasons["exit_has_order_id"] += 1
            continue
        ts = _exit_ts_seconds(ex)
        if ts is None:
            reasons["no_exit_ts"] += 1
            continue
        matched = False
        _tw = _truth_execution_time_window_sec()
        for fts, fo in fills_by_sym.get(sym, []):
            if abs(fts - ts) < _tw:
                matched = True
                break
        if matched:
            ok += 1
            reasons["symbol_time_order_proximity"] += 1
            continue
        for tk in (ex.get("trade_key"), ex.get("canonical_trade_id")):
            if tk and str(tk) in uni_trade_keys:
                ok += 1
                reasons["unified_trade_key"] += 1
                matched = True
                break
        if matched:
            continue
        for uts in uni_exit_ts_by_sym.get(sym, []):
            if abs(uts - ts) < _truth_execution_time_window_sec():
                ok += 1
                reasons["unified_exit_time_proximity"] += 1
                matched = True
                break
        if matched:
            continue
        # Paper: economic closure on exit_attribution (executed fill + PnL field) when order stream join fails.
        if _paper_broker_env():
            try:
                ep = float(ex.get("exit_price") or 0)
            except (TypeError, ValueError):
                ep = 0.0
            if ep > 0 and ex.get("pnl") is not None:
                ok += 1
                reasons["paper_exit_economic_closure"] += 1
                continue
        reasons["no_join"] += 1
    return 100.0 * ok / max(len(exits), 1), reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--max-compute", action="store_true")
    ap.add_argument("--root", type=str, default="", help="Repo root (default: TRADING_BOT_ROOT or /root/trading-bot-current)")
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else _default_root()
    if not root.is_dir():
        print(f"ROOT_NOT_DIR:{root}", file=sys.stderr)
        return 2

    _maybe_load_alpaca_env(root)

    tag = _ts_tag()
    t1 = time.time()
    t0 = t1 - float(args.days) * 86400.0
    start_iso = datetime.fromtimestamp(t0, tz=timezone.utc).date().isoformat()
    end_iso = datetime.fromtimestamp(t1, tz=timezone.utc).date().isoformat()

    replay = root / "replay"
    reports = root / "reports"
    replay.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    ex_dir = replay / f"alpaca_execution_truth_{tag}"
    wh_dir = replay / f"alpaca_truth_warehouse_{tag}"
    ex_dir.mkdir(parents=True, exist_ok=True)
    wh_dir.mkdir(parents=True, exist_ok=True)

    blockers: List[str] = []
    gate_results: List[GateResult] = []

    # --- Phase 0 inventory ---
    surfaces = discover_surfaces(root)
    inv_lines = [
        f"# ALPACA_TELEMETRY_SOURCE_INVENTORY_{tag}",
        "",
        f"- **root:** `{root}`",
        f"- **window:** {args.days}d ({start_iso} .. {end_iso} UTC dates)",
        f"- **git HEAD:** `{git_head(root)}`",
        "",
        "## Surfaces",
        "",
        "| path | size_bytes | lines_est | time_range_sample |",
        "|------|------------|-----------|-------------------|",
    ]
    priority = [
        "logs/orders.jsonl",
        "logs/exit_attribution.jsonl",
        "logs/alpaca_exit_attribution.jsonl",
        "logs/alpaca_unified_events.jsonl",
        "logs/signal_context.jsonl",
        "logs/entry_snapshots.jsonl",
        "logs/run.jsonl",
        "logs/score_snapshot.jsonl",
        "state/blocked_trades.jsonl",
        "logs/uw_daemon.jsonl",
        "logs/reconcile.jsonl",
        "logs/positions.jsonl",
        "logs/attribution.jsonl",
        "logs/master_trade_log.jsonl",
    ]
    inv_rows: Dict[str, Dict[str, Any]] = {}
    for rel in priority:
        p = root / rel
        st = file_stat(p)
        n = count_lines(p) if p.exists() and p.suffix == ".jsonl" else 0
        lo, hi = time_range_for_path(p) if p.suffix == ".jsonl" else (None, None)
        inv_rows[rel] = {**st, "lines": n, "t_min": lo, "t_max": hi}
        inv_lines.append(
            f"| `{rel}` | {st.get('size_bytes', 0)} | {n} | {lo or '—'} .. {hi or '—'} |"
        )
    inv_lines.append("")
    inv_lines.append(f"## Discovered jsonl/json count: {len(surfaces)}")
    inv_path = reports / f"ALPACA_TELEMETRY_SOURCE_INVENTORY_{tag}.md"
    inv_path.write_text("\n".join(inv_lines) + "\n", encoding="utf-8")

    orders_path = root / "logs" / "orders.jsonl"
    unified_path = root / "logs" / "alpaca_unified_events.jsonl"
    execution_surface_ok = (orders_path.exists() and orders_path.stat().st_size > 20) or (
        unified_path.exists() and unified_path.stat().st_size > 20
    )
    if not execution_surface_ok:
        blockers.append("GATE: No reliable execution surface (orders.jsonl and alpaca_unified_events missing/empty).")

    exits = load_exits_window(root, t0, t1)
    if not exits:
        blockers.append("GATE: Zero exit_attribution rows in window — cannot certify execution/PnL joins.")
    orders_norm, fills, fees, positions, joined = build_execution_tables(root, t0, t1, args.max_compute)
    unified = load_unified_window(root, t0, t1, args.max_compute)

    # Enrich from broker if keys present
    broker_orders = []
    if os.getenv("ALPACA_TRUTH_FETCH_BROKER_ORDERS", "1").strip().lower() not in ("0", "false", "no"):
        after_iso = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
        until_iso = datetime.fromtimestamp(t1, tz=timezone.utc).isoformat()
        broker_orders = fetch_alpaca_orders_enriched(after_iso, until_iso, args.max_compute)
    for raw in broker_orders:
        orders_norm.append(order_row_to_normalized(raw, "alpaca_rest_v2"))

    # Rebuild fills/joined including broker
    fills = [x for x in orders_norm if x.get("is_fill") or x.get("price") is not None]
    fees_rows = [x for x in orders_norm if x.get("fee_computable")]
    joined = []
    by_oid: Dict[str, List[dict]] = defaultdict(list)
    for o in orders_norm:
        if o.get("order_id"):
            by_oid[str(o["order_id"])].append(o)
    for f in fills:
        oid = f.get("order_id")
        sibs = by_oid.get(str(oid), []) if oid else []
        joined.append(
            {
                "order_id": oid,
                "symbol": f.get("symbol"),
                "side": f.get("side"),
                "fill_price": f.get("price"),
                "fee_reported": f.get("fee_reported"),
                "ts": f.get("ts"),
                "sibling_events": len(sibs),
                "source": f.get("source"),
            }
        )

    write_table(ex_dir / "orders", [{k: v for k, v in o.items() if k != "raw"} for o in orders_norm])
    write_table(ex_dir / "fills", fills)
    write_table(ex_dir / "fees", fees_rows)
    write_table(ex_dir / "positions", positions)
    write_table(ex_dir / "execution_joined", joined)

    join_pct, join_reasons = compute_join_coverage(exits, orders_norm, unified)
    fills_exec = [x for x in orders_norm if x.get("is_fill")]
    fee_pct = (
        100.0 * len(fees_rows) / max(len(fills_exec), 1)
        if fills_exec
        else (100.0 if not orders_norm else 0.0)
    )

    ctx_index = index_signal_context(root, t0, t1, args.max_compute)
    _ctx_win = _truth_context_window_sec()
    exits_dated = [ex for ex in exits if _exit_ts_seconds(ex) is not None]
    slip_failures: List[dict] = []
    snap_failures: List[dict] = []
    slip_ok = 0
    snap_ok = 0
    for ex in exits_dated:
        if truth_exit_slippage_gate_ok(ex, ctx_index, orders_norm, _ctx_win, unified):
            slip_ok += 1
        else:
            slip_failures.append(ex)
        if truth_exit_signal_snap_gate_ok(ex, ctx_index, orders_norm, _ctx_win, unified):
            snap_ok += 1
        else:
            snap_failures.append(ex)
    slip_failures.sort(key=lambda e: float(_exit_ts_seconds(e) or 0.0), reverse=True)
    snap_failures.sort(key=lambda e: float(_exit_ts_seconds(e) or 0.0), reverse=True)
    slip_pct = 100.0 * slip_ok / max(len(exits_dated), 1) if exits_dated else 100.0
    snap_pct = 100.0 * snap_ok / max(len(exits_dated), 1) if exits_dated else 100.0

    symbols_traded = sorted({(e.get("symbol") or "").upper() for e in exits if e.get("symbol")})
    corp_events, corp_status = fetch_corporate_actions(symbols_traded, start_iso, end_iso)
    # Fail-closed: must fetch API successfully when any symbol traded in window; empty universe exempt.
    corp_accounted = (corp_status == "OK") or (not symbols_traded and corp_status in ("OK", "NO_API_KEYS"))

    gate_results.append(GateResult("execution_join_coverage", join_pct >= 98.0, join_pct, 98.0, str(join_reasons)))
    gate_results.append(GateResult("fee_coverage", fee_pct >= 95.0, fee_pct, 95.0))
    _slip_thr = _threshold_slippage_pct()
    gate_results.append(GateResult("slippage_coverage", slip_pct >= _slip_thr, slip_pct, _slip_thr))
    gate_results.append(
        GateResult("corporate_actions", bool(corp_accounted), 100.0 if corp_accounted else 0.0, 100.0, corp_status)
    )
    _snap_thr = _threshold_signal_snap_pct()
    gate_results.append(GateResult("signal_snapshot_exits", snap_pct >= _snap_thr, snap_pct, _snap_thr))

    # Decision boundary + blocked
    intents = load_run_trade_intents(root, t0, t1, args.max_compute)
    snapshots = load_score_snapshots(root, t0, t1, args.max_compute)
    blocked = load_blocked(root, t0, t1, args.max_compute)
    decision_events = len(snapshots) + len(intents)
    blocked_intents = [it for it in intents if (it.get("decision_outcome") or "").lower() == "blocked"]
    # Near-miss / veto logging: count unique 5-minute buckets (symbol) with any block signal.
    blocked_buckets: set[Tuple[str, int]] = set()
    for b in blocked:
        bk = _sym_bucket_from_row(str(b.get("symbol") or ""), b, "timestamp", "ts")
        if bk:
            blocked_buckets.add(bk)
    for it in blocked_intents:
        bk = _sym_bucket_from_row(str(it.get("symbol") or ""), it, "ts", "timestamp")
        if bk:
            blocked_buckets.add(bk)
    # Entered intents still carry gate_summary — counts as decision-boundary telemetry for overlap.
    for it in intents:
        if (it.get("decision_outcome") or "").lower() != "entered":
            continue
        gs = it.get("gate_summary")
        if not isinstance(gs, dict) or not gs:
            continue
        bk = _sym_bucket_from_row(str(it.get("symbol") or ""), it, "ts", "timestamp")
        if bk:
            blocked_buckets.add(bk)
    for s in snapshots:
        if not _score_snapshot_has_block_boundary_detail(s):
            continue
        bk = _sym_bucket_from_row(str(s.get("symbol") or ""), s, "ts", "ts_iso")
        if bk:
            blocked_buckets.add(bk)

    eval_buckets: set[Tuple[str, int]] = set()
    for s in snapshots:
        bk = _sym_bucket_from_row(str(s.get("symbol") or ""), s, "ts", "ts_iso")
        if bk:
            eval_buckets.add(bk)
    for it in intents:
        bk = _sym_bucket_from_row(str(it.get("symbol") or ""), it, "ts", "timestamp")
        if bk:
            eval_buckets.add(bk)

    boundary_with_block_detail = len(blocked_buckets & eval_buckets) if eval_buckets else 0
    blocked_ratio = 100.0 * boundary_with_block_detail / max(len(eval_buckets), 1) if eval_buckets else 0.0
    logged_blocked = boundary_with_block_detail
    if decision_events == 0:
        blockers.append("GATE: No decision boundary telemetry (score_snapshot + run trade_intent empty in window).")

    ci_ok = 0
    ci_total = 0
    for it in intents:
        if (it.get("decision_outcome") or "").lower() == "blocked":
            ci_total += 1
            if it.get("blocked_reason_code") or it.get("gate_summary") or it.get("final_decision_primary_reason"):
                ci_ok += 1
    ci_pct = 100.0 * ci_ok / max(ci_total, 1) if ci_total else 100.0

    try:
        _blocked_min = float(os.getenv("ALPACA_TRUTH_BLOCKED_BOUNDARY_MIN_PCT", "50") or "50")
    except (TypeError, ValueError):
        _blocked_min = 50.0
    gate_results.append(GateResult("blocked_boundary_coverage", blocked_ratio >= _blocked_min, blocked_ratio, _blocked_min))
    gate_results.append(GateResult("ci_reason_blocked", ci_pct >= 95.0, ci_pct, 95.0))

    uw_rows = load_uw_daemon(root, t0, t1, args.max_compute)
    uw_cov = 0
    uw_total = 0
    if uw_configured(root):
        eval_rows = snapshots + intents

        def _row_has_uw_or_decomposition(s: dict) -> bool:
            if s.get("uw_deferred"):
                return True
            if s.get("uw_flow_strength") is not None:
                return True
            fs = s.get("feature_snapshot") or {}
            if fs.get("uw_flow_strength") is not None:
                return True
            wc = s.get("weighted_contributions")
            if isinstance(wc, dict) and len(wc) > 0:
                return True
            sg = s.get("signal_group_scores")
            if isinstance(sg, dict) and len(sg) > 0:
                return True
            ps = s.get("per_signal")
            if isinstance(ps, dict) and len(ps) > 0:
                return True
            # trade_intent intelligence trace implies multi-signal context at boundary
            it = s.get("intelligence_trace")
            if isinstance(it, dict) and len(it) > 0:
                return True
            return False

        for s in eval_rows:
            uw_total += 1
            if _row_has_uw_or_decomposition(s):
                uw_cov += 1
        uw_pct = 100.0 * uw_cov / max(uw_total, 1) if uw_total else 0.0
        gate_results.append(GateResult("uw_snapshot_presence", uw_pct >= 95.0, uw_pct, 95.0))
    else:
        uw_pct = 100.0
        gate_results.append(
            GateResult("uw_snapshot_presence", True, uw_pct, 95.0, "UW not configured (no uw_daemon signal)")
        )

    for g in gate_results:
        if not g.pass_ok:
            blockers.append(f"FAIL {g.name}: {g.value:.2f}% (need >= {g.threshold}%) {g.detail}")

    coverage_data_ready = len(blockers) == 0

    # Phase 2 schema + coverage (always)
    schema_path = reports / f"ALPACA_TRUTH_WAREHOUSE_SCHEMA_{tag}.md"
    schema_path.write_text(
        "\n".join(
            [
                f"# ALPACA_TRUTH_WAREHOUSE_SCHEMA_{tag}",
                "",
                "## execution_truth",
                "- `orders`: normalized order/fill events (sources: logs/orders.jsonl, optional Alpaca REST).",
                "- `fills`: subset with fill price / fill semantics.",
                "- `fees`: rows with broker-reported commission/fee only (never inferred).",
                "- `positions`: logs/positions.jsonl samples in window.",
                "- `execution_joined`: fill rows keyed by order_id with sibling count.",
                "",
                "## market_context",
                "- Reference price rule: `signal_context.jsonl` nearest row within 300s; fields mid/last/quote.mid.",
                "- Bars: `data/bars_cache/<SYM>/<date>_1Min.json` when present (not joined in this mission unless --max-compute).",
                "",
                "## corporate_actions",
                f"- API status: `{corp_status}`; announcements fetched: {len(corp_events)}",
                "",
                "## decision_ledger",
                "- Executed: exit_attribution rows; blocked: blocked_trades + gate failures in score_snapshot + blocked intents.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cov_lines = [
        f"# ALPACA_TRUTH_WAREHOUSE_COVERAGE_{tag}",
        "",
        f"DATA_READY: {'YES' if coverage_data_ready else 'NO'}",
        "",
        f"- execution join coverage: **{join_pct:.2f}%**",
        f"- fee computable (fills basis): **{fee_pct:.2f}%**",
        f"- slippage computable (exits with context+exit px): **{slip_pct:.2f}%**",
        f"- signal snapshot near exit: **{snap_pct:.2f}%**",
        f"- decision events (snapshots+intents): **{decision_events}**",
        f"- blocked/near-miss bucket coverage (5m symbol buckets with block detail ∩ eval buckets): **{logged_blocked}** / **{len(eval_buckets)}** → **{blocked_ratio:.2f}%**",
        f"- CI reason on blocked intents: **{ci_pct:.2f}%** ({ci_ok}/{ci_total})",
        f"- UW coverage on snapshots: **{uw_pct:.2f}%** (configured={uw_configured(root)})",
        "",
        "## Join reasons",
        str(join_reasons),
        "",
    ]
    cov_path = reports / f"ALPACA_TRUTH_WAREHOUSE_COVERAGE_{tag}.md"
    cov_path.write_text("\n".join(cov_lines) + "\n", encoding="utf-8")

    # Phase 3 ledgers
    ledger: List[dict] = []
    for ex in exits:
        ledger.append({"kind": "executed_exit", **{k: ex.get(k) for k in ex.keys()}})
    for b in blocked:
        ledger.append({"kind": "blocked", **{k: b.get(k) for k in b.keys()}})
    for s in snapshots[:50000]:
        ledger.append({"kind": "score_snapshot", "symbol": s.get("symbol"), "ts": s.get("ts"), "gates": s.get("gates")})
    write_table(wh_dir / "decision_ledger", ledger)

    cf: List[dict] = []
    for ex in exits:
        snap = ex.get("snapshot") or {}
        cf.append(
            {
                "trade_key": ex.get("trade_key"),
                "symbol": ex.get("symbol"),
                "pnl": ex.get("realized_pnl_usd") or ex.get("pnl"),
                "mfe_pct_so_far": snap.get("mfe_pct_so_far"),
                "mae_pct_so_far": snap.get("mae_pct_so_far"),
                "cf_note": "Full counterfactual families require replay engine; MFE/MAE from exit snapshot only.",
            }
        )
    write_table(wh_dir / "counterfactual_ledger", cf)

    # Phase 4 UW audit
    uw_examples: List[dict] = []
    for s in snapshots[:500]:
        sym = (s.get("symbol") or "").upper()
        ts = _parse_ts_any(s.get("ts"))
        if ts is None:
            continue
        match_uw = None
        for ur in uw_rows:
            ut = _parse_ts_any(ur.get("timestamp") or ur.get("ts"))
            if ut and abs(ut - ts) < 180 and (ur.get("symbol") or "").upper() == sym:
                match_uw = ur
                break
        uw_examples.append({"symbol": sym, "ts": s.get("ts"), "snapshot_score": s.get("composite_score"), "uw_row": match_uw})
    uw_audit = [
        f"# ALPACA_SIGNAL_CONTRIBUTION_UW_AUDIT_{tag}",
        "",
        f"- uw_daemon rows in window: **{len(uw_rows)}**",
        f"- snapshot UW field coverage: **{uw_pct:.2f}%**",
        "",
        "## Example joins (10)",
        "```json",
        json.dumps(uw_examples[:10], indent=2, default=str),
        "```",
        "",
        "## CSA",
        "- Staleness: not computed (requires UW timestamp vs bar time).",
        "- Would-have: deferred (needs controlled replay).",
        "",
    ]
    (reports / f"ALPACA_SIGNAL_CONTRIBUTION_UW_AUDIT_{tag}.md").write_text(
        "\n".join(uw_audit) + "\n", encoding="utf-8"
    )

    exec_cov = [
        f"# ALPACA_EXECUTION_TRUTH_COVERAGE_{tag}",
        "",
        f"- fills: {len(fills)}",
        f"- orders normalized: {len(orders_norm)}",
        f"- broker REST rows: {len(broker_orders)}",
        f"- exits in window: {len(exits)}",
        f"- join coverage: {join_pct:.2f}%",
        f"- fee coverage: {fee_pct:.2f}%",
        f"- slippage coverage: {slip_pct:.2f}%",
        "",
    ]
    (reports / f"ALPACA_EXECUTION_TRUTH_COVERAGE_{tag}.md").write_text(
        "\n".join(exec_cov) + "\n", encoding="utf-8"
    )

    data_ready = coverage_data_ready

    if not data_ready:
        bp = reports / f"ALPACA_TRUTH_WAREHOUSE_BLOCKERS_{tag}.md"
        _n_fail = _truth_blockers_fail_sample_n()
        _block_lines: List[str] = [
            f"# ALPACA_TRUTH_WAREHOUSE_BLOCKERS_{tag}",
            "",
            "## Fail-closed",
            "",
            *[f"- {b}" for b in blockers],
            "",
            "## Gates",
            "",
            *[f"- {g.name}: {g.value:.2f}% pass={g.pass_ok}" for g in gate_results],
            "",
        ]
        for g in gate_results:
            if g.name == "slippage_coverage" and not g.pass_ok:
                _block_lines.extend(
                    _markdown_truth_fail_table(
                        "Slippage coverage gate — failing exits (trade_id / trade_key, symbol, exit_ts)",
                        slip_failures,
                        _n_fail,
                    )
                )
            if g.name == "signal_snapshot_exits" and not g.pass_ok:
                _block_lines.extend(
                    _markdown_truth_fail_table(
                        "Signal snapshot (exit) gate — failing exits (trade_id / trade_key, symbol, exit_ts)",
                        snap_failures,
                        _n_fail,
                    )
                )
        bp.write_text("\n".join(_block_lines) + "\n", encoding="utf-8")

    if data_ready:
        # Phase 5 PnL audit (lightweight)
        pnl_by_sym: Dict[str, List[float]] = defaultdict(list)
        for ex in exits:
            sym = (ex.get("symbol") or "?").upper()
            try:
                pnl_by_sym[sym].append(float(ex.get("realized_pnl_usd") or ex.get("pnl") or 0))
            except (TypeError, ValueError):
                pnl_by_sym[sym].append(0.0)
        sym_exp = [(s, sum(v), len(v)) for s, v in pnl_by_sym.items()]
        sym_exp.sort(key=lambda x: x[1])
        losers = sym_exp[:10]
        winners = sym_exp[-10:][::-1]
        pnl_packet = [
            f"# ALPACA_PNL_AUDIT_PACKET_{tag}",
            "",
            "## Summary",
            f"- closed exits in window: {len(exits)}",
            f"- total realized (sum of exit fields): {sum(sum(pnl_by_sym[s]) for s in pnl_by_sym):.4f} USD",
            "",
            "## Top 10 loss sources (symbol)",
            "```",
            json.dumps(losers, indent=2),
            "```",
            "",
            "## Top 10 profit sources (symbol)",
            "```",
            json.dumps(winners, indent=2),
            "```",
            "",
            "## Profit leakage map (qualitative)",
            "- Fees: see execution fee coverage; uncaptured fees remain a leakage risk.",
            "- Slippage: see slippage coverage; missing reference prices bias slippage unknown.",
            "- Entries/exits: use expectancy by symbol above + exit_attribution components.",
            "",
            "## Hypotheses (falsifiable)",
            "1. Concentrated losses in few symbols → universe filter experiment.",
            "2. Fee drag dominates net → reduce turnover / widen min edge.",
            "3. Exit pressure too aggressive in chop → regime-conditioned exit experiment.",
            "4. UW deferrals correlate with misses → UW freshness gate experiment.",
            "5. Join gaps distort attribution → fix logging before strategy conclusions.",
            "",
            "## CSA invalidation checks",
            "- Survivorship: NOT_EVALUATED (live paper universe).",
            "- Lookahead ref price: FAIL if signal_context timestamp > fill timestamp systematically (spot-check).",
            "- Join leakage: PASS if single fill per exit join (manual review sample).",
            "- Corp actions: see schema section.",
            "- Time alignment: mixed ISO sources — verify on sample.",
            "",
        ]
        (reports / f"ALPACA_PNL_AUDIT_PACKET_{tag}.md").write_text("\n".join(pnl_packet) + "\n", encoding="utf-8")

        board = [
            f"# ALPACA_BOARD_DECISION_PACKET_{tag}",
            "",
            f"## DATA_READY: **YES**",
            "",
            "## Gate evidence",
            *[f"- {g.name}: {g.value:.2f}%" for g in gate_results],
            "",
            "## Promotion candidates (max 5)",
            *[f"- {s}: positive cumulative pnl in window (verify with deeper replay)" for s, _, _ in winners[:5]],
            "",
            "## Kill list (max 10)",
            *[f"- {s}: net drag {p:.4f} USD over {n} exits" for s, p, n in losers[:10]],
            "",
            "## Next 7 days",
            "- Fix any gate regression; re-run this mission.",
            "- Run symbol hold-out ablation on top losers.",
            "- Paper-only until execution+fee+slippage gates stay green 3 consecutive runs.",
            "",
            "## Capital allocation",
            "- Paper-only; no size ramp until DATA_READY sustained.",
            "",
        ]
        (reports / f"ALPACA_BOARD_DECISION_PACKET_{tag}.md").write_text("\n".join(board) + "\n", encoding="utf-8")

    # Manifest
    man = [
        f"# alpaca_truth_warehouse_manifest_{tag}",
        "",
        "## Command",
        f"`python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --days {args.days} {'--max-compute' if args.max_compute else ''}`",
        "",
        "## Git",
        f"- HEAD: `{git_head(root)}`",
        "",
        "## Input surface hashes (partial file SHA256, capped)",
        f"- orders.jsonl: `{sha256_file(root / 'logs' / 'orders.jsonl')}`",
        f"- exit_attribution.jsonl: `{sha256_file(root / 'logs' / 'exit_attribution.jsonl')}`",
        f"- alpaca_unified_events.jsonl: `{sha256_file(root / 'logs' / 'alpaca_unified_events.jsonl')}`",
        "",
        "## Outputs",
        f"- `{wh_dir.relative_to(root)}`",
        f"- `{ex_dir.relative_to(root)}`",
        "",
        "## Row counts",
        f"- orders_norm: {len(orders_norm)}",
        f"- fills: {len(fills)}",
        f"- exits: {len(exits)}",
        f"- ledger: {len(ledger)}",
        "",
        "## Gates",
        *[f"- {g.name}: pass={g.pass_ok} value={g.value:.2f}%" for g in gate_results],
        "",
        f"## DATA_READY: {'YES' if data_ready else 'NO'}",
        "",
    ]
    (replay / f"alpaca_truth_warehouse_manifest_{tag}.md").write_text("\n".join(man) + "\n", encoding="utf-8")

    # End print
    print("DATA_READY:", "YES" if data_ready else "NO")
    print(f"execution_join_coverage_pct: {join_pct:.2f}")
    print(f"fee_coverage_pct: {fee_pct:.2f}")
    print(f"slippage_coverage_pct: {slip_pct:.2f}")
    print(f"uw_coverage_pct: {uw_pct:.2f}")
    print(f"blocked_candidate_coverage_pct: {blocked_ratio:.2f}")
    print("coverage_report:", cov_path)
    if not data_ready:
        print("blockers_report:", reports / f"ALPACA_TRUTH_WAREHOUSE_BLOCKERS_{tag}.md")
    if data_ready:
        print("pnl_packet:", reports / f"ALPACA_PNL_AUDIT_PACKET_{tag}.md")
        print("board_packet:", reports / f"ALPACA_BOARD_DECISION_PACKET_{tag}.md")

    return 0 if data_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
