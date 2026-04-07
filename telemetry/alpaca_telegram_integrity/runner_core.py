"""Single coherent Alpaca integrity + Telegram cycle."""
from __future__ import annotations

import importlib.util
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from telemetry.alpaca_telegram_integrity import checks
from telemetry.alpaca_telegram_integrity.checkpoint_10 import (
    checkpoint_10_state_path,
    load_checkpoint_10_state,
    save_checkpoint_10_state,
)
from telemetry.alpaca_telegram_integrity.checkpoint_100 import (
    checkpoint_100_state_path,
    load_checkpoint_100_state,
    save_checkpoint_100_state,
)
from telemetry.alpaca_telegram_integrity.milestone import (
    build_milestone_snapshot,
    load_milestone_state,
    mark_milestone_fired,
    save_milestone_state,
    should_fire_milestone,
    update_integrity_arm_state,
)
from telemetry.alpaca_telegram_integrity.session_clock import session_anchor_date_et_iso
from telemetry.alpaca_telegram_integrity.self_heal import run_self_heal
from telemetry.alpaca_telegram_integrity.templates import (
    format_100trade_checkpoint,
    format_100trade_checkpoint_deferred,
    format_integrity_alert,
    format_milestone_250,
)
from telemetry.alpaca_telegram_integrity.warehouse_summary import (
    CoverageSummary,
    load_latest_coverage,
    run_warehouse_mission,
)


def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", "").strip()
    if r:
        return Path(r).resolve()
    return Path(__file__).resolve().parents[2]


def _apply_strict_chain_backfill(root: Path) -> Dict[str, Any]:
    """
    Idempotent repair: append strict_backfill_* from exit_attribution before strict gate.
    Loaded via importlib so scripts/audit need not be a package.
    """
    p = root / "scripts" / "audit" / "strict_chain_historical_backfill.py"
    if not p.is_file():
        return {"ok": False, "applied": 0, "error": "strict_chain_historical_backfill.py_missing"}
    spec = importlib.util.spec_from_file_location("_strict_chain_hist_bf", p)
    if spec is None or spec.loader is None:
        return {"ok": False, "applied": 0, "error": "import_spec_failed"}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "apply_strict_chain_backfill", None)
    if fn is None:
        return {"ok": False, "applied": 0, "error": "apply_strict_chain_backfill_missing"}
    return fn(root, dry_run=False, max_trades=5000)


def _load_config(root: Path) -> Dict[str, Any]:
    p = root / "config" / "alpaca_telegram_integrity.json"
    if not p.is_file():
        return {}
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _merge_env_files(root: Path) -> None:
    """Populate os.environ for Telegram + Alpaca if unset (droplet parity)."""
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        pass
    for path in (root / ".env", Path("/root/stock-bot/.env"), Path("/root/.alpaca_env")):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def _integrity_state_path(root: Path) -> Path:
    return root / "state" / "alpaca_telegram_integrity_cycle.json"


def _milestone_state_path(root: Path) -> Path:
    return root / "state" / "alpaca_milestone_250_state.json"


def _load_cycle_state(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"version": 1, "cycle_count": 0, "cooldowns": {}, "last_good": {}}
    try:
        o = json.loads(path.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else {"version": 1, "cycle_count": 0, "cooldowns": {}}
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "cycle_count": 0, "cooldowns": {}}


def _save_cycle_state(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _checkpoint_100_integrity_ok(
    cov: CoverageSummary,
    strict: Dict[str, Any],
    cov_reasons: List[str],
    schema_reasons: List[str],
    max_age_h: float,
) -> Tuple[bool, List[str]]:
    """
    Pre-send gate for 100-trade checkpoint: DATA_READY + coverage thresholds + strict ARMED + exit probe.
    Pager / post-close not included (informational checkpoint only).
    """
    bad: List[str] = []
    if cov.path is None:
        bad.append("missing_coverage_artifact")
    elif cov.age_hours is not None and cov.age_hours > max_age_h:
        bad.append(f"coverage_artifact_stale (age_h={cov.age_hours} > max={max_age_h})")
    if cov.data_ready_yes is not True:
        bad.append("DATA_READY not YES (or unknown)")
    bad.extend(cov_reasons)
    bad.extend(schema_reasons)
    if strict.get("LEARNING_STATUS") != "ARMED":
        bad.append(
            f"strict LEARNING_STATUS is not ARMED (got {strict.get('LEARNING_STATUS')!r})"
        )
    return (len(bad) == 0), bad


def _coverage_vs_thresholds(cov: CoverageSummary, thr: Dict[str, float]) -> List[str]:
    reasons: List[str] = []
    if cov.execution_join_pct is not None and cov.execution_join_pct < thr.get("execution_join", 0):
        reasons.append(
            f"execution_join_coverage {cov.execution_join_pct}% < {thr.get('execution_join')}%"
        )
    if cov.fee_pct is not None and cov.fee_pct < thr.get("fee", 0):
        reasons.append(f"fee_coverage {cov.fee_pct}% < {thr.get('fee')}%")
    if cov.slippage_pct is not None and cov.slippage_pct < thr.get("slippage", 0):
        reasons.append(f"slippage_coverage {cov.slippage_pct}% < {thr.get('slippage')}%")
    if cov.data_ready_yes is False:
        reasons.append("DATA_READY reported NO in latest coverage artifact")
    return reasons


def run_integrity_cycle(
    *,
    root: Optional[Path] = None,
    dry_run: bool = False,
    send_test_milestone: bool = False,
    send_test_integrity: bool = False,
    send_test_100trade: bool = False,
    skip_warehouse: bool = False,
    skip_self_heal: bool = False,
) -> Dict[str, Any]:
    root = root or _root()
    root = root.resolve()
    os.chdir(root)
    _merge_env_files(root)
    cfg = _load_config(root)
    if not cfg.get("enabled", True) and not (
        send_test_milestone or send_test_integrity or send_test_100trade
    ):
        return {"skipped": True, "reason": "config.enabled false"}

    out: Dict[str, Any] = {"root": str(root), "utc": datetime.now(timezone.utc).isoformat()}
    st_path = _integrity_state_path(root)
    st = _load_cycle_state(st_path)
    st["cycle_count"] = int(st.get("cycle_count", 0)) + 1
    n = st["cycle_count"]

    if not skip_self_heal:
        out["self_heal"] = run_self_heal(cfg, root)

    target = int(cfg.get("milestone_trade_count", 250))

    # Optional full warehouse run (throttled)
    wh_days = int(cfg.get("warehouse_days_when_run", 30))
    every_n = max(1, int(cfg.get("warehouse_run_every_n_cycles", 6)))
    wh_tail = ""
    run_wh = not skip_warehouse and (n % every_n == 0 or st.get("force_next_warehouse"))
    # Throttle heavy mission outside US RTH (still allow milestone / strict / probes).
    try:
        from zoneinfo import ZoneInfo

        _et = ZoneInfo("America/New_York")
        et_now = datetime.now(timezone.utc).astimezone(_et)
        rth = et_now.weekday() < 5 and (
            (et_now.hour, et_now.minute) >= (9, 30) and (et_now.hour, et_now.minute) <= (16, 10)
        )
    except Exception:
        rth = True
    if run_wh and not rth:
        out["warehouse_run"] = {"skipped": True, "reason": "outside_us_rth_et"}
        run_wh = False
    if run_wh:
        code, wh_tail = run_warehouse_mission(root, wh_days)
        out["warehouse_run"] = {"exit_code": code, "tail": wh_tail[-1500:]}
        st["force_next_warehouse"] = False
    elif skip_warehouse:
        out["warehouse_run"] = {"skipped": True}

    cov = load_latest_coverage(root)
    out["coverage_file"] = str(cov.path) if cov.path else None
    out["coverage_age_hours"] = cov.age_hours
    thr = cfg.get("coverage_thresholds_pct") or {}
    cov_reasons = _coverage_vs_thresholds(cov, {k: float(v) for k, v in thr.items()})

    max_age = float(cfg.get("warehouse_coverage_file_max_age_hours", 36))
    if cov.path is None or (cov.age_hours is not None and cov.age_hours > max_age):
        cov_reasons.append(
            f"stale_or_missing_warehouse_coverage (max_age_h={max_age}, age={cov.age_hours})"
        )

    if cfg.get("strict_chain_backfill_before_strict_gate", True):
        try:
            out["strict_chain_backfill"] = _apply_strict_chain_backfill(root)
        except Exception as e:  # pragma: no cover
            out["strict_chain_backfill_error"] = str(e)

    strict: Dict[str, Any] = {}
    try:
        strict = checks.run_strict_completeness(root)
        out["strict"] = {
            "LEARNING_STATUS": strict.get("LEARNING_STATUS"),
            "trades_seen": strict.get("trades_seen"),
            "trades_incomplete": strict.get("trades_incomplete"),
        }
    except Exception as e:  # pragma: no cover
        strict = {}
        out["strict_error"] = str(e)

    tail_n = int(cfg.get("exit_attribution_tail_lines", 400))
    req_fields = list(cfg.get("exit_required_fields") or ["symbol", "exit_ts", "trade_id"])
    probe = checks.probe_exit_attribution_tail(root / "logs" / "exit_attribution.jsonl", tail_n, req_fields)
    out["exit_probe"] = {"lines_scanned": probe.lines_scanned, "missing": probe.missing_field_counts}
    schema_reasons: List[str] = []
    for field, cnt in probe.missing_field_counts.items():
        if probe.lines_scanned > 0 and cnt > max(5, probe.lines_scanned // 4):
            schema_reasons.append(f"exit_attribution missing {field} in {cnt}/{probe.lines_scanned} tail rows")

    # Strict regression: was ARMED, now BLOCKED
    prev_strict = (st.get("last_good") or {}).get("LEARNING_STATUS")
    cur_strict = strict.get("LEARNING_STATUS")
    reg_reasons: List[str] = []
    if prev_strict == "ARMED" and cur_strict == "BLOCKED":
        reg_reasons.append(
            f"strict completeness regression ARMED→BLOCKED ({strict.get('learning_fail_closed_reason')})"
        )

    reasons = cov_reasons + schema_reasons + reg_reasons

    # Post-close / direction windows (reuse failure detector evaluators).
    # Direction readiness: same auto-heal as telegram_failure_detector (refresh JSON) before
    # turning missing/stale artifact into integrity-alert noise.
    try:
        from scripts.governance.telegram_failure_detector import (
            evaluate_alpaca_direction_readiness,
            evaluate_alpaca_post_close,
            run_auto_heal,
        )

        now_utc = datetime.now(timezone.utc)
        pc = evaluate_alpaca_post_close(root, now_utc)
        dr = evaluate_alpaca_direction_readiness(root, now_utc)
        heal_status: Optional[str] = None
        if dr.state not in ("SENT", "PASS", "SKIPPED", "PENDING"):
            heal_status = run_auto_heal(root, "alpaca", "direction_readiness")
            dr = evaluate_alpaca_direction_readiness(root, now_utc)
            out["direction_readiness_pager_heal"] = heal_status
        out["pager_windows"] = [
            {"key": pc.window_key, "state": pc.state, "cause": pc.root_cause},
            {"key": dr.window_key, "state": dr.state, "cause": dr.root_cause},
        ]
        for ev, label in ((pc, "post_close"), (dr, "direction_readiness")):
            if ev.state not in ("SENT", "PASS", "SKIPPED", "PENDING"):
                reasons.append(f"{label}_pager:{ev.state}:{ev.root_cause}")
    except Exception as e:
        out["pager_import_error"] = str(e)

    cd = float(cfg.get("integrity_alert_cooldown_sec", 7200))
    cd_reg = float(cfg.get("strict_regression_alert_cooldown_sec", 3600))

    def send_msg(text: str, script_name: str) -> bool:
        if dry_run:
            out.setdefault("dry_run_messages", []).append(text[:500])
            return True
        try:
            from scripts.alpaca_telegram import send_governance_telegram

            return send_governance_telegram(text, script_name=script_name)
        except Exception as e:
            out["send_error"] = str(e)
            return False

    data_ready_s = "YES" if cov.data_ready_yes else ("NO" if cov.data_ready_yes is False else "unknown")

    # --- 100-trade informational checkpoint (before 250; state/alpaca_100trade_sent.json) ---
    cp100_path = checkpoint_100_state_path(root)
    cp100_target = int(cfg.get("checkpoint_100_trade_count", 100))
    cp100_on = cfg.get("checkpoint_100_enabled", True)
    exit_probe_ok = len(schema_reasons) == 0
    cp_ok, cp_bad = _checkpoint_100_integrity_ok(
        cov, strict, cov_reasons, schema_reasons, max_age
    )
    out["checkpoint_100_precheck_ok"] = cp_ok
    out["checkpoint_100_precheck_reasons"] = cp_bad

    now_utc = datetime.now(timezone.utc)
    anchor_et = session_anchor_date_et_iso(now_utc)
    basis = str(cfg.get("milestone_counting_basis", "integrity_armed")).strip() or "integrity_armed"
    if basis not in ("session_open", "integrity_armed"):
        basis = "integrity_armed"
    arm_st: Dict[str, Any] = {}
    arm_ep: Optional[float] = None
    if basis == "integrity_armed":
        arm_st = update_integrity_arm_state(root, anchor_et, cp_ok)
        raw = arm_st.get("arm_epoch_utc")
        arm_ep = float(raw) if raw is not None else None
    snap = build_milestone_snapshot(
        root,
        counting_basis=basis,
        arm_epoch_utc=arm_ep,
        now=now_utc,
    )
    out["milestone"] = asdict(snap)
    out["milestone_counting_basis"] = basis
    out["milestone_integrity_arm"] = arm_st if basis == "integrity_armed" else {"basis": "session_open"}

    # --- 10-trade Alpaca V2 harvester ping (once per session_anchor_et) ---
    cp10_path = checkpoint_10_state_path(root)
    cp10_on = cfg.get("checkpoint_10_enabled", True)
    cp10_target = max(1, int(cfg.get("checkpoint_10_trade_count", 10)))
    st10 = load_checkpoint_10_state(cp10_path)
    if st10.get("session_anchor_et") != snap.session_anchor_et:
        st10 = {
            "session_anchor_et": snap.session_anchor_et,
            "checkpoint_10_sent": False,
            "last_count": 0,
        }
    st10["last_count"] = snap.unique_closed_trades
    if cp10_on and snap.unique_closed_trades >= cp10_target and not st10.get("checkpoint_10_sent"):
        msg10 = (
            "🟢 [Alpaca V2 Harvester] 10 Trades Reached. New UW Telemetry is Flowing!"
        )
        if send_msg(msg10, "alpaca_checkpoint_10"):
            st10["checkpoint_10_sent"] = True
            st10["checkpoint_10_sent_at_utc"] = datetime.now(timezone.utc).isoformat()
            out["checkpoint_10_sent"] = True
        else:
            out["checkpoint_10_send_failed"] = True
    save_checkpoint_10_state(cp10_path, st10)
    out["checkpoint_10_guard_file"] = str(cp10_path)

    st100 = load_checkpoint_100_state(cp100_path)
    if st100.get("session_anchor_et") != snap.session_anchor_et:
        st100 = {
            "session_anchor_et": snap.session_anchor_et,
            "checkpoint_100_info_sent": False,
            "checkpoint_100_deferred_sent": False,
            "last_count": 0,
        }
    st100["last_count"] = snap.unique_closed_trades

    if send_test_100trade:
        msg = format_100trade_checkpoint(
            test=True,
            snap=snap,
            cov=cov,
            data_ready=data_ready_s,
            strict_status=str(strict.get("LEARNING_STATUS") or ""),
            exit_probe_ok=exit_probe_ok,
            precheck_ok=cp_ok,
            utc_iso=out["utc"],
        )
        out["test_100trade_sent"] = send_msg(msg, "alpaca_integrity_test_100trade")
        st100["last_test_100trade_utc"] = out["utc"]
        save_checkpoint_100_state(cp100_path, st100)
        out["checkpoint_100_guard_file"] = str(cp100_path)
    elif cp100_on and snap.unique_closed_trades >= cp100_target:
        if st100.get("checkpoint_100_info_sent"):
            out["checkpoint_100_already_complete"] = True
        elif cp_ok:
            msg = format_100trade_checkpoint(
                test=False,
                snap=snap,
                cov=cov,
                data_ready=data_ready_s,
                strict_status=str(strict.get("LEARNING_STATUS") or ""),
                exit_probe_ok=exit_probe_ok,
                precheck_ok=True,
                utc_iso=out["utc"],
            )
            if send_msg(msg, "alpaca_checkpoint_100"):
                st100["checkpoint_100_info_sent"] = True
                st100["checkpoint_100_info_sent_at_utc"] = datetime.now(timezone.utc).isoformat()
                out["checkpoint_100_sent"] = True
            else:
                out["checkpoint_100_send_failed"] = True
        elif not st100.get("checkpoint_100_deferred_sent"):
            dmsg = format_100trade_checkpoint_deferred(
                test=False,
                degradation_reasons=cp_bad,
                snap=snap,
                utc_iso=out["utc"],
            )
            if send_msg(dmsg, "alpaca_checkpoint_100_deferred"):
                st100["checkpoint_100_deferred_sent"] = True
                st100["checkpoint_100_deferred_at_utc"] = datetime.now(timezone.utc).isoformat()
                out["checkpoint_100_deferred_alert_sent"] = True
            else:
                out["checkpoint_100_deferred_send_failed"] = True
        else:
            out["checkpoint_100_waiting_integrity_recovery"] = True
        save_checkpoint_100_state(cp100_path, st100)
        out["checkpoint_100_guard_file"] = str(cp100_path)
    else:
        save_checkpoint_100_state(cp100_path, st100)
        if cp100_on:
            out["checkpoint_100_guard_file"] = str(cp100_path)

    # --- milestone 250 ---
    ms_path = _milestone_state_path(root)
    fire, ms_st = should_fire_milestone(root, target, snap, ms_path)
    spi = checks.latest_spi_pointer(root)
    reports_hint = "reports/ and reports/daily/*/evidence/ on droplet"

    if send_test_milestone:
        msg = format_milestone_250(
            test=True,
            snap=snap,
            data_ready=data_ready_s,
            strict_status=str(strict.get("LEARNING_STATUS") or ""),
            spi_rel=spi,
            reports_hint=reports_hint,
        )
        out["test_milestone_sent"] = send_msg(msg, "alpaca_integrity_test_milestone")
    elif fire:
        msg = format_milestone_250(
            test=False,
            snap=snap,
            data_ready=data_ready_s,
            strict_status=str(strict.get("LEARNING_STATUS") or ""),
            spi_rel=spi,
            reports_hint=reports_hint,
        )
        if send_msg(msg, "alpaca_milestone_250"):
            mark_milestone_fired(ms_path, ms_st)
            out["milestone_fired"] = True
        else:
            out["milestone_fire_failed"] = True
            save_milestone_state(ms_path, ms_st)
    else:
        save_milestone_state(ms_path, ms_st)

    # --- integrity alert ---
    if send_test_integrity:
        msg = format_integrity_alert(
            test=True,
            reasons=["TEST simulated integrity failure"],
            last_good=st.get("last_good"),
            action="Ignore — test message from run_alpaca_telegram_integrity_cycle.py",
        )
        out["test_integrity_sent"] = send_msg(msg, "alpaca_integrity_test_alert")
    elif reasons:
        reg_key = "strict_regression" if reg_reasons else "integrity_general"
        use_cd = cd_reg if reg_reasons else cd
        if checks.cooldown_ok(st, reg_key, use_cd):
            msg = format_integrity_alert(
                test=False,
                reasons=reasons,
                last_good=st.get("last_good"),
                action="Inspect logs, rerun truth warehouse mission, review strict gate output; see MEMORY_BANK section 1.2.",
            )
            if send_msg(msg, "alpaca_data_integrity"):
                checks.touch_cooldown(st, reg_key)
                out["integrity_alert_sent"] = True
        else:
            out["integrity_alert_suppressed_cooldown"] = True

    # Update last_good when healthy
    if not reasons and cov.execution_join_pct is not None:
        st["last_good"] = {
            "utc": datetime.now(timezone.utc).isoformat(),
            "execution_join_pct": cov.execution_join_pct,
            "fee_pct": cov.fee_pct,
            "slippage_pct": cov.slippage_pct,
            "DATA_READY": cov.data_ready_yes,
            "LEARNING_STATUS": cur_strict,
            "coverage_path": str(cov.path) if cov.path else None,
        }

    if cur_strict is not None:
        st.setdefault("last_observed", {})["LEARNING_STATUS"] = cur_strict

    _save_cycle_state(st_path, st)
    out["reasons_evaluated"] = reasons
    return out
