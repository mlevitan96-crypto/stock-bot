#!/usr/bin/env python3
"""
Displacement Counterfactual Lab — offline, read-only.

Quantifies opportunity cost when **capacity + displacement** finds **no eligible incumbent**
(`no_candidates_found` in ``logs/displacement.jsonl``): incumbents fail mainly due to
**``too_young``** or **``in_cooldown``** while a **blocked challenger** (typically
``max_positions_reached``) exists in ``logs/run.jsonl``.

**Join (SRE contract):** ``no_candidates_found`` does **not** log the challenger ticker.
We match each displacement row to the nearest ``trade_intent`` with
``decision_outcome=blocked``, ``blocked_reason=max_positions_reached``, and
``|score - new_signal_score|`` within ``--score-eps``, within ``--join-window-sec``.

**Counterfactual:** For each ``position_details[]`` row with ``fail_reason`` in
``{too_young, in_cooldown}``, compare **forward 1d / 5d signed long returns** from a common
anchor (last **1Day** bar ≤ event ``ts``) for **candidate** vs **incumbent**.
**Swap edge** = ``candidate_fwd - incumbent_fwd`` (approx. net of rotating book from X into Y).

Does **not** import ``main.py`` or submit orders.

Usage:
  PYTHONPATH=. python3 scripts/research/displacement_counterfactual_lab.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

FAIL_RULES = frozenset({"too_young", "in_cooldown"})


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


def _daily_closes_from_alpaca(mod: Any, symbol: str, start: datetime, end: datetime, *, feed: str | None) -> List[Tuple[datetime, float]]:
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


def _long_fwd_returns(
    closes: List[Tuple[datetime, float]],
    event_ts: datetime,
    entry_px: float,
) -> Tuple[Optional[float], Optional[float]]:
    """Signed long forward returns vs entry_px at T+1 / T+5 daily closes."""
    if entry_px <= 0:
        return None, None
    idx = _index_for_entry(closes, event_ts)
    c1 = _forward_close(closes, idx, 1)
    c5 = _forward_close(closes, idx, 5)
    r1 = (c1 - entry_px) / entry_px if c1 is not None else None
    r5 = (c5 - entry_px) / entry_px if c5 is not None else None
    return r1, r5


def _first_price_from_snapshot(fs: Any) -> Optional[float]:
    if not isinstance(fs, dict):
        return None
    for k in ("last_price", "close", "vwap", "price", "mid"):
        v = fs.get(k)
        if v is None:
            continue
        try:
            x = float(v)
            if x > 0:
                return x
        except (TypeError, ValueError):
            continue
    bid = fs.get("bid")
    ask = fs.get("ask")
    try:
        b, a = float(bid), float(ask)
        if b > 0 and a > 0 and a >= b:
            return (a + b) / 2.0
    except (TypeError, ValueError):
        pass
    return None


def _load_max_positions_blocked(run_path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in _iter_jsonl(run_path):
        if str(r.get("event_type") or "") != "trade_intent":
            continue
        if str(r.get("decision_outcome") or "").lower() != "blocked":
            continue
        br = str(r.get("blocked_reason") or "").lower()
        if br == "max_positions_reached" or "max_positions" in br or "capacity" in br:
            out.append(r)
    return out


def _disp_score(d: Dict[str, Any]) -> Optional[float]:
    try:
        return float(d.get("new_signal_score"))
    except (TypeError, ValueError):
        return None


def _intent_score(r: Dict[str, Any]) -> Optional[float]:
    try:
        return float(r.get("score"))
    except (TypeError, ValueError):
        return None


def _best_intent_for_disp(
    disp: Dict[str, Any],
    intents: List[Dict[str, Any]],
    *,
    window_sec: float,
    score_eps: float,
) -> Optional[Dict[str, Any]]:
    ts_d = _parse_ts(disp.get("ts"))
    s_d = _disp_score(disp)
    if ts_d is None or s_d is None:
        return None
    best: Optional[Dict[str, Any]] = None
    best_key: Optional[float] = None
    for it in intents:
        ts_i = _parse_ts(it.get("ts"))
        s_i = _intent_score(it)
        if ts_i is None or s_i is None:
            continue
        if abs(float(s_i) - float(s_d)) > score_eps:
            continue
        delta = abs((ts_i - ts_d).total_seconds())
        if delta > window_sec:
            continue
        if best is None or delta < (best_key or 1e18):
            best = it
            best_key = delta
    return best


def _get_closes_for_symbol(
    sym: str,
    event_ts: datetime,
    *,
    daily_cache: Dict[str, List[Tuple[datetime, float]]],
    bars_db: Optional[Path],
    raf: Any,
    api_ok: bool,
    feed: str | None,
) -> List[Tuple[datetime, float]]:
    sym = str(sym or "").upper().strip()
    if sym in daily_cache:
        return daily_cache[sym]
    closes: List[Tuple[datetime, float]] = []
    if bars_db and bars_db.is_file():
        closes = _daily_closes_from_sqlite(bars_db, sym)
    if not closes and raf is not None and api_ok:
        start = event_ts - timedelta(days=45)
        end = event_ts + timedelta(days=45)
        try:
            closes = _daily_closes_from_alpaca(raf, sym, start, end, feed=feed)
        except Exception:
            closes = []
    daily_cache[sym] = closes
    return closes


@dataclass
class LabStats:
    n_disp_events: int = 0
    n_disp_matched_intent: int = 0
    n_detail_rows_rules: int = 0
    n_priced_pairs_1d: int = 0
    sum_swap_1d: float = 0.0
    sum_missed_pos_1d: float = 0.0
    sum_missed_pos_5d: float = 0.0
    sum_cand_1d: float = 0.0
    sum_inc_1d: float = 0.0
    n_cand_1d: int = 0
    n_inc_1d: int = 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Displacement counterfactual lab (offline).")
    ap.add_argument("--root", type=Path, default=REPO, help="Repo root.")
    ap.add_argument("--displacement-log", type=Path, default=None, help="Override displacement.jsonl path.")
    ap.add_argument("--run-log", type=Path, default=None, help="Override run.jsonl path.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Default: <root>/reports/Gemini")
    ap.add_argument("--join-window-sec", type=float, default=180.0, help="Max |ts| displacement vs trade_intent.")
    ap.add_argument("--score-eps", type=float, default=0.05, help="Max |score - new_signal_score| for join.")
    ap.add_argument("--bars-db", type=Path, default=None, help="SQLite DB (research_bars 1Day).")
    ap.add_argument("--alpaca-feed", default="", help="Optional feed e.g. iex")
    ap.add_argument("--skip-api", action="store_true", help="SQLite only.")
    args = ap.parse_args()
    root = args.root.resolve()
    disp_path = (args.displacement_log or (root / "logs" / "displacement.jsonl")).resolve()
    run_path = (args.run_log or (root / "logs" / "run.jsonl")).resolve()
    out_dir = (args.out_dir or (root / "reports" / "Gemini")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    md_path = out_dir / f"displacement_cost_{ts_tag}.md"
    csv_path = out_dir / f"displacement_cost_{ts_tag}.csv"

    displacements: List[Dict[str, Any]] = []
    for r in _iter_jsonl(disp_path):
        if str(r.get("msg") or "") == "no_candidates_found":
            displacements.append(r)

    intents = _load_max_positions_blocked(run_path) if run_path.is_file() else []

    bars_db = args.bars_db
    if bars_db is None:
        for candidate in (root / "data" / "research_bars.db", root / "data" / "price_bars.db"):
            if candidate.is_file():
                bars_db = candidate
                break

    raf = None if args.skip_api else _load_research_fetch()
    api_ok = bool(
        raf
        and (
            os.getenv("ALPACA_API_KEY")
            or os.getenv("ALPACA_KEY")
            or os.getenv("APCA_API_KEY_ID")
        )
    )
    feed = (args.alpaca_feed or "").strip() or None

    stats = LabStats()
    stats.n_disp_events = len(displacements)
    daily_cache: Dict[str, List[Tuple[datetime, float]]] = {}
    rows_out: List[Dict[str, Any]] = []

    for disp in displacements:
        intent = _best_intent_for_disp(
            disp,
            intents,
            window_sec=float(args.join_window_sec),
            score_eps=float(args.score_eps),
        )
        if intent is None:
            continue
        stats.n_disp_matched_intent += 1

        ts_ev = _parse_ts(disp.get("ts"))
        if ts_ev is None:
            continue

        cand_sym = str(intent.get("symbol") or "").upper().strip()
        fs = intent.get("feature_snapshot")

        details = disp.get("position_details") or []
        if not isinstance(details, list):
            details = []

        cand_closes_all = _get_closes_for_symbol(
            cand_sym, ts_ev, daily_cache=daily_cache, bars_db=bars_db, raf=raf, api_ok=api_ok, feed=feed
        )
        idx_c0 = _index_for_entry(cand_closes_all, ts_ev)
        cand_anchor = _forward_close(cand_closes_all, idx_c0, 0) if idx_c0 >= 0 else None
        cand_entry_fs = _first_price_from_snapshot(fs)
        if cand_entry_fs is not None and cand_entry_fs > 0:
            cand_entry_use = float(cand_entry_fs)
        elif cand_anchor is not None and cand_anchor > 0:
            cand_entry_use = float(cand_anchor)
        else:
            cand_entry_use = None

        for pd in details:
            if not isinstance(pd, dict):
                continue
            fr = str(pd.get("fail_reason") or "").strip().lower()
            if fr not in FAIL_RULES:
                continue
            stats.n_detail_rows_rules += 1
            inc_sym = str(pd.get("symbol") or "").upper().strip()
            if not cand_sym or not inc_sym:
                continue

            inc_closes = _get_closes_for_symbol(
                inc_sym, ts_ev, daily_cache=daily_cache, bars_db=bars_db, raf=raf, api_ok=api_ok, feed=feed
            )
            idx_i = _index_for_entry(inc_closes, ts_ev)
            inc_anchor = _forward_close(inc_closes, idx_i, 0) if idx_i >= 0 else None
            inc_entry_use = float(inc_anchor) if inc_anchor is not None and inc_anchor > 0 else None

            if cand_entry_use is None or cand_entry_use <= 0 or inc_entry_use is None or inc_entry_use <= 0:
                rows_out.append(
                    {
                        "displacement_ts": disp.get("ts"),
                        "candidate_symbol": cand_sym,
                        "incumbent_symbol": inc_sym,
                        "fail_reason": fr,
                        "new_signal_score": _disp_score(disp),
                        "join_score": _intent_score(intent),
                        "swap_edge_1d": None,
                        "swap_edge_5d": None,
                        "candidate_fwd_1d": None,
                        "incumbent_fwd_1d": None,
                        "priced": False,
                    }
                )
                continue

            cr1, cr5 = _long_fwd_returns(cand_closes_all, ts_ev, cand_entry_use)
            ir1, ir5 = _long_fwd_returns(inc_closes, ts_ev, inc_entry_use)

            swap1: Optional[float] = None
            swap5: Optional[float] = None
            if cr1 is not None and ir1 is not None:
                swap1 = cr1 - ir1
                stats.n_priced_pairs_1d += 1
                stats.sum_swap_1d += swap1
                stats.sum_cand_1d += cr1
                stats.sum_inc_1d += ir1
                stats.n_cand_1d += 1
                stats.n_inc_1d += 1
                if swap1 > 0:
                    stats.sum_missed_pos_1d += swap1
            if cr5 is not None and ir5 is not None:
                swap5 = cr5 - ir5
                if swap5 > 0:
                    stats.sum_missed_pos_5d += swap5

            rows_out.append(
                {
                    "displacement_ts": disp.get("ts"),
                    "candidate_symbol": cand_sym,
                    "incumbent_symbol": inc_sym,
                    "fail_reason": fr,
                    "new_signal_score": _disp_score(disp),
                    "join_score": _intent_score(intent),
                    "candidate_entry_proxy": cand_entry_use,
                    "incumbent_entry_proxy": inc_entry_use,
                    "candidate_fwd_1d": cr1,
                    "candidate_fwd_5d": cr5,
                    "incumbent_fwd_1d": ir1,
                    "incumbent_fwd_5d": ir5,
                    "swap_edge_1d": swap1,
                    "swap_edge_5d": swap5,
                    "missed_profit_1d": max(0.0, swap1) if swap1 is not None else None,
                    "priced": swap1 is not None,
                }
            )

    if rows_out:
        fieldnames = list(rows_out[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows_out)
    else:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [
                    "displacement_ts",
                    "candidate_symbol",
                    "incumbent_symbol",
                    "fail_reason",
                    "swap_edge_1d",
                    "swap_edge_5d",
                ]
            )

    avg_cand = stats.sum_cand_1d / stats.n_cand_1d if stats.n_cand_1d else None
    avg_inc = stats.sum_inc_1d / stats.n_inc_1d if stats.n_inc_1d else None
    avg_swap = stats.sum_swap_1d / stats.n_priced_pairs_1d if stats.n_priced_pairs_1d else None

    md: List[str] = [
        "# Displacement Counterfactual Lab",
        "",
    ]
    if stats.n_disp_events == 0:
        md.append("> **No data:** `displacement.jsonl` contained no `no_candidates_found` rows.")
        md.append("")
    md.extend(
        [
            f"- **Generated (UTC):** `{ts_tag}`",
            f"- **Root:** `{root}`",
            f"- **Displacement log:** `{disp_path}`",
            f"- **Run log:** `{run_path}`",
            f"- **Join:** `no_candidates_found` ↔ `trade_intent` blocked `max_positions_reached` within **±{args.join_window_sec:g}s** and **|Δscore| ≤ {args.score_eps:g}**.",
            f"- **Rules attributed:** `{', '.join(sorted(FAIL_RULES))}` on `position_details.fail_reason`.",
            f"- **Pricing:** local `research_bars` / `price_bars` **1Day** `c` if present; else Alpaca Data API (unless `--skip-api`).",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| `no_candidates_found` events | **{stats.n_disp_events}** |",
            f"| Matched to a blocked capacity `trade_intent` | **{stats.n_disp_matched_intent}** |",
            f"| Incumbent rows (`too_young` / `in_cooldown`) evaluated | **{stats.n_detail_rows_rules}** |",
            f"| Priced swap pairs (1d) | **{stats.n_priced_pairs_1d}** |",
            f"| **Total opportunity cost** (Σ max(0, swap_edge_1d)) | **{stats.sum_missed_pos_1d:.6f}** |",
            f"| **Total opportunity cost** (Σ max(0, swap_edge_5d)) | **{stats.sum_missed_pos_5d:.6f}** |",
            f"| Mean swap edge 1d (where priced) | **{avg_swap if avg_swap is not None else 'n/a'}** |",
            f"| Mean candidate 1d fwd (long proxy) | **{avg_cand if avg_cand is not None else 'n/a'}** |",
            f"| Mean incumbent 1d fwd (long proxy) | **{avg_inc if avg_inc is not None else 'n/a'}** |",
            "",
            "## Definitions",
            "",
            "- **Swap edge (1d):** `candidate_fwd_1d - incumbent_fwd_1d` using the same calendar anchor bar.",
            "- **Missed profit (row):** `max(0, swap_edge_1d)` — positive edge foregone by not rotating when the gate was `too_young` / `in_cooldown`.",
            "- **Incumbent entry proxy:** daily **close** at anchor (last 1Day bar ≤ event `ts`) when `position_details` lacks a fill price.",
            "",
            f"- **CSV:** `{csv_path}`",
            "",
        ]
    )
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path}")
    print(
        f"disp={stats.n_disp_events} matched={stats.n_disp_matched_intent} "
        f"rule_rows={stats.n_detail_rows_rules} priced_1d={stats.n_priced_pairs_1d}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
