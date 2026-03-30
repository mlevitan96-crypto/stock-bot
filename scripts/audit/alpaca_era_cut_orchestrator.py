#!/usr/bin/env python3
"""
Alpaca ERA CUT orchestrator — run on droplet from repo root after code deploy.

Phases 0–9 per governance mission; writes evidence under reports/daily/<ET>/evidence/.
Stops on first hard failure after writing ALPACA_ERA_CUT_BLOCKER.md.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

_VENV_PY = REPO / "venv" / "bin" / "python"
PY_EXE = str(_VENV_PY) if _VENV_PY.is_file() else "python3"

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


def _sh(cmd: str, timeout: int = 300) -> Tuple[str, str, int]:
    try:
        r = subprocess.run(
            ["bash", "-lc", cmd],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (r.stdout or ""), (r.stderr or ""), r.returncode
    except Exception as e:
        return "", str(e), 1


def _write_evidence(name: str, body: str) -> Path:
    et = _et_date()
    ev = REPO / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    p = ev / name
    p.write_text(body, encoding="utf-8")
    return p


def _blocker(msg: str, detail: str = "") -> None:
    b = f"# ALPACA ERA CUT — BLOCKER\n\n- UTC: `{_utc_iso()}`\n\n## Error\n\n{msg}\n\n```\n{detail[:12000]}\n```\n"
    _write_evidence("ALPACA_ERA_CUT_BLOCKER.md", b)
    print("BLOCKER:", msg, file=sys.stderr)
    sys.exit(1)


def _git(args: List[str]) -> Tuple[str, int]:
    o, e, rc = _sh("git " + " ".join(args), timeout=120)
    return o + (e or ""), rc


def main() -> None:
    et = _et_date()
    ev = REPO / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    legacy_state = REPO / "state" / "legacy" / et
    legacy_reports = REPO / "reports" / "legacy" / et

    # ---------- PHASE 0 ----------
    p0: List[str] = []
    p0.append("# ALPACA ERA CUT — CONTEXT SNAPSHOT\n\n")
    p0.append(f"- UTC: `{_utc_iso()}`\n- ET date: `{et}`\n\n")

    try:
        import alpaca_trade_api as tradeapi  # type: ignore

        from main import Config

        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
        clk = api.get_clock()
        mo = bool(getattr(clk, "is_open", True))
        p0.append(f"## Alpaca clock\n\n- market_open: `{mo}` (closed expected)\n\n")
        if mo:
            _write_evidence("ALPACA_ERA_CUT_CONTEXT.md", "".join(p0))
            _blocker("Market not closed per Alpaca clock", str(clk))
        pos = api.list_positions() or []
        syms = [getattr(p, "symbol", "") for p in pos]
        p0.append(f"## Broker positions\n\n- count: **{len(pos)}**\n- symbols: `{', '.join(s for s in syms if s)}`\n\n")
    except Exception as e:
        _blocker("Phase 0 broker/clock failed", str(e))

    gh, g0 = _sh("git rev-parse HEAD", 30)
    p0.append(f"## Git HEAD\n\n`{gh.strip()}`\n\n")
    du, _, _ = _sh("date -u '+%Y-%m-%dT%H:%M:%SZ'", 10)
    p0.append(f"## date -u\n\n`{du.strip()}`\n\n")
    st, _, _ = _sh("systemctl status stock-bot --no-pager 2>&1 | head -40", 30)
    p0.append("## systemctl status stock-bot (excerpt)\n\n```\n")
    p0.append(st[:8000])
    p0.append("\n```\n")
    _write_evidence("ALPACA_ERA_CUT_CONTEXT.md", "".join(p0))

    # ---------- PHASE 1 ----------
    era_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    cfg = {
        "alpaca": {
            "era_cut_ts": era_ts,
            "reason": "Governance reset: metadata integrity + exit correctness + learning truth",
            "legacy_policy": {
                "learning": "excluded",
                "decay": "excluded",
                "exit_tuning": "excluded",
                "dashboard_certification": "excluded",
                "governance_audits": "excluded",
            },
        }
    }
    cfg_path = REPO / "config" / "era_cut.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    p1 = []
    p1.append("# ALPACA ERA CUT — DECLARATION\n\n")
    p1.append(f"- **era_cut_ts:** `{cfg['alpaca']['era_cut_ts']}`\n")
    p1.append(f"- Written to: `{cfg_path}`\n\n```json\n")
    p1.append(json.dumps(cfg, indent=2))
    p1.append("\n```\n")
    _write_evidence("ALPACA_ERA_CUT_DECLARATION.md", "".join(p1))

    out, rc = _git(["add", "config/era_cut.json"])
    if rc != 0:
        _blocker("git add config/era_cut.json failed", out)
    out, rc = _git(["commit", "-m", "alpaca: declare era cut config/era_cut.json"])
    if rc != 0 and "nothing to commit" not in out.lower():
        _blocker("git commit era_cut.json failed", out)

    # ---------- PHASE 2 ----------
    legacy_state.mkdir(parents=True, exist_ok=True)
    pm = REPO / "state" / "position_metadata.json"
    if pm.exists():
        pre = legacy_state / "position_metadata.pre_liquidation.json"
        pre.write_bytes(pm.read_bytes())

    o, e, rc = _sh("sudo systemctl stop stock-bot", 90)
    if rc != 0:
        _blocker("systemctl stop stock-bot failed", o + e)

    o2, _, _ = _sh("systemctl is-active stock-bot 2>&1", 15)
    if o2.strip() != "inactive":
        _blocker("stock-bot not inactive after stop", o2)

    liq = _sh(
        f"{PY_EXE} scripts/repair/alpaca_controlled_liquidation.py --execute 2>&1",
        timeout=600,
    )
    liq_out = liq[0] + liq[1]
    summary: Dict[str, Any] = {}
    try:
        for line in reversed(liq_out.strip().splitlines()):
            line = line.strip()
            if line.startswith("{") and "evidence_md" in line:
                summary = json.loads(line)
                break
        if not summary:
            # multi-line JSON
            end = liq_out.rstrip().rfind("}")
            if end >= 0:
                depth = 0
                for i in range(end, -1, -1):
                    c = liq_out[i]
                    if c == "}":
                        depth += 1
                    elif c == "{":
                        depth -= 1
                        if depth == 0:
                            summary = json.loads(liq_out[i : end + 1])
                            break
    except Exception:
        summary = {}

    flat = summary.get("flat") is True
    pos_after = summary.get("positions_after", -1)
    ev_md = summary.get("evidence_md", "")

    p2 = []
    p2.append("# ALPACA ERA CUT — LIQUIDATION EVIDENCE\n\n")
    p2.append(f"- Engine stopped: **yes** (`systemctl stop stock-bot`)\n")
    p2.append(f"- `systemctl is-active` after stop: `{o2.strip()}`\n\n")
    p2.append("## Controlled liquidation stdout (tail)\n\n```\n")
    p2.append(liq_out[-20000:])
    p2.append("\n```\n\n")
    p2.append(f"## Parsed JSON summary\n\n```json\n{json.dumps(summary, indent=2)}\n```\n\n")
    p2.append(f"- **flat:** `{flat}` positions_after=`{pos_after}`\n")
    p2.append(f"- **Liquidation evidence_md:** `{ev_md}`\n")
    _write_evidence("ALPACA_ERA_CUT_LIQUIDATION_EVIDENCE.md", "".join(p2))

    if not flat or pos_after != 0:
        _blocker("Liquidation did not reach flat broker state", json.dumps(summary, indent=2))

    # ---------- PHASE 3 ----------
    legacy_reports.mkdir(parents=True, exist_ok=True)
    ops: List[str] = []
    if pm.exists():
        dst = legacy_state / "position_metadata.post_liquidation.json"
        dst.write_bytes(pm.read_bytes())
        ops.append(f"copied {pm} -> {dst}")
    ssc = REPO / "state" / "signal_strength_cache.json"
    if ssc.exists():
        dst2 = legacy_state / "signal_strength_cache.archive.json"
        dst2.write_bytes(ssc.read_bytes())
        ops.append(f"copied {ssc} -> {dst2}")

    src_ev = REPO / "reports" / "daily" / et / "evidence"
    if src_ev.exists():
        o, _, rcp = _sh(f"cp -r '{src_ev}' '{legacy_reports}/evidence_snapshot_pre_full_archive' 2>&1 || true", 60)
        ops.append(f"copied evidence dir snapshot: {rcp} {o[:200]}")

    p3 = []
    p3.append("# ALPACA ERA CUT — ARCHIVE LOG\n\n")
    p3.append("## Operations\n\n")
    for op in ops:
        p3.append(f"- {op}\n")
    p3.append(f"\n- legacy state dir: `{legacy_state}`\n")
    p3.append(f"- legacy reports dir: `{legacy_reports}`\n")
    _write_evidence("ALPACA_ERA_CUT_ARCHIVE_LOG.md", "".join(p3))

    # ---------- PHASE 4 (verify code present) ----------
    guard = REPO / "utils" / "era_cut.py"
    p4 = []
    p4.append("# ALPACA ERA CUT — CODE GUARD\n\n")
    p4.append("Minimal enforcement (pre-deployed in repo before this run):\n\n")
    p4.append(f"- `{guard}` — load `config/era_cut.json`, parse `era_cut_ts`, exclude legacy from learning + gap flags.\n")
    p4.append("- `dashboard.py` — pre-era rows: empty `metadata_gap_flags`, `governance_certification_excluded`.\n")
    p4.append("- `main.py` — `record_trade_for_learning` skips pre-era feature vectors.\n")
    p4.append("- `comprehensive_learning_orchestrator_v2.py` — skip attribution/exit rows before era cut.\n")
    p4.append("- `scripts/audit/alpaca_post_market_full_governance_audit.py` — era exclusions for Phase 3/6.\n")
    p4.append(f"\nGuard file present: **{guard.is_file()}**\n")
    _write_evidence("ALPACA_ERA_CUT_CODE_GUARD.md", "".join(p4))

    # ---------- PHASE 5 ----------
    o, e, rc = _sh("sudo systemctl start stock-bot", 90)
    if rc != 0:
        _blocker("systemctl start stock-bot failed", o + e)
    o2, _, _ = _sh("sleep 8 && systemctl is-active stock-bot", 30)
    if "active" not in o2.lower():
        _blocker("stock-bot not active after start", o2)

    runj = REPO / "logs" / "run.jsonl"
    o, _, _ = _sh("sleep 15", 30)
    tail_after = runj.read_text(encoding="utf-8", errors="replace")[-8000:] if runj.exists() else ""

    p5 = []
    p5.append("# ALPACA POST-CUT ENGINE SMOKE\n\n")
    p5.append(f"- systemctl is-active: `{o2.strip()}`\n\n")
    p5.append("## run.jsonl tail after restart (excerpt)\n\n```\n")
    p5.append(tail_after[-4000:])
    p5.append("\n```\n\n")
    p5.append("- **Note:** Compare length/content vs pre-restart if needed; engine should append new cycles.\n")
    _write_evidence("ALPACA_POST_CUT_ENGINE_SMOKE.md", "".join(p5))

    # ---------- PHASE 6 ----------
    o6, _, rc6 = _sh(f"{PY_EXE} scripts/audit/alpaca_post_market_full_governance_audit.py 2>&1", timeout=400)
    fv = ev / "ALPACA_POST_MARKET_FINAL_VERDICT.md"
    fv_txt = fv.read_text(encoding="utf-8") if fv.exists() else "(missing)"
    p6 = []
    p6.append("# ALPACA POST-CUT GOVERNANCE AUDIT SUMMARY\n\n")
    p6.append(f"- audit script exit code: `{rc6}`\n\n")
    p6.append("## ALPACA_POST_MARKET_FINAL_VERDICT.md (copy)\n\n")
    p6.append(fv_txt[:12000])
    p6.append("\n\n## Script stdout (tail)\n\n```\n")
    p6.append(o6[-6000:])
    p6.append("\n```\n")
    _write_evidence("ALPACA_POST_CUT_GOVERNANCE_AUDIT_SUMMARY.md", "".join(p6))

    # ---------- PHASE 7 ----------
    o7, _, rc7 = _sh(f"{PY_EXE} scripts/audit/alpaca_post_cut_signal_firing_test.py 2>&1", timeout=180)
    if rc7 != 0:
        _blocker("Signal firing test failed", o7[-4000:])

    # ---------- PHASE 8 ----------
    mb = REPO / "MEMORY_BANK.md"
    tlog = REPO / "memory_bank" / "TELEMETRY_CHANGELOG.md"
    block = f"""

---

## Alpaca era cut ({et})

- **era_cut_ts (canonical):** `{cfg['alpaca']['era_cut_ts']}`
- **Config:** `config/era_cut.json`
- **Legacy policy:** pre-era attribution/positions excluded from adaptive learning, dashboard certification gap flags, and governance audit certification (see `utils/era_cut.py`).
- **Evidence:** `reports/daily/{et}/evidence/ALPACA_ERA_CUT_DECLARATION.md` and related ERA CUT artifacts.

"""
    if mb.is_file():
        mb.write_text(mb.read_text(encoding="utf-8", errors="replace") + block, encoding="utf-8")
    if tlog.is_file():
        entry = f"\n\n---\n\n## {et} — Alpaca era cut\n\n- Era cut timestamp: `{cfg['alpaca']['era_cut_ts']}`; post-cut governance audits exclude pre-era rows per `config/era_cut.json` + `utils/era_cut.py`.\n"
        tlog.write_text(tlog.read_text(encoding="utf-8", errors="replace") + entry, encoding="utf-8")

    p8 = []
    p8.append("# ALPACA ERA CUT — DOC UPDATES\n\n")
    p8.append("Appended sections to MEMORY_BANK.md and memory_bank/TELEMETRY_CHANGELOG.md (see tail of those files).\n\n")
    p8.append("```\n" + block[:2500] + "\n```\n")
    _write_evidence("ALPACA_ERA_CUT_DOC_UPDATES.md", "".join(p8))

    out, rc = _git(["add", "MEMORY_BANK.md", "memory_bank/TELEMETRY_CHANGELOG.md"])
    out2, rc2 = _git(["commit", "-m", "docs: record alpaca era cut and governance enforcement"])
    if rc2 != 0 and "nothing to commit" not in out2.lower():
        _blocker("git commit docs failed", out2)

    # ---------- PHASE 9 ----------
    sig_ok = rc7 == 0
    gov_ok = rc6 == 0
    p9 = []
    p9.append("# ALPACA ERA CUT — FINAL VERDICT\n\n")
    p9.append(f"- **era_cut_ts:** `{cfg['alpaca']['era_cut_ts']}`\n")
    p9.append("- **Liquidation flat:** PASS (verified `flat=true` in controlled liquidation JSON)\n")
    p9.append(f"- **Post-cut governance audit script:** {'PASS' if gov_ok else 'FAIL'} (exit {rc6})\n")
    p9.append(f"- **Signal firing test:** {'PASS' if sig_ok else 'FAIL'} (exit {rc7})\n")
    p9.append("\n## Artifacts\n\n")
    for n in [
        "ALPACA_ERA_CUT_CONTEXT.md",
        "ALPACA_ERA_CUT_DECLARATION.md",
        "ALPACA_ERA_CUT_LIQUIDATION_EVIDENCE.md",
        "ALPACA_ERA_CUT_ARCHIVE_LOG.md",
        "ALPACA_ERA_CUT_CODE_GUARD.md",
        "ALPACA_POST_CUT_ENGINE_SMOKE.md",
        "ALPACA_POST_CUT_GOVERNANCE_AUDIT_SUMMARY.md",
        "ALPACA_POST_CUT_SIGNAL_FIRING_TEST.md",
        "ALPACA_ERA_CUT_DOC_UPDATES.md",
    ]:
        p9.append(f"- `{n}`\n")
    _write_evidence("ALPACA_ERA_CUT_FINAL_VERDICT.md", "".join(p9))

    print(json.dumps({"ok": True, "era_cut_ts": cfg["alpaca"]["era_cut_ts"], "et": et}, indent=2))


if __name__ == "__main__":
    main()
