#!/usr/bin/env python3
"""
Shadow–Primary Concordance Engine (offline, read-only).

Joins ``logs/shadow_executions.jsonl`` to ``logs/run.jsonl`` ``trade_intent`` rows that carried
Challenger shadow fields, then grades forward **1d / 5d** horizon returns using **Alpaca Data API
1Day bars** (optional) or **local** ``data/research_bars.db`` ``1Day`` closes.

Does **not** import ``main.py``, submit orders, or mutate the execution router.

Usage (repo root, e.g. droplet Monday evening):
  PYTHONPATH=. python3 scripts/research/shadow_challenger_concordance.py --root /root/stock-bot

Local:
  PYTHONPATH=. python scripts/research/shadow_challenger_concordance.py --root .
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo

    _NY = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    _NY = timezone.utc  # type: ignore[assignment]


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_RUN_JSONL_ROTATIONS = 36


def _rotated_jsonl_paths(primary: Path) -> List[Path]:
    """``run.jsonl``, ``run.jsonl.1``, … (existing files only; picks up SRE rotations)."""
    seq = [primary] + [primary.with_name(f"{primary.name}.{i}") for i in range(1, _RUN_JSONL_ROTATIONS + 1)]
    return [p for p in seq if p.is_file()]


def _parse_ts(s: Any) -> Optional[datetime]:
    if s is None:
        return None
    t = str(s).strip().replace("Z", "+00:00")
    if not t:
        return None
    try:
        d = datetime.fromisoformat(t)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None


def _side_bucket(side: Any) -> str:
    s = str(side or "").strip().lower()
    if s in ("buy", "long", "cover", "short_cover", "buy_to_cover"):
        return "long"
    if s in ("sell", "short"):
        return "short"
    return s or "unknown"


def _signed_fwd_return(entry: float, exit_px: float, bucket: str) -> Optional[float]:
    try:
        e = float(entry)
        x = float(exit_px)
        if e <= 0 or x <= 0:
            return None
        raw = (x - e) / e
        if bucket == "short":
            return -raw
        return raw
    except (TypeError, ValueError):
        return None


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _load_research_fetch():
    p = REPO / "scripts" / "analysis" / "research_fetch_alpaca_bars.py"
    if not p.is_file():
        return None
    spec = importlib.util.spec_from_file_location("research_fetch_alpaca_bars", p)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _daily_closes_from_sqlite(db: Path, symbol: str) -> List[Tuple[datetime, float]]:
    if not db.is_file():
        return []
    sym = str(symbol or "").upper().strip()
    out: List[Tuple[datetime, float]] = []
    try:
        conn = sqlite3.connect(str(db))
        try:
            cur = conn.execute(
                """
                SELECT ts_utc, c FROM research_bars
                WHERE symbol = ? AND timeframe = '1Day'
                ORDER BY ts_utc ASC
                """,
                (sym,),
            )
            for ts_utc, c in cur.fetchall():
                dt = _parse_ts(ts_utc)
                if dt is None:
                    continue
                try:
                    cl = float(c)
                except (TypeError, ValueError):
                    continue
                if cl > 0:
                    out.append((dt, cl))
        finally:
            conn.close()
    except Exception:
        return []
    return out


def _daily_closes_from_alpaca(
    mod: Any,
    symbol: str,
    start: datetime,
    end: datetime,
    *,
    feed: str | None,
) -> List[Tuple[datetime, float]]:
    sym = str(symbol or "").upper().strip()
    bars = mod.fetch_symbol_range_chunked(sym, start, end, "1Day", 30, feed)
    out: List[Tuple[datetime, float]] = []
    for b in bars:
        dt = _parse_ts(b.get("t"))
        if dt is None:
            continue
        try:
            cl = float(b.get("c", 0))
        except (TypeError, ValueError):
            continue
        if cl > 0:
            out.append((dt, cl))
    out.sort(key=lambda x: x[0])
    return out


def _index_for_entry(closes: List[Tuple[datetime, float]], entry: datetime) -> int:
    """Last bar with bar time <= entry (UTC compare on API bar open timestamps)."""
    if not closes:
        return -1
    best = -1
    for i, (t_bar, _) in enumerate(closes):
        if t_bar <= entry:
            best = i
        else:
            break
    return best


def _forward_close(closes: List[Tuple[datetime, float]], start_i: int, days_fwd: int) -> Optional[float]:
    if start_i < 0 or not closes or start_i + days_fwd >= len(closes):
        return None
    return closes[start_i + days_fwd][1]


@dataclass
class ConcordanceStats:
    n_shadow: int = 0
    n_joined: int = 0
    n_priced: int = 0
    wins_1d: int = 0
    wins_5d: int = 0
    sum_ret_1d: float = 0.0
    sum_ret_5d: float = 0.0
    n_ret_1d: int = 0
    n_ret_5d: int = 0
    missed_right_1d: int = 0
    missed_sum_ret_1d: float = 0.0


def _load_trade_intent_candidates(run_path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for path in _rotated_jsonl_paths(run_path):
        for r in _iter_jsonl(path):
            if str(r.get("event_type") or "") != "trade_intent":
                continue
            if str(r.get("decision_outcome") or "").lower() != "blocked":
                continue
            if not r.get("challenger_ai_approved"):
                continue
            out.append(r)
    return out


def _best_intent_for_shadow(
    shadow: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    *,
    window_sec: float,
) -> Optional[Dict[str, Any]]:
    ts_s = _parse_ts(shadow.get("ts"))
    if ts_s is None:
        return None
    sym = str(shadow.get("symbol") or "").upper().strip()
    sb = _side_bucket(shadow.get("side"))
    best: Optional[Dict[str, Any]] = None
    best_dt: Optional[float] = None
    for r in candidates:
        if str(r.get("symbol") or "").upper().strip() != sym:
            continue
        if _side_bucket(r.get("side")) != sb:
            continue
        ts_r = _parse_ts(r.get("ts"))
        if ts_r is None:
            continue
        delta = abs((ts_r - ts_s).total_seconds())
        if delta > window_sec:
            continue
        if best is None or delta < (best_dt or 1e18):
            best = r
            best_dt = delta
    return best


def _flatten_joined_intel(intent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not intent:
        return {}
    fs = intent.get("feature_snapshot")
    if not isinstance(fs, dict):
        return {}
    # Shallow copy of top-level snapshot keys for CSV (avoid huge rows)
    keep = (
        "v2_score",
        "regime_label",
        "posture",
        "realized_vol_20d",
        "uw_flow_strength",
        "dark_pool_bias",
        "attribution_snapshot_stage",
    )
    return {k: fs.get(k) for k in keep if k in fs}


def main() -> int:
    ap = argparse.ArgumentParser(description="Shadow–Primary concordance (offline).")
    ap.add_argument("--root", type=Path, default=REPO, help="Repo root (default: infer from script).")
    ap.add_argument(
        "--shadow-log",
        type=Path,
        default=None,
        help="Override path to shadow_executions.jsonl",
    )
    ap.add_argument("--run-log", type=Path, default=None, help="Override path to run.jsonl")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory (default: <root>/reports/Gemini)")
    ap.add_argument("--join-window-sec", type=float, default=45.0, help="Max |ts| delta shadow vs trade_intent")
    ap.add_argument(
        "--bars-db",
        type=Path,
        default=None,
        help="SQLite research_bars.db (default: <root>/data/research_bars.db if exists)",
    )
    ap.add_argument("--alpaca-feed", default="", help="Optional Alpaca data feed (e.g. iex)")
    ap.add_argument(
        "--skip-api",
        action="store_true",
        help="Do not call Alpaca Data API (SQLite only; forward returns may be sparse)",
    )
    args = ap.parse_args()
    root: Path = args.root.resolve()
    shadow_path = (args.shadow_log or (root / "logs" / "shadow_executions.jsonl")).resolve()
    run_path = (args.run_log or (root / "logs" / "run.jsonl")).resolve()
    out_dir = (args.out_dir or (root / "reports" / "Gemini")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    md_path = out_dir / f"shadow_concordance_{ts_tag}.md"
    csv_path = out_dir / f"shadow_concordance_{ts_tag}.csv"

    shadows: List[Dict[str, Any]] = []
    for r in _iter_jsonl(shadow_path):
        if str(r.get("event_type") or "") == "SHADOW_EXECUTION" or r.get("model") == "vanguard_challenger":
            shadows.append(r)

    candidates = _load_trade_intent_candidates(run_path) if run_path.is_file() else []

    bars_db = args.bars_db
    if bars_db is None:
        _def = root / "data" / "research_bars.db"
        bars_db = _def if _def.is_file() else None

    raf = None if args.skip_api else _load_research_fetch()
    api_ok = bool(
        raf
        and (
            os.getenv("ALPACA_API_KEY")
            or os.getenv("ALPACA_KEY")
            or os.getenv("APCA_API_KEY_ID")
        )
    )

    stats = ConcordanceStats()
    stats.n_shadow = len(shadows)

    rows_out: List[Dict[str, Any]] = []
    daily_cache: Dict[str, List[Tuple[datetime, float]]] = {}

    feed = (args.alpaca_feed or "").strip() or None

    for sh in shadows:
        intent = _best_intent_for_shadow(sh, candidates, window_sec=float(args.join_window_sec))
        joined = intent is not None
        if joined:
            stats.n_joined += 1

        sym = str(sh.get("symbol") or "").upper()
        try:
            entry = float(sh.get("entry_price") or 0)
        except (TypeError, ValueError):
            entry = 0.0
        if entry <= 0 and intent:
            try:
                from telemetry.shadow_evaluator import _deep_scan_dicts_for_price, _scan_mapping_for_price

                fs = intent.get("feature_snapshot")
                if isinstance(fs, dict):
                    ep, _sub = _scan_mapping_for_price(fs)
                    if ep is None:
                        ep, _sub = _deep_scan_dicts_for_price(fs, label="intent.feature_snapshot")
                    if ep is not None and ep > 0:
                        entry = float(ep)
            except Exception:
                pass
        sb = _side_bucket(sh.get("side"))
        ts_entry = _parse_ts(sh.get("ts"))

        r1: Optional[float] = None
        r5: Optional[float] = None
        priced = False

        if sym and entry > 0 and ts_entry is not None:
            if sym not in daily_cache:
                closes: List[Tuple[datetime, float]] = []
                if bars_db and Path(bars_db).is_file():
                    closes = _daily_closes_from_sqlite(Path(bars_db), sym)
                if not closes and raf is not None and api_ok:
                    start = ts_entry - timedelta(days=40)
                    end = ts_entry + timedelta(days=40)
                    try:
                        closes = _daily_closes_from_alpaca(raf, sym, start, end, feed=feed)
                    except Exception:
                        closes = []
                daily_cache[sym] = closes
            closes = daily_cache.get(sym) or []
            idx = _index_for_entry(closes, ts_entry)
            c1 = _forward_close(closes, idx, 1)
            c5 = _forward_close(closes, idx, 5)
            if c1 is not None:
                r1 = _signed_fwd_return(entry, c1, sb)
            if c5 is not None:
                r5 = _signed_fwd_return(entry, c5, sb)
            priced = r1 is not None or r5 is not None
            if priced:
                stats.n_priced += 1
            if r1 is not None:
                stats.n_ret_1d += 1
                stats.sum_ret_1d += r1
                if r1 > 0:
                    stats.wins_1d += 1
            if r5 is not None:
                stats.n_ret_5d += 1
                stats.sum_ret_5d += r5
                if r5 > 0:
                    stats.wins_5d += 1

            primary_blocked = str(sh.get("primary_decision_outcome") or "").lower() == "blocked"
            if primary_blocked and r1 is not None and r1 > 0:
                stats.missed_right_1d += 1
                stats.missed_sum_ret_1d += r1

        flat_intel = _flatten_joined_intel(intent)
        rows_out.append(
            {
                "shadow_ts": sh.get("ts"),
                "symbol": sym,
                "side": sh.get("side"),
                "side_bucket": sb,
                "entry_price": entry,
                "entry_price_source": sh.get("entry_price_source"),
                "challenger_proba": sh.get("challenger_proba"),
                "challenger_threshold": sh.get("challenger_threshold"),
                "primary_decision_outcome": sh.get("primary_decision_outcome"),
                "primary_blocked_reason": sh.get("primary_blocked_reason"),
                "joined_trade_intent": joined,
                "join_run_ts": intent.get("ts") if intent else None,
                "join_decision_event_id": intent.get("decision_event_id") if intent else None,
                "join_score": intent.get("score") if intent else None,
                "join_v2_score": flat_intel.get("v2_score"),
                "join_regime_label": flat_intel.get("regime_label"),
                "fwd_return_1d_signed": r1,
                "fwd_return_5d_signed": r5,
                "shadow_correct_1d": (r1 is not None and r1 > 0),
                "shadow_correct_5d": (r5 is not None and r5 > 0),
                "missed_profit_1d_flag": (
                    str(sh.get("primary_decision_outcome") or "").lower() == "blocked"
                    and r1 is not None
                    and r1 > 0
                ),
            }
        )

    exp_1d = stats.sum_ret_1d / stats.n_ret_1d if stats.n_ret_1d else None
    exp_5d = stats.sum_ret_5d / stats.n_ret_5d if stats.n_ret_5d else None
    wr_1d = stats.wins_1d / stats.n_ret_1d if stats.n_ret_1d else None
    wr_5d = stats.wins_5d / stats.n_ret_5d if stats.n_ret_5d else None

    # CSV
    if rows_out:
        fieldnames = list(rows_out[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows_out)
    else:
        placeholder = [
            "shadow_ts",
            "symbol",
            "side",
            "fwd_return_1d_signed",
            "fwd_return_5d_signed",
            "missed_profit_1d_flag",
        ]
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(placeholder)

    def _fmt_pct(x: Optional[float]) -> str:
        if x is None or x != x:
            return "n/a"
        return f"{100.0 * x:.4f}%"

    def _fmt_float(x: Optional[float]) -> str:
        if x is None or x != x:
            return "n/a"
        return f"{x:.6f}"

    md_lines: List[str] = [
        "# Shadow–Primary Concordance Report",
        "",
    ]
    if stats.n_shadow == 0:
        md_lines.append("> **Tape empty:** `shadow_executions.jsonl` had no qualifying rows — nothing to grade yet.")
        md_lines.append("")
    md_lines.extend(
        [
        f"- **Generated (UTC):** `{ts_tag}`",
        f"- **Root:** `{root}`",
        f"- **Shadow log:** `{shadow_path}` ({'missing' if not shadow_path.is_file() else 'present'})",
        f"- **Run log:** `{run_path}` ({'missing' if not run_path.is_file() else 'present'})",
        f"- **Join window:** ±{args.join_window_sec:g}s (shadow `ts` ↔ `trade_intent.ts`)",
        f"- **Pricing:** "
        + (
            "Alpaca Data API `1Day` bars (when keys present)"
            if api_ok and not args.skip_api
            else "API disabled or keys missing"
        )
        + " · "
        + (f"SQLite `{bars_db}`" if bars_db and Path(bars_db).is_file() else "no local `research_bars.db`"),
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Shadow rows ingested | **{stats.n_shadow}** |",
        f"| Joined to `trade_intent` (blocked + `challenger_ai_approved`) | **{stats.n_joined}** |",
        f"| Rows with forward 1d or 5d return | **{stats.n_priced}** |",
        f"| Win rate (1d, signed return > 0) | **{_fmt_pct(wr_1d)}** ({stats.wins_1d}/{stats.n_ret_1d}) |",
        f"| Win rate (5d) | **{_fmt_pct(wr_5d)}** ({stats.wins_5d}/{stats.n_ret_5d}) |",
        f"| Expectancy (mean signed 1d return) | **{_fmt_float(exp_1d)}** |",
        f"| Expectancy (mean signed 5d return) | **{_fmt_float(exp_5d)}** |",
        f"| **Missed profit** (Primary blocked & 1d right) — count | **{stats.missed_right_1d}** |",
        f"| **Missed profit** — sum signed 1d returns (fraction of entry) | **{_fmt_float(stats.missed_sum_ret_1d)}** |",
        "",
        "## Definitions",
        "",
        "- **Join:** Closest `trade_intent` with `decision_outcome=blocked`, `challenger_ai_approved=true`, same `symbol` and side bucket (`buy`/`long` vs `sell`/`short`), within join window.",
        "- **Signed forward return:** Long: `(close_fwd - entry) / entry`. Short: `(entry - close_fwd) / entry`.",
        "- **1d / 5d:** Next 1 / 5 **available** daily bars after the last daily bar with `bar_time <= shadow_ts` (UTC ordering; aligns with `research_bars` / Alpaca `1Day` timestamps).",
        "- **Missed profit (opportunity cost):** Primary blocked the live trade while Challenger-approved shadow would have gained on **1d** signed return (`> 0`).",
        "",
        "## Artifacts",
        "",
        f"- CSV: `{csv_path}`",
        "",
        ]
    )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path}")
    print(f"shadow_rows={stats.n_shadow} joined={stats.n_joined} priced={stats.n_priced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
