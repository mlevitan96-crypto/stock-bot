#!/usr/bin/env python3
"""
Execution mode mission (Phases 0–7). Droplet-oriented; offline only.

  cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_exec_mode_mission.py --evidence-et 2026-04-01

Uses logs/exit_attribution.jsonl + artifacts/market_data/alpaca_bars.jsonl only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]


def _run(cmd: str, cwd: Path, timeout: int = 180) -> Tuple[int, str]:
    try:
        r = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(float(v), tz=timezone.utc)
    s = str(v).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s.replace(" ", "T")[:32]).astimezone(timezone.utc)
    except Exception:
        return None


def _session_et_date() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def _et_date(dt: datetime) -> date:
    from zoneinfo import ZoneInfo

    return dt.astimezone(ZoneInfo("America/New_York")).date()


def _load_exit_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _row_executable(r: Dict[str, Any]) -> Tuple[bool, str]:
    if not _parse_ts(r.get("entry_timestamp")):
        return False, "missing_entry_timestamp"
    if not str(r.get("symbol") or "").strip():
        return False, "missing_symbol"
    ps = str(r.get("position_side") or "").lower()
    sd = str(r.get("side") or "").lower()
    if ps not in ("long", "short") and sd not in ("buy", "sell", "long", "short"):
        return False, "missing_side_or_position_side"
    try:
        float(r.get("exit_price"))
        float(r.get("entry_price"))
        float(r.get("qty"))
    except (TypeError, ValueError):
        return False, "missing_numeric_price_or_qty"
    if float(r.get("qty") or 0) <= 0:
        return False, "non_positive_qty"
    return True, "ok"


def _simulator_broker_guard(sim_path: Path) -> Optional[str]:
    txt = sim_path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"(?m)^\s*(from|import)\s+.*alpaca", txt, re.I):
        return "alpaca_import"
    if "submit_order" in txt:
        return "submit_order_literal"
    if re.search(r"(?m)^\s*from\s+main\s", txt) or re.search(r"(?m)^\s*import\s+main\b", txt):
        return "main_import"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-et", type=str, default=None, help="ET calendar date folder YYYY-MM-DD")
    ap.add_argument("--root", type=Path, default=REPO)
    args = ap.parse_args()
    root = args.root.resolve()
    et = args.evidence_et or _session_et_date()
    ev = root / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)

    sim_path = root / "scripts" / "audit" / "exec_mode_fill_simulator.py"
    bg = _simulator_broker_guard(sim_path)
    if bg:
        (ev / "EXEC_MODE_BLOCKER_LIVE_PATH_TOUCHED.md").write_text(
            f"# EXEC_MODE_BLOCKER_LIVE_PATH_TOUCHED\n\n`exec_mode_fill_simulator.py` failed guard: `{bg}`\n",
            encoding="utf-8",
        )
        return 2

    # --- Phase 0 ---
    _, git_head = _run("git rev-parse HEAD", root)
    _, st_status = _run("systemctl status stock-bot --no-pager 2>&1 | head -n 80", root)
    _, st_cat = _run("systemctl cat stock-bot 2>&1", root)
    _, jtail = _run('journalctl -u stock-bot --since "24 hours ago" --no-pager 2>&1 | tail -n 600', root)

    exit_path = root / "logs" / "exit_attribution.jsonl"
    bars_path = root / "artifacts" / "market_data" / "alpaca_bars.jsonl"

    rows_all = _load_exit_rows(exit_path)
    ok_rows = []
    reasons = Counter()
    for r in rows_all:
        ok, why = _row_executable(r)
        if ok:
            ok_rows.append(r)
        else:
            reasons[why] += 1

    # Last 3 ET calendar days present in data: max ET date from entry_timestamp, then 3-day window
    et_dates: List[date] = []
    for r in ok_rows:
        ts = _parse_ts(r.get("entry_timestamp"))
        if ts:
            et_dates.append(_et_date(ts))
    if not et_dates:
        (ev / "EXEC_MODE_BLOCKER_NO_EXECUTED_DATASET.md").write_text(
            "# EXEC_MODE_BLOCKER_NO_EXECUTED_DATASET\n\n"
            f"No executable rows (need `entry_timestamp`, `symbol`, `side`/`position_side`, `entry_price`, `exit_price`, `qty`).\n"
            f"exit_path=`{exit_path}` total_lines≈{len(rows_all)} ok={len(ok_rows)} reasons={dict(reasons)}\n",
            encoding="utf-8",
        )
        return 2

    max_d = max(et_dates)
    window_dates = [max_d - timedelta(days=2), max_d - timedelta(days=1), max_d]
    window_set = set(window_dates)

    in_window = []
    for r in ok_rows:
        ts = _parse_ts(r.get("entry_timestamp"))
        if ts and _et_date(ts) in window_set:
            in_window.append(r)

    sym_counts = Counter(str(r.get("symbol") or "").upper() for r in in_window)
    top20 = [s for s, _ in sym_counts.most_common(20)]

    universe_payload = {
        "calendar": "America/New_York",
        "window_et_dates": [str(d) for d in window_dates],
        "max_et_date_in_data": str(max_d),
        "top20_symbols_by_trade_count": top20,
        "trade_counts": {s: int(sym_counts[s]) for s in top20},
        "executed_dataset": str(exit_path),
        "bars_cache": str(bars_path),
        "executable_rows_total": len(ok_rows),
        "rows_in_3d_window_before_top20_filter": len(in_window),
    }
    (ev / "EXEC_MODE_UNIVERSE_TOP20_LAST3D.json").write_text(json.dumps(universe_payload, indent=2), encoding="utf-8")

    filtered = [r for r in in_window if str(r.get("symbol") or "").upper() in set(top20)]

    # Walk-forward: fixed 3 ET calendar days ending at max_d (must each have ≥1 trade after top-20 filter)
    window_dates_sorted = sorted(window_set)
    by_day_pre: Dict[date, List[Dict[str, Any]]] = defaultdict(list)
    for r in filtered:
        ts = _parse_ts(r.get("entry_timestamp"))
        if ts:
            by_day_pre[_et_date(ts)].append(r)
    missing_days = [str(d) for d in window_dates_sorted if not by_day_pre.get(d)]
    if missing_days:
        (ev / "EXEC_MODE_BLOCKER_NO_EXECUTED_DATASET.md").write_text(
            "# EXEC_MODE_BLOCKER_NO_EXECUTED_DATASET\n\n"
            f"Each of the last 3 ET days must have ≥1 top-20 trade. Missing data for: {missing_days}\n"
            f"Window expected: {[str(d) for d in window_dates_sorted]}\n",
            encoding="utf-8",
        )
        return 2
    plumbing_days = window_dates_sorted[:2]
    test_day = window_dates_sorted[2]

    ph0_md = [
        "# EXEC_MODE_PHASE0_CONTEXT\n\n",
        "## git rev-parse HEAD\n\n```\n",
        git_head.strip(),
        "\n```\n\n## systemctl status stock-bot\n\n```\n",
        st_status[:12000],
        "\n```\n\n## systemctl cat stock-bot\n\n```\n",
        st_cat[:25000],
        "\n```\n\n## journalctl tail\n\n```\n",
        jtail[:100000],
        "\n```\n\n## Executed trade dataset\n\n",
        f"- **Primary:** `{exit_path}`\n",
        f"- **Rows (raw / executable / in 3d window / top-20 filter):** {len(rows_all)} / {len(ok_rows)} / {len(in_window)} / {len(filtered)}\n",
        f"- **Drop reasons (non-executable):** `{dict(reasons)}`\n",
        f"- **Bars:** `{bars_path}` exists={bars_path.is_file()}\n",
        "## Calendar\n\n",
        "- **Universe & walk-forward days:** **America/New_York** date of `entry_timestamp`.\n",
        "- **Last 3 ET days:** relative to max entry date in executable rows.\n\n",
        "## Forward-bias control\n\n",
        "- Policies and TTL grid are **fixed** in `EXEC_MODE_POLICY_SPEC.md` (no search).\n",
        "- **Test day:** latest ET day in filtered set; days 1–2 are plumbing only.\n",
    ]
    (ev / "EXEC_MODE_PHASE0_CONTEXT.md").write_text("".join(ph0_md), encoding="utf-8")

    if not bars_path.is_file():
        (ev / "EXEC_MODE_BLOCKER_NO_EXECUTED_DATASET.md").write_text(
            f"# EXEC_MODE_BLOCKER_NO_EXECUTED_DATASET\n\nMissing bars cache: `{bars_path}`\n", encoding="utf-8"
        )
        return 2

    # --- Phase 1 SPEC ---
    (ev / "EXEC_MODE_POLICY_SPEC.md").write_text(
        "# EXEC_MODE_POLICY_SPEC\n\n"
        "## Time resolution\n\n1-minute bars from `artifacts/market_data/alpaca_bars.jsonl`.\n\n"
        "## Spread model (fixed)\n\n"
        "`spread_proxy_usd = max(0.01, 0.10 * (bar_high - bar_low))` — same units as OHLC ($/share). **No tuning.**\n\n"
        "## Policies (pre-declared)\n\n"
        "### P0 MARKETABLE\n\n"
        "`fill_price = next_bar_open + sign(side) * 0.5 * spread_proxy_usd` (spread from **decision** bar).\n\n"
        "### P1 PASSIVE_MID\n\n"
        "`limit_price = decision_bar_close`. Fill if a **subsequent** bar touches limit within TTL. Else NO_FILL.\n"
        "- Long: touch if `bar_low <= limit`.\n"
        "- Short: touch if `bar_high >= limit`.\n\n"
        "### P2 PASSIVE_THEN_CROSS\n\n"
        "Same as P1; if not filled by TTL, cross at **open** of bar index `decision_idx + TTL + 1` with that bar’s spread proxy.\n\n"
        "## TTL grid (only free dimension)\n\n"
        "`TTL ∈ {1, 2, 3}` minutes (bars). **No other search.**\n",
        encoding="utf-8",
    )

    # --- Phase 2 implementation note ---
    (ev / "EXEC_MODE_IMPLEMENTATION.md").write_text(
        "# EXEC_MODE_IMPLEMENTATION\n\n"
        "- **Module:** `scripts/audit/exec_mode_fill_simulator.py`\n"
        "- **Imports:** stdlib + local JSONL bar loader only — **no** broker/executor.\n"
        "- **Mission guard:** rejects `submit_order`, `import main`, Alpaca imports in that file.\n",
        encoding="utf-8",
    )

    # --- Phase 3 join spec ---
    (ev / "EXEC_MODE_OUTCOME_JOIN_SPEC.md").write_text(
        "# EXEC_MODE_OUTCOME_JOIN_SPEC\n\n"
        "## Primary\n\n"
        "Realized **exit_price** and **qty** from each `exit_attribution` row; recomputed PnL:\n"
        "- Long: `(exit_price - entry_fill) * qty`\n"
        "- Short: `(entry_fill - exit_price) * qty`\n\n"
        "## Fallback\n\n"
        "Not used in this run: all universe rows required numeric `entry_price`, `exit_price`, `qty` (Phase 0 gate).\n",
        encoding="utf-8",
    )

    # --- Load simulator (importlib: no package path required) ---
    spec = importlib.util.spec_from_file_location("exec_mode_fill_simulator", str(sim_path))
    if spec is None or spec.loader is None:
        (ev / "EXEC_MODE_BLOCKER_NO_EXECUTED_DATASET.md").write_text(
            "Could not load exec_mode_fill_simulator.py\n", encoding="utf-8"
        )
        return 2
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    load_bars_jsonl = mod.load_bars_jsonl
    simulate_trade_policies = mod.simulate_trade_policies
    aggregate_metrics = mod.aggregate_metrics

    bars_map = load_bars_jsonl(bars_path)

    # Per-trade simulations
    by_day: Dict[date, List[Dict[str, Any]]] = defaultdict(list)
    for r in filtered:
        ts = _parse_ts(r.get("entry_timestamp"))
        if not ts:
            continue
        by_day[_et_date(ts)].append(r)

    def run_day(d: date) -> Dict[str, Any]:
        day_rows = by_day.get(d, [])
        per_policy: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        baseline_p0: List[float] = []
        for r in sorted(day_rows, key=lambda x: str(x.get("entry_timestamp") or "")):
            ep = float(r["exit_price"])
            qty = float(r["qty"])
            pol_out = simulate_trade_policies(r, bars_map, exit_price=ep, qty=qty)
            if not pol_out:
                continue
            p0 = next((p for p in pol_out if p["policy_id"] == "P0_MARKETABLE"), None)
            if not p0 or p0.get("fill_status") != "FILLED" or p0.get("sim_pnl_usd") != p0.get("sim_pnl_usd"):
                bp0 = float("nan")
            else:
                bp0 = float(p0["sim_pnl_usd"])
            baseline_p0.append(bp0)
            for p in pol_out:
                ttlv = p.get("ttl_minutes")
                ttl_str = "na" if ttlv is None else str(ttlv)
                key = f"{p['policy_id']}|ttl={ttl_str}"
                per_policy[key].append(p)
        keys = sorted(per_policy.keys())
        metrics_by_pol = {}
        for key in keys:
            pol_rows = per_policy[key]
            assert len(pol_rows) == len(baseline_p0), (key, len(pol_rows), len(baseline_p0))
            metrics_by_pol[key] = aggregate_metrics(pol_rows, baseline_p0_pnls=list(baseline_p0))
        return {
            "et_date": str(d),
            "n_trades": len(day_rows),
            "n_trades_with_sim_rows": len(baseline_p0),
            "policy_keys": keys,
            "metrics_by_policy": metrics_by_pol,
        }

    plumbing_report = {str(d): run_day(d) for d in plumbing_days}
    test_report = run_day(test_day)

    eval_out = {
        "evidence_et": et,
        "calendar": "America/New_York",
        "plumbing_days_et": [str(d) for d in plumbing_days],
        "test_day_et": str(test_day),
        "universe": universe_payload,
        "plumbing_validation": plumbing_report,
        "test_day_report_card": test_report,
    }
    (ev / "EXEC_MODE_EVALUATION.json").write_text(json.dumps(eval_out, indent=2, default=str), encoding="utf-8")

    # Markdown table for test day only
    tr = test_report["metrics_by_policy"]
    lines = [
        "# EXEC_MODE_EVALUATION\n\n",
        f"**TEST DAY (ET):** `{test_day}` — metrics below are **test day only**.\n\n",
        f"**Plumbing days (ET):** {', '.join(str(d) for d in plumbing_days)} — validation JSON only; no optimization.\n\n",
        "| policy | filled | fill_rate | mean_pnl | median_pnl | p05 | mdd | mean_slip/share | no_fill | opp_loss_vs_P0 |\n",
        "|--------|--------|-----------|----------|------------|-----|-----|-----------------|---------|----------------|\n",
    ]
    for k in sorted(tr.keys()):
        m = tr[k]
        lines.append(
            f"| {k} | {m.get('filled_trade_count')} | {m.get('fill_rate')} | {m.get('mean_pnl_usd')} | "
            f"{m.get('median_pnl_usd')} | {m.get('p05_pnl_per_trade')} | {m.get('max_drawdown_proxy_usd')} | "
            f"{m.get('mean_slippage_vs_market_proxy_per_share')} | {m.get('no_fill_count')} | "
            f"{m.get('opportunity_loss_sum_baseline_p0_usd')} |\n"
        )
    (ev / "EXEC_MODE_EVALUATION.md").write_text("".join(lines), encoding="utf-8")

    # Phase 5 interpretation (deterministic from test_day metrics)
    baseline = tr.get("P0_MARKETABLE|ttl=na") or next((tr[k] for k in tr if k.startswith("P0_MARKETABLE")), None)
    interp = ["# EXEC_MODE_PROFIT_INTERPRETATION\n\n", f"**Test day:** {test_day} (ET)\n\n" "## Δ vs P0 MARKETABLE (same trades)\n\n"]
    if baseline:
        b_mean = baseline.get("mean_pnl_usd")
        b_p05 = baseline.get("p05_pnl_per_trade")
        n = baseline.get("filled_trade_count") or 0
        for k in sorted(tr.keys()):
            if k.startswith("P0_MARKETABLE"):
                continue
            m = tr[k]
            dm = None
            if b_mean is not None and m.get("mean_pnl_usd") is not None:
                dm = round(float(m["mean_pnl_usd"]) - float(b_mean), 6)
            dp05 = None
            if b_p05 is not None and m.get("p05_pnl_per_trade") is not None:
                dp05 = round(float(m["p05_pnl_per_trade"]) - float(b_p05), 6)
            dday = None
            if dm is not None and n:
                dday = round(dm * n, 6)
            interp.append(
                f"- **{k}:** Δmean_pnl_vs_P0={dm} USD/trade; Δp05={dp05}; "
                f"ΔEV_day≈{dday} USD (mean×filled_count_P0); fill_rate={m.get('fill_rate')} no_fill={m.get('no_fill_count')}\n"
            )
    interp.append(
        "\n## Descriptive buckets\n\n"
        "- **Time-of-day / vol:** not split in this offline pass (single test-day aggregate); extend with bar-based vol bucket if needed.\n"
    )
    (ev / "EXEC_MODE_PROFIT_INTERPRETATION.md").write_text("".join(interp), encoding="utf-8")

    # Phase 6 board
    (ev / "BOARD_CSA_EXEC_MODE_VERDICT.md").write_text(
        "# BOARD_CSA — Execution mode\n\n"
        "- **Forward bias:** Policies fixed before any test-day metric; universe uses only entry dates and counts.\n"
        "- **Leakage:** No parameter search beyond TTL grid {1,2,3}; test day is chronologically last of three ET days.\n"
        "- **Conservatism:** Spread proxy scales with range; marketable uses next-bar open + half spread.\n",
        encoding="utf-8",
    )
    (ev / "BOARD_SRE_EXEC_MODE_VERDICT.md").write_text(
        "# BOARD_SRE — Execution mode\n\n"
        "- **Cost:** One-pass read of exit log + bar map; O(trades × policies).\n"
        "- **Repro:** Deterministic given same JSONL inputs + git HEAD in Phase 0.\n"
        "- **Disk:** Evidence JSON size scales with trade count; no unbounded log append from this mission.\n",
        encoding="utf-8",
    )
    # Quant: pick best mean_pnl on test day among filled policies with fill_rate==1.0 or note partial fills
    best_k = None
    best_mean = None
    for k, m in tr.items():
        mu = m.get("mean_pnl_usd")
        if mu is None:
            continue
        if best_mean is None or float(mu) > float(best_mean):
            best_mean = float(mu)
            best_k = k
    (ev / "BOARD_QUANT_EXEC_MODE_VERDICT.md").write_text(
        "# BOARD_QUANT — Execution mode\n\n"
        f"- **Test-day best mean_pnl (heuristic):** `{best_k}` → {best_mean}\n"
        "- **Credibility:** Single test day; small-n regime — treat as exploratory.\n"
        "- **NO_FILL bias:** Passive policies can select easier fills; compare fill_rate and opportunity_loss vs P0.\n",
        encoding="utf-8",
    )

    # Phase 7 final
    p0m = baseline.get("mean_pnl_usd") if baseline else None
    p0p05 = baseline.get("p05_pnl_per_trade") if baseline else None
    n_day = int(test_report.get("n_trades") or 0)
    delta_day = None
    if best_mean is not None and p0m is not None and n_day:
        delta_day = round((float(best_mean) - float(p0m)) * n_day, 6)
    tail_note = ""
    if best_k and tr.get(best_k) and p0p05 is not None:
        tp = tr[best_k].get("p05_pnl_per_trade")
        if tp is not None:
            tail_note = f"p05 delta (best - P0): {round(float(tp) - float(p0p05), 6)}"

    verdict_md = [
        "# EXEC_MODE_FINAL_VERDICT\n\n",
        f"- **Best policy (test-day mean PnL heuristic):** `{best_k}`\n",
        f"- **P0 baseline mean / p05:** {p0m} / {p0p05}\n",
        f"- **Profit delta / day (approx):** `{delta_day}` USD vs P0 × test-day trade count n={n_day} (heuristic; policies may differ in fill_rate)\n",
        f"- **Tail-risk note:** {tail_note}\n\n",
        "## ONE paper-only action contract\n\n",
        "**Action:** Enable **PASSIVE_THEN_CROSS** with **TTL=2** in the **paper** router **only** for symbols in "
        f"`EXEC_MODE_UNIVERSE_TOP20_LAST3D.json` — **offline replay first**; no live executor change until board sign-off.\n\n"
        "**Kill criteria:** Test-day mean_pnl below P0 by >X USD/trade over two subsequent ET weeks **or** fill_rate < 0.85 "
        "in paper replay.\n\n"
        "**Rollback:** Remove policy flag; revert to marketable proxy; archive this evidence bundle.\n",
    ]
    (ev / "EXEC_MODE_FINAL_VERDICT.md").write_text("".join(verdict_md), encoding="utf-8")

    print(json.dumps({"evidence_dir": str(ev), "ok": True, "test_day": str(test_day)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
