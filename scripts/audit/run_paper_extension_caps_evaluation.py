#!/usr/bin/env python3
"""
Paper extension evaluation: QUANT_CF_001 (counterfactual 60m) and QUANT_EMU_001 (exit emulator)
with optional paper caps replay. Read-only inputs; no broker.

Run (droplet):
  cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_paper_extension_caps_evaluation.py \\
    --evidence-et 2026-04-01 --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import statistics
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]


def _load_ddv():
    p = REPO / "scripts" / "audit" / "run_displacement_deepdive_addon.py"
    spec = importlib.util.spec_from_file_location("ddv", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def _window_days(dates: List[date]) -> Tuple[date, date]:
    u = sorted(set(dates))
    if not u:
        raise ValueError("no_dates")
    if len(u) >= 7:
        start = u[-7]
    else:
        start = u[max(0, len(u) - 3)]
    end = u[-1]
    return start, end


def _max_drawdown_pnls(pnls: List[float]) -> float:
    if not pnls:
        return 0.0
    cum = 0.0
    peak = 0.0
    mdd = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        mdd = min(mdd, cum - peak)
    return round(mdd, 6)


def _p05(xs: List[float]) -> Optional[float]:
    if not xs:
        return None
    s = sorted(xs)
    i = max(0, int(0.05 * (len(s) - 1)))
    return round(s[i], 6)


def run_cf_branch(
    rows: List[Dict[str, Any]],
    *,
    caps_enabled: bool,
    log_decisions: bool,
) -> Dict[str, Any]:
    from src.paper.paper_cap_enforcement import (
        PaperCapReplayState,
        append_paper_cap_log,
        enforce_paper_caps,
        load_paper_caps_from_env,
        pretrade_key,
    )

    caps = load_paper_caps_from_env()
    st = PaperCapReplayState()
    pnls: List[float] = []
    blocked_oc: List[float] = []
    fail_codes: Dict[str, int] = {}
    rows_sorted = sorted(rows, key=lambda r: _parse_ts(r.get("block_ts")) or datetime.min.replace(tzinfo=timezone.utc))

    for r in rows_sorted:
        ts = _parse_ts(r.get("block_ts"))
        if ts is None:
            continue
        sym = str(r.get("symbol") or "").upper()
        side = str(r.get("side_norm") or "long")
        dp = r.get("decision_price")
        qty = r.get("qty_notional_500")
        try:
            px = float(dp or 0)
            q = float(qty or 0)
        except (TypeError, ValueError):
            px, q = 0.0, 0.0
        notional = abs(px * q) if px > 0 and q > 0 else 500.0

        pva = r.get("pnl_variant_a_usd") or {}
        p60 = pva.get("pnl_60m")
        try:
            p60f = float(p60)
        except (TypeError, ValueError):
            continue

        if not caps_enabled:
            pnls.append(p60f)
            continue

        caps_run = {**caps, "enabled": True}
        intent = {"symbol": sym, "side": side, "intended_notional_usd": notional, "ts": ts}
        ok, reasons, diag = enforce_paper_caps(intent=intent, state=st, caps=caps_run)

        ts_iso = ts.isoformat()
        log_row = {
            "ts": ts_iso,
            "symbol": sym,
            "side": side,
            "intended_notional_usd": round(notional, 6),
            "current_gross_usd": diag.get("current_gross_usd"),
            "current_net_usd": diag.get("current_net_usd"),
            "per_symbol_usd": diag.get("per_symbol_usd"),
            "cap_check_result": "PASS" if ok else "FAIL",
            "fail_reason_codes": reasons,
            "decision_outcome": "allowed" if ok else "blocked",
            "pretrade_key": pretrade_key(sym, side, ts_iso, notional),
            "action": "QUANT_CF_001",
            "caps_enabled": True,
        }
        if log_decisions:
            append_paper_cap_log(log_row)

        if ok:
            pnls.append(p60f)
        else:
            blocked_oc.append(p60f)
            for c in reasons:
                fail_codes[c] = fail_codes.get(c, 0) + 1

    wr = sum(1 for x in pnls if x > 0) / len(pnls) if pnls else None
    return {
        "trade_count": len(pnls),
        "blocked_by_caps_count": len(blocked_oc),
        "total_pnl_usd": round(sum(pnls), 6) if pnls else 0.0,
        "pnl_per_trade_mean": round(statistics.mean(pnls), 6) if pnls else None,
        "win_rate": round(wr, 6) if wr is not None else None,
        "max_drawdown_usd": _max_drawdown_pnls(pnls),
        "tail_p05_pnl_per_trade": _p05(pnls),
        "top_fail_reason_codes": sorted(fail_codes.items(), key=lambda x: -x[1])[:12],
        "opportunity_cost_blocked_pnl60_sum_usd": round(sum(blocked_oc), 6) if blocked_oc else 0.0,
    }


def run_emu_branch(
    rows: List[Dict[str, Any]],
    bars_map: Dict[str, List[Dict[str, Any]]],
    ddv: Any,
    *,
    caps_enabled: bool,
    log_decisions: bool,
    k: float,
    m: float,
    n_bars: int,
) -> Dict[str, Any]:
    from src.paper.paper_cap_enforcement import (
        PaperCapReplayState,
        append_paper_cap_log,
        enforce_paper_caps,
        load_paper_caps_from_env,
        pretrade_key,
    )

    caps = load_paper_caps_from_env()
    st = PaperCapReplayState()
    pnls: List[float] = []
    blocked_oc: List[float] = []
    fail_codes: Dict[str, int] = {}
    rows_sorted = sorted(rows, key=lambda r: _parse_ts(r.get("block_ts")) or datetime.min.replace(tzinfo=timezone.utc))

    for r in rows_sorted:
        ts = _parse_ts(r.get("block_ts"))
        if ts is None:
            continue
        sym = str(r.get("symbol") or "").upper()
        side = str(r.get("side_norm") or "long")
        if side not in ("long", "short"):
            continue
        dp = r.get("decision_price")
        qty = r.get("qty_notional_500")
        try:
            px = float(dp or 0)
            q = float(qty or 0)
        except (TypeError, ValueError):
            px, q = 0.0, 0.0
        notional = abs(px * q) if px > 0 and q > 0 else 500.0

        blist = bars_map.get(sym)
        i0 = ddv.bar_idx_at_or_after(blist, ts) if blist else -1
        atr_a = ddv.atr_abs_proxy(blist, i0, 14) if blist and i0 >= 14 else None
        ep = blist[i0]["o"] if blist and i0 >= 0 else None
        emu_pnl = None
        q_exec = q if q > 0 else max(notional / max(ep or 1e-9, 1e-9), 0.0001)
        if blist is not None and i0 >= 0 and atr_a is not None and ep is not None:
            emu_pnl = ddv.emulate_exit(blist, i0, side, q_exec, ep, float(atr_a), k, m, n_bars)
        if emu_pnl is None:
            continue
        emu_f = float(emu_pnl)

        if not caps_enabled:
            pnls.append(emu_f)
            continue

        caps_run = {**caps, "enabled": True}
        intent = {"symbol": sym, "side": side, "intended_notional_usd": notional, "ts": ts}
        ok, reasons, diag = enforce_paper_caps(intent=intent, state=st, caps=caps_run)

        ts_iso = ts.isoformat()
        log_row = {
            "ts": ts_iso,
            "symbol": sym,
            "side": side,
            "intended_notional_usd": round(notional, 6),
            "current_gross_usd": diag.get("current_gross_usd"),
            "current_net_usd": diag.get("current_net_usd"),
            "per_symbol_usd": diag.get("per_symbol_usd"),
            "cap_check_result": "PASS" if ok else "FAIL",
            "fail_reason_codes": reasons,
            "decision_outcome": "allowed" if ok else "blocked",
            "pretrade_key": pretrade_key(sym, side, ts_iso, notional),
            "action": "QUANT_EMU_001",
            "caps_enabled": True,
        }
        if log_decisions:
            append_paper_cap_log(log_row)

        if ok:
            pnls.append(emu_f)
        else:
            blocked_oc.append(emu_f)
            for c in reasons:
                fail_codes[c] = fail_codes.get(c, 0) + 1

    wr = sum(1 for x in pnls if x > 0) / len(pnls) if pnls else None
    return {
        "trade_count": len(pnls),
        "blocked_by_caps_count": len(blocked_oc),
        "total_pnl_usd": round(sum(pnls), 6) if pnls else 0.0,
        "pnl_per_trade_mean": round(statistics.mean(pnls), 6) if pnls else None,
        "win_rate": round(wr, 6) if wr is not None else None,
        "max_drawdown_usd": _max_drawdown_pnls(pnls),
        "tail_p05_pnl_per_trade": _p05(pnls),
        "top_fail_reason_codes": sorted(fail_codes.items(), key=lambda x: -x[1])[:12],
        "opportunity_cost_blocked_sum_usd": round(sum(blocked_oc), 6) if blocked_oc else 0.0,
        "emulator_params": {"k_atr_stop": k, "m_atr_tp": m, "N_max_bars": n_bars},
    }


def _apply_paper_cap_env_for_on() -> None:
    """Tight-but-realistic defaults for caps-on branch (env-only; no live trading)."""
    vals = {
        "PAPER_CAPS_ENABLED": "1",
        "PAPER_CAP_FAIL_CLOSED": "1",
        "PAPER_CAP_MAX_GROSS_USD": "12000",
        "PAPER_CAP_MAX_NET_USD": "10000",
        "PAPER_CAP_MAX_PER_SYMBOL_USD": "2500",
        "PAPER_CAP_MAX_ORDERS_PER_MINUTE": "40",
        "PAPER_CAP_MAX_NEW_POSITIONS_PER_CYCLE": "4",
        "PAPER_CAP_HOLD_MINUTES": "60",
        "PAPER_CAP_CYCLE_MINUTES": "1",
    }
    for k, v in vals.items():
        os.environ[k] = v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-et", required=True)
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--log-cap-decisions", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    ev = root / "reports" / "daily" / args.evidence_et / "evidence"
    cf_path = ev / "BLOCKED_COUNTERFACTUAL_PNL_FULL.json"
    bars_path = root / "artifacts" / "market_data" / "alpaca_bars.jsonl"

    data = json.loads(cf_path.read_text(encoding="utf-8"))
    per = data.get("per_row") or []
    disp: List[Dict[str, Any]] = []
    for r in per:
        if str(r.get("block_reason") or "") != "displacement_blocked":
            continue
        if not r.get("coverage"):
            continue
        ts = _parse_ts(r.get("block_ts"))
        if ts is None:
            continue
        disp.append(r)

    dates = [ts.date() for r in disp for ts in [_parse_ts(r.get("block_ts"))] if ts]
    start_d, end_d = _window_days(dates)
    window_rows = []
    for r in disp:
        ts = _parse_ts(r.get("block_ts"))
        if ts and start_d <= ts.date() <= end_d:
            window_rows.append(r)

    ddv = _load_ddv()
    bars_map = ddv.load_bars(bars_path)

    # Emulator params: best mean cell from prior artifact if present
    k, m, nb = 1.5, 1.0, 60
    emu_path = ev / "DISPLACEMENT_EXIT_EMULATOR_RESULTS.json"
    if emu_path.exists():
        try:
            eg = json.loads(emu_path.read_text(encoding="utf-8"))
            best = None
            for cell in eg.get("grid") or []:
                mu = cell.get("mean_pnl_usd")
                if mu is None:
                    continue
                if best is None or float(mu) > float(best.get("mean_pnl_usd")):
                    best = cell
            if best:
                k = float(best.get("k_atr_stop", k))
                m = float(best.get("m_atr_tp", m))
                nb = int(best.get("N_max_minutes", nb))
        except Exception:
            pass

    out: Dict[str, Any] = {
        "evidence_et": args.evidence_et,
        "extension_window": {
            "start_date_inclusive": str(start_d),
            "end_date_inclusive": str(end_d),
            "rule": "last_7_calendar_days_if>=7_unique_days_else_last_3",
            "unique_days_observed": len(set(dates)),
            "rows_in_window": len(window_rows),
        },
        "caps_env_snapshot": {},
        "QUANT_CF_001": {},
        "QUANT_EMU_001": {},
    }

    out["QUANT_CF_001"]["baseline_caps_off"] = run_cf_branch(window_rows, caps_enabled=False, log_decisions=False)
    out["QUANT_EMU_001"]["baseline_caps_off"] = run_emu_branch(
        window_rows, bars_map, ddv, caps_enabled=False, log_decisions=False, k=k, m=m, n_bars=nb
    )

    _apply_paper_cap_env_for_on()
    out["caps_env_snapshot"] = {k: os.environ.get(k) for k in (
        "PAPER_CAPS_ENABLED",
        "PAPER_CAP_MAX_GROSS_USD",
        "PAPER_CAP_MAX_NET_USD",
        "PAPER_CAP_MAX_PER_SYMBOL_USD",
        "PAPER_CAP_MAX_ORDERS_PER_MINUTE",
        "PAPER_CAP_MAX_NEW_POSITIONS_PER_CYCLE",
        "PAPER_CAP_HOLD_MINUTES",
        "PAPER_CAP_CYCLE_MINUTES",
    )}
    out["QUANT_CF_001"]["caps_on"] = run_cf_branch(window_rows, caps_enabled=True, log_decisions=args.log_cap_decisions)
    out["QUANT_EMU_001"]["caps_on"] = run_emu_branch(
        window_rows, bars_map, ddv, caps_enabled=True, log_decisions=args.log_cap_decisions, k=k, m=m, n_bars=nb
    )

    (ev / "PAPER_EXTENSION_EVALUATION.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(ev / "PAPER_EXTENSION_EVALUATION.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
