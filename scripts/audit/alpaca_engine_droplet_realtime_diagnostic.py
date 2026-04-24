#!/usr/bin/env python3
"""
Read-only Alpaca droplet engine diagnostic (Phases 1–6 evidence MDs).
Run on the droplet from repo root: python3 scripts/audit/alpaca_engine_droplet_realtime_diagnostic.py
"""
from __future__ import annotations

import json
import math
import os
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

import main as bot_main
import uw_enrichment_v2 as uw_enrich
import uw_composite_v2 as uw_v2
from config.registry import StateFiles
from main import Config, get_exit_urgency, load_metadata_with_lock, read_uw_cache
from src.exit.exit_score_v2 import compute_exit_score_v2
from src.exit.profit_targets_v2 import compute_profit_target
from src.exit.stops_v2 import compute_stop_price


def _now_ts_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def _et_date() -> str:
    try:
        r = subprocess.run(
            ["TZ=America/New_York", "date", "+%Y-%m-%d"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            shell=False,
        )
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["bash", "-lc", "TZ=America/New_York date +%Y-%m-%d"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def tail_jsonl(path: Path, n: int = 200) -> str:
    if not path.exists():
        return f"(missing) {path}\n"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        chunk = lines[-n:] if len(lines) > n else lines
        return "\n".join(chunk) + ("\n" if chunk else "")
    except Exception as e:
        return f"(read error {path}: {e})\n"


def journal_snippet(unit: str, n: int = 200) -> str:
    try:
        r = subprocess.run(
            ["journalctl", "-u", unit, "-n", str(n), "--no-pager"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.stdout or r.stderr or "(empty journal)"
    except Exception as e:
        return f"(journalctl error: {e})"


def _parse_entry_ts(s: Any) -> datetime:
    if isinstance(s, datetime):
        t = s
    elif isinstance(s, str):
        try:
            t = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            t = datetime.utcnow()
    else:
        t = datetime.utcnow()
    if t.tzinfo is not None:
        t = t.replace(tzinfo=None)
    return t


def _global_regime() -> str:
    try:
        p = StateFiles.REGIME_DETECTOR
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            if isinstance(d, dict):
                r = d.get("current_regime") or d.get("regime")
                if isinstance(r, str) and r.strip():
                    return r.strip()
    except Exception:
        pass
    return "mixed"


def _exit_timing_cfg(regime: str) -> dict:
    try:
        from src.governance.apply_exit_timing_policy import apply_exit_timing_to_exit_config
        from strategies.context import get_strategy_id

        _mode = getattr(Config, "TRADING_MODE", "PAPER") or "PAPER"
        _strategy = "EQUITY"
        try:
            _sid = get_strategy_id()
            if _sid:
                _strategy = str(_sid).upper()
        except Exception:
            pass
        _scenario = os.getenv("EXIT_TIMING_SCENARIO", "minhold_5_promoted")
        return apply_exit_timing_to_exit_config(
            exit_cfg={},
            mode=_mode,
            strategy=_strategy,
            regime=regime or "NEUTRAL",
            scenario=_scenario,
        )
    except Exception:
        return {}


def _passes_hold_floor(cfg: dict, hold_sec: float) -> bool:
    if not cfg or cfg.get("min_hold_seconds") is None:
        return True
    return hold_sec >= float(cfg["min_hold_seconds"])


def analyze_symbol(
    symbol: str,
    pos: Any,
    all_metadata: dict,
    uw_cache: dict,
    current_regime_global: str,
    exit_timing_cfg: dict,
    now: datetime,
) -> Dict[str, Any]:
    meta = all_metadata.get(symbol, {}) if isinstance(all_metadata, dict) else {}
    qty = float(getattr(pos, "qty", 0) or 0)
    side = "buy" if qty > 0 else "sell"
    current_price = float(getattr(pos, "current_price", 0) or 0)
    entry_price = float(getattr(pos, "avg_entry_price", 0) or meta.get("entry_price") or 0)
    try:
        pnl_pct = float(getattr(pos, "unrealized_plpc", 0) or 0)
    except Exception:
        pnl_pct = 0.0
    if entry_price <= 0 and current_price > 0:
        entry_price = current_price

    info_ts = _parse_entry_ts(meta.get("entry_ts"))
    age_min = (now - info_ts).total_seconds() / 60.0
    age_days = age_min / (24 * 60)
    age_hours = age_days * 24
    hold_seconds = age_min * 60.0

    entry_score = float(meta.get("entry_score", 0.0) or 0.0)
    high_water_price = float(meta.get("high_water", current_price) or current_price)
    high_water_pct = ((high_water_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
    direction_norm = str(meta.get("direction") or ("bullish" if side == "buy" else "bearish"))

    enriched = uw_cache.get(symbol, {}) or {}
    try:
        enriched_live = uw_enrich.enrich_signal(symbol, uw_cache, current_regime_global) or enriched
    except Exception:
        enriched_live = enriched
    composite = uw_v2.compute_composite_score_v2(symbol, enriched_live, current_regime_global) or {}
    current_composite_score = float(composite.get("score", 0.0) or 0.0)
    current_v2_intel_snapshot: Dict[str, Any] = {}
    try:
        current_v2_intel_snapshot = {
            "v2_inputs": composite.get("v2_inputs") if isinstance(composite.get("v2_inputs"), dict) else {},
            "v2_uw_inputs": composite.get("v2_uw_inputs") if isinstance(composite.get("v2_uw_inputs"), dict) else {},
            "v2_uw_sector_profile": composite.get("v2_uw_sector_profile")
            if isinstance(composite.get("v2_uw_sector_profile"), dict)
            else {},
            "v2_uw_regime_profile": composite.get("v2_uw_regime_profile")
            if isinstance(composite.get("v2_uw_regime_profile"), dict)
            else {},
            "uw_intel_version": composite.get("uw_intel_version", ""),
            "now_v2_score": current_composite_score,
        }
    except Exception:
        pass

    flow_sent = str(enriched_live.get("sentiment", "NEUTRAL") or "NEUTRAL").upper()
    flow_reversal = (direction_norm == "bullish" and flow_sent == "BEARISH") or (
        direction_norm == "bearish" and flow_sent == "BULLISH"
    )

    entry_v2_ctx = meta.get("v2", {}) if isinstance(meta.get("v2"), dict) else {}
    entry_uw_inputs = entry_v2_ctx.get("v2_uw_inputs") if isinstance(entry_v2_ctx.get("v2_uw_inputs"), dict) else {}
    now_uw_inputs = (
        current_v2_intel_snapshot.get("v2_uw_inputs")
        if isinstance(current_v2_intel_snapshot.get("v2_uw_inputs"), dict)
        else {}
    )
    entry_reg_prof = (
        entry_v2_ctx.get("v2_uw_regime_profile")
        if isinstance(entry_v2_ctx.get("v2_uw_regime_profile"), dict)
        else {}
    )
    now_reg_prof = (
        current_v2_intel_snapshot.get("v2_uw_regime_profile")
        if isinstance(current_v2_intel_snapshot.get("v2_uw_regime_profile"), dict)
        else {}
    )
    entry_sec_prof = (
        entry_v2_ctx.get("v2_uw_sector_profile")
        if isinstance(entry_v2_ctx.get("v2_uw_sector_profile"), dict)
        else {}
    )
    now_sec_prof = (
        current_v2_intel_snapshot.get("v2_uw_sector_profile")
        if isinstance(current_v2_intel_snapshot.get("v2_uw_sector_profile"), dict)
        else {}
    )
    entry_reg_label = str(entry_reg_prof.get("regime_label") or meta.get("market_regime") or "NEUTRAL")
    now_reg_label = str(now_reg_prof.get("regime_label") or current_regime_global or "NEUTRAL")
    entry_sector = str(entry_sec_prof.get("sector") or "UNKNOWN")
    now_sector = str(now_sec_prof.get("sector") or "UNKNOWN")

    v2_in = current_v2_intel_snapshot.get("v2_inputs") or {}
    realized_vol_20d = None
    try:
        rv = v2_in.get("realized_vol_20d") if isinstance(v2_in, dict) else None
        realized_vol_20d = float(rv) if rv is not None else None
    except Exception:
        realized_vol_20d = None

    v2_exit_score, v2_components, v2_exit_reason, _, _ = compute_exit_score_v2(
        symbol=str(symbol),
        direction=direction_norm,
        entry_v2_score=entry_score,
        now_v2_score=current_composite_score,
        entry_uw_inputs=entry_uw_inputs,
        now_uw_inputs=now_uw_inputs,
        entry_regime=entry_reg_label,
        now_regime=now_reg_label,
        entry_sector=entry_sector,
        now_sector=now_sector,
        realized_vol_20d=realized_vol_20d,
        thesis_flags=None,
    )

    flow_strength_now = float((now_uw_inputs or {}).get("flow_strength", 0.0) or 0.0)
    profit_target_px, profit_reasoning = compute_profit_target(
        entry_price=float(entry_price) if entry_price else None,
        realized_vol_20d=realized_vol_20d,
        flow_strength=flow_strength_now,
        regime_label=now_reg_label,
        sector=now_sector,
        direction=direction_norm,
    )
    stop_px, stop_reasoning = compute_stop_price(
        entry_price=float(entry_price) if entry_price else None,
        realized_vol_20d=realized_vol_20d,
        flow_reversal=bool(flow_reversal),
        regime_label=now_reg_label,
        sector_collapse=False,
        direction=direction_norm,
    )

    trailing_stop_pct = float(Config.TRAILING_STOP_PCT)
    profit_accel = bool(meta.get("profit_acceleration_applied"))
    if age_min >= 30 and pnl_pct > 0:
        if not profit_accel:
            trailing_stop_pct = 0.005
        else:
            trailing_stop_pct = 0.005
    elif profit_accel:
        trailing_stop_pct = 0.005
    rg = (current_regime_global or "").upper()
    if not (age_min >= 30 and pnl_pct > 0) and not profit_accel:
        if rg in ("MIXED",):
            trailing_stop_pct = 0.01

    trail_dist = meta.get("trail_dist")
    if trail_dist is not None:
        try:
            hw = max(float(high_water_price), current_price)
            trail_stop = hw - float(trail_dist)
        except Exception:
            trail_stop = max(high_water_price, current_price) * (1 - trailing_stop_pct)
    else:
        hw_use = max(high_water_price, current_price)
        trail_stop = hw_use * (1 - trailing_stop_pct)

    regime_exit = (current_regime_global or "").upper()
    if regime_exit == "BEAR":
        stop_loss_pct = -0.008
        profit_target_decimal = 0.01
    else:
        stop_loss_pct = -0.01
        profit_target_decimal = 0.0075
    pnl_pct_decimal = pnl_pct / 100.0
    stop_loss_hit = pnl_pct_decimal <= stop_loss_pct
    profit_target_hit = pnl_pct_decimal >= profit_target_decimal
    stop_hit = False
    if not (math.isnan(trail_stop) or math.isinf(trail_stop) or trail_stop <= 0):
        stop_hit = current_price <= trail_stop

    position_data = {
        "entry_score": meta.get("entry_score", 3.0) or 3.0,
        "current_pnl_pct": pnl_pct,
        "age_hours": age_hours,
        "high_water_pct": high_water_pct,
        "direction": "LONG" if side == "buy" else "SHORT",
    }
    current_signals = {
        "composite_score": current_composite_score,
        "flow_reversal": flow_reversal,
        "momentum": 0.0,
    }
    exit_rec_adaptive = get_exit_urgency(position_data, current_signals)

    decay_ratio = None
    signal_decay_exit = False
    decay_threshold = 0.50
    min_hold_sec_no_decay = 90
    try:
        from board.eod.exit_regimes import get_exit_regime, get_effective_decay_threshold, MIN_HOLD_SECONDS_NO_DECAY

        min_hold_sec_no_decay = MIN_HOLD_SECONDS_NO_DECAY
        current_composite_tmp = current_composite_score
        signal_delta_tmp = (float(current_composite_tmp) - float(entry_score)) if (entry_score and current_composite_tmp) else None
        price_delta_pct_tmp = (
            (float(current_price - entry_price) / float(entry_price) * 100.0) if entry_price and entry_price > 0 else None
        )
        exit_regime_for_decay, _, _ = get_exit_regime(
            signal_delta=signal_delta_tmp,
            price_delta_pct=price_delta_pct_tmp,
            entry_signal_strength=float(entry_score) if entry_score else None,
            pnl_delta_15m=None,
            catastrophic_decay=False,
        )
        decay_threshold = get_effective_decay_threshold(exit_regime_for_decay, base=0.60)
    except Exception:
        decay_threshold = 0.50
    try:
        from policy_variants import get_variant_params

        variant = get_variant_params(symbol, "equity")
        variant_decay = float(variant.get("decay_ratio_threshold", 0.60))
        min_hold_min = float(variant.get("min_hold_minutes_before_decay_exit", 0))
        disable_for_top_quartile = bool(variant.get("disable_decay_for_top_quartile_entry", False))
        decay_threshold = min(decay_threshold, variant_decay)
    except Exception:
        min_hold_min = 0.0
        disable_for_top_quartile = False

    position_age_sec = (now - info_ts).total_seconds()
    position_age_min = position_age_sec / 60.0
    min_hold_sec = max(float(min_hold_sec_no_decay), float(min_hold_min) * 60.0)
    if entry_score > 0 and position_age_sec >= min_hold_sec:
        if not (disable_for_top_quartile and entry_score >= 7.0):
            cc = current_composite_score
            if cc != 0:
                decay_ratio = cc / entry_score
                signal_decay_exit = decay_ratio < decay_threshold

    structural_rec: Dict[str, Any] = {}
    try:
        from structural_intelligence import get_structural_exit

        structural_exit = get_structural_exit()
        position_data_s = {
            "current_price": current_price,
            "side": side,
            "entry_price": entry_price,
            "unrealized_pnl_pct": pnl_pct / 100.0,
        }
        structural_rec = structural_exit.get_exit_recommendation(symbol, position_data_s)
    except Exception as e:
        structural_rec = {"error": str(e)[:200]}

    time_exit_min = float(os.environ.get("TIME_EXIT_MINUTES", "240"))
    stale_alpha_eligible_trace = age_min >= time_exit_min
    stale_time_days_hit = age_days >= Config.TIME_EXIT_DAYS_STALE and abs(pnl_pct / 100) < Config.TIME_EXIT_STALE_PNL_THRESH_PCT

    stale_alpha_cutoff = age_min >= Config.STALE_TRADE_EXIT_MINUTES and pnl_pct < 0.20
    pnl_abs_pct = abs(pnl_pct / 100.0)
    stale_trade_momentum = age_min >= Config.STALE_TRADE_EXIT_MINUTES and pnl_abs_pct <= Config.STALE_TRADE_MOMENTUM_THRESH_PCT

    v2_would_close = float(v2_exit_score) >= 0.80 and _passes_hold_floor(exit_timing_cfg, hold_seconds)
    v2_blocked_hold_floor = float(v2_exit_score) >= 0.80 and not _passes_hold_floor(exit_timing_cfg, hold_seconds)

    adaptive_would = (
        exit_rec_adaptive.get("action") == "EXIT"
        and float(exit_rec_adaptive.get("urgency", 0) or 0) >= 0.8
        and _passes_hold_floor(exit_timing_cfg, hold_seconds)
    )

    regime_prot = (
        str(meta.get("market_regime") or current_regime_global or "").lower() == "high_vol_neg_gamma"
        and side == "buy"
        and pnl_pct < -0.5
    )

    decay_suppressed_entry_score_zero = entry_score <= 0

    b2_suppress = (
        signal_decay_exit
        and position_age_min < 30
        and getattr(Config, "FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT", False)
    )

    rule_should_exit = stop_loss_hit or (signal_decay_exit and not b2_suppress) or profit_target_hit or stop_hit
    rule_would_close = rule_should_exit and _passes_hold_floor(exit_timing_cfg, hold_seconds)

    notes: List[str] = []
    if decay_suppressed_entry_score_zero and entry_score <= 0:
        notes.append("entry_score<=0: decay_ratio path inactive (current/entry ratio)")
    if b2_suppress:
        notes.append("B2 would suppress early signal_decay exit (<30m)")
    if not _passes_hold_floor(exit_timing_cfg, hold_seconds):
        notes.append(
            f"hold_floor: hold_sec={hold_seconds:.0f} < min_hold_seconds={exit_timing_cfg.get('min_hold_seconds')}"
        )

    return {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "entry_price": entry_price,
        "current_price": current_price,
        "pnl_pct": round(pnl_pct, 4),
        "age_min": round(age_min, 2),
        "age_days": round(age_days, 3),
        "entry_score": entry_score,
        "now_v2_score": round(current_composite_score, 4),
        "v2_exit_score": round(float(v2_exit_score), 4),
        "v2_exit_reason": v2_exit_reason,
        "v2_components": v2_components,
        "profit_target_price": profit_target_px,
        "profit_target_decimal_engine": profit_target_decimal,
        "profit_target_hit": profit_target_hit,
        "stop_loss_price_v2": stop_px,
        "stop_loss_hit_engine_pct": stop_loss_hit,
        "trailing_stop_pct_effective": trailing_stop_pct,
        "trail_stop_price": round(trail_stop, 6),
        "trail_stop_hit": stop_hit,
        "high_water_price": high_water_price,
        "high_water_pct": round(high_water_pct, 4),
        "stale_time_days_eligible": stale_time_days_hit,
        "stale_alpha_eligible": stale_alpha_eligible_trace,
        "stale_alpha_cutoff_would_trigger": stale_alpha_cutoff,
        "stale_trade_momentum_would_trigger": stale_trade_momentum,
        "structural": structural_rec,
        "adaptive_urgency": exit_rec_adaptive,
        "regime_protection_neg_gamma_would": regime_prot,
        "flow_reversal": flow_reversal,
        "decay_ratio": None if decay_ratio is None else round(decay_ratio, 4),
        "decay_threshold_effective": round(decay_threshold, 4),
        "signal_decay_exit": signal_decay_exit,
        "decay_suppressed_entry_score_zero": decay_suppressed_entry_score_zero,
        "v2_would_close": v2_would_close,
        "v2_blocked_hold_floor": v2_blocked_hold_floor,
        "adaptive_would_close": adaptive_would,
        "rule_based_would_close": rule_would_close,
        "meta_keys_present": sorted(meta.keys()) if isinstance(meta, dict) else [],
        "has_entry_reason": bool(meta.get("entry_reason") or meta.get("reason")),
        "notes": notes,
    }


def _md_table(rows: List[Dict[str, Any]], keys: List[str]) -> str:
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    lines = [header, sep]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
    return "\n".join(lines)


def main() -> int:
    ts = _now_ts_utc()
    et = _et_date()
    evdir = REPO / "reports" / "daily" / et / "evidence"
    evdir.mkdir(parents=True, exist_ok=True)

    logd = REPO / "logs"
    p1 = evdir / f"ALPACA_ENGINE_STATE_{ts}.md"
    p2 = evdir / f"ALPACA_EXIT_DIAGNOSTIC_{ts}.md"
    p3 = evdir / f"ALPACA_ENTRY_DIAGNOSTIC_{ts}.md"
    p4 = evdir / f"ALPACA_METADATA_HEALTH_{ts}.md"
    p5a = evdir / f"ALPACA_ENGINE_CSA_VERDICT_{ts}.md"
    p5b = evdir / f"ALPACA_ENGINE_SRE_VERDICT_{ts}.md"
    p6 = evdir / f"ALPACA_ENGINE_FIX_RECOMMENDATIONS_{ts}.md"

    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    positions = api.list_positions() or []
    pos_count = len(positions)

    # Phase 1
    lines_p1: List[str] = []
    lines_p1.append(f"# ALPACA ENGINE STATE (droplet)\n")
    lines_p1.append(f"- Captured UTC: `{ts}`  ET date folder: `{et}`\n")
    lines_p1.append(f"- Open Alpaca positions: **{pos_count}**\n")
    lines_p1.append("\n## Note on attribution log\n")
    lines_p1.append(
        "`logs/attribution.jsonl` may be absent; `logs/uw_attribution.jsonl` is the UW attribution stream on this host.\n"
    )

    for name, rel in [
        ("run.jsonl", "logs/run.jsonl"),
        ("exit.jsonl", "logs/exit.jsonl"),
        ("scoring_flow.jsonl", "logs/scoring_flow.jsonl"),
        ("uw_attribution.jsonl (stand-in for attribution.jsonl)", "logs/uw_attribution.jsonl"),
    ]:
        lines_p1.append(f"\n## Last 200 lines — {name}\n\n```\n")
        lines_p1.append(tail_jsonl(REPO / rel.split("/", 1)[1], 200))
        lines_p1.append("\n```\n")

    for title, relp in [
        ("state/position_metadata.json", "state/position_metadata.json"),
        ("state/peak_equity.json", "state/peak_equity.json"),
        ("state/signal_strength_cache.json", "state/signal_strength_cache.json"),
    ]:
        p = REPO / relp
        lines_p1.append(f"\n## {title}\n\n")
        if not p.exists():
            lines_p1.append("(missing)\n")
            continue
        try:
            raw = p.read_text(encoding="utf-8", errors="replace")
            if len(raw) > 12000:
                lines_p1.append(f"(truncated, {len(raw)} chars total)\n\n```json\n{raw[:12000]}\n...```\n")
            else:
                lines_p1.append(f"```json\n{raw}\n```\n")
        except Exception as e:
            lines_p1.append(f"(read error: {e})\n")

    lines_p1.append("\n## Alpaca positions (API snapshot)\n\n")
    try:
        rows = []
        for p in positions:
            rows.append(
                {
                    "symbol": getattr(p, "symbol", ""),
                    "qty": getattr(p, "qty", ""),
                    "avg_entry": getattr(p, "avg_entry_price", ""),
                    "current": getattr(p, "current_price", ""),
                    "unrealized_pl": getattr(p, "unrealized_pl", ""),
                    "unrealized_plpc": getattr(p, "unrealized_plpc", ""),
                }
            )
        lines_p1.append(_md_table(rows, ["symbol", "qty", "avg_entry", "current", "unrealized_pl", "unrealized_plpc"]))
        lines_p1.append("\n")
    except Exception as e:
        lines_p1.append(f"(api error: {e})\n")

    lines_p1.append("\n## journalctl — stock-bot (last 200)\n\n```\n")
    lines_p1.append(journal_snippet("stock-bot", 200))
    lines_p1.append("\n```\n")

    p1.write_text("".join(lines_p1), encoding="utf-8")

    # Shared state for phases 2–4
    all_metadata = load_metadata_with_lock(StateFiles.POSITION_METADATA)
    if not isinstance(all_metadata, dict):
        all_metadata = {}
    uw_cache = read_uw_cache()
    cache_syms = len([k for k in uw_cache.keys() if not str(k).startswith("_")])
    regime = _global_regime()
    exit_timing_cfg = _exit_timing_cfg(regime)
    now = datetime.utcnow()

    rows_exit: List[Dict[str, Any]] = []
    for p in positions:
        sym = getattr(p, "symbol", "") or ""
        if not sym:
            continue
        try:
            rows_exit.append(analyze_symbol(sym, p, all_metadata, uw_cache, regime, exit_timing_cfg, now))
        except Exception as e:
            rows_exit.append({"symbol": sym, "error": str(e)})

    summary_counts = Counter()
    for r in rows_exit:
        if r.get("v2_would_close"):
            summary_counts["v2_would_close"] += 1
        if r.get("rule_based_would_close"):
            summary_counts["rule_based_would_close"] += 1
        if r.get("adaptive_would_close"):
            summary_counts["adaptive_would_close"] += 1
        if r.get("v2_blocked_hold_floor"):
            summary_counts["v2_blocked_hold_floor"] += 1
        if r.get("decay_suppressed_entry_score_zero"):
            summary_counts["positions_entry_score_le_0"] += 1

    p2_body: List[str] = []
    p2_body.append(f"# ALPACA EXIT DIAGNOSTIC\n\n- UTC `{ts}`  positions **{pos_count}**\n")
    p2_body.append(f"- Global regime (state file): `{regime}`\n")
    p2_body.append(f"- Exit timing min_hold_seconds: `{exit_timing_cfg.get('min_hold_seconds')}`\n")
    p2_body.append(f"- EXIT_PRESSURE_ENABLED: `{os.environ.get('EXIT_PRESSURE_ENABLED', '')}`\n")
    p2_body.append(f"- TIME_EXIT_MINUTES (trace/stale-alpha): `{os.environ.get('TIME_EXIT_MINUTES', '240')}`\n")
    p2_body.append(f"- STALE_TRADE_EXIT_MINUTES: `{Config.STALE_TRADE_EXIT_MINUTES}`\n")
    p2_body.append(f"- TIME_EXIT_DAYS_STALE / thresh: `{Config.TIME_EXIT_DAYS_STALE}` / `{Config.TIME_EXIT_STALE_PNL_THRESH_PCT}`\n")
    p2_body.append(f"- FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT: `{getattr(Config, 'FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT', False)}`\n")
    p2_body.append("\n## Summary counts\n\n")
    p2_body.append(json.dumps(dict(summary_counts), indent=2))
    p2_body.append("\n\n## Per position (key columns)\n\n")
    slim_keys = [
        "symbol",
        "pnl_pct",
        "age_min",
        "entry_score",
        "now_v2_score",
        "v2_exit_score",
        "trail_stop_hit",
        "stop_loss_hit_engine_pct",
        "profit_target_hit",
        "signal_decay_exit",
        "decay_ratio",
        "stale_trade_momentum_would_trigger",
        "stale_alpha_cutoff_would_trigger",
        "v2_would_close",
        "rule_based_would_close",
        "adaptive_would_close",
    ]
    p2_body.append(_md_table(rows_exit, slim_keys))
    p2_body.append("\n\n## Full JSON (per symbol)\n\n```json\n")
    p2_body.append(json.dumps(rows_exit, indent=2, default=str)[:500000])
    p2_body.append("\n```\n")
    p2.write_text("".join(p2_body), encoding="utf-8")

    # Phase 3 — entry
    run_tail = tail_jsonl(logd / "run.jsonl", 80).splitlines()
    risk_freezes = [ln for ln in run_tail if "risk_freeze" in ln and "complete" in ln]
    max_conc = int(Config.MAX_CONCURRENT_POSITIONS)
    lines_p3: List[str] = []
    lines_p3.append(f"# ALPACA ENTRY DIAGNOSTIC\n\n- UTC `{ts}`\n\n")
    lines_p3.append("## Capacity\n\n")
    lines_p3.append(f"- `MAX_CONCURRENT_POSITIONS` (env/registry): **{max_conc}**\n")
    lines_p3.append(f"- Current open positions: **{pos_count}**\n")
    if pos_count >= max_conc:
        lines_p3.append(
            "- **Finding:** At or above concurrent cap — new entries typically blocked unless displacement closes a slot.\n"
        )
    else:
        lines_p3.append("- **Finding:** Below concurrent cap — cap alone does not explain zero new entries.\n")
    lines_p3.append("\n## Recent run.jsonl lines mentioning risk_freeze (last 80 lines scan)\n\n```\n")
    lines_p3.append("\n".join(risk_freezes[-20:] if risk_freezes else ["(none in last 80 lines)"]))
    lines_p3.append("\n```\n")
    lines_p3.append("\n## Last 200 lines — freeze.jsonl\n\n```\n")
    lines_p3.append(tail_jsonl(logd / "freeze.jsonl", 200))
    lines_p3.append("\n```\n")
    lines_p3.append("\n## Last 120 lines — scoring_flow.jsonl\n\n```\n")
    lines_p3.append(tail_jsonl(logd / "scoring_flow.jsonl", 120))
    lines_p3.append("\n```\n")
    lines_p3.append("\n## Last 120 lines — gate.jsonl\n\n```\n")
    lines_p3.append(tail_jsonl(logd / "gate.jsonl", 120))
    lines_p3.append("\n```\n")
    lines_p3.append("\n## Last 80 lines — displacement.jsonl\n\n```\n")
    lines_p3.append(tail_jsonl(logd / "displacement.jsonl", 80))
    lines_p3.append("\n```\n")
    lines_p3.append(f"\n## UW cache symbol count (non-meta keys): **{cache_syms}**\n")
    if cache_syms == 0:
        lines_p3.append("- **Finding:** Empty UW cache → clustering/scoring may produce zero candidates (see run logs).\n")
    p3.write_text("".join(lines_p3), encoding="utf-8")

    # Phase 4 — metadata health
    entry_scores = []
    missing_reason = 0
    missing_v2 = 0
    for sym, m in all_metadata.items():
        if sym.startswith("_"):
            continue
        if not isinstance(m, dict):
            continue
        es = m.get("entry_score")
        entry_scores.append(es)
        if not (m.get("entry_reason") or m.get("reason")):
            missing_reason += 1
        v2 = m.get("v2")
        if not isinstance(v2, dict) or not v2:
            missing_v2 += 1

    lines_p4: List[str] = []
    lines_p4.append(f"# ALPACA METADATA HEALTH\n\n- UTC `{ts}`\n\n")
    lines_p4.append(f"- Metadata symbols (non-internal): **{len([k for k in all_metadata if not str(k).startswith('_')])}**\n")
    lines_p4.append(f"- Positions missing entry_reason/reason field: **{missing_reason}**\n")
    lines_p4.append(f"- Positions missing v2 snapshot block: **{missing_v2}**\n")
    z = sum(1 for x in entry_scores if x is None or float(x or 0) <= 0)
    lines_p4.append(f"- entry_score null/zero: **{z}** / {len(entry_scores)}\n")
    lines_p4.append("\n## signal_strength_cache.json freshness (sample)\n\n```json\n")
    scp = REPO / "state/signal_strength_cache.json"
    if scp.exists():
        try:
            sj = json.loads(scp.read_text(encoding="utf-8", errors="replace"))
            if isinstance(sj, dict):
                sample = list(sj.items())[:5]
                lines_p4.append(json.dumps(dict(sample), indent=2))
            else:
                lines_p4.append(str(type(sj)))
        except Exception as e:
            lines_p4.append(str(e))
    else:
        lines_p4.append("(missing)")
    lines_p4.append("\n```\n")
    lines_p4.append("\n## peak_equity.json\n\n```json\n")
    pe = REPO / "state/peak_equity.json"
    lines_p4.append(pe.read_text(encoding="utf-8", errors="replace") if pe.exists() else "(missing)")
    lines_p4.append("\n```\n")
    p4.write_text("".join(lines_p4), encoding="utf-8")

    # Phase 5 CSA / SRE
    csa: List[str] = []
    csa.append(f"# ALPACA ENGINE — CSA VERDICT\n\n- UTC `{ts}`\n\n")
    csa.append("## Exit pathways\n\n")
    csa.append(
        f"- Positions with **entry_score<=0** (decay path inactive): **{summary_counts.get('positions_entry_score_le_0', 0)}**\n"
    )
    csa.append(
        f"- Count where **v2_exit_score>=0.80** but hold_floor blocked: **{summary_counts.get('v2_blocked_hold_floor', 0)}**\n"
    )
    csa.append(
        f"- Count where **rule_based_would_close** (stop/decay/profit/trail, after B2 mask): **{summary_counts.get('rule_based_would_close', 0)}**\n"
    )
    csa.append(f"- **B2** early decay suppression active: `{getattr(Config, 'FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT', False)}`\n")
    csa.append("\n## Interpretation (evidence-limited)\n\n")
    if summary_counts.get("positions_entry_score_le_0", 0) > pos_count * 0.5:
        csa.append(
            "- Majority of open positions show **entry_score<=0** in metadata → composite decay exits and some stale-regime gates that depend on score ratios are weakened or inactive.\n"
        )
    if pos_count >= max_conc:
        csa.append(
            "- **Concurrent cap** reached → structural rotation depends on exits or displacement; if exits do not fire, book stalls.\n"
        )
    if cache_syms == 0:
        csa.append("- **UW cache empty** → live scoring for exits/entries may be degraded; verify uw-flow-daemon and cache file.\n")
    csa.append(
        "\nSee `ALPACA_EXIT_DIAGNOSTIC_{ts}.md` for per-symbol v2 score, trails, and flags.\n".replace("{ts}", ts)
    )
    p5a.write_text("".join(csa), encoding="utf-8")

    sre: List[str] = []
    sre.append(f"# ALPACA ENGINE — SRE VERDICT\n\n- UTC `{ts}`\n\n")
    try:
        hb = subprocess.run(
            ["systemctl", "is-active", "stock-bot"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        sre.append(f"- `stock-bot` active: **{hb.stdout.strip()}**\n")
    except Exception as e:
        sre.append(f"- systemctl check failed: {e}\n")
    try:
        hb2 = subprocess.run(
            ["systemctl", "is-active", "uw-flow-daemon"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        sre.append(f"- `uw-flow-daemon` active: **{hb2.stdout.strip()}**\n")
    except Exception:
        pass
    sre.append("\n## Log health (heuristic)\n\n")
    ex = tail_jsonl(logd / "exit.jsonl", 30)
    sre.append("- Recent `exit.jsonl` tail captured in ENGINE_STATE + below sample.\n\n```\n" + ex + "\n```\n")
    sre.append(
        "\n## Notes\n\n- Confirm `evaluate_exits` cadence via stock-bot logs / worker_debug if enabled.\n"
        "- If `list_positions` works (Phase 1 API table), broker connectivity is OK.\n"
    )
    p5b.write_text("".join(sre), encoding="utf-8")

    # Phase 6 recommendations (non-code-changing)
    fixl: List[str] = []
    fixl.append(f"# ALPACA ENGINE — FIX RECOMMENDATIONS (advisory)\n\n- UTC `{ts}`\n\n")
    fixl.append("1. **Metadata backfill** — ensure `entry_score`, `entry_reason`, and `v2` snapshot blocks are populated on open fills for decay/v2-exit parity.\n")
    fixl.append(
        "2. **Stale windows** — review `TIME_EXIT_MINUTES`, `STALE_TRADE_EXIT_MINUTES`, `TIME_EXIT_DAYS_STALE` vs observed holding periods.\n"
    )
    fixl.append("3. **Trailing stop** — review `TRAILING_STOP_PCT`, profit-acceleration at 30m, and MIXED-regime 1.0% tightening.\n")
    fixl.append("4. **Profit / stop rationalization** — align `profit_targets_v2` / `stops_v2` advisory levels with engine decimal targets (0.75% / -1% default).\n")
    fixl.append("5. **Structural exit** — validate `structural_intelligence` recommendations vs live book.\n")
    fixl.append("6. **v2 exit score** — audit weights via tuning; threshold 0.80 is the promotion line in code.\n")
    fixl.append(
        "7. **Position cap policy** — reconcile `MAX_CONCURRENT_POSITIONS` with live slot usage and displacement eligibility.\n"
    )
    fixl.append("8. **Peak equity** — verify `state/peak_equity.json` initialization after restarts for drawdown/risk gates.\n")
    p6.write_text("".join(fixl), encoding="utf-8")

    print(json.dumps({"ok": True, "evidence_dir": str(evdir), "ts": ts, "files": [p1.name, p2.name, p3.name, p4.name, p5a.name, p5b.name, p6.name]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
