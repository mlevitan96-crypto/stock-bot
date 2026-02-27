#!/usr/bin/env python3
"""
Adjustment chain forensics: join ledger ↔ adjustment logs, attribute deltas, dominant killer.
Run on DROPLET from repo root. Writes reports/score_autopsy/*.md and bars_alignment_20_sample.md.
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "score_autopsy"
LEDGER_PATH = REPO / "reports" / "decision_ledger" / "decision_ledger.jsonl"
SIGNAL_QUALITY_LOG = REPO / "logs" / "signal_quality_adjustments.jsonl"
UW_ADJUSTMENTS_LOG = REPO / "logs" / "uw_entry_adjustments.jsonl"
SURVIVORSHIP_LOG = REPO / "logs" / "survivorship_entry_adjustments.jsonl"
ATTRIBUTION_PATH = REPO / "logs" / "attribution.jsonl"
BARS_DIR = REPO / "data" / "bars"
DAILY_PARQUET = REPO / "data" / "bars" / "alpaca_daily.parquet"

TOL = 0.08  # score_before match tolerance for join


def load_jsonl(path: Path, limit: int = 100000):
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(out) >= limit:
            break
    return out


def load_ledger():
    events = []
    if not LEDGER_PATH.exists():
        return events
    for line in LEDGER_PATH.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            sr = e.get("signal_raw") or {}
            pre = sr.get("score") if isinstance(sr, dict) else None
            if pre is not None:
                try:
                    pre = float(pre)
                except (TypeError, ValueError):
                    pre = None
            post = e.get("score_final")
            if post is not None:
                try:
                    post = float(post)
                except (TypeError, ValueError):
                    post = None
            if pre is not None and post is not None:
                e["_pre"] = pre
                e["_post"] = post
                e["_drop"] = pre - post
                events.append(e)
        except json.JSONDecodeError:
            continue
    return events


def join_event_to_adjustments(event, sq_by_sym, uw_by_sym, surv_by_sym):
    """Best-effort: for one event (symbol, _pre, _post), find matching adjustment lines. Returns (delta_sq, delta_uw, delta_surv, reason_sq, reason_uw, reason_surv)."""
    symbol = event.get("symbol", "")
    pre = event.get("_pre", 0)
    post = event.get("_post", 0)
    delta_sq = delta_uw = delta_surv = 0.0
    reason_sq = reason_uw = reason_surv = ""

    # Signal quality: find line with symbol and score_before ≈ pre
    sq_candidates = [r for r in (sq_by_sym.get(symbol) or []) if abs(float(r.get("score_before", 0)) - pre) <= TOL]
    if sq_candidates:
        r = min(sq_candidates, key=lambda r: abs(float(r.get("score_before", 0)) - pre))
        delta_sq = float(r.get("delta", 0))
        reason_sq = f"delta={delta_sq:.3f}"
    after_sq = pre + delta_sq

    # UW: find line with symbol and score_before ≈ after_sq
    uw_candidates = [r for r in (uw_by_sym.get(symbol) or []) if abs(float(r.get("score_before", 0)) - after_sq) <= TOL]
    if uw_candidates:
        r = min(uw_candidates, key=lambda r: abs(float(r.get("score_before", 0)) - after_sq))
        delta_uw = float(r.get("delta", 0))
        if r.get("rejected"):
            reason_uw = "rejected_low_quality"
        else:
            reason_uw = f"delta={delta_uw:.3f}"
    after_uw = after_sq + delta_uw

    # Survivorship: find line with symbol and score_before ≈ after_uw
    surv_candidates = [r for r in (surv_by_sym.get(symbol) or []) if abs(float(r.get("score_before", 0)) - after_uw) <= TOL]
    if surv_candidates:
        r = min(surv_candidates, key=lambda r: abs(float(r.get("score_before", 0)) - after_uw))
        delta_surv = float(r.get("delta", 0))
        reason_surv = r.get("action") or f"delta={delta_surv:.3f}"
    return delta_sq, delta_uw, delta_surv, reason_sq, reason_uw, reason_surv


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    events = load_ledger()
    if not events:
        (OUT_DIR / "adjustment_delta_attribution.md").write_text(
            "No ledger found. Run run_decision_ledger_capture.py first.\n", encoding="utf-8"
        )
        print("No ledger events.")
        return 0

    # Load adjustment logs and group by symbol
    sq_lines = load_jsonl(SIGNAL_QUALITY_LOG, limit=50000)
    uw_lines = load_jsonl(UW_ADJUSTMENTS_LOG, limit=50000)
    surv_lines = load_jsonl(SURVIVORSHIP_LOG, limit=50000)
    sq_by_sym = defaultdict(list)
    uw_by_sym = defaultdict(list)
    surv_by_sym = defaultdict(list)
    for r in sq_lines:
        sq_by_sym[r.get("symbol", "")].append(r)
    for r in uw_lines:
        uw_by_sym[r.get("symbol", "")].append(r)
    for r in surv_lines:
        surv_by_sym[r.get("symbol", "")].append(r)

    # Join: for each event get deltas (best-effort)
    killed = []  # pre >= 2.5 and post < 2.5
    deltas_sq, deltas_uw, deltas_surv = [], [], []
    for e in events:
        dq, du, ds, rq, ru, rs = join_event_to_adjustments(e, sq_by_sym, uw_by_sym, surv_by_sym)
        e["_delta_sq"] = dq
        e["_delta_uw"] = du
        e["_delta_surv"] = ds
        e["_reason_sq"] = rq
        e["_reason_uw"] = ru
        e["_reason_surv"] = rs
        deltas_sq.append(dq)
        deltas_uw.append(du)
        deltas_surv.append(ds)
        if e.get("_pre", 0) >= 2.5 and e.get("_post", 0) < 2.5:
            killed.append(e)

    # Aggregate by stage: kill count (score_before>=2.5 and score_after<2.5) from raw logs.
    # UW: also count lines with rejected=True (no score_after written).
    def kill_count_sq_surv(log_lines):
        return sum(1 for r in log_lines if float(r.get("score_before") or 0) >= 2.5 and float(r.get("score_after") or 0) < 2.5)

    def kill_count_uw(log_lines):
        n = sum(1 for r in log_lines if float(r.get("score_before") or 0) >= 2.5 and float(r.get("score_after") or 0) < 2.5)
        n += sum(1 for r in log_lines if r.get("rejected") is True)
        return n

    sq_kills = kill_count_sq_surv(sq_lines)
    uw_kills = kill_count_uw(uw_lines)
    surv_kills = kill_count_sq_surv(surv_lines)
    total_drop = sum(e.get("_drop", 0) for e in events)
    sum_sq = sum(e.get("_delta_sq", 0) for e in events)
    sum_uw = sum(e.get("_delta_uw", 0) for e in events)
    sum_surv = sum(e.get("_delta_surv", 0) for e in events)
    pct_sq = 100 * sum_sq / total_drop if total_drop != 0 else 0
    pct_uw = 100 * sum_uw / total_drop if total_drop != 0 else 0
    pct_surv = 100 * sum_surv / total_drop if total_drop != 0 else 0

    # Dominant killer: stage with highest kill count
    stage_kills = [("signal_quality", sq_kills), ("uw", uw_kills), ("survivorship", surv_kills)]
    dominant_stage = max(stage_kills, key=lambda x: x[1])[0]
    dominant_count = max(sq_kills, uw_kills, surv_kills)

    # Top punitive rules per stage (from raw logs)
    from collections import Counter

    def rule_counts_surv(log_lines):
        c = Counter()
        for r in log_lines:
            if float(r.get("score_before") or 0) >= 2.5 and float(r.get("score_after") or 0) < 2.5:
                c[str(r.get("action") or "delta")] += 1
        return c.most_common(10)

    def rule_counts_uw(log_lines):
        c = Counter()
        for r in log_lines:
            if r.get("rejected") is True:
                c["rejected_low_quality"] += 1
            elif float(r.get("score_before") or 0) >= 2.5 and float(r.get("score_after") or 0) < 2.5:
                c[f"delta={r.get('delta')}"] += 1
        return c.most_common(10)

    sq_rule_agg = Counter()
    for r in sq_lines:
        if float(r.get("score_before") or 0) >= 2.5 and float(r.get("score_after") or 0) < 2.5:
            sq_rule_agg[round(float(r.get("delta", 0)), 3)] += 1
    sq_rules = sq_rule_agg.most_common(10)
    surv_rules = rule_counts_surv(surv_lines)
    uw_rules = rule_counts_uw(uw_lines)

    dominant_rule = "unknown"
    if dominant_stage == "survivorship" and surv_rules:
        dominant_rule = str(surv_rules[0][0])
    elif dominant_stage == "uw" and uw_rules:
        dominant_rule = str(uw_rules[0][0])
    elif dominant_stage == "signal_quality" and sq_rules:
        dominant_rule = f"delta={sq_rules[0][0]}"

    # --- 1) adjustment_delta_attribution.md ---
    lines = [
        "# Adjustment delta attribution (droplet)",
        "",
        "## Join strategy",
        "Ledger events have pre_score = signal_raw.score, post_score = score_final. Adjustment logs have no timestamps; join by symbol + score_before within tolerance 0.08. For each event we pick from each log the line with same symbol and score_before closest to expected (pre, after_sq, after_uw). Best-effort; document exact logic in script.",
        "",
        "## Distribution of deltas per stage (joined)",
        f"- delta_signal_quality: median={median(deltas_sq):.4f}, mean={sum(deltas_sq)/len(deltas_sq):.4f}, n={len(deltas_sq)}",
        f"- delta_uw: median={median(deltas_uw):.4f}, mean={sum(deltas_uw)/len(deltas_uw):.4f}",
        f"- delta_survivorship: median={median(deltas_surv):.4f}, mean={sum(deltas_surv)/len(deltas_surv):.4f}",
        "",
        "## % of total drop attributable to each stage (sum of joined deltas)",
        f"- signal_quality: {pct_sq:.1f}%",
        f"- uw: {pct_uw:.1f}%",
        f"- survivorship: {pct_surv:.1f}%",
        "",
        "## Kill counts (raw log: score_before>=2.5 and score_after<2.5)",
        f"- signal_quality: {sq_kills}",
        f"- uw: {uw_kills}",
        f"- survivorship: {surv_kills}",
        "",
        "## Dominant killer",
        f"- Stage: **{dominant_stage}**",
        f"- Rule/reason: **{dominant_rule}** (kill count from raw log: {dominant_count})",
        "",
        "## Top 10 punitive rules per stage (count)",
    ]
    lines.append("### signal_quality (delta bucket)")
    for k, v in sq_rules:
        lines.append(f"- {k}: {v}")
    lines.append("### uw")
    for k, v in uw_rules:
        lines.append(f"- {k}: {v}")
    lines.append("### survivorship (action)")
    for k, v in surv_rules[:10]:
        lines.append(f"- {k}: {v}")
    (OUT_DIR / "adjustment_delta_attribution.md").write_text("\n".join(lines), encoding="utf-8")

    # --- 2) top_50_killed_by_adjustments.md ---
    killed_sorted = sorted(killed, key=lambda e: -e.get("_drop", 0))[:50]
    lines2 = ["# Top 50 killed by adjustments (pre>=2.5, post<2.5)", ""]
    for i, e in enumerate(killed_sorted, 1):
        lines2.append(f"## {i}. {e.get('symbol')} ts={e.get('ts')}")
        lines2.append(f"- pre_score={e.get('_pre'):.3f}, delta_sq={e.get('_delta_sq'):.3f}, delta_uw={e.get('_delta_uw'):.3f}, delta_surv={e.get('_delta_surv'):.3f}, post_score={e.get('_post'):.3f}")
        lines2.append(f"- reason_sq={e.get('_reason_sq')}, reason_uw={e.get('_reason_uw')}, reason_surv={e.get('_reason_surv')}")
        lines2.append("")
    (OUT_DIR / "top_50_killed_by_adjustments.md").write_text("\n".join(lines2), encoding="utf-8")

    # --- 3) adjustment_vs_executed_comparison.md ---
    attr = load_jsonl(ATTRIBUTION_PATH, limit=5000)
    executed_scores = []
    for r in attr:
        if r.get("type") != "attribution" or str(r.get("trade_id", "")).startswith("open_"):
            continue
        ctx = r.get("context") or {}
        es = ctx.get("entry_score") or r.get("entry_score") or r.get("entry_v2_score")
        if es is not None:
            try:
                executed_scores.append(float(es))
            except (TypeError, ValueError):
                pass
    # Compare: blocked have post in [0.17, 1.04]; executed have entry_score in [3, 8.8]. So adjustment log lines with score_after in blocked band vs executed band.
    sq_blocked = [r for r in sq_lines if float(r.get("score_after") or 0) < 2.5]
    sq_executed_band = [r for r in sq_lines if 2.5 <= float(r.get("score_after") or 0) <= 10]
    uw_blocked = [r for r in uw_lines if float(r.get("score_after") or 0) < 2.5]
    uw_executed_band = [r for r in uw_lines if 2.5 <= float(r.get("score_after") or 0) <= 10]
    lines3 = [
        "# Adjustment vs executed comparison",
        "",
        "## Executed trades (attribution entry_score)",
        f"- count={len(executed_scores)}, min={min(executed_scores):.3f}, max={max(executed_scores):.3f}, median={median(executed_scores):.3f}" if executed_scores else "- no data",
        "",
        "## Blocked (ledger post_score)",
        f"- count={len(events)}, post min={min(e.get('_post') for e in events):.3f}, max={max(e.get('_post') for e in events):.3f}",
        "",
        "## Adjustment log: lines where score_after in blocked band (0, 2.5) vs executed band [2.5, 10]",
        f"- signal_quality: blocked_band lines={len(sq_blocked)}, executed_band lines={len(sq_executed_band)}",
        f"- uw: blocked_band lines={len(uw_blocked)}, executed_band lines={len(uw_executed_band)}",
        "",
    ]
    if sq_blocked:
        mean_delta_sq_blocked = sum(float(r.get("delta", 0)) for r in sq_blocked) / len(sq_blocked)
        lines3.append(f"- Mean delta (signal_quality) when score_after<2.5: {mean_delta_sq_blocked:.4f}")
    if sq_executed_band:
        mean_delta_sq_exec = sum(float(r.get("delta", 0)) for r in sq_executed_band) / len(sq_executed_band)
        lines3.append(f"- Mean delta (signal_quality) when score_after in [2.5,10]: {mean_delta_sq_exec:.4f}")
    lines3.append("")
    (OUT_DIR / "adjustment_vs_executed_comparison.md").write_text("\n".join(lines3), encoding="utf-8")

    # --- 4) bars_alignment_20_sample.md ---
    top_by_drop = sorted(killed, key=lambda e: -e.get("_drop", 0))
    if len(killed) >= 20:
        random_10 = random.sample(killed, 10)
        seen = {(e.get("symbol"), e.get("ts")) for e in random_10}
        top_10 = [e for e in top_by_drop if (e.get("symbol"), e.get("ts")) not in seen][:10]
        sample_20 = random_10 + top_10
    else:
        sample_20 = killed[:20]
    bars_lines = [
        "# Bars alignment 20-sample (droplet)",
        "",
        "Sample: 10 random + 10 top by drop from killed (pre>=2.5, post<2.5). For each: entry_dt, bars used (path/count/timestamps), lookback, empty/zero/clipped.",
        "",
    ]
    bars_ok = 0
    lookback_min = 390  # ~6.5h session
    for i, e in enumerate(sample_20, 1):
        sym = e.get("symbol", "")
        ts = e.get("ts")
        if not ts:
            bars_lines.append(f"## {i}. {sym} ts=missing — skip")
            continue
        try:
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = ""
        bars_path = BARS_DIR / date_str / f"{sym}_1Min.json" if date_str else None
        bar_count = 0
        ts_min = ts_max = ""
        _err = ""
        try:
            from data.bars_loader import load_bars, cache_path
            start_ts = int(ts) - lookback_min * 60
            end_ts = int(ts) + 60
            bars = load_bars(sym, date_str, "1Min", start_ts=start_ts, end_ts=end_ts)
            bars_path = cache_path(sym, date_str, "1Min")
            if isinstance(bars, list):
                bar_count = len(bars)
                if bars:
                    t0 = bars[0].get("t") or bars[0].get("timestamp")
                    t1 = bars[-1].get("t") or bars[-1].get("timestamp")
                    ts_min, ts_max = str(t0), str(t1)
        except Exception as ex:
            _err = str(ex)
            bars_path = BARS_DIR / date_str / f"{sym}_1Min.json" if date_str else None
            if bars_path and bars_path.exists():
                try:
                    data = json.loads(bars_path.read_text(encoding="utf-8"))
                    bars = data.get("bars", data) if isinstance(data, dict) else data
                    if isinstance(bars, list):
                        bar_count = len(bars)
                        if bars:
                            t0 = bars[0].get("t") or bars[0].get("timestamp")
                            t1 = bars[-1].get("t") or bars[-1].get("timestamp")
                            ts_min, ts_max = str(t0), str(t1)
                except Exception:
                    pass
        if bar_count >= 10:
            bars_ok += 1
        empty_or_zero = "empty" if bar_count == 0 else ("sparse" if bar_count < 10 else "ok")
        bars_lines.append(f"## {i}. {sym} ts={ts} ({date_str})")
        bars_lines.append(f"- bars path: {bars_path}")
        bars_lines.append(f"- lookback: {lookback_min} min before entry")
        bars_lines.append(f"- bars count: {bar_count}, timestamps: {ts_min} .. {ts_max}")
        bars_lines.append(f"- inputs empty/zero/clipped: {empty_or_zero}")
        if _err:
            bars_lines.append(f"- bars load error: {_err}")
        bars_lines.append("")
    verdict = "OK" if bars_ok >= 16 else "NOT OK"
    bars_lines.append(f"## Verdict: Bars alignment {verdict} ({bars_ok}/20 with >=10 bars)")
    (OUT_DIR / "bars_alignment_20_sample.md").write_text("\n".join(bars_lines), encoding="utf-8")

    # Terminal output
    print(f"Dominant killer stage: {dominant_stage}")
    print(f"Dominant killer rule/reason: {dominant_rule} (kill count {dominant_count})")
    print(f"Median deltas: signal_quality={median(deltas_sq):.4f}, uw={median(deltas_uw):.4f}, survivorship={median(deltas_surv):.4f}")
    print(f"Bars alignment: {verdict}")
    return 0


if __name__ == "__main__":
    random.seed(42)
    sys.exit(main())
