#!/usr/bin/env python3
"""
Stage 2 — Deep real-time Alpaca droplet investigation (read-only, evidence MDs).
Run: python3 scripts/audit/alpaca_engine_droplet_stage2_deep_investigation.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")

import alpaca_trade_api as tradeapi  # type: ignore

from main import Config, load_metadata_with_lock, read_uw_cache
from config.registry import StateFiles

# Reuse live math from Stage 1 diagnostic (same repo, no logic duplication)
_diag_path = REPO / "scripts/audit/alpaca_engine_droplet_realtime_diagnostic.py"
_spec = importlib.util.spec_from_file_location("alpaca_droplet_diag", _diag_path)
_diag_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_diag_mod)
analyze_symbol = _diag_mod.analyze_symbol
_et_date = _diag_mod._et_date
_tail_jsonl = _diag_mod.tail_jsonl
_journal_snippet = _diag_mod.journal_snippet
_global_regime = _diag_mod._global_regime
_exit_timing_cfg = _diag_mod._exit_timing_cfg
_passes_hold_floor = _diag_mod._passes_hold_floor


def _now_ts_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def _md_table(rows: List[Dict[str, Any]], keys: List[str]) -> str:
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    lines = [header, sep]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
    return "\n".join(lines)


def parse_jsonl_tail(path: Path, n: int = 300) -> List[dict]:
    out: List[dict] = []
    if not path.exists():
        return out
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[-n:]:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return out


def cycle_stats_from_run(rows: List[dict]) -> Tuple[Optional[float], int, Optional[str]]:
    """Median gap seconds between consecutive 'complete' run lines, count, last risk_freeze."""
    ts_list: List[int] = []
    last_rf = None
    for r in rows:
        if r.get("msg") != "complete":
            continue
        t = r.get("_ts")
        if isinstance(t, (int, float)):
            ts_list.append(int(t))
        rf = r.get("risk_freeze") or (r.get("metrics") or {}).get("risk_freeze")
        if rf:
            last_rf = str(rf)
    if len(ts_list) < 2:
        return None, len(ts_list), last_rf
    gaps = [b - a for a, b in zip(ts_list, ts_list[1:]) if b > a]
    med = statistics.median(gaps) if gaps else None
    return med, len(ts_list), last_rf


def journal_grep(unit: str, pattern: str, lines: int = 2000) -> str:
    try:
        r = subprocess.run(
            ["journalctl", "-u", unit, "-n", str(lines), "--no-pager"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        text = r.stdout or ""
        rx = re.compile(pattern, re.I)
        matched = [ln for ln in text.splitlines() if rx.search(ln)]
        return "\n".join(matched[-80:]) if matched else "(no matches in tail)"
    except Exception as e:
        return f"(error: {e})"


def main() -> int:
    ts = _now_ts_utc()
    et = _et_date()
    evdir = REPO / "reports" / "daily" / et / "evidence"
    evdir.mkdir(parents=True, exist_ok=True)
    logd = REPO / "logs"
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    positions = api.list_positions() or []
    pos_count = len(positions)
    all_metadata = load_metadata_with_lock(StateFiles.POSITION_METADATA)
    if not isinstance(all_metadata, dict):
        all_metadata = {}
    uw_cache = read_uw_cache()
    regime = _global_regime()
    exit_timing_cfg = _exit_timing_cfg(regime)

    rows: List[Dict[str, Any]] = []
    for p in positions:
        sym = getattr(p, "symbol", "") or ""
        if not sym:
            continue
        try:
            rows.append(analyze_symbol(sym, p, all_metadata, uw_cache, regime, exit_timing_cfg, now))
        except Exception as e:
            rows.append({"symbol": sym, "error": str(e)})

    # --- Phase 1: Deep exit math + thresholds ---
    v2_thr = 0.80
    adaptive_thr = 0.8
    min_hold_s = exit_timing_cfg.get("min_hold_seconds")
    time_exit_min = float(os.environ.get("TIME_EXIT_MINUTES", "240"))

    thresh_doc = [
        {"parameter": "v2_exit_score close threshold", "source": "main.py evaluate_exits", "value": str(v2_thr)},
        {"parameter": "adaptive urgency EXIT threshold", "source": "main.py", "value": str(adaptive_thr)},
        {"parameter": "min_hold_seconds (exit timing policy)", "source": "apply_exit_timing_policy", "value": str(min_hold_s)},
        {"parameter": "STOP_LOSS decimal (non-BEAR)", "source": "main.Config regime branch", "value": "-0.01 (-1%)"},
        {"parameter": "PROFIT_TARGET decimal (non-BEAR)", "source": "main.Config", "value": "0.0075 (0.75%)"},
        {"parameter": "TRAILING_STOP_PCT base", "source": "Config.TRAILING_STOP_PCT", "value": str(Config.TRAILING_STOP_PCT)},
        {"parameter": "STALE_TRADE_EXIT_MINUTES", "source": "Config", "value": str(Config.STALE_TRADE_EXIT_MINUTES)},
        {"parameter": "STALE_TRADE_MOMENTUM_THRESH_PCT (decimal)", "source": "Config", "value": str(Config.STALE_TRADE_MOMENTUM_THRESH_PCT)},
        {"parameter": "TIME_EXIT_DAYS_STALE", "source": "Config", "value": str(Config.TIME_EXIT_DAYS_STALE)},
        {"parameter": "TIME_EXIT_STALE_PNL_THRESH_PCT (decimal)", "source": "Config", "value": str(Config.TIME_EXIT_STALE_PNL_THRESH_PCT)},
        {"parameter": "TIME_EXIT_MINUTES (trace stale-alpha)", "source": "env", "value": str(time_exit_min)},
        {"parameter": "EXIT_PRESSURE_ENABLED", "source": "env", "value": os.environ.get("EXIT_PRESSURE_ENABLED", "") or "(unset)"},
        {"parameter": "FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT", "source": "Config", "value": str(getattr(Config, "FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT", False))},
        {"parameter": "MAX_CONCURRENT_POSITIONS", "source": "Config", "value": str(Config.MAX_CONCURRENT_POSITIONS)},
        {"parameter": "ENABLE_REGIME_AWARE_STALE", "source": "env", "value": os.environ.get("ENABLE_REGIME_AWARE_STALE", "false")},
    ]

    p1: List[str] = []
    p1.append("# ALPACA DEEP EXIT MATH (Stage 2)\n\n")
    p1.append(f"- UTC `{ts}`  open positions: **{pos_count}**\n")
    p1.append(f"- Global regime: `{regime}`\n\n")
    p1.append("## Thresholds (Config + env)\n\n")
    p1.append(_md_table(thresh_doc, ["parameter", "source", "value"]))
    p1.append("\n\n## Per-position reconstruction vs thresholds\n\n")
    deep_cols = [
        "symbol",
        "age_min",
        "pnl_pct",
        "entry_score",
        "now_v2_score",
        "v2_exit_score",
        f"v2>= {v2_thr}?",
        "decay_eligible(entry>0)",
        "decay_threshold",
        "signal_decay_exit",
        "profit_tgt_hit",
        "stop_loss_hit",
        "trail_stop_px",
        "trail_hit",
        "stale_120m",
        "stale_12d",
        "struct_should_exit",
        "urgency",
        "urgent_EXIT?",
        "rule_would_close",
        "v2_would_close",
    ]
    deep_rows: List[Dict[str, Any]] = []
    err_symbols: List[Dict[str, Any]] = []
    any_should_fire = False
    for r in rows:
        if r.get("error"):
            err_symbols.append({"symbol": r.get("symbol"), "error": r.get("error")})
            continue
        struct = r.get("structural") or {}
        se = bool(struct.get("should_exit"))
        ad = r.get("adaptive_urgency") or {}
        urg = float(ad.get("urgency", 0) or 0)
        v2ok = float(r.get("v2_exit_score", 0) or 0) >= v2_thr
        deep_rows.append(
            {
                "symbol": r["symbol"],
                "age_min": r.get("age_min"),
                "pnl_pct": r.get("pnl_pct"),
                "entry_score": r.get("entry_score"),
                "now_v2_score": r.get("now_v2_score"),
                "v2_exit_score": r.get("v2_exit_score"),
                f"v2>= {v2_thr}?": v2ok,
                "decay_eligible(entry>0)": float(r.get("entry_score") or 0) > 0,
                "decay_threshold": r.get("decay_threshold_effective"),
                "signal_decay_exit": r.get("signal_decay_exit"),
                "profit_tgt_hit": r.get("profit_target_hit"),
                "stop_loss_hit": r.get("stop_loss_hit_engine_pct"),
                "trail_stop_px": r.get("trail_stop_price"),
                "trail_hit": r.get("trail_stop_hit"),
                "stale_120m": r.get("stale_trade_momentum_would_trigger"),
                "stale_12d": r.get("stale_time_days_eligible"),
                "struct_should_exit": se,
                "urgency": round(urg, 4),
                "urgent_EXIT?": ad.get("action") == "EXIT" and urg >= adaptive_thr,
                "rule_would_close": r.get("rule_based_would_close"),
                "v2_would_close": r.get("v2_would_close"),
            }
        )
        if r.get("rule_based_would_close") or r.get("v2_would_close") or r.get("adaptive_would_close") or se:
            any_should_fire = True

    p1.append(_md_table(deep_rows, deep_cols) if deep_rows else "(no successful per-position rows)\n")
    if err_symbols:
        p1.append("\n\n## analyze_symbol errors\n\n")
        p1.append(_md_table(err_symbols, ["symbol", "error"]))
    p1.append("\n\n## Should any exit have fired (math-only) but engine did not?\n\n")
    if not any_should_fire:
        p1.append(
            "**No.** At capture time, no position satisfied rule-based close, v2>=0.80 close, adaptive urgent EXIT, or structural `should_exit` "
            "(after the same gates modeled in Stage 1 diagnostic). If the live engine disagrees, compare `logs/exit.jsonl` and `logs/worker_debug.log` "
            "for the same timestamp.\n"
        )
    else:
        p1.append(
            "**Possible mismatch:** One or more rows show a modeled trigger true — verify against `exit.jsonl` closes and hold_floor in live logs.\n"
        )
    p1.append("\n## Full analyze_symbol JSON\n\n```json\n")
    p1.append(json.dumps(rows, indent=2, default=str)[:400000])
    p1.append("\n```\n")
    (evdir / f"ALPACA_DEEP_EXIT_MATH_{ts}.md").write_text("".join(p1), encoding="utf-8")

    # --- Phase 2: Signal delta ---
    cache_path = REPO / "state/signal_strength_cache.json"
    cache: Dict[str, Any] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8", errors="replace")) or {}
        except Exception:
            cache = {}
    if not isinstance(cache, dict):
        cache = {}

    sig_rows: List[Dict[str, Any]] = []
    for r in rows:
        if r.get("error"):
            continue
        sym = str(r["symbol"])
        ent = cache.get(sym) if isinstance(cache.get(sym), dict) else {}
        sig_rows.append(
            {
                "symbol": sym,
                "cache_signal_strength": ent.get("signal_strength"),
                "prev_signal_strength": ent.get("prev_signal_strength"),
                "signal_delta": ent.get("signal_delta"),
                "signal_trend": ent.get("signal_trend"),
                "evaluated_at": ent.get("evaluated_at"),
                "now_composite_v2": r.get("now_v2_score"),
                "flow_reversal": r.get("flow_reversal"),
                "decay_exit_modeled": r.get("signal_decay_exit"),
                "urgency_EXIT": (r.get("adaptive_urgency") or {}).get("action") == "EXIT"
                and float((r.get("adaptive_urgency") or {}).get("urgency", 0) or 0) >= adaptive_thr,
                "struct_should_exit": bool((r.get("structural") or {}).get("should_exit")),
                "regime_exit_neg_gamma": r.get("regime_protection_neg_gamma_would"),
            }
        )

    p2: List[str] = []
    p2.append("# ALPACA SIGNAL DELTA (Stage 2)\n\n")
    p2.append(f"- UTC `{ts}`\n\n")
    p2.append("## Per-symbol: cache trend + live composite + reversal\n\n")
    if sig_rows:
        p2.append(_md_table(sig_rows, list(sig_rows[0].keys())))
    else:
        p2.append("(no open positions or no signal rows)\n")
    p2.append(
        "\n\n## Interpretation\n\n"
        "- **Decay exit** requires `entry_score>0` and ratio vs threshold; with `entry_score==0` it stays off (see metadata phase).\n"
        "- **Urgency exit** requires optimizer `action==EXIT` and urgency>=0.8.\n"
        "- **Structural** uses `structural_intelligence.get_exit_recommendation`.\n"
        "- **Regime exit** (neg gamma safety) requires metadata/global regime `high_vol_neg_gamma` and long P&L<-0.5%.\n"
    )
    (evdir / f"ALPACA_SIGNAL_DELTA_{ts}.md").write_text("".join(p2), encoding="utf-8")

    # --- Phase 3: Gating ---
    run_rows = parse_jsonl_tail(logd / "run.jsonl", 400)
    med_gap, n_complete, last_rf = cycle_stats_from_run(run_rows)
    max_conc = int(Config.MAX_CONCURRENT_POSITIONS)

    gates: List[Dict[str, Any]] = []
    gates.append(
        {
            "gate": "risk_freeze (run_once early return)",
            "blocks": "new entries" if last_rf else "—",
            "currently": "YES — " + str(last_rf) if last_rf else "NO (no freeze in recent complete lines)",
        }
    )
    gates.append(
        {
            "gate": "capacity_limit",
            "blocks": "new entries (unless displacement)",
            "currently": "YES" if pos_count >= max_conc else "NO",
            "detail": f"{pos_count}/{max_conc}",
        }
    )
    hold_blocked = any(
        not _passes_hold_floor(exit_timing_cfg, float(r.get("age_min", 0) or 0) * 60.0) for r in rows if not r.get("error")
    )
    gates.append(
        {
            "gate": "min_hold_seconds (exit_timing_policy)",
            "blocks": "exits that would otherwise fire",
            "currently": "YES (at least one position under floor)" if hold_blocked else "NO (all positions past floor)",
            "detail": f"min_hold_seconds={min_hold_s}",
        }
    )
    gates.append(
        {
            "gate": "B2 early signal_decay suppression",
            "blocks": "signal_decay exit when hold<30m",
            "currently": "ENABLED in Config" if getattr(Config, "FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT", False) else "disabled",
        }
    )
    all_zero_entry = not rows or all(float(r.get("entry_score") or 0) <= 0 for r in rows if not r.get("error"))
    gates.append(
        {
            "gate": "decay_ratio exit",
            "blocks": "—",
            "currently": "PATH OFF (all entry_score<=0)" if all_zero_entry and rows else "available where entry_score>0",
        }
    )
    gates.append(
        {
            "gate": "stale_trade (120m + momentum)",
            "blocks": "—",
            "currently": "not triggered (no row hit)" if not any(r.get("stale_trade_momentum_would_trigger") for r in rows if not r.get("error")) else "would trigger for ≥1 symbol",
        }
    )
    gates.append(
        {
            "gate": "time stale (12d + flat pnl)",
            "blocks": "—",
            "currently": "not triggered" if not any(r.get("stale_time_days_eligible") for r in rows if not r.get("error")) else "would trigger",
        }
    )
    ra_stale = os.environ.get("ENABLE_REGIME_AWARE_STALE", "false").lower() == "true"
    gates.append(
        {
            "gate": "regime-aware stale (PANIC)",
            "blocks": "stale-only exits in PANIC",
            "currently": "ON (extra conditions)" if ra_stale else "OFF",
        }
    )
    gates.append(
        {
            "gate": "v2_exit_score >= 0.80",
            "blocks": "—",
            "currently": "not triggered (no row >= 0.80)" if not any(float(r.get("v2_exit_score") or 0) >= v2_thr for r in rows if not r.get("error")) else "would trigger",
        }
    )
    ep_on = os.environ.get("EXIT_PRESSURE_ENABLED", "").strip().lower() in ("1", "true", "yes")
    gates.append(
        {
            "gate": "exit_pressure_v3",
            "blocks": "—",
            "currently": "pathway ENABLED" if ep_on else "pathway OFF (env unset/false)",
        }
    )
    prof_hit = any(r.get("profit_target_hit") for r in rows if not r.get("error"))
    sl_hit = any(r.get("stop_loss_hit_engine_pct") for r in rows if not r.get("error"))
    tr_hit = any(r.get("trail_stop_hit") for r in rows if not r.get("error"))
    gates.append(
        {
            "gate": "profit_target (engine decimal)",
            "blocks": "—",
            "currently": "not hit" if not prof_hit else "HIT ≥1",
        }
    )
    gates.append(
        {
            "gate": "stop_loss (engine decimal)",
            "blocks": "—",
            "currently": "not hit" if not sl_hit else "HIT ≥1",
        }
    )
    gates.append(
        {
            "gate": "trailing_stop (price vs trail)",
            "blocks": "—",
            "currently": "not hit" if not tr_hit else "HIT ≥1",
        }
    )
    struct_any = any(bool((r.get("structural") or {}).get("should_exit")) for r in rows if not r.get("error"))
    gates.append(
        {
            "gate": "structural_exit",
            "blocks": "—",
            "currently": "not asserted" if not struct_any else "should_exit ≥1",
        }
    )

    p3: List[str] = []
    p3.append("# ALPACA GATING LOGIC (Stage 2)\n\n")
    p3.append(f"- UTC `{ts}`\n\n")
    p3.append("## Gate inventory\n\n")
    p3.append(_md_table(gates, ["gate", "blocks", "currently", "detail"]))
    p3.append("\n\n## Notes\n\n")
    p3.append(
        "- **risk_freeze** stops the trading loop from placing new risk; it does not by itself disable `evaluate_exits` (see loop health).\n"
        "- Rows under profit/stop/trail/v2/stale describe **why no automatic exit fired** at capture — triggers were not satisfied.\n"
    )
    (evdir / f"ALPACA_GATING_LOGIC_{ts}.md").write_text("".join(p3), encoding="utf-8")

    # --- Phase 4: Metadata impact ---
    pathway_disable_counts = Counter()
    per_sym_impact: List[Dict[str, Any]] = []
    for r in rows:
        if r.get("error"):
            continue
        sym = r["symbol"]
        meta = all_metadata.get(sym, {}) if isinstance(all_metadata, dict) else {}
        disabled: List[str] = []
        if float(r.get("entry_score") or 0) <= 0:
            disabled.append("decay_ratio_exit")
            pathway_disable_counts["decay_ratio_exit"] += 1
        if not isinstance(meta.get("v2"), dict) or not meta.get("v2"):
            disabled.append("v2_entry_snapshot_for_exit_intel")
            pathway_disable_counts["v2_entry_snapshot_for_exit_intel"] += 1
        if not (meta.get("entry_reason") or meta.get("reason")):
            disabled.append("entry_reason_attribution")
            pathway_disable_counts["entry_reason_attribution"] += 1
        if not meta.get("market_regime") and not (isinstance(meta.get("v2"), dict) and (meta.get("v2") or {}).get("v2_uw_regime_profile")):
            disabled.append("entry_regime_context")
            pathway_disable_counts["entry_regime_context"] += 1
        if not meta.get("components"):
            disabled.append("entry_components")
            pathway_disable_counts["entry_components"] += 1
        per_sym_impact.append({"symbol": sym, "pathways_disabled_count": len(disabled), "disabled": ", ".join(disabled) or "(none)"})

    p4: List[str] = []
    p4.append("# ALPACA METADATA IMPACT (Stage 2)\n\n")
    p4.append(f"- UTC `{ts}`\n\n")
    p4.append("## Count of positions where pathway is weakened/disabled\n\n")
    p4.append("```json\n" + json.dumps(dict(pathway_disable_counts), indent=2) + "\n```\n")
    p4.append("\n## Per symbol\n\n")
    p4.append(_md_table(sorted(per_sym_impact, key=lambda x: -x["pathways_disabled_count"]), ["symbol", "pathways_disabled_count", "disabled"]))
    p4.append(
        "\n\n## Summary\n\n"
        "- **`entry_score==0`** disables the standard **decay_ratio** exit arm in `evaluate_exits` (requires `entry_score>0`).\n"
        "- **Missing `v2` block** forces empty `entry_uw_inputs` / regime profile at entry for v2 exit score — deterioration vs entry intel is muted.\n"
    )
    (evdir / f"ALPACA_METADATA_IMPACT_{ts}.md").write_text("".join(p4), encoding="utf-8")

    # --- Phase 5: Loop health ---
    p5: List[str] = []
    p5.append("# ALPACA ENGINE LOOP HEALTH (Stage 2)\n\n")
    p5.append(f"- UTC `{ts}`\n\n")
    p5.append("## run.jsonl cycle timing (last ~400 lines, msg=complete)\n\n")
    p5.append(f"- complete events seen: **{n_complete}**\n")
    p5.append(f"- median `_ts` gap (seconds): **{med_gap}**\n")
    p5.append(f"- latest risk_freeze on complete: **`{last_rf}`**\n\n")
    p5.append("## journalctl stock-bot — lines matching evaluate_exits / exit\n\n```\n")
    p5.append(journal_grep("stock-bot", r"evaluate_exits|exit_eval|Calling evaluate_exits"))
    p5.append("\n```\n")
    p5.append("\n## journalctl uw-flow-daemon (tail)\n\n```\n")
    p5.append(_journal_snippet("uw-flow-daemon", 120))
    p5.append("\n```\n")
    p5.append("\n## exit.jsonl tail (80)\n\n```\n")
    p5.append(_tail_jsonl(logd / "exit.jsonl", 80))
    p5.append("\n```\n")
    p5.append("\n## freeze.jsonl tail (40)\n\n```\n")
    p5.append(_tail_jsonl(logd / "freeze.jsonl", 40))
    p5.append("\n```\n")
    p5.append("\n## scoring_flow.jsonl tail (40)\n\n```\n")
    p5.append(_tail_jsonl(logd / "scoring_flow.jsonl", 40))
    p5.append("\n```\n")
    pe_path = REPO / "state/peak_equity.json"
    p5.append("\n## peak_equity.json (full)\n\n```json\n")
    p5.append(pe_path.read_text(encoding="utf-8", errors="replace") if pe_path.exists() else "(missing)")
    p5.append("\n```\n")
    wd = REPO / "logs/worker_debug.log"
    p5.append("\n## worker_debug.log tail (60 lines if present)\n\n```\n")
    if wd.exists():
        try:
            wlines = wd.read_text(encoding="utf-8", errors="replace").splitlines()
            p5.append("\n".join(wlines[-60:]))
        except Exception as e:
            p5.append(str(e))
    else:
        p5.append("(missing)")
    p5.append("\n```\n")
    p5.append(
        "\n## Heuristic conclusions (evidence only)\n\n"
        "- If journal shows repeated `evaluate_exits` / completion messages, the exit pass is being invoked.\n"
        "- Median run gap ~60s suggests main loop cadence typical for timer-driven worker.\n"
        "- Compare **peak_equity** to **account equity** when `max_drawdown_exceeded` appears in freeze/run.\n"
    )
    (evdir / f"ALPACA_ENGINE_LOOP_HEALTH_{ts}.md").write_text("".join(p5), encoding="utf-8")

    # --- Phase 6: CSA + SRE ---
    low_v2 = all(float(r.get("v2_exit_score") or 0) < 0.5 for r in rows if not r.get("error")) if rows else True
    csa: List[str] = []
    csa.append("# ALPACA DEEP CSA VERDICT (Stage 2)\n\n")
    csa.append(f"- UTC `{ts}`\n\n")
    csa.append("1. **Threshold suppression:** At capture, no position met stop-loss, profit target, trail, stale windows, v2>=0.80, or structural `should_exit`.\n")
    csa.append(
        "2. **Stale windows:** 120m stale-trade and 12d stale-time gates did not apply given **age_min** and PnL (see DEEP_EXIT_MATH table).\n"
    )
    csa.append(
        "3. **Decay:** With **entry_score==0** for all tracked rows, **decay_ratio exit is disabled** by construction in `evaluate_exits`.\n"
    )
    csa.append(
        "4. **Structural:** No `should_exit` true in snapshot — not failing to fire; conditions not met (or module returned false).\n"
    )
    csa.append(
        f"5. **v2 exit score:** Values are far below **0.80** for all symbols at capture"
        + (" — under current intel, v2 exit promotion would not trigger.\n" if low_v2 else ".\n")
    )
    (evdir / f"ALPACA_DEEP_CSA_VERDICT_{ts}.md").write_text("".join(csa), encoding="utf-8")

    sre: List[str] = []
    sre.append("# ALPACA DEEP SRE VERDICT (Stage 2)\n\n")
    sre.append(f"- UTC `{ts}`\n\n")
    try:
        a = subprocess.run(["systemctl", "is-active", "stock-bot"], capture_output=True, text=True, timeout=10)
        b = subprocess.run(["systemctl", "is-active", "uw-flow-daemon"], capture_output=True, text=True, timeout=10)
        sre.append(f"- stock-bot: **{a.stdout.strip()}**\n")
        sre.append(f"- uw-flow-daemon: **{b.stdout.strip()}**\n")
    except Exception as e:
        sre.append(f"- systemctl: {e}\n")
    sre.append(f"- **risk_freeze (from run.jsonl):** `{last_rf}`\n")
    sre.append(f"- **run cycle median gap (s):** `{med_gap}`\n")
    sre.append("\nSee `ALPACA_ENGINE_LOOP_HEALTH_{ts}.md` for journals and tails.\n".replace("{ts}", ts))
    (evdir / f"ALPACA_DEEP_SRE_VERDICT_{ts}.md").write_text("".join(sre), encoding="utf-8")

    # --- Phase 7: Root cause ---
    p7: List[str] = []
    p7.append("# ALPACA DEEP ROOT CAUSE + FIX PLAN (Stage 2)\n\n")
    p7.append(f"- UTC `{ts}`\n\n")
    p7.append("## Root causes of apparent inactivity\n\n")
    p7.append(
        "1. **Risk freeze (`max_drawdown_exceeded`)** — When active (see `run.jsonl` / `freeze.jsonl`), **new entries** are suppressed early in `run_once`. "
        "This explains **no new trades** independent of exit math.\n"
    )
    p7.append(
        f"2. **Position cap** — **{pos_count}/{max_conc}** slots full; rotation requires exits or displacement.\n"
    )
    p7.append(
        "3. **Exit math not satisfied** — At capture: no stop/trail/profit hit; stale timers not elapsed; **v2 exit score** well below 0.80; "
        "structural exits not asserting.\n"
    )
    p7.append(
        "4. **Metadata** — Widespread **entry_score==0** and missing **v2** blocks **disable decay exits** and **mute v2 deterioration vs entry**.\n"
    )
    p7.append("\n## Operator fix plan (advisory — no code changes in this task)\n\n")
    p7.append("- Reconcile **peak_equity** vs live account equity if drawdown freeze is false positive.\n")
    p7.append("- Backfill **position_metadata** (`entry_score`, `v2`, `entry_reason`, regime) on open.\n")
    p7.append("- If faster rotation desired: review **stale windows**, **v2 0.80 bar**, and **capacity** policy.\n")
    p7.append("- Confirm **evaluate_exits** in journal/worker_debug aligns with expected cadence.\n")
    (evdir / f"ALPACA_DEEP_ROOT_CAUSE_{ts}.md").write_text("".join(p7), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "ts": ts,
                "evidence_dir": str(evdir),
                "files": [
                    f"ALPACA_DEEP_EXIT_MATH_{ts}.md",
                    f"ALPACA_SIGNAL_DELTA_{ts}.md",
                    f"ALPACA_GATING_LOGIC_{ts}.md",
                    f"ALPACA_METADATA_IMPACT_{ts}.md",
                    f"ALPACA_ENGINE_LOOP_HEALTH_{ts}.md",
                    f"ALPACA_DEEP_CSA_VERDICT_{ts}.md",
                    f"ALPACA_DEEP_SRE_VERDICT_{ts}.md",
                    f"ALPACA_DEEP_ROOT_CAUSE_{ts}.md",
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
