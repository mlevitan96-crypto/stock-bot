#!/usr/bin/env python3
"""
250-trade threshold diagnosis (droplet evidence). Read-only on strategy.

Writes reports/daily/<ET-date>/evidence/ALPACA_250_*.md

Run: cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_alpaca_250_threshold_diagnosis.py
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


def _sh(cmd: List[str], timeout: int = 60) -> Tuple[str, str, int]:
    try:
        r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=timeout)
        return (r.stdout or ""), (r.stderr or ""), r.returncode
    except Exception as e:
        return "", str(e), 1


def _merge_env_like_runner(root: Path) -> None:
    """Match telemetry.alpaca_telegram_integrity.runner_core._merge_env_files."""
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


def _ground_truth_ordered_trades(root: Path, floor_epoch: Optional[float]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Unique trade_key from exit_attribution.jsonl (era-cut excluded), optional exit-time floor.
    Each trade: first row with minimum exit epoch for that key (chronological first close).
    """
    from src.telemetry.alpaca_trade_key import build_trade_key
    from utils.era_cut import learning_excluded_for_exit_record

    exit_path = root / "logs" / "exit_attribution.jsonl"

    def _parse_exit_epoch(rec: dict) -> Optional[float]:
        for k in ("exit_ts", "timestamp", "ts", "exit_timestamp"):
            v = rec.get(k)
            if not v:
                continue
            try:
                s = str(v).strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except (TypeError, ValueError):
                continue
        return None

    best: Dict[str, Dict[str, Any]] = {}
    era_ex = floor_ex = skip_tk = 0

    if not exit_path.is_file():
        return [], {"era_excluded": 0, "floor_excluded": 0, "skipped_no_trade_key": 0}

    with exit_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            if learning_excluded_for_exit_record(rec):
                era_ex += 1
                continue
            ex = _parse_exit_epoch(rec)
            if floor_epoch is not None:
                if ex is None or ex < floor_epoch:
                    floor_ex += 1
                    continue
            elif ex is None:
                continue
            sym = rec.get("symbol")
            side = rec.get("side") or rec.get("position_side")
            et = rec.get("entry_ts") or rec.get("entry_timestamp")
            try:
                tk = build_trade_key(sym, side, et)
            except Exception:
                skip_tk += 1
                continue
            tid = rec.get("trade_id") or rec.get("canonical_trade_id") or ""
            prev = best.get(tk)
            if prev is None or ex < prev["exit_epoch"]:
                best[tk] = {
                    "trade_key": tk,
                    "trade_id": str(tid) if tid is not None else "",
                    "exit_epoch": ex,
                    "exit_ts": rec.get("exit_ts") or rec.get("exit_timestamp") or rec.get("ts"),
                    "symbol": sym,
                }

    ordered = sorted(best.values(), key=lambda x: x["exit_epoch"])
    stats = {"era_excluded": era_ex, "floor_excluded": floor_ex, "skipped_no_trade_key": skip_tk}
    return ordered, stats


def main() -> int:
    root = REPO.resolve()
    ev = _evidence_dir()
    et = _et_date_iso()

    head_o, _, hc = _sh(["git", "rev-parse", "HEAD"])
    head = head_o.strip() if hc == 0 else f"(rc={hc})"
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st_o, _, _ = _sh(["systemctl", "status", "stock-bot", "--no-pager"], timeout=30)

    # Phase 0
    (ev / "ALPACA_250_THRESHOLD_CONTEXT.md").write_text(
        "\n".join(
            [
                "# ALPACA_250_THRESHOLD_CONTEXT",
                "",
                f"- **ET date (folder):** `{et}`",
                f"- **git HEAD:** `{head}`",
                f"- **UTC now:** `{utc}`",
                "",
                "## systemctl status stock-bot",
                "",
                "```",
                (st_o or "(no output)")[:14000],
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Canonical definition paths
    req_path = root / "docs" / "pnl_audit" / "REQUIRED_FIELDS.md"
    canon_def = root / "reports" / "daily" / et / "evidence" / "ALPACA_CANONICAL_TRADE_DEFINITION.md"
    if not canon_def.is_file():
        # fallback: any recent evidence copy
        cand = sorted(root.glob("reports/daily/*/evidence/ALPACA_CANONICAL_TRADE_DEFINITION.md"))
        canon_def = cand[-1] if cand else canon_def

    req_ex = req_path.is_file()
    canon_ex = canon_def.is_file()

    ordered_all, stats_all = _ground_truth_ordered_trades(root, floor_epoch=None)
    n_all = len(ordered_all)
    ge250 = n_all >= 250
    trade_250: Optional[Dict[str, Any]] = ordered_all[249] if ge250 else None

    ids_path = ev / "ALPACA_250_THRESHOLD_GROUND_TRUTH_TRADE_IDS.json"
    ids_payload = {
        "total_post_era_trades": n_all,
        "trade_ids_chronological": [t.get("trade_id") or "" for t in ordered_all],
        "trade_keys_chronological": [t.get("trade_key") or "" for t in ordered_all],
        "stats": stats_all,
    }
    ids_path.write_text(json.dumps(ids_payload, indent=2), encoding="utf-8")

    # Phase 1
    t250_block = ""
    if trade_250:
        t250_block = (
            f"- **Trade #250 (chronological first close per trade_key):**\n"
            f"  - `trade_id`: `{trade_250.get('trade_id')}`\n"
            f"  - `trade_key`: `{trade_250.get('trade_key')}`\n"
            f"  - `exit_ts`: `{trade_250.get('exit_ts')}`\n"
        )
    else:
        t250_block = "- **Trade #250:** N/A (count < 250)\n"

    (ev / "ALPACA_250_THRESHOLD_GROUND_TRUTH.md").write_text(
        "\n".join(
            [
                "# ALPACA_250_THRESHOLD_GROUND_TRUTH",
                "",
                "## Definition sources (loaded)",
                f"- `docs/pnl_audit/REQUIRED_FIELDS.md` exists: **{req_ex}**",
                f"- `ALPACA_CANONICAL_TRADE_DEFINITION.md` (evidence): **{canon_ex}** — path used: `{canon_def}`",
                "",
                "## Method (matches `compute_canonical_trade_count`, no floor)",
                "- Ledger: `logs/exit_attribution.jsonl`",
                "- Unit: unique `trade_key` = `build_trade_key(symbol, side, entry_ts)`",
                "- Exclude: `learning_excluded_for_exit_record` (era cut)",
                "- Require: parsable exit timestamp",
                "- Order: ascending by **first** qualifying exit epoch per key (chronological closes)",
                "- Identity for audit: `trade_id` from the row that supplied that first close (fallback `canonical_trade_id`)",
                "",
                "## Results",
                f"- **total_post_era_trades:** {n_all}",
                f"- **count >= 250:** {'YES' if ge250 else 'NO'}",
                t250_block,
                f"- **Full id list:** `{ids_path.relative_to(root)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 2 — notifier snapshot (same as runner)
    from telemetry.alpaca_telegram_integrity.milestone import (
        build_milestone_snapshot,
        integrity_arm_state_path,
        load_integrity_arm_state,
        load_milestone_state,
        should_fire_milestone,
    )
    from telemetry.alpaca_telegram_integrity.runner_core import _load_config, _milestone_state_path
    from telemetry.alpaca_telegram_integrity.session_clock import session_anchor_date_et_iso

    cfg = _load_config(root)
    target = int(cfg.get("milestone_trade_count", 250))
    basis = str(cfg.get("milestone_counting_basis", "integrity_armed")).strip() or "integrity_armed"
    if basis not in ("session_open", "integrity_armed"):
        basis = "integrity_armed"

    now_utc = datetime.now(timezone.utc)
    anchor_et = session_anchor_date_et_iso(now_utc)
    ms_path = _milestone_state_path(root)
    raw_st = load_milestone_state(ms_path)

    arm_ep: Optional[float] = None
    arm_path = integrity_arm_state_path(root)
    arm_disk = load_integrity_arm_state(arm_path)
    if basis == "integrity_armed":
        # Read-only: do not call update_integrity_arm_state (would mutate disk).
        if arm_disk.get("session_anchor_et") != anchor_et:
            arm_ep = None
            precheck_note = (
                f"disk session_anchor_et={arm_disk.get('session_anchor_et')!r} != today {anchor_et!r} "
                "→ treat as unarmed until next integrity cycle updates arm file"
            )
        else:
            raw_arm = arm_disk.get("arm_epoch_utc")
            arm_ep = float(raw_arm) if raw_arm is not None else None
            precheck_note = "arm_epoch read from state/alpaca_milestone_integrity_arm.json (read-only)"
    else:
        precheck_note = "basis=session_open (no integrity arm)"

    snap = build_milestone_snapshot(
        root, counting_basis=basis, arm_epoch_utc=arm_ep, now=now_utc
    )
    fire, ms_st_after_eval = should_fire_milestone(root, target, snap, ms_path)

    # last trade id from notifier's counting window (ordered with same floor as snap)
    floor_epoch = None
    if basis == "session_open":
        from telemetry.alpaca_telegram_integrity.session_clock import effective_regular_session_open_utc

        floor_epoch = effective_regular_session_open_utc(now_utc).timestamp()
    elif basis == "integrity_armed" and arm_ep is not None:
        floor_epoch = arm_ep

    last_tid = ""
    if basis == "integrity_armed" and arm_ep is None:
        ordered_floor, stats_floor = [], {"note": "integrity not armed — no floor; notifier uses 0 trades"}
    else:
        ordered_floor, stats_floor = _ground_truth_ordered_trades(root, floor_epoch=floor_epoch)
    if ordered_floor:
        last_tid = str(ordered_floor[-1].get("trade_id") or "")

    notifier_st_on_disk = dict(raw_st)
    (ev / "ALPACA_250_MILESTONE_NOTIFIER_STATE.md").write_text(
        "\n".join(
            [
                "# ALPACA_250_MILESTONE_NOTIFIER_STATE",
                "",
                "## Config",
                f"- `config/alpaca_telegram_integrity.json`: `milestone_trade_count` = **{target}**",
                f"- `milestone_counting_basis` = **{basis}**",
                f"- `enabled` = **{cfg.get('enabled', True)}**",
                "",
                "## Persisted state file",
                f"- Path: `{ms_path.relative_to(root)}`",
                "```json",
                json.dumps(notifier_st_on_disk, indent=2),
                "```",
                "",
        "## Integrity arm (when basis=integrity_armed)",
        f"- Path: `{arm_path.relative_to(root)}`",
        "```json",
        json.dumps(arm_disk, indent=2),
        "```",
                f"- **Precheck note (for arm update):** {precheck_note}",
                "",
                "## Computed snapshot (this run)",
                "```json",
                json.dumps(
                    {
                        "session_anchor_et": snap.session_anchor_et,
                        "counting_basis": snap.counting_basis,
                        "count_floor_utc_iso": snap.count_floor_utc_iso,
                        "integrity_armed": snap.integrity_armed,
                        "unique_closed_trades": snap.unique_closed_trades,
                        "realized_pnl_sum_usd": snap.realized_pnl_sum_usd,
                        "sample_trade_keys": snap.sample_trade_keys,
                    },
                    indent=2,
                ),
                "```",
                "",
                "## should_fire_milestone(target)",
                f"- **notifier_trade_count** (snap.unique_closed_trades): **{snap.unique_closed_trades}**",
                f"- **fired_milestone** (from should_fire in-memory state; resets on new session_anchor_et): **{bool(ms_st_after_eval.get('fired_milestone'))}**",
                f"- **should_fire now:** **{fire}**",
                f"- **last_count** in returned state: **{ms_st_after_eval.get('last_count')}**",
                f"- **notifier_last_trade_id_seen** (chronological last in floored set): `{last_tid}`",
                f"- **Floored trade count (recomputed):** {len(ordered_floor)} (floor_epoch={floor_epoch!r})",
                f"- **Floor stats:** {json.dumps(stats_floor)}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 3 reconciliation
    n_notifier = snap.unique_closed_trades
    cls = "A"
    if n_all < 250 and n_notifier < 250 and n_all == n_notifier:
        cls = "A"
    elif n_all >= 250 and n_notifier >= 250 and n_all == n_notifier:
        cls = "B"
    elif n_all >= 250 and n_notifier < 250:
        cls = "C"
    elif n_notifier >= 250 and n_all < 250:
        cls = "D"
    else:
        cls = "MIXED (counts differ but not C/D pattern — see numbers)"

    (ev / "ALPACA_250_COUNT_RECONCILIATION.md").write_text(
        "\n".join(
            [
                "# ALPACA_250_COUNT_RECONCILIATION",
                "",
                "| Source | Count |",
                "|--------|-------|",
                f"| Ground truth (post-era, no floor) | {n_all} |",
                f"| Notifier / milestone snap (basis={basis}, floored) | {n_notifier} |",
                f"| Recomputed floored list length | {len(ordered_floor)} |",
                "",
                f"## Classification: **{cls}**",
                "- **A)** Match and < 250",
                "- **B)** Match and >= 250",
                "- **C)** Ground truth >= 250, notifier < 250",
                "- **D)** Notifier >= 250, ground truth < 250",
                "",
            ]
        ),
        encoding="utf-8",
    )

    _merge_env_like_runner(root)

    # Phase 4
    integ_only = os.environ.get("TELEGRAM_GOVERNANCE_INTEGRITY_ONLY", "").strip().lower()
    fired_already = bool(notifier_st_on_disk.get("fired_milestone")) and notifier_st_on_disk.get(
        "session_anchor_et"
    ) == snap.session_anchor_et

    suppression_lines = [
        "## Suppression / blockers",
        "",
        f"- **config.enabled:** {cfg.get('enabled', True)}",
        f"- **TELEGRAM_GOVERNANCE_INTEGRITY_ONLY:** `{integ_only or '(unset)'}`",
        f"- **Duplicate-send guard:** `fired_milestone` for current `session_anchor_et` = **{fired_already}**",
        f"- **Integrity not armed (basis=integrity_armed):** {not snap.integrity_armed} → milestone count forced to **0** until armed",
        "",
        "### Milestone vs 100-trade checkpoint",
        "- **250 milestone** does **not** use the same DATA_READY / strict ARMED gate as the 100-trade checkpoint; it keys off `unique_closed_trades >= target` and `not fired_milestone` for the ET session anchor.",
        "",
        "### If ground truth >= 250 but notifier < 250 (class C)",
        "- Primary cause: **count floor** (`session_open` or `integrity_armed` epoch) excludes closes before the floor while post-era cumulative count includes them.",
        "",
    ]

    if trade_250:
        suppression_lines.extend(
            [
                "### Trade #250 row (era / key)",
                f"- Row used for #250 identity is from first close per key; verify `trade_id` present: `{bool(trade_250.get('trade_id'))}`",
                "",
            ]
        )

    (ev / "ALPACA_250_ALERT_SUPPRESSION_ANALYSIS.md").write_text(
        "\n".join(suppression_lines), encoding="utf-8"
    )

    # Phase 5 — no HTTP; do not run full integrity --dry-run (would mark milestone fired if fire True)
    token = bool(os.environ.get("TELEGRAM_BOT_TOKEN"))
    chat = bool(os.environ.get("TELEGRAM_CHAT_ID"))
    msg_preview = ""
    try:
        from telemetry.alpaca_telegram_integrity.templates import format_milestone_250
        from telemetry.alpaca_telegram_integrity import checks

        spi = checks.latest_spi_pointer(root)
        msg_preview = format_milestone_250(
            test=False,
            snap=snap,
            data_ready="YES",
            strict_status="ARMED",
            spi_rel=spi,
            reports_hint="reports/daily/*/evidence/",
        )[:1200]
    except Exception as e:
        msg_preview = f"(format_milestone_250 failed: {e})"

    (ev / "ALPACA_250_TELEGRAM_DRY_RUN.md").write_text(
        "\n".join(
            [
                "# ALPACA_250_TELEGRAM_DRY_RUN",
                "",
                "## Scope",
                "- **No Telegram HTTP** performed.",
                "- **Did not run** `run_alpaca_telegram_integrity_cycle.py --dry-run` when `should_fire` could be True: in current code, dry-run `send_msg` returns True and **`mark_milestone_fired` would run**, mutating state without a real send (hazard).",
                "",
                "## Environment (after merging `.env` / `.alpaca_env` like runner)",
                f"- **TELEGRAM_BOT_TOKEN set:** {token}",
                f"- **TELEGRAM_CHAT_ID set:** {chat}",
                "",
                "## Message construction",
                "- `format_milestone_250(...)` with current **snap** (truncated preview):",
                "",
                "```",
                msg_preview,
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Phase 6
    crossed = "YES" if ge250 else "NO"
    should_have = "NO"
    reason = ""
    corrective = ""

    if not ge250:
        should_have = "NO"
        reason = "Post-era canonical count is below 250; milestone is defined vs floored notifier count — see reconciliation."
    elif n_notifier >= target and fire:
        should_have = "YES"
        reason = "Notifier count >= 250 and should_fire is True; if no Telegram was received, investigate send_governance_telegram failure (TELEGRAM_NOTIFICATION_LOG.md) or quiet-hours suppression."
    elif n_notifier >= target and not fire and fired_already:
        should_have = "NO"
        reason = "Milestone already marked fired for this session_anchor_et (duplicate protection)."
    elif n_notifier >= target and not fire and not fired_already:
        should_have = "YES"
        reason = "Inconsistent: count >= target but should_fire False — inspect should_fire_milestone state logic / race."
    else:
        should_have = "NO"
        if ge250 and basis == "integrity_armed" and not snap.integrity_armed:
            reason = (
                "Ground truth >= 250, but `milestone_counting_basis` is **integrity_armed** and the session is **not armed** "
                "(arm_epoch unset until DATA_READY + coverage freshness + strict ARMED + exit tail probe pass). "
                "Notifier count stays **0** until then — independent of cumulative post-era closes."
            )
            corrective = (
                "No strategy change. Let the integrity cycle run green to arm the day, or governance may set "
                "`milestone_counting_basis` to `session_open` (policy only). Check warehouse coverage / strict gate / exit_probe if arm never arms."
            )
        else:
            reason = (
                f"Ground truth >= 250 but notifier floored count is {n_notifier} (< {target}). "
                "Milestone uses session/arm floor, not cumulative post-era count."
            )
            corrective = (
                "No strategy change required. For Telegram to fire at 250 **on the floored basis**, "
                "the session must accumulate 250 closes after the count floor; "
                "or change `milestone_counting_basis` / policy (governance decision, not done here). "
                "If a prior send failed, check `TELEGRAM_NOTIFICATION_LOG.md` and re-run send only per governance."
            )

    if ge250 and n_notifier >= target and not fired_already and not fire:
        corrective = "Inspect `should_fire_milestone` and `alpaca_milestone_250_state.json` for corruption or session_anchor mismatch."

    if_yes_no_fire = reason if should_have == "YES" else "N/A (milestone should not have fired under current rules)"
    (ev / "ALPACA_250_THRESHOLD_FINAL_VERDICT.md").write_text(
        "\n".join(
            [
                "# ALPACA_250_THRESHOLD_FINAL_VERDICT",
                "",
                f"- **Has the system crossed 250 canonical trades (post-era, no floor)?** **{crossed}**",
                f"- **Should the 250 milestone have fired (per notifier rules)?** **{should_have}**",
                f"- **If YES and it did not fire — exact reason:** {if_yes_no_fire}",
                f"- **Why notifier has not fired (operator summary):** {reason}",
                f"- **Corrective action:** {corrective or 'None required for threshold semantics; verify Telegram credentials and logs if send failed while should_fire was True.'}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps({"evidence_dir": str(ev), "classification": cls, "n_all": n_all, "n_notifier": n_notifier}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
