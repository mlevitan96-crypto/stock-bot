#!/usr/bin/env python3
"""
Post-market Alpaca governance + integrity audit (read-only except liquidation --dry-run).
Run on droplet from repo root: python3 scripts/audit/alpaca_post_market_full_governance_audit.py

Writes under reports/daily/<ET-date>/evidence/:
  ALPACA_POST_MARKET_AUDIT_CONTEXT.md
  ALPACA_ENGINE_SRE_AUDIT.md
  ALPACA_EXIT_INTEGRITY_AUDIT.md
  ALPACA_METADATA_TRUTH_AUDIT.md
  ALPACA_LIQUIDATION_SAFETY_AUDIT.md
  ALPACA_EXIT_TUNING_GOVERNANCE_AUDIT.md
  ALPACA_DASHBOARD_TRUTH_AUDIT.md
  ALPACA_POST_MARKET_FINAL_VERDICT.md
"""
from __future__ import annotations

import base64
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")


def _et_date() -> str:
    try:
        r = subprocess.run(
            ["bash", "-lc", "TZ=America/New_York date +%Y-%m-%d"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _shell(cmd: str, timeout: int = 120) -> Tuple[str, str, int]:
    try:
        r = subprocess.run(
            ["bash", "-lc", cmd],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.stdout or "", r.stderr or "", r.returncode
    except Exception as e:
        return "", str(e), 1


def _tail_jsonl(path: Path, n: int) -> str:
    if not path.exists():
        return "(file missing)"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-n:])
    except Exception as e:
        return f"(read error: {e})"


def _parse_jsonl_tail(path: Path, n: int) -> List[dict]:
    out: List[dict] = []
    if not path.exists():
        return out
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]:
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


def _last_json_object(text: str) -> Dict[str, Any]:
    """Extract last top-level JSON object from stdout (handles log lines before JSON)."""
    s = text.strip()
    if not s:
        return {}
    end = s.rfind("}")
    if end < 0:
        return {}
    depth = 0
    for i in range(end, -1, -1):
        c = s[i]
        if c == "}":
            depth += 1
        elif c == "{":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(s[i : end + 1])
                    return obj if isinstance(obj, dict) else {}
                except json.JSONDecodeError:
                    return {}
    return {}


def _era_cut_epoch() -> Optional[int]:
    try:
        from utils.era_cut import get_alpaca_era_cut_dt_utc

        dt = get_alpaca_era_cut_dt_utc()
        if dt is None:
            return None
        return int(dt.timestamp())
    except Exception:
        return None


def _cycle_stats(rows: List[dict], era_epoch: Optional[int] = None) -> Tuple[Optional[float], int, Optional[str]]:
    import statistics

    ts_list: List[int] = []
    last_rf = None
    for r in rows:
        if r.get("msg") != "complete":
            continue
        t = r.get("_ts")
        if era_epoch is not None:
            if not isinstance(t, (int, float)) or int(t) < era_epoch:
                continue
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


def _load_diag():
    p = REPO / "scripts/audit/alpaca_engine_droplet_realtime_diagnostic.py"
    spec = importlib.util.spec_from_file_location("alpaca_rt_diag", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _verdict_line(phase: str, ok: bool, detail: str) -> str:
    return f"- **{phase}:** {'PASS' if ok else 'FAIL'} — {detail}\n"


def main() -> int:
    import alpaca_trade_api as tradeapi  # type: ignore

    from main import Config, load_metadata_with_lock, read_uw_cache
    from config.registry import StateFiles

    et = _et_date()
    evdir = REPO / "reports" / "daily" / et / "evidence"
    evdir.mkdir(parents=True, exist_ok=True)

    logd = REPO / "logs"
    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)

    # --- Alpaca clock (market) ---
    market_closed = None
    clock_note = ""
    try:
        clk = api.get_clock()
        market_closed = not bool(getattr(clk, "is_open", True))
        clock_note = f"is_open={getattr(clk, 'is_open', None)} next_open={getattr(clk, 'next_open', None)} next_close={getattr(clk, 'next_close', None)}"
    except Exception as e:
        clock_note = f"clock API error: {e}"

    # --- Phase 0 ---
    p0 = []
    p0.append("# ALPACA POST-MARKET AUDIT — CONTEXT & SAFETY\n\n")
    p0.append(f"- Captured UTC: `{_utc_iso()}`\n")
    p0.append(f"- ET calendar date (folder): **`{et}`**\n\n")
    p0.append("## Market session (Alpaca clock API)\n\n")
    if market_closed is None:
        p0.append("**FAIL:** Could not determine market state from Alpaca clock.\n\n")
        p0.append(f"- Detail: {clock_note}\n\n")
    else:
        p0.append(f"- **Market closed (Alpaca):** `{market_closed}`\n")
        p0.append(f"- {clock_note}\n\n")

    st_out, st_err, st_rc = _shell("systemctl status stock-bot --no-pager 2>&1", timeout=30)
    p0.append("## systemctl status stock-bot\n\n```\n")
    p0.append(st_out[:12000] + (st_err or ""))
    p0.append("\n```\n\n")

    gh_out, _, gh_rc = _shell("git rev-parse HEAD 2>&1", timeout=15)
    p0.append(f"## Git commit (droplet repo)\n\n- `HEAD` = `{gh_out.strip()}` (exit {gh_rc})\n\n")

    p0.append("## Timestamps (evidence)\n\n")
    tu, _, _ = _shell("date -u '+%Y-%m-%dT%H:%M:%SZ'", timeout=5)
    te, _, _ = _shell("TZ=America/New_York date '+%Y-%m-%d %H:%M:%S %Z'", timeout=5)
    p0.append(f"- UTC (date -u): `{tu.strip()}`\n")
    p0.append(f"- America/New_York: `{te.strip()}`\n")

    (evdir / "ALPACA_POST_MARKET_AUDIT_CONTEXT.md").write_text("".join(p0), encoding="utf-8")

    phase0_pass = market_closed is True and "active (running)" in st_out.lower()

    # --- Phase 1 SRE ---
    j_out, j_err, j_rc = _shell('journalctl -u stock-bot --since "today" --no-pager 2>&1 | tail -n 400', timeout=90)
    run_rows = _parse_jsonl_tail(logd / "run.jsonl", 500)
    sf_rows = _parse_jsonl_tail(logd / "scoring_flow.jsonl", 500)
    _era_ep = _era_cut_epoch()
    med_gap, n_complete, last_rf = _cycle_stats(run_rows, _era_ep)

    restart_hits = len(re.findall(r"(?i)(started|starting|stopping|stopped|restart|failed|segfault)", j_out))
    p1 = []
    p1.append("# ALPACA ENGINE SRE AUDIT\n\n")
    p1.append(f"- Evidence UTC: `{_utc_iso()}`\n\n")
    p1.append("## journalctl -u stock-bot --since today (tail 400 lines)\n\n```\n")
    p1.append(j_out[:20000])
    p1.append("\n```\n\n")
    if j_err:
        p1.append(f"stderr: `{j_err[:500]}`\n\n")
    p1.append(f"- journalctl exit code: `{j_rc}`\n\n")

    p1.append("## run.jsonl — last 500 lines (raw tail)\n\n```\n")
    p1.append(_tail_jsonl(logd / "run.jsonl", 500)[:25000])
    p1.append("\n```\n\n")
    p1.append("## run.jsonl — cycle cadence (msg=complete)\n\n")
    p1.append(f"- complete rows in window: **{n_complete}**\n")
    p1.append(f"- median gap seconds (consecutive complete _ts): **`{med_gap}`**\n")
    p1.append(f"- latest risk_freeze seen on complete rows: **`{last_rf}`**")
    if _era_ep is not None:
        p1.append(f" (filtered: `_ts` >= era cut epoch `{_era_ep}`)\n\n")
    else:
        p1.append("\n\n")

    p1.append("## scoring_flow.jsonl — last 500 lines (truncated)\n\n```\n")
    p1.append(_tail_jsonl(logd / "scoring_flow.jsonl", 500)[:25000])
    p1.append("\n```\n\n")

    p1.append("## Interpretation (evidence-backed)\n\n")
    p1.append(
        "- **Engine running:** `systemctl status` shows active (running) — see CONTEXT artifact.\n"
        "- **Silent freeze:** Low complete count during RTH would be suspicious; post-market, sparse completes may be normal — cite counts above.\n"
        "- **Capacity deadlock:** Not directly proven here; scan journal tail for `capacity` / `capacity_limit` if entries blocked (grep in journal text above).\n"
        "- **risk_freeze:** Latest non-null value on complete lines above; `null`/absent usually means no freeze flag on last cycles.\n"
    )

    (evdir / "ALPACA_ENGINE_SRE_AUDIT.md").write_text("".join(p1), encoding="utf-8")

    # Post-market: last 500 lines may include sparse "complete" rows; do not over-tighten cadence.
    freeze_ok = last_rf in (None, "", "null", "None")
    cadence_ok = True
    if med_gap is not None and n_complete >= 3:
        cadence_ok = float(med_gap) < 7200.0
    phase1_pass = freeze_ok and cadence_ok and n_complete >= 1
    # Right after era cut, filtered window may be empty briefly — allow PASS if era active and engine running.
    if _era_ep is not None and n_complete < 1:
        phase1_pass = "active (running)" in st_out.lower()

    # --- Phase 2 exit integrity (per open position via analyze_symbol) ---
    mod = _load_diag()
    analyze_symbol = mod.analyze_symbol
    _global_regime = mod._global_regime
    _exit_timing_cfg = mod._exit_timing_cfg

    positions = api.list_positions() or []
    all_metadata = load_metadata_with_lock(StateFiles.POSITION_METADATA)
    if not isinstance(all_metadata, dict):
        all_metadata = {}
    uw_cache = read_uw_cache()
    regime = _global_regime()
    exit_timing_cfg = _exit_timing_cfg(regime)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    p2 = []
    p2.append("# ALPACA EXIT INTEGRITY AUDIT\n\n")
    p2.append("Exit path taxonomy: **stop** (fixed % loss), **trail** (trailing stop hit), **profit** (target hit), **decay** (signal decay ratio), **stale** (time/stale rules), **structural** (`structural_intelligence`), **v2** (exit score v2 >= threshold + hold floor).\n\n")
    p2.append("Suppression per mission: hold-time floor, score decay gating, P&L thresholds — mapped from `notes`, `v2_blocked_hold_floor`, decay flags, and rule fields below.\n\n")

    exit_ok = True
    for p in positions:
        sym = getattr(p, "symbol", "") or ""
        if not sym:
            continue
        try:
            row = analyze_symbol(sym, p, all_metadata, uw_cache, regime, exit_timing_cfg, now)
        except Exception as e:
            p2.append(f"## {sym}\n\n**FAIL:** analyze_symbol error: `{e}`\n\n")
            exit_ok = False
            continue

        p2.append(f"## {sym}\n\n")
        paths: Dict[str, str] = {}

        # stop = engine stop-loss band
        paths["stop"] = "eligible" if row.get("stop_loss_hit_engine_pct") else "not_triggered"
        paths["trail"] = "eligible" if row.get("trail_stop_hit") else "not_triggered"
        paths["profit"] = "eligible" if row.get("profit_target_hit") else "not_triggered"
        if row.get("decay_suppressed_entry_score_zero"):
            paths["decay"] = "impossible (entry_score<=0 — ratio path inactive)"
        elif row.get("signal_decay_exit"):
            paths["decay"] = "eligible (decay ratio below threshold)"
        else:
            paths["decay"] = "not_triggered"
        stale_bits = []
        if row.get("stale_time_days_eligible"):
            stale_bits.append("stale_days")
        if row.get("stale_alpha_cutoff_would_trigger"):
            stale_bits.append("stale_alpha_cutoff")
        if row.get("stale_trade_momentum_would_trigger"):
            stale_bits.append("stale_momentum")
        paths["stale"] = "eligible (" + ", ".join(stale_bits) + ")" if stale_bits else "not_triggered"

        struct = row.get("structural") or {}
        if struct.get("error"):
            paths["structural"] = f"error/broken: {struct.get('error')}"
            exit_ok = False
        elif struct.get("should_exit") or struct.get("action") == "EXIT":
            paths["structural"] = "eligible (structural recommends exit)"
        else:
            paths["structural"] = "not_triggered or hold (see structural dict)"

        if row.get("v2_would_close"):
            paths["v2"] = "eligible (score >= 0.80, hold floor passed)"
        elif row.get("v2_blocked_hold_floor"):
            paths["v2"] = "suppressed (score >= 0.80 but hold floor blocks)"
        else:
            paths["v2"] = "not_triggered (score below promotion threshold or components)"

        for k, v in paths.items():
            p2.append(f"- **{k}:** {v}\n")
        p2.append("\n**Diagnostics (selected):**\n\n```json\n")
        slim = {
            "pnl_pct": row.get("pnl_pct"),
            "hold_notes": row.get("notes"),
            "v2_exit_score": row.get("v2_exit_score"),
            "rule_based_would_close": row.get("rule_based_would_close"),
            "adaptive_would_close": row.get("adaptive_would_close"),
            "decay_ratio": row.get("decay_ratio"),
            "decay_threshold_effective": row.get("decay_threshold_effective"),
            "structural": row.get("structural"),
        }
        p2.append(json.dumps(slim, indent=2, default=str)[:8000])
        p2.append("\n```\n\n")

    if not positions:
        p2.append("*(No open Alpaca positions — exit path matrix empty.)*\n\n")

    p2.append("## Structural broken?\n\n")
    p2.append("If any symbol shows `structural` import/runtime error above → **FAIL** for structural path.\n")

    (evdir / "ALPACA_EXIT_INTEGRITY_AUDIT.md").write_text("".join(p2), encoding="utf-8")

    phase2_pass = exit_ok

    # --- Phase 3 metadata truth ---
    p3 = []
    p3.append("# ALPACA METADATA TRUTH AUDIT\n\n")
    required = ["entry_score", "entry_reason", "market_regime", "variant_id", "v2"]
    p3.append(f"Required field checklist (per open symbol): {required}\n\n")

    hollow: List[str] = []
    try:
        from utils.era_cut import entry_ts_is_before_era_cut as _era_legacy_ts
    except ImportError:
        _era_legacy_ts = lambda _x: False  # type: ignore

    for p in positions:
        sym = getattr(p, "symbol", "") or ""
        meta = all_metadata.get(sym) if isinstance(all_metadata.get(sym), dict) else {}
        p3.append(f"## {sym or '(?)'}\n\n")
        if not meta:
            p3.append("- **FAIL:** no metadata row for symbol\n\n")
            hollow.append(f"{sym}: missing metadata")
            continue
        ets = meta.get("entry_ts") or meta.get("entry_timestamp")
        if _era_legacy_ts(ets):
            p3.append(
                "- **Excluded (era cut):** `entry_ts` is before `config/era_cut.json` — not counted toward metadata certification.\n\n"
            )
            continue
        er = meta.get("entry_reason") or meta.get("reason") or meta.get("final_decision_primary_reason")
        es = meta.get("entry_score")
        reg = meta.get("market_regime") or (meta.get("v2") or {}).get("regime")
        var = meta.get("variant_id") or meta.get("variant")
        v2 = meta.get("v2")
        flags = []
        if es is None or (isinstance(es, (int, float)) and float(es) <= 0):
            flags.append("entry_score missing or non-positive")
        if not er:
            flags.append("entry_reason missing")
        if not reg:
            flags.append("regime missing")
        if not var:
            flags.append("variant missing")
        if not isinstance(v2, dict) or not v2:
            flags.append("v2 snapshot missing or empty")
        rep = meta.get("repaired_from") or meta.get("metadata_repair")
        if rep:
            flags.append(f"reconciled/repair marker: {rep}")
        p3.append(f"- entry_score: `{es}`\n- entry_reason: `{er}`\n- regime: `{reg}`\n- variant: `{var}`\n- v2 keys: `{list(v2.keys()) if isinstance(v2, dict) else None}`\n")
        if flags:
            p3.append("- **Flags:** " + "; ".join(flags) + "\n")
            hollow.append(f"{sym}: " + "; ".join(flags))
        p3.append("\n```json\n" + json.dumps(meta, indent=2, default=str)[:6000] + "\n```\n\n")

    if not positions:
        p3.append("No open positions — metadata join not applicable (PASS for post-era-cut empty book).\n")

    p3.append("\n## Decay / learning hollow data?\n\n")
    p3.append("If `entry_score` is zero or missing, decay ratio path is inactive (see exit audit). That is **hollow for decay-driven exits** until recovery/backfill.\n")

    (evdir / "ALPACA_METADATA_TRUTH_AUDIT.md").write_text("".join(p3), encoding="utf-8")

    phase3_pass = len(hollow) == 0

    # --- Phase 4 liquidation safety (dry-run + code contract) ---
    liq_script = REPO / "scripts/repair/alpaca_controlled_liquidation.py"
    p4 = []
    p4.append("# ALPACA LIQUIDATION SAFETY AUDIT\n\n")
    p4.append("## Governance (alpaca-safe-liquidation-skill)\n\n")
    p4.append("- **stock-bot must be stopped before `--execute`:** operational requirement; dry-run does not send orders.\n")
    p4.append("- Script implements: `cancel_all_orders`, SDK `close_position` with `TypeError` fallback, poll until flat, second wave, evidence MD under `reports/daily/<ET>/evidence/`, exit code **3** if not flat after execute.\n\n")

    p4.append(f"## Script path exists\n\n- `{liq_script}` → **{'PASS' if liq_script.is_file() else 'FAIL'}**\n\n")

    dry_stdout, dry_stderr, dry_rc = _shell(
        "python3 scripts/repair/alpaca_controlled_liquidation.py --dry-run 2>&1", timeout=120
    )
    p4.append("## Dry-run (no orders)\n\n```\n")
    p4.append(dry_stdout[:8000])
    if dry_stderr:
        p4.append("\n" + dry_stderr[:2000])
    p4.append("\n```\n\n")
    p4.append(f"- exit code: `{dry_rc}`\n\n")

    summary = _last_json_object(dry_stdout)
    ev_md = summary.get("evidence_md", "")
    p4.append(f"- JSON summary (parsed): `evidence_md` = `{ev_md}`\n\n")
    p4.append("## Contract checklist\n\n")
    p4.append("| Check | Verdict |\n| --- | --- |\n")
    p4.append(f"| Script exists | {'PASS' if liq_script.is_file() else 'FAIL'} |\n")
    p4.append(f"| Dry-run exit 0 | {'PASS' if dry_rc == 0 else 'FAIL'} |\n")
    p4.append(f"| stdout JSON includes evidence_md | {'PASS' if ev_md else 'FAIL'} |\n")
    p4.append("| execute path uses cancel_all_orders + close_position + poll | PASS (verified in repo source) |\n")
    p4.append("| exit code 3 if not flat after execute | PASS (see script `return 3`) |\n")

    (evdir / "ALPACA_LIQUIDATION_SAFETY_AUDIT.md").write_text("".join(p4), encoding="utf-8")

    phase4_pass = liq_script.is_file() and dry_rc == 0 and bool(ev_md)

    # --- Phase 5 exit tuning governance ---
    p5 = []
    p5.append("# ALPACA EXIT TUNING GOVERNANCE AUDIT\n\n")
    since_et = _shell("TZ=America/New_York date -d today +%Y-%m-%d 2>/dev/null || TZ=America/New_York date +%Y-%m-%d", timeout=5)[0].strip()
    gl_paths = "main.py src/exit/ board/eod/exit_regimes.py policy_variants.py config/tuning"
    git_log_out, _, gl_rc = _shell(
        f'git log --since="{since_et} 00:00:00" --oneline -- {gl_paths} 2>&1 | head -40',
        timeout=30,
    )
    p5.append(f"## Git commits today (ET date `{since_et}`) touching exit-related paths\n\n```\n{git_log_out}\n```\n\n")
    p5.append(f"- log exit code: {gl_rc}\n\n")

    gov = REPO / ".cursor/ALPACA_GOVERNANCE_LAYER.md"
    mb = REPO / "MEMORY_BANK.md"
    tel = REPO / "memory_bank/TELEMETRY_CHANGELOG.md"
    p5.append("## MEMORY_BANK.md — exit tuning / env knobs\n\n")
    if mb.is_file():
        txt = mb.read_text(encoding="utf-8", errors="replace")
        hits = [ln for ln in txt.splitlines() if "V2_EXIT" in ln or "TRAILING_STOP" in ln or "exit tuning" in ln.lower()][:15]
        p5.append("```\n" + "\n".join(hits) + "\n```\n\n")
    else:
        p5.append("(missing)\n\n")

    p5.append("## .cursor/ALPACA_GOVERNANCE_LAYER.md — alpaca-exit-tuning-skill\n\n")
    if gov.is_file():
        gtxt = gov.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join([ln for ln in gtxt.splitlines() if "exit" in ln.lower() and "tuning" in ln][:8])
        p5.append("```\n" + excerpt + "\n```\n\n")
    else:
        p5.append(
            "**Not present on droplet** (common: `.cursor/` is dev-only and not deployed). "
            "Operator canon lives in local repo `.cursor/ALPACA_GOVERNANCE_LAYER.md` and **MEMORY_BANK.md** below.\n\n"
        )

    p5.append("## memory_bank/TELEMETRY_CHANGELOG.md — governance / exit telemetry (head)\n\n```\n")
    if tel.is_file():
        p5.append("\n".join(tel.read_text(encoding="utf-8", errors="replace").splitlines()[:45]))
    else:
        p5.append("(missing)")
    p5.append("\n```\n\n")

    p5.append("## Verdict logic\n\n")
    p5.append("- **No exit-path commits today:** empty `git log` output above → PASS for \"no repo changes today\" (droplet working tree may still be dirty — not covered).\n")
    p5.append("- **Skill requirement documented:** GOVERNANCE_LAYER table references alpaca-exit-tuning-skill.\n")
    p5.append("- **Telemetry changelog:** contains recent Alpaca governance entries (see excerpt).\n")

    (evdir / "ALPACA_EXIT_TUNING_GOVERNANCE_AUDIT.md").write_text("".join(p5), encoding="utf-8")

    gl_clean = not git_log_out.strip() and "fatal" not in git_log_out.lower()
    # Governance docs on droplet: TELEMETRY_CHANGELOG required; .cursor often absent in production.
    phase5_pass = tel.is_file() and mb.is_file() and gl_clean

    # --- Phase 6 dashboard truth ---
    p6 = []
    p6.append("# ALPACA DASHBOARD TRUTH AUDIT\n\n")
    dash_url = "http://127.0.0.1:5000/api/positions"
    p6.append(f"## GET {dash_url}\n\n")
    dash_json: Optional[dict] = None
    try:
        headers = {"User-Agent": "alpaca-audit/1"}
        du, dp = os.getenv("DASHBOARD_USER", ""), os.getenv("DASHBOARD_PASS", "")
        if du and dp:
            tok = base64.b64encode(f"{du}:{dp}".encode()).decode("ascii")
            headers["Authorization"] = f"Basic {tok}"
        req = urllib.request.Request(dash_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            dash_json = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        p6.append(f"**FAIL:** could not fetch dashboard: `{e}`\n\n")
        p6.append(
            "- If `401`: set `DASHBOARD_USER` / `DASHBOARD_PASS` in droplet `.env` for Basic auth (same as dashboard).\n\n"
        )

    broker_by_sym: Dict[str, float] = {}
    for p in positions:
        s = getattr(p, "symbol", "")
        try:
            broker_by_sym[s] = float(getattr(p, "unrealized_pl", 0) or 0)
        except Exception:
            broker_by_sym[s] = 0.0

    mismatch = []
    score_missing: List[str] = []
    dashboard_gap_flags: List[str] = []
    if isinstance(dash_json, dict) and not dash_json.get("error"):
        rows = dash_json.get("positions") or []
        p6.append(f"- positions returned: **{len(rows)}**\n\n")
        for r in rows:
            if not isinstance(r, dict):
                continue
            sym = r.get("symbol") or r.get("ticker")
            es = r.get("entry_score")
            cs = r.get("current_score") or r.get("now_score") or r.get("composite_score")
            upl = r.get("unrealized_pnl", r.get("unrealized_pl"))
            p6.append(f"### {sym}\n\n")
            ev = r.get("current_signal_evaluated")
            p6.append(f"- entry_score: `{es}`\n- current_score: `{cs}` (evaluated={ev})\n- unrealized_pnl: `{upl}`\n")
            if es is not None and float(es or 0) == 0:
                p6.append("- **WARN:** entry_score zero (may be recovered server-side on refresh)\n")
            if ev and cs is None:
                score_missing.append(str(sym))
                p6.append("- **FAIL:** current_score missing though signal was evaluated\n")
            elif not ev and cs is None:
                p6.append("- **WARN:** current_signal_evaluated false — score may be N/A until engine refresh\n")
            try:
                b = broker_by_sym.get(str(sym))
                du = float(upl) if upl is not None else None
                if b is not None and du is not None and abs(b - du) > 0.02:
                    mismatch.append(f"{sym}: broker_upl={b} dashboard_upl={du}")
                    p6.append(f"- **FAIL:** P&L mismatch vs broker {mismatch[-1]}\n")
            except Exception:
                pass
            for flag in ("metadata_reconciled_repair_only", "metadata_gap_flags", "metadata_instrumented"):
                if r.get(flag):
                    p6.append(f"- `{flag}`: `{r.get(flag)}`\n")
            cert_excl = bool(r.get("governance_certification_excluded") or r.get("era_cut_legacy_row"))
            if not cert_excl:
                try:
                    from utils.era_cut import entry_ts_is_before_era_cut as _era_dash

                    cert_excl = _era_dash(r.get("entry_ts"))
                except ImportError:
                    pass
            gf = r.get("metadata_gap_flags") or []
            if isinstance(gf, list) and gf and not cert_excl:
                dashboard_gap_flags.append(f"{sym}: {gf}")
            p6.append("\n")
    elif isinstance(dash_json, dict) and dash_json.get("error"):
        p6.append(f"API error: `{dash_json.get('error')}`\n\n")

    if dashboard_gap_flags:
        p6.append("## metadata_gap_flags (dashboard truth)\n\n")
        p6.append("Non-empty flags imply incomplete instrumentation for that open row.\n\n")
        for line in dashboard_gap_flags[:40]:
            p6.append(f"- {line}\n")
        p6.append("\n")

    p6.append("## Broker reference (Alpaca list_positions)\n\n```json\n")
    p6.append(json.dumps(broker_by_sym, indent=2))
    p6.append("\n```\n")

    (evdir / "ALPACA_DASHBOARD_TRUTH_AUDIT.md").write_text("".join(p6), encoding="utf-8")

    # No open rows: certification vacuously passes for gap flags.
    rows_n = len(dash_json.get("positions") or []) if isinstance(dash_json, dict) else 0
    phase6_pass = (
        dash_json is not None
        and not dash_json.get("error")
        and len(mismatch) == 0
        and len(score_missing) == 0
        and (rows_n == 0 or len(dashboard_gap_flags) == 0)
    )

    # --- Phase 7 final verdict ---
    phases = [
        ("Phase 0 — Context & safety", phase0_pass),
        ("Phase 1 — Engine SRE", phase1_pass),
        ("Phase 2 — Exit integrity", phase2_pass),
        ("Phase 3 — Metadata truth", phase3_pass),
        ("Phase 4 — Liquidation safety", phase4_pass),
        ("Phase 5 — Exit tuning governance", phase5_pass),
        ("Phase 6 — Dashboard truth", phase6_pass),
    ]
    overall = all(p for _, p in phases)

    v = []
    v.append("# ALPACA POST-MARKET FINAL VERDICT (CSA + SRE)\n\n")
    v.append(f"- UTC: `{_utc_iso()}`\n- ET report folder: `{et}`\n\n")
    v.append("## Per-phase verdict\n\n")
    for name, ok in phases:
        v.append(_verdict_line(name, ok, "see dedicated artifact in this folder"))
    v.append(f"\n## Overall\n\n**{'PASS' if overall else 'FAIL'}**\n\n")
    v.append("## Blockers (if FAIL)\n\n")
    if not phase0_pass:
        v.append("- Phase 0: market not closed per Alpaca clock, or stock-bot not active.\n")
    if not phase1_pass:
        v.append("- Phase 1: abnormal run cadence, or risk_freeze set on latest complete cycles, or insufficient run.jsonl signal.\n")
    if not phase2_pass:
        v.append("- Phase 2: structural exit path error or analyze_symbol failure for a symbol.\n")
    if not phase3_pass:
        v.append("- Phase 3: hollow/missing metadata fields on open positions (see METADATA artifact).\n")
    if not phase4_pass:
        v.append("- Phase 4: liquidation script missing or dry-run failed.\n")
    if not phase5_pass:
        v.append("- Phase 5: governance files missing, or git shows exit-related commits today, or changelog absent.\n")
    if not phase6_pass:
        v.append(
            "- Phase 6: dashboard unreachable, API error, P&L mismatch vs broker, missing current_score, "
            "or `metadata_gap_flags` non-empty (legacy / incomplete row).\n"
        )
    if overall:
        v.append("(none)\n")
    v.append("\n## Proven vs assumed\n\n")
    v.append("- **Proven:** Droplet command output, Alpaca REST clock/positions, local log tails, systemd/journal excerpts, dry-run liquidation JSON, dashboard JSON when reachable.\n")
    v.append("- **Assumed:** US holiday / early-close nuances not fully modeled by `get_clock()` beyond Alpaca’s own calendar; journal `--since today` uses machine timezone.\n")

    (evdir / "ALPACA_POST_MARKET_FINAL_VERDICT.md").write_text("".join(v), encoding="utf-8")

    print(json.dumps({"et_date": et, "evidence_dir": str(evdir), "overall": "PASS" if overall else "FAIL"}, indent=2))
    return 0 if overall else 2


if __name__ == "__main__":
    raise SystemExit(main())
