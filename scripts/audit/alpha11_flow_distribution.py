#!/usr/bin/env python3
"""
Alpha 11 flow-strength distribution + blocked shadow expectancy (Operation Apex — Q / Data).

Reads the last N ``trade_intent`` rows from ``logs/run.jsonl`` (strict-chain entry decisions:
entered + blocked). ``trade_intent`` is the persisted entry-intent record; there is no
separate ``entry_intent`` event type in this repo.

Bins ``flow_strength`` (UW) into operator buckets, then for **blocked** intents with bars
(local jsonl or ``--fetch-bars-live`` via Alpaca REST) computes shadow path metrics at 60m
(variant A from ``run_blocked_why_pipeline`` — first bar at/after intent time, bar closes).

Usage:
  PYTHONPATH=. python3 scripts/audit/alpha11_flow_distribution.py --root /root/stock-bot
  PYTHONPATH=. python3 scripts/audit/alpha11_flow_distribution.py --root /root/stock-bot --fetch-bars-live
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_blocked_why_module():
    path = REPO_ROOT / "scripts" / "audit" / "run_blocked_why_pipeline.py"
    spec = importlib.util.spec_from_file_location("blocked_why_mod", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _iter_jsonl(path: Path):
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


def _deep_scan_flow_strength(obj: Any, depth: int = 0) -> Optional[float]:
    """Bounded DFS for ``flow_strength`` / ``uw_flow_strength`` / ``conviction`` in nested telemetry."""
    if depth > 10 or obj is None:
        return None
    if isinstance(obj, dict):
        for key in ("flow_strength", "uw_flow_strength", "conviction"):
            if key not in obj:
                continue
            v = obj.get(key)
            if v is None or isinstance(v, (dict, list)):
                continue
            try:
                f = float(v)
                if math.isfinite(f):
                    return f
            except (TypeError, ValueError):
                continue
        for v in obj.values():
            r = _deep_scan_flow_strength(v, depth + 1)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _deep_scan_flow_strength(v, depth + 1)
            if r is not None:
                return r
    return None


def _from_composite_meta(cm: Any) -> Optional[float]:
    if not isinstance(cm, dict):
        return None
    uw = cm.get("v2_uw_inputs")
    if not isinstance(uw, dict):
        return None
    for k in ("flow_strength", "conviction"):
        v = uw.get(k)
        if v is None:
            continue
        try:
            f = float(v)
            if math.isfinite(f):
                return f
        except (TypeError, ValueError):
            continue
    return None


def _parse_ts_any(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def _load_alpha11_blocked_flow_index(root: Path) -> List[Tuple[str, float, float]]:
    """(symbol, ts_epoch, flow_strength) for rows blocked specifically by Alpha 11."""
    out: List[Tuple[str, float, float]] = []
    p = root / "state" / "blocked_trades.jsonl"
    for r in _iter_jsonl(p):
        if str(r.get("reason") or r.get("block_reason") or "") != "alpha11_flow_strength_below_gate":
            continue
        fs = _from_composite_meta(r.get("composite_meta"))
        if fs is None:
            continue
        sym = str(r.get("symbol") or "").upper().strip()
        ts = _parse_ts_any(r.get("timestamp") or r.get("ts"))
        if not sym or ts is None:
            continue
        out.append((sym, float(ts), float(fs)))
    out.sort(key=lambda x: x[1])
    return out


def _nearest_blocked_fs(sym: str, t: float, idx: List[Tuple[str, float, float]], max_dt: float = 300.0) -> Optional[float]:
    best: Optional[Tuple[float, float]] = None
    for s, ts, fs in idx:
        if s != sym:
            continue
        d = abs(ts - t)
        if d > max_dt:
            continue
        if best is None or d < best[0]:
            best = (d, fs)
    return best[1] if best else None


def _flow_strength_from_intent(rec: dict) -> Optional[float]:
    """Prefer top-level ``alpha11_flow_strength`` from ``_emit_trade_intent``; then legacy joins."""
    try:
        _top = rec.get("alpha11_flow_strength")
        if _top is not None and str(_top).strip() != "":
            f = float(_top)
            if math.isfinite(f):
                return f
    except (TypeError, ValueError):
        pass
    fs: Optional[float] = None

    def _from_uw(uw: Any) -> Optional[float]:
        if not isinstance(uw, dict):
            return None
        for k in ("flow_strength", "conviction"):
            v = uw.get(k)
            if v is None:
                continue
            try:
                f = float(v)
                if math.isfinite(f):
                    return f
            except (TypeError, ValueError):
                continue
        return None

    cm = rec.get("composite_meta")
    if isinstance(cm, dict):
        fs = _from_composite_meta(cm) or _from_uw(cm.get("v2_uw_inputs"))
    cr = rec.get("composite_result")
    if fs is None and isinstance(cr, dict):
        fs = _from_uw(cr.get("v2_uw_inputs"))
    snap = rec.get("feature_snapshot")
    if fs is None and isinstance(snap, dict):
        for k in ("uw_flow_strength", "flow_strength", "conviction"):
            v = snap.get(k)
            if v is not None:
                try:
                    f = float(v)
                    if math.isfinite(f):
                        fs = f
                        break
                except (TypeError, ValueError):
                    continue
        if fs is None and isinstance(snap.get("v2_uw_inputs"), dict):
            fs = _from_uw(snap.get("v2_uw_inputs"))
    if fs is None:
        fs = _deep_scan_flow_strength(rec.get("feature_snapshot"))
    if fs is None:
        fs = _deep_scan_flow_strength(rec.get("intelligence_trace"))
    if fs is None:
        fs = _deep_scan_flow_strength(rec.get("blocked_reason_details"))
    return fs


def _flow_bin(fs: Optional[float]) -> str:
    if fs is None or not math.isfinite(fs):
        return "missing_flow_telemetry"
    if fs >= 0.99:
        return "d1_0.99_1.00"
    if fs >= 0.95:
        return "d2_0.95_0.989"
    if fs >= 0.90:
        return "d3_0.90_0.949"
    return "d4_lt_0.90"


def _last_trade_intents(path: Path, n: int) -> List[dict]:
    buf: List[dict] = []
    for r in _iter_jsonl(path):
        if (r.get("event_type") or r.get("event")) != "trade_intent":
            continue
        buf.append(r)
        if len(buf) > max(n * 4, n + 5000):
            buf = buf[-(n * 2) :]
    return buf[-n:] if len(buf) >= n else buf


def _norm_side(row: Dict[str, Any]) -> str:
    for k in ("side", "direction"):
        x = str(row.get(k) or "").lower()
        if x in ("long", "buy", "bull", "bullish"):
            return "long"
        if x in ("short", "sell", "bear", "bearish"):
            return "short"
    return "unknown"


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


def _maybe_load_dotenv(root: Path) -> None:
    for p in (root / ".env", Path("/root/stock-bot/.env"), root / ".alpaca_env"):
        if p.is_file():
            _merge_env_file(p)


def _alpaca_rest_client():
    try:
        key = (
            os.getenv("APCA_API_KEY_ID")
            or os.getenv("ALPACA_API_KEY_ID")
            or os.getenv("ALPACA_API_KEY")
            or os.getenv("ALPACA_KEY")
        )
        secret = (
            os.getenv("APCA_API_SECRET_KEY")
            or os.getenv("ALPACA_SECRET_KEY")
            or os.getenv("ALPACA_SECRET")
        )
        base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        if not key or not secret:
            return None
        from alpaca_trade_api import REST  # type: ignore

        return REST(key, secret, base_url=base)
    except Exception:
        return None


def _fetch_live_1m_bars(api: Any, symbol: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    """1-minute bars inclusive window; ``t`` is aware UTC datetime (blocked_why contract)."""
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    else:
        start = start.astimezone(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    else:
        end = end.astimezone(timezone.utc)
    start_s = start.isoformat().replace("+00:00", "Z")
    end_s = end.isoformat().replace("+00:00", "Z")
    try:
        resp = api.get_bars(str(symbol).upper(), "1Min", start=start_s, end=end_s, limit=5000)
    except Exception:
        return []
    df = getattr(resp, "df", None)
    if df is None or len(df) == 0:
        return []
    out: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        t = idx
        if hasattr(t, "to_pydatetime"):
            t = t.to_pydatetime()
        if isinstance(t, datetime):
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            else:
                t = t.astimezone(timezone.utc)
        else:
            continue
        try:
            _g = row.get if hasattr(row, "get") else lambda k, d=None: row[k] if k in row else d  # type: ignore[index]
            o = float(_g("open", _g("o", 0)))
            h = float(_g("high", _g("h", 0)))
            l = float(_g("low", _g("l", 0)))
            c = float(_g("close", _g("c", 0)))
            v = int(_g("volume", _g("v", 0)) or 0)
        except (TypeError, ValueError, KeyError):
            continue
        out.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})
    out.sort(key=lambda b: b["t"])
    return out


def _build_live_bars_index(
    root: Path,
    blocked_rows: List[Tuple[dict, str, datetime, str]],
    delay_sec: float,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    One REST window per symbol covering all blocked intents' [ts, ts+60m] (plus slack).
    ``blocked_rows``: (rec, symbol, ts_dt, flow_bin).
    """
    _maybe_load_dotenv(root)
    api = _alpaca_rest_client()
    if api is None:
        print("ERROR: --fetch-bars-live requires Alpaca API keys in environment.", file=sys.stderr)
        return {}
    by_sym: Dict[str, List[datetime]] = defaultdict(list)
    for _, sym, ts, _ in blocked_rows:
        by_sym[sym].append(ts)
    out: Dict[str, List[Dict[str, Any]]] = {}
    for sym, ts_list in by_sym.items():
        t0 = min(ts_list)
        t1 = max(ts_list) + timedelta(seconds=3600 + 120)
        time.sleep(max(0.0, float(delay_sec)))
        bars = _fetch_live_1m_bars(api, sym, t0, t1)
        if bars:
            out[sym] = bars
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpha11 flow distribution + blocked shadow expectancy.")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--n", type=int, default=1000, help="Last N trade_intent rows (default 1000).")
    ap.add_argument(
        "--bars",
        type=Path,
        default=None,
        help="Alpaca bars jsonl (default: <root>/artifacts/market_data/alpaca_bars.jsonl). Ignored with --fetch-bars-live.",
    )
    ap.add_argument(
        "--fetch-bars-live",
        action="store_true",
        help="Fetch 1m bars via Alpaca REST per symbol (no local artifacts jsonl).",
    )
    ap.add_argument(
        "--live-fetch-delay-sec",
        type=float,
        default=0.12,
        help="Sleep between per-symbol REST calls when --fetch-bars-live (default 0.12).",
    )
    ap.add_argument("--notional-usd", type=float, default=500.0, help="Sizing for shadow USD PnL.")
    ap.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Write JSON summary (default: reports/audit/alpha11_flow_distribution.json).",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    run_path = root / "logs" / "run.jsonl"
    bars_path = args.bars or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")

    bwp = _load_blocked_why_module()
    a11_idx = _load_alpha11_blocked_flow_index(root)

    intents = _last_trade_intents(run_path, max(1, int(args.n)))
    if not intents:
        print("No trade_intent rows found.", file=sys.stderr)
        return 1

    counts_all: Dict[str, int] = defaultdict(int)
    counts_blocked: Dict[str, int] = defaultdict(int)
    shadow_pnl60: Dict[str, List[float]] = defaultdict(list)
    shadow_mfe60: Dict[str, List[float]] = defaultdict(list)
    shadow_mae60: Dict[str, List[float]] = defaultdict(list)
    shadow_miss: Dict[str, int] = defaultdict(int)

    staged_blocked: List[Tuple[dict, str, datetime, str]] = []

    for rec in intents:
        fs = _flow_strength_from_intent(rec)
        if fs is None and str(rec.get("decision_outcome", "")).lower() == "blocked":
            br = str(rec.get("blocked_reason") or rec.get("final_decision_primary_reason") or "")
            if "alpha11" in br.lower() or "flow_strength" in br.lower():
                t_i = _parse_ts_any(rec.get("ts") or rec.get("timestamp"))
                sym = str(rec.get("symbol") or "").upper().strip()
                if t_i is not None and sym:
                    fs = _nearest_blocked_fs(sym, float(t_i), a11_idx)
        b = _flow_bin(fs)
        counts_all[b] += 1
        if str(rec.get("decision_outcome", "")).lower() != "blocked":
            continue
        counts_blocked[b] += 1
        sym = str(rec.get("symbol") or "").upper().strip()
        ts = bwp._parse_ts(rec.get("ts") or rec.get("timestamp"))
        if not sym or ts is None:
            shadow_miss[b] += 1
            continue
        staged_blocked.append((rec, sym, ts, b))

    bars_by_sym: Dict[str, List[Dict[str, Any]]] = {}
    if args.fetch_bars_live:
        bars_by_sym = _build_live_bars_index(root, staged_blocked, float(args.live_fetch_delay_sec))
        if not bars_by_sym and staged_blocked:
            return 2
    else:
        bars_by_sym = bwp.load_bars(bars_path)

    for rec, sym, ts, b in staged_blocked:
        side = _norm_side(rec)
        if side == "unknown":
            shadow_miss[b] += 1
            continue
        bsym = bars_by_sym.get(sym) or []
        if not bsym:
            shadow_miss[b] += 1
            continue
        px_hint = rec.get("feature_snapshot") or {}
        dp = None
        if isinstance(px_hint, dict):
            for k in ("last", "mid", "close", "last_price"):
                v = px_hint.get(k)
                if v is not None:
                    try:
                        dp = float(v)
                        break
                    except (TypeError, ValueError):
                        continue
        qty = bwp._qty_shares(dp, float(args.notional_usd))
        out, skips = bwp.compute_variant_pnls(bsym, ts, side, qty)
        va = out.get("variant_a") or {}
        p60 = va.get("pnl_60m")
        mfe_a = out.get("mfe_usd_proxy_a") or {}
        mae_a = out.get("mae_usd_proxy_a") or {}
        m60 = mfe_a.get("pnl_60m")
        a60 = mae_a.get("pnl_60m")
        if p60 is not None and isinstance(p60, (int, float)) and math.isfinite(float(p60)):
            shadow_pnl60[b].append(float(p60))
            if m60 is not None and isinstance(m60, (int, float)) and math.isfinite(float(m60)):
                shadow_mfe60[b].append(float(m60))
            if a60 is not None and isinstance(a60, (int, float)) and math.isfinite(float(a60)):
                shadow_mae60[b].append(float(a60))
        else:
            shadow_miss[b] += 1

    rows_out: List[Dict[str, Any]] = []
    bin_order = ("d1_0.99_1.00", "d2_0.95_0.989", "d3_0.90_0.949", "d4_lt_0.90", "missing_flow_telemetry")
    for lab in bin_order:
        pnls = shadow_pnl60.get(lab) or []
        mfes = shadow_mfe60.get(lab) or []
        maes = shadow_mae60.get(lab) or []
        n_all = int(counts_all.get(lab, 0))
        n_blk = int(counts_blocked.get(lab, 0))
        exp_pct = (100.0 * (sum(pnls) / len(pnls)) / float(args.notional_usd)) if pnls else None
        rows_out.append(
            {
                "bin": lab,
                "intents_total": n_all,
                "intents_blocked": n_blk,
                "blocked_shadow_n_scored": len(pnls),
                "blocked_shadow_n_miss_bars": int(shadow_miss.get(lab, 0)),
                "blocked_shadow_expectancy_pct_notional_60m": round(exp_pct, 4) if exp_pct is not None else None,
                "blocked_shadow_mean_usd_pnl_60m": round(sum(pnls) / len(pnls), 4) if pnls else None,
                "blocked_shadow_sum_usd_pnl_60m": round(sum(pnls), 4) if pnls else None,
                "blocked_shadow_mean_mfe_usd_60m": round(sum(mfes) / len(mfes), 4) if mfes else None,
                "blocked_shadow_mean_mae_usd_60m": round(sum(maes) / len(maes), 4) if maes else None,
            }
        )

    n_blk_total = sum(int(counts_blocked.get(lab, 0)) for lab in bin_order)
    below_gate = int(counts_blocked.get("d2_0.95_0.989", 0)) + int(counts_blocked.get("d3_0.90_0.949", 0)) + int(
        counts_blocked.get("d4_lt_0.90", 0)
    )
    d3_pnls = shadow_pnl60.get("d3_0.90_0.949") or []
    d3_total = round(sum(d3_pnls), 4) if d3_pnls else None
    d3_mean_pct = (
        (100.0 * (sum(d3_pnls) / len(d3_pnls)) / float(args.notional_usd)) if d3_pnls else None
    )
    gate_floor = 0.985
    verdict = (
        f"Among last {len(intents)} trade_intents, {n_blk_total} blocked. "
        f"Bins below {gate_floor} (d2+d3+d4) count={below_gate}. "
        f"[0.90,0.95) bucket shadow: n_scored={len(d3_pnls)}, sum_60m_pnl_usd={d3_total}, "
        f"mean_pct_notional_60m={round(d3_mean_pct, 4) if d3_mean_pct is not None else None}. "
        f"Future intents carry alpha11_flow_strength on the row; missing_flow_telemetry replaces unknown."
    )

    out_payload = {
        "root": str(root),
        "run_jsonl": str(run_path),
        "bars_source": "alpaca_rest_live" if args.fetch_bars_live else str(bars_path),
        "bars_loaded_symbols": len(bars_by_sym),
        "alpha11_blocked_join_rows": len(a11_idx),
        "trade_intents_analyzed": len(intents),
        "d3_bin_blocked_shadow_sum_usd_pnl_60m": d3_total,
        "d3_bin_blocked_shadow_mean_pct_notional_60m": round(d3_mean_pct, 6) if d3_mean_pct is not None else None,
        "q_verdict": verdict,
        "bins": rows_out,
    }
    out_path = (args.out_json or (root / "reports" / "audit" / "alpha11_flow_distribution.json")).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")

    print("| bin | intents (all) | blocked | shadow n | miss | mean%@60m | sum USD@60m | mean MFE@60m | mean MAE@60m |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows_out:
        print(
            f"| `{row['bin']}` | {row['intents_total']} | {row['intents_blocked']} | "
            f"{row['blocked_shadow_n_scored']} | {row['blocked_shadow_n_miss_bars']} | "
            f"{row['blocked_shadow_expectancy_pct_notional_60m'] if row['blocked_shadow_expectancy_pct_notional_60m'] is not None else ''} | "
            f"{row['blocked_shadow_sum_usd_pnl_60m'] if row['blocked_shadow_sum_usd_pnl_60m'] is not None else ''} | "
            f"{row['blocked_shadow_mean_mfe_usd_60m'] if row['blocked_shadow_mean_mfe_usd_60m'] is not None else ''} | "
            f"{row['blocked_shadow_mean_mae_usd_60m'] if row['blocked_shadow_mean_mae_usd_60m'] is not None else ''} |"
        )
    print("")
    print(verdict)
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
