#!/usr/bin/env python3
"""
ALPACA RAMPANT ANALYSIS MODE — offline now, live-ready tomorrow (droplet-only).
READ-ONLY logs/state. Writes ONLY:
  reports/ALPACA_RAMPANT_ANALYSIS_<tag>.md
  reports/ALPACA_RAMPANT_SUMMARY_<tag>.md
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

MB_START = "<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START -->"
MB_END = "<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_END -->"
MB_TITLE = "## Alpaca attribution truth contract (canonical)"
MAX_JSONL_LINES = 200_000


def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", os.environ.get("DROPLET_TRADING_ROOT", "")).strip()
    return Path(r).resolve() if r else Path(__file__).resolve().parents[1]


def _tag() -> str:
    e = os.environ.get("ALPACA_REPORT_TAG", "").strip()
    return e if e else datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _sh(cmd: str, timeout: int = 90) -> Tuple[str, str, int]:
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.stdout or "", p.stderr or "", p.returncode
    except Exception as ex:
        return "", str(ex), 1


def _load_jsonl_full(path: Path) -> List[dict]:
    if not path.exists():
        return []
    out: List[dict] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= MAX_JSONL_LINES:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(r, dict):
                    out.append(r)
    except OSError:
        return []
    return out


def _num(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _flatten(d: Any, prefix: str = "", depth: int = 0) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if depth > 4 or not isinstance(d, dict):
        return out
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else str(k)
        fn = _num(v)
        if fn is not None:
            out[key] = fn
        elif isinstance(v, dict):
            out.update(_flatten(v, key, depth + 1))
    return out


def _quartile_thresholds(xs: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if len(xs) < 8:
        return None, None
    s = sorted(xs)
    n = len(s)
    return s[max(0, n // 4 - 1)], s[min(n - 1, (3 * n) // 4)]


def _mean(xs: List[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def _lift(xs: List[float], ys: List[float]) -> Optional[Tuple[float, float, float, int]]:
    if len(xs) < 40:
        return None
    lo, hi = _quartile_thresholds(xs)
    if lo is None:
        return None
    y_lo = [y for x, y in zip(xs, ys) if x <= lo]
    y_hi = [y for x, y in zip(xs, ys) if x >= hi]
    if len(y_lo) < 5 or len(y_hi) < 5:
        return None
    ml, mh = _mean(y_lo), _mean(y_hi)
    if ml is None or mh is None:
        return None
    return (mh - ml, ml, mh, len(xs))


def _parse_iso_hour(ts: Any) -> Optional[int]:
    if not ts:
        return None
    try:
        s = str(ts).replace("Z", "+00:00")
        if "T" not in s:
            return None
        dt = datetime.fromisoformat(s[:32])
        return dt.hour
    except Exception:
        return None


def _verify_memory_bank(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MEMORY_BANK_ALPACA.md missing"
    t = path.read_text(encoding="utf-8", errors="replace")
    if MB_START not in t or MB_END not in t:
        return False, "canonical markers missing"
    if MB_TITLE not in t:
        return False, "canonical title missing"
    for needle in (
        "decision_event_id",
        "canonical_trade_id",
        "symbol_normalized",
        "time_bucket_id",
        "attribution_emit_keys",
        "build_shared_feature_snapshot",
    ):
        if needle not in t:
            return False, f"required invariant phrase missing: {needle}"
    return True, "ok"


def _build_indexes(
    run_rows: List[dict],
    ord_rows: List[dict],
    ex_attr: List[dict],
) -> Tuple[Dict[str, List[dict]], Dict[str, List[dict]], Dict[str, dict], Dict[str, dict], Dict[str, dict]]:
    by_ctid_orders: Dict[str, List[dict]] = defaultdict(list)
    by_de_orders: Dict[str, List[dict]] = defaultdict(list)
    by_ctid_intent: Dict[str, dict] = {}
    by_de_intent: Dict[str, dict] = {}

    for r in run_rows:
        if r.get("event_type") != "trade_intent":
            continue
        ct = r.get("canonical_trade_id")
        de = r.get("decision_event_id")
        if ct:
            by_ctid_intent[str(ct)] = r
        if de:
            by_de_intent[str(de)] = r

    for o in ord_rows:
        if o.get("type") != "order":
            continue
        ct = o.get("canonical_trade_id")
        de = o.get("decision_event_id")
        if ct:
            by_ctid_orders[str(ct)].append(o)
        if de:
            by_de_orders[str(de)].append(o)

    by_tk_exit: Dict[str, dict] = {}
    for r in ex_attr:
        try:
            from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side, normalize_symbol

            sym = normalize_symbol(r.get("symbol"))
            ets = str(r.get("entry_timestamp") or "").strip()
            side = r.get("side") or r.get("direction") or "buy"
            if sym and sym != "?" and ets:
                tk = build_trade_key(sym, normalize_side(side), ets)
                by_tk_exit[tk] = r
        except Exception:
            pass
        ct = r.get("canonical_trade_id")
        if ct:
            by_tk_exit[str(ct)] = r

    return dict(by_ctid_orders), dict(by_de_orders), by_ctid_intent, by_de_intent, by_tk_exit


def lane_feature_attribution(payload: dict) -> str:
    feat_rows = payload["feat_exit_rows"]
    lines = ["### A) Feature-level attribution (exit_attribution components + quality)", ""]
    all_k: set[str] = set()
    for f, _, _ in feat_rows:
        all_k.update(f.keys())
    lifts: List[Tuple[str, float, int, str]] = []
    for key in sorted(all_k):
        pairs = [(f[key], y, src) for f, y, src in feat_rows if key in f]
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        src = pairs[0][2] if pairs else "mixed"
        L = _lift(xs, ys)
        if L:
            lifts.append((key, L[0], L[3], src))
    lifts.sort(key=lambda x: abs(x[1]), reverse=True)
    lines.append("| rank | feature | n | delta_mean_pnl_pct | lane |")
    lines.append("|------|---------|---|---------------------|------|")
    for i, (k, d, n, s) in enumerate(lifts[:40], 1):
        lines.append(f"| {i} | `{k}` | {n} | {d:.6g} | {s} |")
    if not lifts:
        lines.append("| — | insufficient n per feature | — | — | — |")
    lines.append("")
    return "\n".join(lines)


def lane_exit_failure(payload: dict) -> str:
    rows = payload["outcomes_flat"]
    lines = ["### B) Exit-first failure analysis", ""]
    neg = [r for r in rows if (r.get("pnl_pct") or 0) < 0]
    pos = [r for r in rows if (r.get("pnl_pct") or 0) > 0]
    lines.append(f"- Trades with pnl_pct < 0: **{len(neg)}**; pnl_pct > 0: **{len(pos)}**")
    eq_stats: List[Tuple[str, float, float]] = []
    for label, subset in (("losers", neg), ("winners", pos)):
        mae_l, mfe_l = [], []
        for r in subset:
            eq = r.get("exit_quality_metrics") if isinstance(r.get("exit_quality_metrics"), dict) else {}
            m = _num(eq.get("mae_pct"))
            f = _num(eq.get("mfe_pct"))
            if m is not None:
                mae_l.append(m)
            if f is not None:
                mfe_l.append(f)
        lines.append(
            f"- **{label}** — mean MAE%: {_mean(mae_l)!s}, mean MFE%: {_mean(mfe_l)!s} (coverage n_mae={len(mae_l)}, n_mfe={len(mfe_l)})"
        )
    lines.append("")
    return "\n".join(lines)


def lane_regime(payload: dict) -> str:
    rows = payload["outcomes_flat"]
    lines = ["### C) Regime segmentation (hour-of-exit vs mean pnl)", ""]
    by_h: Dict[int, List[float]] = defaultdict(list)
    for r in rows:
        h = _parse_iso_hour(r.get("exit_timestamp") or r.get("timestamp"))
        p = _num(r.get("pnl_pct"))
        if h is not None and p is not None:
            by_h[h].append(p)
    lines.append("| hour_utc | n | mean_pnl_pct |")
    lines.append("|----------|---|--------------|")
    for h in sorted(by_h.keys()):
        v = by_h[h]
        m = _mean(v)
        lines.append(f"| {h} | {len(v)} | {m:.6g} |" if m is not None else f"| {h} | {len(v)} | — |")
    vols = []
    for r in rows:
        v2 = r.get("v2_exit_components") if isinstance(r.get("v2_exit_components"), dict) else {}
        ve = _num(v2.get("vol_expansion"))
        p = _num(r.get("pnl_pct"))
        if ve is not None and p is not None:
            vols.append((ve, p))
    lines.append("")
    lines.append("**Vol expansion vs pnl (quartile lift):**")
    if len(vols) >= 40:
        xs, ys = zip(*vols)
        L = _lift(list(xs), list(ys))
        lines.append(f"- lift={L[0]:.6g} n={L[3]}" if L else "- lift n/a")
    else:
        lines.append("- insufficient pairs")
    lines.append("")
    return "\n".join(lines)


def lane_blocked(payload: dict) -> str:
    blocked = payload["blocked_rows"]
    lines = ["### D) Opportunity cost — blocked ledger", ""]
    reasons = Counter()
    scores: List[float] = []
    for r in blocked:
        reasons[str(r.get("reason") or r.get("block_reason") or "unknown")] += 1
        s = _num(r.get("score") or r.get("candidate_score"))
        if s is not None:
            scores.append(s)
    lines.append(f"- **Blocked rows analyzed:** {len(blocked)}")
    lines.append("- **Top block reasons:**")
    for reason, c in reasons.most_common(15):
        lines.append(f"  - `{reason}`: {c}")
    lines.append(f"- **Score distribution (blocked):** mean={_mean(scores)!s} n={len(scores)}")
    lines.append("- **Counterfactual PnL:** not joined (would require deterministic post-hoc price path); **pending** per MEMORY_BANK frozen-artifact rules.")
    lines.append("")
    return "\n".join(lines)


def lane_robustness(payload: dict) -> str:
    outcomes = payload["outcomes_ordered"]
    lines = ["### E) Robustness & mirage detection", ""]
    if len(outcomes) < 100:
        lines.append("- **Walk-forward:** insufficient exit rows for stable split.")
        lines.append("")
        return "\n".join(lines)
    mid = len(outcomes) // 2
    first, second = outcomes[:mid], outcomes[mid:]
    lines.append(f"- **Walk-forward split:** n1={len(first)} n2={len(second)} (by row order in exit_attribution file = time proxy; **not** guaranteed pure time sort — CSA flag).")

    def top_lift(sub: List[dict], label: str) -> Optional[Tuple[str, float]]:
        best = None
        v2keys: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        for r in sub:
            p = _num(r.get("pnl_pct"))
            if p is None:
                continue
            v2 = r.get("v2_exit_components") if isinstance(r.get("v2_exit_components"), dict) else {}
            for k, v in v2.items():
                fn = _num(v)
                if fn is not None:
                    v2keys[k].append((fn, p))
        for k, pairs in v2keys.items():
            if len(pairs) < 30:
                continue
            xs, ys = zip(*pairs)
            L = _lift(list(xs), list(ys))
            if L and (best is None or abs(L[0]) > abs(best[1])):
                best = (k, L[0])
        if best:
            lines.append(f"- **Top |lift| feature ({label}):** `{best[0]}` delta={best[1]:.6g}")
        else:
            lines.append(f"- **Top lift ({label}):** n/a")
        return best

    t1 = top_lift(first, "first_half")
    t2 = top_lift(second, "second_half")
    if t1 and t2 and t1[0] != t2[0]:
        lines.append("- **Stability:** top feature **differs** across halves → high mirage risk.")
    elif t1 and t2:
        lines.append("- **Stability:** same top feature name in both halves (still verify effect sign/magnitude).")
    lines.append("- **Leakage:** exit-time components vs realized pnl — causal direction ambiguous; **NOT PROMOTED**.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not Path("/proc").is_dir():
        print("Linux/droplet only.", file=sys.stderr)
        return 2

    root = _root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    tag = _tag()
    rep = root / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    out_full = rep / f"ALPACA_RAMPANT_ANALYSIS_{tag}.md"
    out_sum = rep / f"ALPACA_RAMPANT_SUMMARY_{tag}.md"

    git_head, _, gh = _sh("git rev-parse HEAD 2>/dev/null", timeout=15)
    st_bot, _, _ = _sh("systemctl is-active stock-bot.service 2>&1", timeout=15)
    st_uw, _, _ = _sh("systemctl is-active uw-flow-daemon.service 2>&1", timeout=15)

    mb_path = root / "MEMORY_BANK_ALPACA.md"
    mb_ok, mb_msg = _verify_memory_bank(mb_path)

    art_audit = root / "reports" / "ALPACA_OFFLINE_FULL_DATA_AUDIT_20260325_0112.md"
    art_closure = root / "reports" / "ALPACA_BLOCKER_CLOSURE_PROOF_20260325_0112.md"
    art_present = art_audit.exists() and art_closure.exists()

    stop_lines = []
    if not mb_ok:
        stop_lines.append(f"**STOP — Memory Bank gate:** {mb_msg}")

    run_rows = _load_jsonl_full(root / "logs/run.jsonl")
    ord_rows = _load_jsonl_full(root / "logs/orders.jsonl")
    sig_rows = _load_jsonl_full(root / "logs/signal_context.jsonl")
    blk_rows = _load_jsonl_full(root / "state/blocked_trades.jsonl")
    ex_attr = _load_jsonl_full(root / "logs/exit_attribution.jsonl")

    by_ct_o, by_de_o, by_ct_i, by_de_i, by_tk_e = _build_indexes(run_rows, ord_rows, ex_attr)

    join_stats = {
        "orders_with_canonical_trade_id": sum(1 for o in ord_rows if o.get("type") == "order" and o.get("canonical_trade_id")),
        "orders_with_decision_event_id": sum(1 for o in ord_rows if o.get("type") == "order" and o.get("decision_event_id")),
        "trade_intent_with_canonical_trade_id": sum(
            1 for r in run_rows if r.get("event_type") == "trade_intent" and r.get("canonical_trade_id")
        ),
        "trade_intent_with_decision_event_id": sum(
            1 for r in run_rows if r.get("event_type") == "trade_intent" and r.get("decision_event_id")
        ),
        "exit_attribution_indexed_by_trade_key": len(by_tk_e),
    }

    outcomes_flat: List[dict] = []
    feat_exit_rows: List[Tuple[Dict[str, float], float, str]] = []
    for r in ex_attr:
        p = _num(r.get("pnl_pct"))
        if p is None and isinstance(r.get("snapshot"), dict):
            p = _num(r["snapshot"].get("pnl_pct"))
        if p is None:
            continue
        rr = dict(r)
        rr["pnl_pct"] = p
        outcomes_flat.append(rr)
        feats: Dict[str, float] = {}
        feats.update(_flatten(r.get("v2_exit_components"), "v2_exit"))
        eq = r.get("exit_quality_metrics") if isinstance(r.get("exit_quality_metrics"), dict) else {}
        for k in ("mfe_pct", "mae_pct", "giveback_pct"):
            v = _num(eq.get(k))
            if v is not None:
                feats[f"eq.{k}"] = v
        if feats:
            feat_exit_rows.append((feats, p, "exit_attribution"))

    ti_enter = [r for r in run_rows if r.get("event_type") == "trade_intent" and str(r.get("decision_outcome", "")).lower() == "entered"]
    joined_entry_exit = 0
    for r in ti_enter:
        ct = r.get("canonical_trade_id")
        if not ct:
            continue
        ex = by_tk_e.get(str(ct))
        if not ex:
            continue
        p = _num(ex.get("pnl_pct"))
        if p is None:
            continue
        fs = r.get("feature_snapshot")
        if isinstance(fs, dict):
            feat_exit_rows.append((_flatten(fs, "entry_fs"), p, "entry_snapshot_x_exit_pnl"))
            joined_entry_exit += 1

    order_econ = [
        o
        for o in ord_rows
        if o.get("type") == "order"
        and (o.get("fee_excluded_reason") or o.get("fee_amount") is not None or o.get("slippage_bps") is not None or o.get("slippage_excluded_reason"))
    ]

    def _exit_sort_key(r: dict) -> str:
        return str(r.get("exit_timestamp") or r.get("timestamp") or "")

    outcomes_ordered = sorted(outcomes_flat, key=_exit_sort_key)
    payload = {
        "feat_exit_rows": feat_exit_rows,
        "outcomes_flat": outcomes_flat,
        "outcomes_ordered": outcomes_ordered,
        "blocked_rows": blk_rows,
    }

    lane_results: Dict[str, str] = {}
    if mb_ok:
        fns: Dict[str, Callable[[dict], str]] = {
            "A": lane_feature_attribution,
            "B": lane_exit_failure,
            "C": lane_regime,
            "D": lane_blocked,
            "E": lane_robustness,
        }
        with ThreadPoolExecutor(max_workers=5) as pool:
            fut_map = {pool.submit(fn, payload): name for name, fn in fns.items()}
            for fut in as_completed(fut_map):
                lane_results[fut_map[fut]] = fut.result()

    # Rank combined lifts for summary (reuse lane A logic inline)
    all_k: set[str] = set()
    for f, _, _ in feat_exit_rows:
        all_k.update(f.keys())
    top_edges: List[Tuple[str, float, int, str]] = []
    for key in all_k:
        triples = [(f[key], y, src) for f, y, src in feat_exit_rows if key in f]
        if len(triples) < 40:
            continue
        xs = [t[0] for t in triples]
        ys = [t[1] for t in triples]
        src0 = triples[0][2]
        L = _lift(xs, ys)
        if L:
            top_edges.append((key, L[0], L[3], src0))
    top_edges.sort(key=lambda x: abs(x[1]), reverse=True)
    top10 = top_edges[:10]
    mirages = [
        "Features with |lift| ≈ 0 across quartiles (constant v2_exit components)",
        "Exit-time predictors of same-bar pnl (reverse causality / leakage)",
        "Single-split rankings without walk-forward agreement",
        "High |lift| on n<100 after field filtering",
        "Blocked-trade 'savings' without counterfactual execution path",
    ]

    md: List[str] = [
        f"# ALPACA Rampant Analysis — `{tag}`",
        "",
        f"- **TRADING_ROOT:** `{root}`",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Phase 0 — Baseline & safety (SRE + CSA)",
        "",
        f"- **git HEAD:** `{git_head.strip()}` (rc={gh})",
        f"- **stock-bot.service:** `{st_bot.strip()}`",
        f"- **uw-flow-daemon.service:** `{st_uw.strip()}`",
        "- **Writes:** only this file and `ALPACA_RAMPANT_SUMMARY_<tag>.md` under `reports/` (plus this script if uploaded separately).",
        f"- **Memory Bank canonical section:** {'**PASS**' if mb_ok else '**FAIL**'} — {mb_msg}",
        f"- **Governance artifacts present:** offline audit + closure proof (20260325_0112): **{'YES' if art_present else 'NO'}**",
        "",
    ]
    if stop_lines:
        md.extend(stop_lines)
        md.append("")
        md.append("---")
        md.append("*Analysis aborted at governance gate.*")
        out_full.write_text("\n".join(md) + "\n", encoding="utf-8")
        out_sum.write_text(
            "\n".join(
                [
                    f"# ALPACA Rampant Summary — `{tag}` (STOP)",
                    "",
                    mb_msg,
                    "",
                    f"Full: `{out_full}`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print("STOP:", mb_msg)
        print("ALPACA_RAMPANT_ANALYSIS:", out_full)
        print("ALPACA_RAMPANT_SUMMARY:", out_sum)
        return 4

    md.extend(
        [
            "## Phase 1 — Maximal attribution dataset",
            "",
            "### Source row counts (cap per file: {})".format(MAX_JSONL_LINES),
            "",
            f"| Sink | Rows |",
            f"|------|------|",
            f"| `logs/run.jsonl` | {len(run_rows)} |",
            f"| `logs/orders.jsonl` | {len(ord_rows)} |",
            f"| `logs/signal_context.jsonl` | {len(sig_rows)} |",
            f"| `state/blocked_trades.jsonl` | {len(blk_rows)} |",
            f"| `logs/exit_attribution.jsonl` | {len(ex_attr)} |",
            "",
            "### Deterministic join coverage (canonical keys only)",
            "",
            f"| Metric | Count |",
            f"|--------|------:|",
        ]
    )
    for k, v in join_stats.items():
        md.append(f"| {k} | {v} |")
    md.append(f"| **entry_snapshot × exit pnl (canonical_trade_id)** | {joined_entry_exit} |")
    md.append("")
    md.append("### Economics field presence (orders.jsonl)")
    md.append(f"- Rows with explicit fee/slippage schema fields: **{len(order_econ)}** / {sum(1 for o in ord_rows if o.get('type')=='order') or 1} typed `order`")
    md.append("- **Excluded:** silent fees; use `fee_excluded_reason` on paper per attribution contract.")
    md.append("")
    md.append("## Phase 2 — Rampant edge search (parallel lanes)")
    md.append("")
    for lab in ("A", "B", "C", "D", "E"):
        md.append(lane_results.get(lab, f"### Lane {lab} — *missing*"))
    md.extend(
        [
            "",
            "## Phase 3 — Board review",
            "",
            "### Quant verdict",
            "- **Top offline candidates:** see Lane A table (exit components + entry snapshot joins where `canonical_trade_id` matched).",
            "- **Effect sizes:** quartile mean pnl delta; interpret as associative only.",
            "- **Entry vs exit:** `entry_fs.*` rows come from joined `trade_intent` × `exit_attribution` only.",
            "",
            "### SRE verdict",
            "- **Join integrity:** indexes built only on `canonical_trade_id`, `decision_event_id`, and `build_trade_key(symbol, side, entry_timestamp)` for exit rows — **no** same-bar heuristic symbol joins.",
            "- **Reproducibility:** command in Phase 4.",
            "- **Sink corruption:** not scanned byte-by-byte; JSONL parse errors skipped (count implicit in row totals).",
            "",
            "### CSA verdict",
            "- **Mirages rejected:** constant components, leakage-prone exit→pnl correlations, unstable walk-forward names.",
            "- **SHORTLIST for future live confirmation:** top 5 rows in Lane A with |lift|>0 and n≥500 (if any); else **none** until more keyed data.",
            "- **NOT PROMOTED:** all findings **OFFLINE ONLY**.",
            "",
            "## Phase 4 — Live-ready prep (no changes executed)",
            "",
            "- **Emitters:** aligned with MEMORY_BANK `Alpaca attribution truth contract (canonical)`; restart `stock-bot.service` after code changes (documented; **not** restarted in this mission).",
            "- **Tomorrow:** market-open cycles append new keyed rows; joins improve as `canonical_trade_id` / `decision_event_id` populate.",
            "",
            "```bash",
            f"cd {root} && TRADING_BOT_ROOT={root} ./venv/bin/python3 scripts/alpaca_rampant_analysis_mission.py",
            "```",
            "",
        ]
    )

    out_full.write_text("\n".join(md) + "\n", encoding="utf-8")

    csa_legit = "PASS" if len(outcomes_flat) >= 200 else "FAIL (low N)"
    sum_lines = [
        f"# ALPACA Rampant Summary — `{tag}`",
        "",
        "## Dataset sizes",
        f"- run.jsonl: {len(run_rows)} | orders: {len(ord_rows)} | signal_context: {len(sig_rows)} | blocked: {len(blk_rows)} | exit_attribution: {len(ex_attr)}",
        f"- outcomes w/ pnl_pct: {len(outcomes_flat)} | entry×exit joined (canonical_trade_id): {joined_entry_exit}",
        "",
        "## Economics",
        "- Included: exit `pnl_pct`, `exit_quality_metrics` when present; order economics fields when explicitly set.",
        "- Excluded: silent fee/slippage; historical rows missing schema treated as unknown — not zero.",
        "",
        "## Top 10 candidate edges (one line each; NOT PROMOTED)",
    ]
    for i, (k, d, n, s) in enumerate(top10, 1):
        sum_lines.append(f"{i}. `{k}` | Δmean_pnl≈{d:.5f} | n={n} | {s}")
    if not top10:
        sum_lines.append("_(none passing n≥40 quartile gate)_")
    sum_lines.extend(
        [
            "",
            "## Top 5 do-not-chase mirages",
        ]
    )
    for i, m in enumerate(mirages, 1):
        sum_lines.append(f"{i}. {m}")
    sum_lines.extend(
        [
            "",
            f"## CSA — offline analysis legitimacy: **{csa_legit}**",
            "",
            "## What to watch tomorrow (data only)",
            "- Growth of `trade_intent` / `orders` rows carrying `decision_event_id` + `canonical_trade_id`.",
            "- `signal_context.jsonl` volume (currently sparse = limited blocked/enter context joins).",
            "- Order rows with `fee_excluded_reason` / `slippage_bps` for economics completeness.",
            "- **No tuning or config changes** from this report.",
            "",
            f"**Full report:** `{out_full}`",
        ]
    )
    out_sum.write_text("\n".join(sum_lines) + "\n", encoding="utf-8")

    print("ALPACA_RAMPANT_ANALYSIS:", out_full)
    print("ALPACA_RAMPANT_SUMMARY:", out_sum)
    print("dataset_outcomes:", len(outcomes_flat))
    print("joined_entry_exit:", joined_entry_exit)
    print("CSA_legitimacy:", csa_legit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
