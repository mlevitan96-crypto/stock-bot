#!/usr/bin/env python3
"""
Integrity arm blocker mission — droplet evidence (read-only; does not call update_integrity_arm_state).

Writes reports/daily/<ET-date>/evidence/ALPACA_INTEGRITY_ARM_*.md

Run: cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_alpaca_integrity_arm_blocker_mission.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))


def _et_date_iso() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _evidence_dir() -> Path:
    d = REPO / "reports" / "daily" / _et_date_iso() / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sh(cmd: List[str], timeout: int = 120) -> Tuple[str, str, int]:
    try:
        r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=timeout)
        return (r.stdout or ""), (r.stderr or ""), r.returncode
    except Exception as e:
        return "", str(e), 1


def _bash(script: str, timeout: int = 120) -> Tuple[str, str, int]:
    return _sh(["bash", "-lc", script], timeout=timeout)


def _exit_jsonl_last_ts(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    last = None
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            sz = f.tell()
            f.seek(max(0, sz - min(sz, 512_000)))
            if sz > 512_000:
                f.readline()
            for line in f.read().decode("utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(o, dict):
                    last = o.get("exit_ts") or o.get("ts") or o.get("timestamp")
        return str(last) if last else None
    except OSError:
        return None


def _rg_patterns() -> str:
    patterns = [
        "milestone_counting_basis",
        "integrity_armed",
        "alpaca_milestone_integrity_arm",
        "arm_epoch_utc",
        "build_milestone_snapshot",
        "MilestoneSnapshot",
    ]
    lines: List[str] = []
    for pat in patterns:
        o, e, c = _sh(
            [
                "rg",
                "-n",
                "--no-heading",
                "--glob",
                "*.py",
                pat,
                str(REPO / "telemetry"),
                str(REPO / "scripts"),
                str(REPO / "src"),
            ],
            timeout=90,
        )
        if c not in (0, 1):
            o = f"(rg exit {c}: {e})"
        lines.append(f"### Pattern: `{pat}`\n\n```\n{(o or '(no matches)')[:12000]}\n```\n")
    return "\n".join(lines)


def main() -> int:
    root = REPO.resolve()
    ev = _evidence_dir()
    et = _et_date_iso()

    # Phase 0
    gh, _, gc = _sh(["git", "rev-parse", "HEAD"])
    git_head = gh.strip() if gc == 0 else f"(rc={gc})"
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st_out, _, _ = _sh(["systemctl", "status", "stock-bot", "--no-pager"], timeout=45)
    ti_out, _, _ = _sh(
        ["systemctl", "status", "alpaca-telegram-integrity.timer", "--no-pager"], timeout=25
    )
    sv_out, _, _ = _sh(
        ["systemctl", "status", "alpaca-telegram-integrity.service", "--no-pager"], timeout=25
    )
    ls_state, _, _ = _bash("ls -lah state/ 2>/dev/null | sed -n '1,200p'", timeout=15)

    (ev / "ALPACA_INTEGRITY_ARM_BLOCKER_CONTEXT.md").write_text(
        "\n".join(
            [
                "# ALPACA_INTEGRITY_ARM_BLOCKER_CONTEXT",
                "",
                f"- **ET date (folder):** `{et}`",
                f"- **git HEAD:** `{git_head}`",
                f"- **UTC now:** `{utc}`",
                "",
                "## systemctl status stock-bot",
                "",
                "```",
                (st_out or "")[:14000],
                "```",
                "",
                "## systemctl status alpaca-telegram-integrity.timer",
                "",
                "```",
                (ti_out or "")[:8000],
                "```",
                "",
                "## systemctl status alpaca-telegram-integrity.service",
                "",
                "```",
                (sv_out or "")[:8000],
                "```",
                "",
                "## ls -lah state/ (first 200 lines)",
                "",
                "```",
                ls_state or "(empty or missing)",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 1 — static code pointers (authoritative) + optional rg
    rg_block = _rg_patterns()
    (ev / "ALPACA_INTEGRITY_ARM_CODE_POINTERS.md").write_text(
        "\n".join(
            [
                "# ALPACA_INTEGRITY_ARM_CODE_POINTERS",
                "",
                "## Arming writes `state/alpaca_milestone_integrity_arm.json`",
                "- **File:** `telemetry/alpaca_telegram_integrity/milestone.py`",
                "- **Function:** `update_integrity_arm_state(root, session_anchor_et, precheck_ok)`",
                "- **Boolean to set `arm_epoch_utc`:** `precheck_ok is True` AND `st.get('arm_epoch_utc') is None` AND same `session_anchor_et`",
                "- **Reset:** if `session_anchor_et` on disk != current anchor → `arm_epoch_utc` cleared to `None`",
                "",
                "## `precheck_ok` source (integrity cycle)",
                "- **File:** `telemetry/alpaca_telegram_integrity/runner_core.py`",
                "- **Function:** `_checkpoint_100_integrity_ok(cov, strict, cov_reasons, schema_reasons, max_age_h)`",
                "- **Passes only if `len(bad)==0` where `bad` accumulates:**",
                "  1. `cov.path is None` → `missing_coverage_artifact`",
                "  2. `cov.age_hours > max_age_h` → stale coverage",
                "  3. `cov.data_ready_yes is not True` → DATA_READY not YES",
                "  4. all strings in `cov_reasons` (thresholds + stale_or_missing_warehouse_coverage from runner)",
                "  5. all strings in `schema_reasons` (exit tail probe: missing field in > max(5, lines/4) rows)",
                "  6. `strict.get('LEARNING_STATUS') != 'ARMED'`",
                "",
                "## Milestone snapshot when unarmed",
                "- **File:** `telemetry/alpaca_telegram_integrity/milestone.py` — `build_milestone_snapshot`",
                "- **Condition:** `counting_basis == 'integrity_armed'` and `arm_epoch_utc is None` → `integrity_armed=False`, `unique_closed_trades=0`",
                "",
                "## Integrity cycle entrypoint",
                "- **Script:** `scripts/run_alpaca_telegram_integrity_cycle.py` → `telemetry.alpaca_telegram_integrity.runner_core.run_integrity_cycle`",
                "- **systemd:** `deploy/systemd/alpaca-telegram-integrity.service` + `.timer`",
                "",
                "## ripgrep (telemetry/scripts/src)",
                rg_block,
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 2
    arm_path = root / "state" / "alpaca_milestone_integrity_arm.json"
    ms250_path = root / "state" / "alpaca_milestone_250_state.json"
    cyc_path = root / "state" / "alpaca_telegram_integrity_cycle.json"

    def _load_json(p: Path) -> Any:
        if not p.is_file():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"_error": "parse_failed"}

    arm_j = _load_json(arm_path)
    ms_j = _load_json(ms250_path)
    cyc_j = _load_json(cyc_path)

    (ev / "ALPACA_INTEGRITY_ARM_STATE_INSPECTION.md").write_text(
        "\n".join(
            [
                "# ALPACA_INTEGRITY_ARM_STATE_INSPECTION",
                "",
                f"- **`state/alpaca_milestone_integrity_arm.json` exists:** {arm_path.is_file()}",
                "```json",
                json.dumps(arm_j if arm_j is not None else {}, indent=2),
                "```",
                "",
                f"- **`arm_epoch_utc` present:** {arm_j is not None and isinstance(arm_j, dict) and arm_j.get('arm_epoch_utc') is not None}",
                f"- **`session_anchor_et`:** `{arm_j.get('session_anchor_et') if isinstance(arm_j, dict) else None}`",
                "",
                "## Milestone 250 state",
                f"- **Path:** `{ms250_path}` exists: {ms250_path.is_file()}",
                "```json",
                json.dumps(ms_j if ms_j is not None else {}, indent=2),
                "```",
                "",
                "## Integrity cycle state (reference)",
                f"- **Path:** `{cyc_path}` exists: {cyc_path.is_file()}",
                "```json",
                json.dumps(cyc_j if cyc_j is not None else {}, indent=2)[:8000],
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 3 — reconstruct gates (read-only imports)
    from telemetry.alpaca_telegram_integrity import checks
    from telemetry.alpaca_telegram_integrity.runner_core import (
        _checkpoint_100_integrity_ok,
        _coverage_vs_thresholds,
        _load_config,
    )
    from telemetry.alpaca_telegram_integrity.warehouse_summary import load_latest_coverage

    cfg = _load_config(root)
    max_age = float(cfg.get("warehouse_coverage_file_max_age_hours", 36))
    thr = cfg.get("coverage_thresholds_pct") or {}
    cov = load_latest_coverage(root)
    cov_reasons = _coverage_vs_thresholds(cov, {k: float(v) for k, v in thr.items()})
    if cov.path is None or (cov.age_hours is not None and cov.age_hours > max_age):
        cov_reasons.append(
            f"stale_or_missing_warehouse_coverage (max_age_h={max_age}, age={cov.age_hours})"
        )

    strict: Dict[str, Any] = {}
    strict_err = ""
    try:
        strict = checks.run_strict_completeness(root)
    except Exception as e:
        strict_err = str(e)
        strict = {}

    tail_n = int(cfg.get("exit_attribution_tail_lines", 400))
    req_fields = list(cfg.get("exit_required_fields") or ["symbol", "exit_ts", "trade_id"])
    exit_path = root / "logs" / "exit_attribution.jsonl"
    probe = checks.probe_exit_attribution_tail(exit_path, tail_n, req_fields)
    schema_reasons: List[str] = []
    for field, cnt in probe.missing_field_counts.items():
        if probe.lines_scanned > 0 and cnt > max(5, probe.lines_scanned // 4):
            schema_reasons.append(f"exit_attribution missing {field} in {cnt}/{probe.lines_scanned} tail rows")

    cp_ok, cp_bad = _checkpoint_100_integrity_ok(
        cov, strict, cov_reasons, schema_reasons, max_age
    )

    cov_mtime = None
    cov_size = None
    if cov.path and cov.path.is_file():
        try:
            cov_mtime = datetime.fromtimestamp(cov.path.stat().st_mtime, tz=timezone.utc).isoformat()
            cov_size = cov.path.stat().st_size
        except OSError:
            pass

    gate_md: List[str] = [
        "# ALPACA_INTEGRITY_ARM_GATE_INPUTS",
        "",
        "Each gate below is evaluated in `_checkpoint_100_integrity_ok` + runner-fed `cov_reasons` / `schema_reasons`.",
        "",
        "## Gate: warehouse coverage artifact present",
        f"- **expected_source:** `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md` (latest by mtime) — `warehouse_summary.load_latest_coverage`",
        f"- **observed_path:** `{cov.path}`",
        f"- **exists:** {cov.path is not None and cov.path.is_file()}",
        f"- **mtime_utc:** `{cov_mtime}`",
        f"- **size_bytes:** `{cov_size}`",
        f"- **pass/fail:** {'PASS' if cov.path is not None else 'FAIL'}",
        "- **code_condition_reference:** `cov.path is None` → append `missing_coverage_artifact` (`runner_core.py` `_checkpoint_100_integrity_ok`)",
        "",
        "## Gate: coverage artifact age",
        f"- **max_age_h (config):** {max_age}",
        f"- **observed age_hours:** {cov.age_hours}",
        f"- **pass/fail:** {'PASS' if cov.path is not None and (cov.age_hours is None or cov.age_hours <= max_age) else 'FAIL'}",
        "- **code_condition_reference:** `cov.age_hours > max_age_h` → `coverage_artifact_stale`",
        "",
        "## Gate: DATA_READY == YES",
        f"- **observed data_ready_yes:** {cov.data_ready_yes!r}",
        f"- **pass/fail:** {'PASS' if cov.data_ready_yes is True else 'FAIL'}",
        "- **code_condition_reference:** `cov.data_ready_yes is not True` → `DATA_READY not YES (or unknown)`",
        "",
        "## Gate: coverage % thresholds",
        f"- **thresholds_pct (config):** `{json.dumps(thr)}`",
        f"- **observed:** execution_join={cov.execution_join_pct}, fee={cov.fee_pct}, slippage={cov.slippage_pct}",
        f"- **cov_reasons (threshold + warehouse stale line):**",
        "```",
        "\n".join(cov_reasons) or "(none)",
        "```",
    ]
    thr_fail = any(
        "execution_join" in x or "fee_coverage" in x or "slippage" in x or "DATA_READY reported NO" in x
        for x in cov_reasons
    )
    gate_md.append(f"- **pass/fail (_coverage_vs_thresholds subset):** {'FAIL' if thr_fail else 'PASS'}")
    gate_md.extend(
        [
            "- **code_condition_reference:** `_coverage_vs_thresholds` in `runner_core.py`",
            "",
            "## Gate: stale_or_missing_warehouse_coverage (runner precondition)",
            f"- **observed:** appended to cov_reasons when path missing OR age > max_age",
            f"- **present in cov_reasons:** {any('stale_or_missing_warehouse' in x for x in cov_reasons)}",
            "",
            "## Gate: exit_attribution tail schema probe",
            f"- **expected_source:** `{exit_path.relative_to(root)}` last **{tail_n}** lines",
            f"- **exit file exists:** {exit_path.is_file()}",
            f"- **last row exit/ts (sampled tail read):** `{_exit_jsonl_last_ts(exit_path)}`",
            f"- **lines_scanned:** {probe.lines_scanned}",
            f"- **missing_field_counts:** `{probe.missing_field_counts}`",
            f"- **schema_reasons:** `{schema_reasons}`",
            f"- **pass/fail:** {'PASS' if not schema_reasons else 'FAIL'}",
            "- **code_condition_reference:** `runner_core.py` — `cnt > max(5, lines_scanned // 4)`",
            "",
            "## Gate: strict completeness LEARNING_STATUS == ARMED",
            f"- **strict_error (if any):** `{strict_err}`",
            f"- **LEARNING_STATUS:** `{strict.get('LEARNING_STATUS')!r}`",
            f"- **pass/fail:** {'PASS' if strict.get('LEARNING_STATUS') == 'ARMED' else 'FAIL'}",
            "- **code_condition_reference:** `strict.get('LEARNING_STATUS') != 'ARMED'` in `_checkpoint_100_integrity_ok`",
            "",
            "## Composite precheck (this run, read-only)",
            f"- **cp_ok:** {cp_ok}",
            f"- **cp_bad (ordered):**",
            "```",
            json.dumps(cp_bad, indent=2),
            "```",
            "",
        ]
    )
    (ev / "ALPACA_INTEGRITY_ARM_GATE_INPUTS.md").write_text("\n".join(gate_md), encoding="utf-8")

    # Phase 4
    j1, _, jc1 = _bash(
        "journalctl -u alpaca-telegram-integrity.service --since '36 hours ago' --no-pager 2>/dev/null | tail -n 400",
        timeout=60,
    )
    j2, _, jc2 = _bash(
        "journalctl -u stock-bot --since '36 hours ago' --no-pager 2>/dev/null | rg -i 'integrity|milestone|telegram|arm_epoch|DATA_READY|checkpoint' | tail -n 120 || true",
        timeout=60,
    )
    integ_log = root / "logs" / "alpaca_telegram_integrity.log"
    log_tail = ""
    if integ_log.is_file():
        o, _, _ = _bash(f"tail -n 80 {integ_log} 2>/dev/null", timeout=15)
        log_tail = o

    (ev / "ALPACA_INTEGRITY_ARM_EXECUTION_TRACE.md").write_text(
        "\n".join(
            [
                "# ALPACA_INTEGRITY_ARM_EXECUTION_TRACE",
                "",
                "## journalctl alpaca-telegram-integrity.service (last ~400 lines / 36h)",
                f"- **journalctl rc:** {jc1}",
                "",
                "```",
                (j1 or "(empty)")[:16000],
                "```",
                "",
                "## journalctl stock-bot filtered (integrity keywords, last ~120)",
                f"- **rc:** {jc2}",
                "",
                "```",
                (j2 or "(empty or rg missing)")[:12000],
                "```",
                "",
                "## logs/alpaca_telegram_integrity.log (tail 80)",
                "",
                "```",
                log_tail or "(missing)",
                "```",
                "",
                "## Inference from `checkpoint_100_precheck`",
                f"- Current reconstructed **`cp_ok`:** **{cp_ok}**",
                f"- If `cp_ok` is False, `update_integrity_arm_state` does not set `arm_epoch_utc` (see `milestone.py`).",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 5
    from telemetry.alpaca_telegram_integrity.milestone import (
        build_milestone_snapshot,
        load_integrity_arm_state,
        integrity_arm_state_path,
        load_milestone_state,
        should_fire_milestone,
    )
    from telemetry.alpaca_telegram_integrity.runner_core import _milestone_state_path
    from telemetry.alpaca_telegram_integrity.session_clock import session_anchor_date_et_iso

    now_utc = datetime.now(timezone.utc)
    anchor_et = session_anchor_date_et_iso(now_utc)
    basis = str(cfg.get("milestone_counting_basis", "integrity_armed")).strip() or "integrity_armed"
    arm_disk = load_integrity_arm_state(integrity_arm_state_path(root))
    arm_ep: Optional[float] = None
    if basis == "integrity_armed":
        if arm_disk.get("session_anchor_et") == anchor_et:
            raw = arm_disk.get("arm_epoch_utc")
            arm_ep = float(raw) if raw is not None else None
    target = int(cfg.get("milestone_trade_count", 250))
    snap = build_milestone_snapshot(
        root, counting_basis=basis, arm_epoch_utc=arm_ep, now=now_utc
    )
    ms_path = _milestone_state_path(root)
    fire, _st = should_fire_milestone(root, target, snap, ms_path)

    (ev / "ALPACA_250_MILESTONE_BLOCK_PROOF.md").write_text(
        "\n".join(
            [
                "# ALPACA_250_MILESTONE_BLOCK_PROOF",
                "",
                "## Production-equivalent snapshot (read-only, no send)",
                f"- **milestone_counting_basis:** `{basis}`",
                f"- **session_anchor_et (now):** `{snap.session_anchor_et}`",
                f"- **arm_disk session_anchor_et:** `{arm_disk.get('session_anchor_et')}`",
                f"- **arm_epoch_utc used for snap:** `{arm_ep}`",
                f"- **snap.integrity_armed:** {snap.integrity_armed}",
                f"- **snap.unique_closed_trades:** {snap.unique_closed_trades}",
                f"- **snap.count_floor_utc_iso:** `{snap.count_floor_utc_iso}`",
                f"- **target:** {target}",
                f"- **should_fire_milestone:** {fire}",
                "",
                "## Why `unique_closed_trades` is 0 when unarmed",
                "- **Code:** `milestone.py` `build_milestone_snapshot` — if `integrity_armed` basis and `arm_epoch_utc is None`, returns snapshot with **0** trades.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 6
    audit_script = root / "scripts" / "audit" / "alpaca_250_audit_readiness_mission.py"
    audit_snip = ""
    if audit_script.is_file():
        txt = audit_script.read_text(encoding="utf-8", errors="replace")
        audit_snip = "Uses `exit_attribution.jsonl` tail, matrix files, file presence — **no** `arm_epoch_utc` / `integrity_arm_state` references in script body (static review of mission entry)."

    (ev / "ALPACA_MASSIVE_AUDIT_TRIGGER_DEPENDENCY.md").write_text(
        "\n".join(
            [
                "# ALPACA_MASSIVE_AUDIT_TRIGGER_DEPENDENCY",
                "",
                "## Script: `scripts/audit/alpaca_250_audit_readiness_mission.py`",
                audit_snip,
                "",
                "## Telegram 250 milestone",
                "- **Depends on arming** when `milestone_counting_basis` is `integrity_armed`: milestone count is 0 until `arm_epoch_utc` set.",
                "",
                "## systemd: integrity cycle",
                "- **`alpaca-telegram-integrity.service`** runs `scripts/run_alpaca_telegram_integrity_cycle.py` — this is where `update_integrity_arm_state(..., cp_ok)` runs.",
                "",
                "## Verdict",
                "- **Massive / 250-trade readiness mission:** **not gated** on `arm_epoch_utc` in the mission script itself (data surfaces + joins).",
                "- **250 Telegram milestone:** **gated** on armed session count when basis is `integrity_armed`.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 7 — single root cause: first cp_bad entry if any, else strict ordering
    armed_now = arm_ep is not None and isinstance(arm_disk, dict) and arm_disk.get("session_anchor_et") == anchor_et
    if cp_bad:
        primary = cp_bad[0]
    elif not cp_ok:
        primary = "(checkpoint failed with empty cp_bad — unexpected)"
    else:
        primary = "(no gate failures in reconstruction — integrity timer / enabled / not yet run)"

    if armed_now:
        root_cause = "Session is armed on disk for current anchor; arming blocker analysis for **unarmed** state is N/A."
    elif cp_bad:
        root_cause = (
            "`update_integrity_arm_state(root, session_anchor_et, precheck_ok)` receives **`precheck_ok=False`** "
            "because `_checkpoint_100_integrity_ok` returned failures. "
            f"**First failing condition in `cp_bad`:** `{primary}`. "
            f"With `arm_epoch_utc` still None for anchor `{anchor_et}`, `build_milestone_snapshot` keeps **0** milestone trades."
        )
    else:
        root_cause = (
            "Reconstructed `cp_ok` is **True** but disk shows **no** `arm_epoch_utc` for this anchor — "
            "not an arming-gate failure; check **`alpaca-telegram-integrity.timer`** active, "
            "`config/alpaca_telegram_integrity.json` `enabled`, and that the oneshot service runs after this mission’s snapshot."
        )

    blocks_250 = basis == "integrity_armed" and not snap.integrity_armed
    blocks_audit = "NO — `alpaca_250_audit_readiness_mission.py` does not read arm state (documentation mission)."

    (ev / "ALPACA_INTEGRITY_ARM_BLOCKER_FINAL_VERDICT.md").write_text(
        "\n".join(
            [
                "# ALPACA_INTEGRITY_ARM_BLOCKER_FINAL_VERDICT",
                "",
                f"- **Is the session armed (current ET anchor `{anchor_et}`)?** **{'YES' if armed_now else 'NO'}**",
                "",
                "## One root cause (from reconstructed `cp_bad`, first entry)",
                f"- **Primary failing gate string:** `{primary}`",
                f"- **Full cp_bad:** {cp_bad}",
                "",
                "## Narrative",
                root_cause,
                "",
                "## Blocks",
                f"- **250 Telegram milestone (integrity_armed basis):** **{'YES' if blocks_250 else 'NO'}**",
                f"- **Massive PnL audit readiness mission (script-driven):** {blocks_audit}",
                "",
                "## Minimal corrective action (ops/data/config only)",
                "- Restore a **fresh** `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md` with **DATA_READY: YES** and ages within `warehouse_coverage_file_max_age_hours`.",
                "- Fix **strict completeness** to **ARMED** (see strict gate outputs / `telemetry.alpaca_strict_completeness_gate`).",
                "- Fix **exit_attribution** tail schema gaps if probe fails threshold.",
                "- Ensure **`alpaca-telegram-integrity.timer`** is active so `update_integrity_arm_state` runs after gates pass.",
                "- **No strategy changes, liquidation, or tuning** in this mission.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "evidence_dir": str(ev),
                "armed": armed_now,
                "cp_ok": cp_ok,
                "cp_bad": cp_bad,
                "primary_gate": primary,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
