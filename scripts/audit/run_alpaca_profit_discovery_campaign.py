#!/usr/bin/env python3
"""
Alpaca profit discovery campaign — READ-ONLY. Streams canonical logs; writes Phase 0–10 artifacts.

NO strategy / execution changes. Run on droplet:
  PYTHONPATH=. python3 scripts/audit/run_alpaca_profit_discovery_campaign.py --root /root/stock-bot

Outputs: reports/daily/<ET-date>/evidence/ALPACA_PROFIT_*.md|json and BOARD_*.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]


def _parse_ts_any(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("Z", "+00:00")
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s[:32])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (TypeError, ValueError):
        return None


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        f = float(x)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _tail_text_lines(path: Path, max_lines: int, max_bytes: int = 40_000_000) -> List[str]:
    if not path.is_file():
        return []
    size = path.stat().st_size
    start = max(0, size - max_bytes)
    lines: List[str] = []
    with path.open("rb") as f:
        f.seek(start)
        if start > 0:
            f.readline()
        for raw in f:
            try:
                lines.append(raw.decode("utf-8", errors="replace").rstrip("\n\r"))
            except Exception:
                pass
    return lines[-max_lines:] if len(lines) > max_lines else lines


def _iter_jsonl_tail(path: Path, max_lines: int) -> List[dict]:
    out: List[dict] = []
    for ln in _tail_text_lines(path, max_lines):
        ln = ln.strip()
        if not ln:
            continue
        try:
            o = json.loads(ln)
            if isinstance(o, dict):
                out.append(o)
        except json.JSONDecodeError:
            continue
    return out


def _count_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    n = 0
    with path.open("rb") as f:
        for _ in f:
            n += 1
    return n


def _norm_side(s: Any) -> str:
    x = str(s or "").upper().strip()
    if x in ("LONG", "BUY", "BULL", "BULLISH"):
        return "LONG"
    if x in ("SHORT", "SELL", "BEAR", "BEARISH"):
        return "SHORT"
    return x or "UNKNOWN"


def _extract_components(snap: dict) -> Dict[str, float]:
    comps = snap.get("weighted_contributions") or snap.get("signal_group_scores") or {}
    if isinstance(comps, dict) and "components" in comps:
        comps = comps.get("components") or {}
    if not isinstance(comps, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in comps.items():
        fv = _safe_float(v)
        if fv is not None:
            out[str(k)] = fv
    return out


def _session_anchor_et(now: datetime) -> str:
    try:
        from zoneinfo import ZoneInfo

        et = ZoneInfo("America/New_York")
        return now.astimezone(et).date().isoformat()
    except Exception:
        return now.date().isoformat()


def _percentiles(vals: List[float], ps: Tuple[float, ...]) -> Dict[str, float]:
    if not vals:
        return {f"p{int(p*100)}": float("nan") for p in ps}
    s = sorted(vals)
    n = len(s)
    out: Dict[str, float] = {}
    for p in ps:
        idx = min(n - 1, max(0, int(p * (n - 1))))
        out[f"p{int(p*100)}"] = round(s[idx], 6)
    return out


def _correlation_matrix(
    names: List[str], rows: List[Dict[str, float]]
) -> Dict[str, Dict[str, Optional[float]]]:
    """Pearson r for pairs (skip if constant)."""
    if len(names) < 2 or len(rows) < 5:
        return {}
    mat: Dict[str, Dict[str, Optional[float]]] = {a: {b: None for b in names} for a in names}
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            xs = [r.get(a) for r in rows if r.get(a) is not None and r.get(b) is not None]
            ys = [r.get(b) for r in rows if r.get(a) is not None and r.get(b) is not None]
            if len(xs) < 5:
                continue
            mx = statistics.mean(xs)
            my = statistics.mean(ys)
            vx = sum((x - mx) ** 2 for x in xs)
            vy = sum((y - my) ** 2 for y in ys)
            if vx < 1e-12 or vy < 1e-12:
                mat[a][b] = mat[b][a] = None
                continue
            cov = sum((xs[j] - mx) * (ys[j] - my) for j in range(len(xs)))
            r = cov / math.sqrt(vx * vy)
            if r > 1.0:
                r = 1.0
            if r < -1.0:
                r = -1.0
            mat[a][b] = mat[b][a] = round(r, 4)
    return mat


def run_campaign(root: Path, max_exit: int, max_snap: int, max_blocked: int, max_sigctx: int) -> Path:
    root = root.resolve()
    logs = root / "logs"
    state = root / "state"
    reports = root / "reports"
    now = datetime.now(timezone.utc)
    et_date = _session_anchor_et(now)
    ev = reports / "daily" / et_date / "evidence"
    ev.mkdir(parents=True, exist_ok=True)

    meta = {
        "generated_at_utc": now.isoformat(),
        "root": str(root),
        "session_anchor_et": et_date,
        "max_exit_rows_tail": max_exit,
        "max_score_snapshot_tail": max_snap,
        "disclaimer": "Read-only campaign; tail windows are a sample of full history unless noted.",
    }
    (ev / "ALPACA_PROFIT_DISCOVERY_META.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    # ---------- Phase 0 inventory ----------
    paths = {
        "exit_attribution.jsonl": logs / "exit_attribution.jsonl",
        "orders.jsonl": logs / "orders.jsonl",
        "signal_context.jsonl": logs / "signal_context.jsonl",
        "run.jsonl": logs / "run.jsonl",
        "score_snapshot.jsonl": logs / "score_snapshot.jsonl",
        "blocked_trades.jsonl": state / "blocked_trades.jsonl",
        "alpaca_unified_events.jsonl": logs / "alpaca_unified_events.jsonl",
    }
    inv: Dict[str, Any] = {"row_counts": {}, "files_present": {}}
    for name, p in paths.items():
        inv["files_present"][name] = p.is_file()
        inv["row_counts"][name] = _count_lines(p) if p.is_file() else 0

    exits = _iter_jsonl_tail(paths["exit_attribution.jsonl"], max_exit)
    orders = _iter_jsonl_tail(paths["orders.jsonl"], min(max_exit * 3, 80000))
    snaps = _iter_jsonl_tail(paths["score_snapshot.jsonl"], max_snap)
    blocked = _iter_jsonl_tail(paths["blocked_trades.jsonl"], max_blocked)
    sigctx = _iter_jsonl_tail(paths["signal_context.jsonl"], max_sigctx)

    # Join coverage: exits with pnl vs orders canonical_trade_id
    ctid_exit = sum(1 for r in exits if r.get("canonical_trade_id") or r.get("trade_id"))
    order_ct = sum(1 for o in orders if o.get("canonical_trade_id"))
    inv["join_notes"] = {
        "exit_rows_in_tail_with_trade_id": sum(1 for r in exits if r.get("trade_id")),
        "exit_tail_with_canonical_trade_id": sum(1 for r in exits if r.get("canonical_trade_id")),
        "orders_tail_with_canonical_trade_id": order_ct,
    }

    # Regime / SPI file discovery
    spi_files = sorted(
        reports.glob("ALPACA_SPI_SECTION_*.md"), key=lambda p: p.stat().st_mtime, reverse=True
    )[:5]
    inv["latest_spi_md"] = [str(p.relative_to(root)) for p in spi_files]

    md0 = [
        "# ALPACA_PROFIT_INTEL_DATA_INVENTORY",
        "",
        f"- **Generated (UTC):** {now.isoformat()}",
        f"- **Session anchor (ET):** {et_date}",
        "",
        "## Row counts (full file scan)",
        "",
        "| File | Rows | Present |",
        "|------|------|--------|",
    ]
    for name, p in paths.items():
        md0.append(f"| `{name}` | {inv['row_counts'][name]} | {inv['files_present'][name]} |")
    md0.extend(
        [
            "",
            "## Tail sample used for deep phases",
            "",
            f"- `exit_attribution` tail rows loaded: **{len(exits)}**",
            f"- `score_snapshot` tail rows loaded: **{len(snaps)}**",
            f"- `blocked_trades` tail rows loaded: **{len(blocked)}**",
            f"- `signal_context` tail rows loaded: **{len(sigctx)}**",
            "",
            "## Join coverage (tail)",
            "",
            "```json",
            json.dumps(inv["join_notes"], indent=2),
            "```",
            "",
            "## SPI artifacts (newest)",
            "",
        ]
    )
    for s in inv["latest_spi_md"]:
        md0.append(f"- `{s}`")
    md0.append("")
    (ev / "ALPACA_PROFIT_INTEL_DATA_INVENTORY.md").write_text("\n".join(md0) + "\n", encoding="utf-8")

    # ---------- Phase 1 directional ----------
    long_pnls: List[float] = []
    short_pnls: List[float] = []
    unk_pnls: List[float] = []
    by_reg_dir: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

    for r in exits:
        pnl = _safe_float(r.get("pnl"))
        if pnl is None:
            continue
        side = _norm_side(r.get("side"))
        reg = str(r.get("exit_regime") or r.get("regime_at_exit") or "UNKNOWN")
        if side == "LONG":
            long_pnls.append(pnl)
            by_reg_dir[reg]["LONG"].append(pnl)
        elif side == "SHORT":
            short_pnls.append(pnl)
            by_reg_dir[reg]["SHORT"].append(pnl)
        else:
            unk_pnls.append(pnl)
            by_reg_dir[reg]["UNKNOWN"].append(pnl)

    def _stats(xs: List[float]) -> Dict[str, Any]:
        if not xs:
            return {"n": 0, "sum_pnl": 0.0, "win_rate": None, "expectancy": None}
        wins = sum(1 for x in xs if x > 0)
        return {
            "n": len(xs),
            "sum_pnl": round(sum(xs), 4),
            "win_rate": round(wins / len(xs), 4),
            "expectancy": round(sum(xs) / len(xs), 6),
            **_percentiles(xs, (0.05, 0.5, 0.95)),
        }

    dir_stats = {
        "LONG": _stats(long_pnls),
        "SHORT": _stats(short_pnls),
        "UNKNOWN_SIDE": _stats(unk_pnls),
    }
    regime_dir_md = []
    for reg, dirs in sorted(by_reg_dir.items(), key=lambda x: -sum(len(v) for v in x[1].values()))[:20]:
        regime_dir_md.append(f"### Regime `{reg or 'EMPTY'}`")
        for dname in ("LONG", "SHORT", "UNKNOWN"):
            st = _stats(list(dirs.get(dname, [])))
            if st["n"] == 0:
                continue
            regime_dir_md.append(
                f"- **{dname}**: n={st['n']}, sum_pnl={st['sum_pnl']}, win_rate={st['win_rate']}, "
                f"E[pnl]={st['expectancy']}, p5={st.get('p5')}, p95={st.get('p95')}"
            )

    flip_bias = "INSUFFICIENT_DATA"
    if long_pnls and short_pnls:
        el = sum(long_pnls) / len(long_pnls)
        es = sum(short_pnls) / len(short_pnls)
        if el > es * 1.15 and el > 0:
            flip_bias = "NO_FLIP_LONG_OUTPERFORMS_IN_TAIL"
        elif es > el * 1.15 and es > 0:
            flip_bias = "REVIEW_SHORT_EDGE_IN_TAIL_NOT_A_REC_TO_FLIP_WITHOUT_SHADOW"
        else:
            flip_bias = "MIXED_NO_CLEAR_DOMINANCE_IN_TAIL"

    md1 = [
        "# ALPACA_DIRECTIONAL_PNL_ANALYSIS",
        "",
        "## Summary (tail sample, realized `pnl` present)",
        "",
        "```json",
        json.dumps(dir_stats, indent=2),
        "```",
        "",
        "## Regime × direction (top regimes by row count)",
        "",
        *regime_dir_md,
        "",
        "## Questions",
        "",
        f"- **Should we flip bias?** Evidence: `{flip_bias}` — based on expectancy in **this tail only**; not causal proof of alpha (confounders: symbol mix, time).",
        "- **Gate direction by regime or confidence?** If regime cells are sparse (low n), gating increases variance; use shadow tests before production gates.",
        "",
        "## Method",
        "",
        "- Direction from `side` (normalized LONG/SHORT).",
        "- PnL from `pnl` USD field.",
        "",
    ]
    (ev / "ALPACA_DIRECTIONAL_PNL_ANALYSIS.md").write_text("\n".join(md1) + "\n", encoding="utf-8")

    # ---------- Phase 2 signal contribution via snapshot match ----------
    # Index snapshots by symbol -> sorted (ts, components)
    by_sym_snaps: Dict[str, List[Tuple[float, Dict[str, float]]]] = defaultdict(list)
    for s in snaps:
        sym = str(s.get("symbol") or s.get("ticker") or "").upper().strip()
        if not sym:
            continue
        ts = _parse_ts_any(s.get("ts") or s.get("timestamp") or s.get("ts_iso"))
        if ts is None:
            continue
        comp = _extract_components(s)
        if comp:
            by_sym_snaps[sym].append((ts, comp))
    for sym in by_sym_snaps:
        by_sym_snaps[sym].sort(key=lambda x: x[0])
    sym_times = {sym: [t for t, _ in arr] for sym, arr in by_sym_snaps.items()}

    all_comp_names: set[str] = set()
    matched_exits = 0
    exit_pnls_with_comp: List[Tuple[float, Dict[str, float]]] = []

    for r in exits:
        pnl = _safe_float(r.get("pnl"))
        if pnl is None:
            continue
        sym = str(r.get("symbol") or "").upper().strip()
        if not sym or sym not in by_sym_snaps:
            continue
        ent_ts = _parse_ts_any(
            r.get("entry_timestamp") or r.get("entry_ts") or r.get("timestamp")
        )
        if ent_ts is None:
            continue
        arr = by_sym_snaps[sym]
        times = sym_times[sym]
        i = bisect_left(times, ent_ts) - 1
        if i < 0:
            continue
        ts_i, comp = arr[i]
        if ent_ts - ts_i > 600:
            continue
        matched_exits += 1
        exit_pnls_with_comp.append((pnl, comp))
        all_comp_names.update(comp.keys())

    comp_names = sorted(all_comp_names)
    ranking: List[Dict[str, Any]] = []
    for cname in comp_names:
        vals_high: List[float] = []
        vals_low: List[float] = []
        contrib_vals = [p[1].get(cname, 0.0) for p in exit_pnls_with_comp]
        if len(contrib_vals) < 10:
            continue
        med = statistics.median(contrib_vals)
        for pnl, comp in exit_pnls_with_comp:
            v = comp.get(cname, 0.0)
            (vals_high if v >= med else vals_low).append(pnl)
        eh = sum(vals_high) / len(vals_high) if vals_high else 0.0
        el = sum(vals_low) / len(vals_low) if vals_low else 0.0
        delta = eh - el
        ranking.append(
            {
                "signal": cname,
                "n_matched_trades": len(vals_high) + len(vals_low),
                "median_split_on_contribution": round(med, 6),
                "mean_pnl_high_component": round(eh, 6),
                "mean_pnl_low_component": round(el, 6),
                "delta_mean_pnl": round(delta, 6),
                "proxy_contribution_score": round(delta * (len(vals_high) + len(vals_low)), 4),
            }
        )
    ranking.sort(key=lambda x: x["proxy_contribution_score"], reverse=True)
    (ev / "ALPACA_SIGNAL_RANKING.json").write_text(
        json.dumps(
            {
                "matched_exits_with_snapshot": matched_exits,
                "signals_ranked": ranking[:80],
                "caveat": "Marginal split at median of matched entry-time snapshot contribution; not IV regression; confounded.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    md2 = [
        "# ALPACA_SIGNAL_CONTRIBUTION_MATRIX",
        "",
        f"- Exits with pnl matched to `score_snapshot` within 600s before entry, same symbol: **{matched_exits}**",
        "",
        "## Interpretation",
        "",
        "- **High vs low** = median split on component value at nearest pre-entry snapshot.",
        "- **delta_mean_pnl** = naive association with realized PnL; **not** causal uplift.",
        "",
        "## Top 25 by proxy score (delta × n)",
        "",
        "| signal | n | delta_mean_pnl | mean_pnl high | mean_pnl low |",
        "|--------|---|----------------|---------------|--------------|",
    ]
    for row in ranking[:25]:
        md2.append(
            f"| `{row['signal']}` | {row['n_matched_trades']} | {row['delta_mean_pnl']} | "
            f"{row['mean_pnl_high_component']} | {row['mean_pnl_low_component']} |"
        )
    md2.extend(
        [
            "",
            "## Full JSON",
            "",
            f"- `ALPACA_SIGNAL_RANKING.json`",
            "",
        ]
    )
    (ev / "ALPACA_SIGNAL_CONTRIBUTION_MATRIX.md").write_text("\n".join(md2) + "\n", encoding="utf-8")

    # ---------- Phase 3 exit causal (aggregates) ----------
    by_reason: Dict[str, List[float]] = defaultdict(list)
    by_winner: Dict[str, List[float]] = defaultdict(list)
    v2dom: Dict[str, List[float]] = defaultdict(list)
    tmin_buckets: Dict[str, List[float]] = defaultdict(list)

    for r in exits:
        pnl = _safe_float(r.get("pnl"))
        if pnl is None:
            continue
        reason = str(r.get("exit_reason") or r.get("exit_reason_code") or "unknown")
        by_reason[reason].append(pnl)
        w = str(r.get("winner") or r.get("thesis_break_reason") or "")
        if w:
            by_winner[w].append(pnl)
        v2 = r.get("v2_exit_components") if isinstance(r.get("v2_exit_components"), dict) else {}
        if v2:
            dom = max(v2.items(), key=lambda kv: abs(_safe_float(kv[1]) or 0.0))[0]
            v2dom[dom].append(pnl)
        tmin = _safe_float(r.get("time_in_trade_minutes"))
        if tmin is not None:
            if tmin < 15:
                tmin_buckets["<15m"].append(pnl)
            elif tmin < 60:
                tmin_buckets["15-60m"].append(pnl)
            elif tmin < 240:
                tmin_buckets["1-4h"].append(pnl)
            else:
                tmin_buckets[">=4h"].append(pnl)

    def _agg_reason(m: Dict[str, List[float]]) -> List[str]:
        lines = []
        for k, xs in sorted(m.items(), key=lambda kv: -len(kv[1]))[:30]:
            st = _stats(xs)
            lines.append(
                f"- **{k}**: n={st['n']}, sum={st['sum_pnl']}, E={st['expectancy']}, win_rate={st['win_rate']}"
            )
        return lines

    md3 = [
        "# ALPACA_EXIT_CAUSAL_ANALYSIS",
        "",
        "## By `exit_reason` / code (tail)",
        "",
        *_agg_reason(by_reason),
        "",
        "## By `winner` / thesis break (when present)",
        "",
        *_agg_reason(by_winner),
        "",
        "## Dominant `v2_exit_component` (when dict present)",
        "",
        *_agg_reason(v2dom),
        "",
        "## Time-in-trade buckets",
        "",
        *_agg_reason(tmin_buckets),
        "",
        "## Counterfactual note",
        "",
        "- **Early vs late exit** full replay requires bar path + `replay_exit_timing_counterfactuals.py`.",
        "- **Loss amplification from delayed exits:** infer only from time bucket expectancy differences above (associational).",
        "",
    ]
    (ev / "ALPACA_EXIT_CAUSAL_ANALYSIS.md").write_text("\n".join(md3) + "\n", encoding="utf-8")

    # ---------- Phase 4 time counterfactuals ----------
    bars_path = root / "artifacts" / "market_data" / "alpaca_bars.jsonl"
    bars_alt = list((root / "data" / "bars_cache").glob("*.jsonl"))[:1]
    mfe_pnl_pairs: List[Tuple[float, float]] = []
    for r in exits:
        pnl_pct = _safe_float(r.get("pnl_pct"))
        eq = r.get("exit_quality_metrics") if isinstance(r.get("exit_quality_metrics"), dict) else {}
        mfe = _safe_float(eq.get("mfe_pct")) or _safe_float(
            (r.get("snapshot") or {}).get("mfe") if isinstance(r.get("snapshot"), dict) else None
        )
        if pnl_pct is not None and mfe is not None:
            mfe_pnl_pairs.append((mfe, pnl_pct))

    giveback = [m - p for m, p in mfe_pnl_pairs] if mfe_pnl_pairs else []
    gb_stats = _stats(giveback) if giveback else {"n": 0}

    md4 = [
        "# ALPACA_TIME_COUNTERFACTUALS",
        "",
        "## Status: +1m/+5m/+15m simulated exits",
        "",
    ]
    if bars_path.is_file():
        md4.append(f"- **Bars file present:** `{bars_path.relative_to(root)}` — run `scripts/replay_exit_timing_counterfactuals.py` for path-level counterfactuals (not executed in this read-only pass).")
    elif bars_alt:
        md4.append(f"- **Alternate bars sample:** `{bars_alt[0].relative_to(root)}` — same note.")
    else:
        md4.append("- **Bars file missing** under `artifacts/market_data/alpaca_bars.jsonl` — **no** per-trade minute-step simulation in this campaign.")

    md4.extend(
        [
            "",
            "## MFE vs realized pnl% proxy (rows with both)",
            "",
            f"- Pairs: **{len(mfe_pnl_pairs)}**",
            f"- Distribution of `(mfe_pct - pnl_pct)` — positive ⇒ left favorable excursion on table (sign depends on convention):",
            "",
            "```json",
            json.dumps({"giveback_or_left_on_table_delta_stats": gb_stats}, indent=2),
            "```",
            "",
            "## Limitation",
            "",
            "- MFE is path-dependent; without bar replay, minute buckets are **not** computed here.",
            "",
        ]
    )
    (ev / "ALPACA_TIME_COUNTERFACTUALS.md").write_text("\n".join(md4) + "\n", encoding="utf-8")

    # ---------- Phase 5 blocked ----------
    b_reasons = Counter()
    for b in blocked:
        for key in ("reason", "block_reason", "gate", "decision_outcome", "ci_reason"):
            v = b.get(key)
            if v:
                b_reasons[str(v)[:120]] += 1
                break
        else:
            b_reasons["(no_reason_field)"] += 1

    md5 = [
        "# ALPACA_BLOCKED_MISSED_INTEL",
        "",
        f"- **Blocked rows (tail):** {len(blocked)}",
        "",
        "## Reasons (top)",
        "",
    ]
    for reason, cnt in b_reasons.most_common(40):
        md5.append(f"- `{reason}`: **{cnt}**")
    md5.extend(
        [
            "",
            "## Net opportunity cost",
            "",
            "- **Not computed** without forward price path per blocked symbol/time (would be replay).",
            "",
            "## Gates strict vs loose",
            "",
            "- Use reason counts above + `run.jsonl` blocked intents for ops review; causal \"too strict\" needs A/B shadow.",
            "",
        ]
    )
    (ev / "ALPACA_BLOCKED_MISSED_INTEL.md").write_text("\n".join(md5) + "\n", encoding="utf-8")

    # ---------- Phase 6 SPI + orthogonality ----------
    comp_rows: List[Dict[str, float]] = []
    for _, comp in [x for arr in by_sym_snaps.values() for x in arr][-5000:]:
        comp_rows.append(comp)
    # unify keys
    keys = sorted(set(k for r in comp_rows for k in r))
    if len(keys) > 15:
        keys = keys[:15]
    slim = [{k: r.get(k) for k in keys if r.get(k) is not None} for r in comp_rows if r]
    ortho = _correlation_matrix(keys, [{k: r.get(k, 0.0) for k in keys} for r in comp_rows[:3000]])

    md6 = [
        "# ALPACA_SPI_ORTHOGONALITY_ANALYSIS",
        "",
        "## SPI artifacts",
        "",
    ]
    for s in inv["latest_spi_md"][:3]:
        md6.append(f"- `{s}` (see file for path-level narrative)")
    md6.extend(
        [
            "",
            "## Signal orthogonality (Pearson r, recent snapshot sample)",
            "",
            "High |r| suggests redundancy; does not prove overfitting.",
            "",
            "```json",
            json.dumps(ortho, indent=2)[:12000],
            "```",
            "",
            "## Overfitting risk",
            "",
            "- Many correlated features + small effective sample ⇒ elevated variance in any ranking from this tail.",
            "",
        ]
    )
    (ev / "ALPACA_SPI_ORTHOGONALITY_ANALYSIS.md").write_text("\n".join(md6) + "\n", encoding="utf-8")

    # ---------- Phase 7 synthesis ----------
    total_n = dir_stats["LONG"]["n"] + dir_stats["SHORT"]["n"]
    sum_all = dir_stats["LONG"]["sum_pnl"] + dir_stats["SHORT"]["sum_pnl"]
    struct_profitable = sum_all > 0 and total_n >= 20

    md7 = [
        "# ALPACA_PROFIT_WHY_SYNTHESIS",
        "",
        "## WHY we make money (evidence-limited)",
        "",
    ]
    top3 = ranking[:3]
    if top3:
        md7.append(
            "- Associated with **higher snapshot components** (see ranking): "
            + ", ".join(f"`{t['signal']}`" for t in top3)
            + " — **associational only**."
        )
    if dir_stats["LONG"]["expectancy"] and dir_stats["SHORT"]["expectancy"]:
        md7.append(
            f"- **Direction:** LONG E[pnl]={dir_stats['LONG']['expectancy']}, SHORT E[pnl]={dir_stats['SHORT']['expectancy']} in tail."
        )
    md7.extend(
        [
            "",
            "## WHY we lose money",
            "",
            "- Exit reasons with negative aggregate in tail (see exit analysis).",
            "- Giveback proxy `(mfe - pnl)` when positive suggests exits not at peak favorable excursion (mechanical, not optimal exit proof).",
            "",
            "## WHY signals may fail",
            "",
            "- Non-stationary regime; snapshot-exit mismatch; sparse UW in some names.",
            "",
            "## WHY exits hurt",
            "",
            "- Cluster of losses under specific `exit_reason` / dominant v2 component (see Phase 3).",
            "",
        ]
    )
    (ev / "ALPACA_PROFIT_WHY_SYNTHESIS.md").write_text("\n".join(md7) + "\n", encoding="utf-8")

    # ---------- Phase 8 action plan ----------
    actions = [
        {
            "rank": 1,
            "action": "Shadow-test direction filter per regime",
            "expected_impact": "Reduce drawdown if one direction is systematically negative in specific regimes",
            "risk": "Miss winners; sample split instability",
            "confidence": "LOW-MEDIUM (tail-only evidence)",
            "verification": "30d shadow ledger; compare realized vs baseline per regime cell",
            "rollback": "Disable shadow flag; no production gate",
        },
        {
            "rank": 2,
            "action": "Replay exit timing with bars artifact",
            "expected_impact": "Quantify minute-level opportunity cost vs realized",
            "risk": "Look-ahead if bars misaligned",
            "confidence": "MEDIUM when bars present",
            "verification": "Run replay_exit_timing_counterfactuals; compare distributions",
            "rollback": "Discard scenario JSON changes",
        },
        {
            "rank": 3,
            "action": "Deepen blocked-trade forward PnL lab",
            "expected_impact": "Estimate opportunity cost of gates",
            "risk": "Survivorship in manual labels",
            "confidence": "LOW without price path",
            "verification": "Replay blocked symbols with stored bars",
            "rollback": "N/A read-only",
        },
        {
            "rank": 4,
            "action": "Prune or downweight low-delta signals (from ranking tail)",
            "expected_impact": "Lower noise; faster decisions",
            "risk": "Remove hidden nonlinear value",
            "confidence": "LOW (median split ≠ causal)",
            "verification": "Shadow portfolio with component ablation",
            "rollback": "Restore weights from git",
        },
    ]
    (ev / "ALPACA_PROFIT_ACTION_PLAN.json").write_text(
        json.dumps({"actions": actions, "note": "Conceptual; NO production tuning in this mission"}, indent=2) + "\n",
        encoding="utf-8",
    )
    md8 = ["# ALPACA_PROFIT_ACTION_PLAN", "", "## Ranked actions", ""]
    for a in actions:
        md8.append(f"### Rank {a['rank']}: {a['action']}")
        for k in ("expected_impact", "risk", "confidence", "verification", "rollback"):
            md8.append(f"- **{k}:** {a[k]}")
        md8.append("")
    (ev / "ALPACA_PROFIT_ACTION_PLAN.md").write_text("\n".join(md8) + "\n", encoding="utf-8")

    # ---------- Phase 9 board ----------
    (ev / "BOARD_CSA_PROFIT_VERDICT.md").write_text(
        "\n".join(
            [
                "# BOARD_CSA_PROFIT_VERDICT",
                "",
                "## Causal validity",
                "",
                "- **Mostly associational.** Median splits on snapshots, regime/direction buckets — **not** IV or randomized.",
                "",
                "## Integrity",
                "",
                "- Read-only; no log mutation. Tail windows may omit oldest history.",
                "",
                "## Governance",
                "",
                "- Action plan is **shadow-first**; production gate changes would violate mission constraints.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ev / "BOARD_SRE_PROFIT_VERDICT.md").write_text(
        "\n".join(
            [
                "# BOARD_SRE_PROFIT_VERDICT",
                "",
                "## Operational",
                "",
                "- Campaign is CPU/IO bounded by jsonl tail reads; safe to run off-hours.",
                "",
                "## Performance",
                "",
                "- Full line counts scan large files O(n); tail read capped by `max_bytes`.",
                "",
                "## Monitoring gaps",
                "",
                "- No continuous dashboard for `mfe_pct - pnl_pct` distribution; consider metric export.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ev / "BOARD_QUANT_PROFIT_VERDICT.md").write_text(
        "\n".join(
            [
                "# BOARD_QUANT_PROFIT_VERDICT",
                "",
                "## Statistical validity",
                "",
                "- Subgroups (regime × direction) often **small n**; wide confidence intervals implied.",
                "",
                "## Sample size",
                "",
                f"- Directional stats: LONG n={dir_stats['LONG']['n']}, SHORT n={dir_stats['SHORT']['n']}.",
                f"- Snapshot-matched exits: {matched_exits}.",
                "",
                "## Overfitting",
                "",
                "- Ranking signals on same tail used for exploration inflates apparent edge; **holdout** or **walk-forward** required.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # ---------- Phase 10 ----------
    first_shadow = (
        "Shadow direction/regime gate with paper-only sizing; log counterfactual entry/exit from same signals; "
        "compare 30d to baseline without changing live gates."
    )
    md10 = [
        "# ALPACA_PROFIT_DISCOVERY_FINAL_VERDICT",
        "",
        f"- **Structurally profitable (tail, realized sum > 0, n≥20)?** **{'YES' if struct_profitable else 'NO'}**",
        f"  - sum_pnl LONG+SHORT in tail ≈ **{sum_all}**, n ≈ **{total_n}**",
        "",
        "- **If NO:** losses concentrated per exit-reason buckets and/or negative expectancy direction; **not** proven \"broken\" without full history and holdout.",
        "",
        "- **Shortest path to profitability:** improve **exit timing replay** (bars) + **gate opportunity lab** (blocked forward path) + **shadow ablation** on bottom-ranked signals.",
        "",
        f"- **First shadow experiment:** {first_shadow}",
        "",
        "## Evidence index",
        "",
        "- `ALPACA_PROFIT_INTEL_DATA_INVENTORY.md`",
        "- `ALPACA_DIRECTIONAL_PNL_ANALYSIS.md`",
        "- `ALPACA_SIGNAL_CONTRIBUTION_MATRIX.md` + `ALPACA_SIGNAL_RANKING.json`",
        "- `ALPACA_EXIT_CAUSAL_ANALYSIS.md`",
        "- `ALPACA_TIME_COUNTERFACTUALS.md`",
        "- `ALPACA_BLOCKED_MISSED_INTEL.md`",
        "- `ALPACA_SPI_ORTHOGONALITY_ANALYSIS.md`",
        "- `ALPACA_PROFIT_WHY_SYNTHESIS.md`",
        "- `ALPACA_PROFIT_ACTION_PLAN.md` + `.json`",
        "- Board: `BOARD_*_PROFIT_VERDICT.md`",
        "",
    ]
    (ev / "ALPACA_PROFIT_DISCOVERY_FINAL_VERDICT.md").write_text("\n".join(md10) + "\n", encoding="utf-8")

    return ev


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--max-exit-rows", type=int, default=25000)
    ap.add_argument("--max-snapshot-rows", type=int, default=60000)
    ap.add_argument("--max-blocked-rows", type=int, default=15000)
    ap.add_argument("--max-signal-context-rows", type=int, default=20000)
    args = ap.parse_args()
    ev = run_campaign(
        args.root,
        args.max_exit_rows,
        args.max_snapshot_rows,
        args.max_blocked_rows,
        args.max_signal_context_rows,
    )
    print(str(ev))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
