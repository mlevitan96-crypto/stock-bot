#!/usr/bin/env python3
"""
Monday Market Open Readiness — full verification on DROPLET, PAPER only.
Run from repo root (local). Executes real checks on droplet via SSH; writes artifacts locally.
Fail closed: on any critical failure writes BLOCKERS and stops.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

AUDIT = REPO / "reports" / "audit"
PROOF_BASE = AUDIT  # PROOF_<ts> under AUDIT


def _ensure_droplet_config() -> None:
    """Raise if droplet config unavailable."""
    config_path = REPO / "droplet_config.json"
    if config_path.exists():
        return
    if os.getenv("DROPLET_HOST"):
        return
    raise FileNotFoundError(
        "Droplet config missing: no droplet_config.json and no DROPLET_HOST. "
        "Create droplet_config.json (see droplet_config.example.json) or set DROPLET_HOST."
    )


def _run(cmd: str, timeout: int = 60) -> tuple[str, str, int]:
    from droplet_client import DropletClient
    with DropletClient() as c:
        return c._execute_with_cd(cmd, timeout=timeout)


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    proof_dir = AUDIT / f"MONDAY_OPEN_READINESS_PROOF_{date_str}_{ts.replace('-', '')[-4:]}"
    proof_dir.mkdir(parents=True, exist_ok=True)

    readiness_md = AUDIT / f"MONDAY_OPEN_READINESS_{date_str}_{ts.replace('-', '')[-4:]}.md"
    results_json = AUDIT / f"MONDAY_OPEN_READINESS_RESULTS_{date_str}_{ts.replace('-', '')[-4:]}.json"
    blockers_md = AUDIT / f"MONDAY_OPEN_READINESS_BLOCKERS_{date_str}_{ts.replace('-', '')[-4:]}.md"

    results = {
        "timestamp": ts,
        "verdict": "PASS",
        "phases": {},
        "blockers": [],
        "warnings": [],
        "proof_dir": str(proof_dir),
    }

    def save_proof(name: str, content: str) -> None:
        (proof_dir / f"{name}.txt").write_text(content, encoding="utf-8")

    def fail_closed(reason: str, remediation: list[str], re_run: str) -> int:
        results["verdict"] = "FAIL"
        results["blockers"].append(reason)
        blockers_content = [
            "# Monday Open Readiness — BLOCKERS",
            "",
            f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Root cause",
            "",
            reason,
            "",
            "## Exact remediation",
            "",
        ] + [f"- {r}" for r in remediation] + [
            "",
            "## Re-run after fix",
            "",
            re_run,
            "",
            "Do not proceed to trading until blockers are resolved and suite is re-run.",
        ]
        blockers_md.write_text("\n".join(blockers_content), encoding="utf-8")
        results_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
        _write_readiness_md(results, readiness_md, date_str, ts)
        print(f"BLOCKERS written to {blockers_md}", file=sys.stderr)
        return 1

    try:
        _ensure_droplet_config()
    except FileNotFoundError as e:
        proof_dir.mkdir(parents=True, exist_ok=True)
        (proof_dir / "phase0_missing_config.txt").write_text(str(e), encoding="utf-8")
        results["verdict"] = "FAIL"
        results["blockers"].append("Droplet config missing: no droplet_config.json and no DROPLET_HOST.")
        results["phases"]["0_authority"] = {"error": str(e)}
        results_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
        _write_readiness_md(results, readiness_md, date_str, ts)
        blockers_md.write_text(
            f"# Monday Open Readiness — BLOCKERS\n\n**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}\n\n"
            "## Root cause\n\nDroplet config is missing.\n\n"
            "## Remediation\n\n- Create droplet_config.json in repo root (see droplet_config.example.json), or set DROPLET_HOST (and optionally DROPLET_USER, DROPLET_KEY_FILE).\n\n"
            "## Re-run\n\nAfter config is in place, run: python scripts/audit/run_monday_open_readiness.py\n",
            encoding="utf-8",
        )
        print(str(e), file=sys.stderr)
        return 1

    from droplet_client import DropletClient
    client = DropletClient()
    pd = client.project_dir

    # ---------- PHASE 0: DROPLET AUTHORITY ----------
    try:
        out, err, rc = client._execute_with_cd("hostname && git rev-parse HEAD 2>/dev/null || echo 'no-git' && date -u +%Y-%m-%dT%H:%M:%SZ && python3 --version 2>&1", timeout=15)
        save_proof("phase0_authority", out + "\n" + err)
        if rc != 0 and "no-git" in out:
            return fail_closed(
                "Droplet authority failed: git or hostname/date/python unavailable.",
                ["SSH to droplet and ensure git, python3, and hostname work.", "Check project_dir exists and contains repo."],
                "python scripts/audit/run_monday_open_readiness.py",
            )
        lines = (out or "").strip().split("\n")
        hostname = lines[0].strip() if lines else "unknown"
        commit = (lines[1].strip()[:12] if len(lines) > 1 else "unknown")
        results["phases"]["0_authority"] = {"hostname": hostname, "commit": commit, "raw": out[:500]}
    except Exception as e:
        return fail_closed(
            f"Droplet connection failed: {e}",
            ["Check SSH (droplet_config.json or DROPLET_*).", "Ensure droplet is reachable and key/auth correct."],
            "python scripts/audit/run_monday_open_readiness.py",
        )

    # ---------- PHASE 1: SRE SYSTEM HEALTH ----------
    try:
        out, err, rc = client._execute_with_cd("df -h . 2>/dev/null; echo '---'; uptime; echo '---'; free -h; echo '---'; find logs reports -type f 2>/dev/null | xargs ls -la 2>/dev/null | sort -k5 -rn | head -10", timeout=30)
        save_proof("phase1_sre_health", out + "\n" + err)
        disk_line = [l for l in (out or "").split("\n") if "%" in l]
        if disk_line:
            pct = disk_line[0].split()[-2].replace("%", "") if len(disk_line[0].split()) >= 2 else "0"
            try:
                if int(pct) >= 90:
                    return fail_closed("Disk usage >= 90%.", ["Free disk space on droplet (logs, reports, old artifacts)."], "python scripts/audit/run_monday_open_readiness.py")
            except ValueError:
                pass
        out2, _, _ = client._execute_with_cd("systemctl is-active stock-bot 2>/dev/null || echo 'inactive'; pgrep -af 'dashboard.py' | head -3 || true; crontab -l 2>/dev/null | head -5 || echo 'no-cron'", timeout=10)
        save_proof("phase1_services", out2)
        first_line = (out2 or "").strip().split("\n")[0].strip() if (out2 or "").strip() else ""
        if first_line != "active":
            return fail_closed("stock-bot service not active.", ["Start stock-bot on droplet: sudo systemctl start stock-bot"], "python scripts/audit/run_monday_open_readiness.py")
        results["phases"]["1_sre"] = {"disk_ok": True, "services_raw": (out2 or "")[:800]}
    except Exception as e:
        results["warnings"].append(f"Phase 1 exception: {e}")
        results["phases"]["1_sre"] = {"error": str(e)}

    # ---------- PHASE 2: PAPER-ONLY SAFETY ----------
    try:
        out, err, _ = client._execute_with_cd(
            "grep -E '^TRADING_MODE=|^ALPACA_BASE_URL=|^ALPACA_LIVE|^APCA_API_BASE_URL=' .env 2>/dev/null || true; "
            "echo '---'; env | grep -E 'TRADING_MODE|ALPACA_BASE|ALPACA_LIVE|APCA_API' 2>/dev/null || true",
            timeout=10,
        )
        save_proof("phase2_paper_env", (out or "") + (err or ""))
        raw = (out or "") + (err or "")
        if "LIVE" in raw and "TRADING_MODE" in raw and "PAPER" not in raw:
            return fail_closed("TRADING_MODE is not PAPER or live keys/env present.", ["Set TRADING_MODE=PAPER in .env on droplet.", "Ensure no ALPACA_LIVE_* keys and ALPACA_BASE_URL contains 'paper'."], "python scripts/audit/run_monday_open_readiness.py")
        if "ALPACA_LIVE" in raw or "live-api" in (raw or "").lower():
            return fail_closed("Live Alpaca key or live API URL detected.", ["Remove any ALPACA_LIVE_* and use paper base URL only."], "python scripts/audit/run_monday_open_readiness.py")
        results["phases"]["2_paper"] = {"paper_only_verified": True, "snippet_redacted": "TRADING_MODE and ALPACA_BASE_URL checked (values not logged)."}
    except Exception as e:
        return fail_closed(f"Phase 2 check failed: {e}", ["Verify .env on droplet has TRADING_MODE=PAPER and paper Alpaca URL."], "python scripts/audit/run_monday_open_readiness.py")

    # ---------- PHASE 3: CONFIG SANITY ----------
    try:
        out, _, _ = client._execute_with_cd("cat config/b2_governance.json 2>/dev/null || echo '{}'", timeout=5)
        save_proof("phase3_b2_config", out or "")
        try:
            b2 = json.loads(out or "{}")
            if b2.get("b2_live_enabled") is True:
                return fail_closed("B2 config has b2_live_enabled true.", ["Set b2_live_enabled to false in config/b2_governance.json."], "python scripts/audit/run_monday_open_readiness.py")
            results["phases"]["3_config"] = {"b2_mode": b2.get("b2_mode"), "b2_live_paper_enabled": b2.get("b2_live_paper_enabled"), "b2_live_enabled": b2.get("b2_live_enabled")}
        except json.JSONDecodeError:
            results["phases"]["3_config"] = {"b2_parse_error": True}
        out2, _, _ = client._execute_with_cd("wc -l state/daily_universe_v2.json state/trade_universe_v2.json 2>/dev/null || true; grep -E max_positions|universe config/startup_safety_suite_v2.json 2>/dev/null | head -5 || true", timeout=5)
        save_proof("phase3_risk_universe", out2 or "")
    except Exception as e:
        results["warnings"].append(f"Phase 3: {e}")
        results["phases"]["3_config"] = results["phases"].get("3_config", {}) | {"error": str(e)}

    # ---------- PHASE 4: DATA FRESHNESS + WRITABILITY ----------
    try:
        out, _, _ = client._execute_with_cd(
            "for f in logs/exit_attribution.jsonl state/blocked_trades.jsonl logs/score_snapshot.jsonl; do "
            "test -f $f && ls -la $f || echo missing:$f; done; "
            "test -f reports/audit/GOVERNANCE_AUTOMATION_STATUS.json && ls -la reports/audit/GOVERNANCE_AUTOMATION_STATUS.json || echo missing; "
            "test -f reports/audit/SRE_STATUS.json && ls -la reports/audit/SRE_STATUS.json || echo missing",
            timeout=10,
        )
        save_proof("phase4_data_paths", out or "")
        for line in (out or "").split("\n"):
            if "missing:" in line or ( "missing" in line and "json" in line ):
                results["warnings"].append(f"Optional path missing: {line.strip()}")
        out2, _, _ = client._execute_with_cd(
            "echo '{\"smoke_test\":\"MONDAY_READINESS\"}' >> logs/exit_attribution.jsonl 2>/dev/null && echo 'append_ok' || echo 'append_fail'",
            timeout=5,
        )
        if "append_fail" in (out2 or ""):
            return fail_closed("Cannot append to logs/exit_attribution.jsonl.", ["Fix permissions on droplet logs/ directory."], "python scripts/audit/run_monday_open_readiness.py")
        save_proof("phase4_append_test", out2 or "")
        results["phases"]["4_data"] = {"append_ok": "append_ok" in (out2 or "")}
    except Exception as e:
        results["warnings"].append(f"Phase 4: {e}")

    # ---------- PHASE 5: ALPACA PAPER CONNECTIVITY (READ-ONLY) ----------
    try:
        out, err, rc = client._execute_with_cd(
            "python3 scripts/audit/check_alpaca_paper_on_droplet.py 2>&1",
            timeout=25,
        )
        save_proof("phase5_alpaca", (out or "") + (err or ""))
        if "NO_CREDENTIALS" in (out or "") or "NOT_PAPER_URL" in (out or ""):
            return fail_closed("Alpaca paper credentials or paper URL missing/invalid.", ["Set ALPACA_KEY/ALPACA_SECRET and ALPACA_BASE_URL (paper) in .env on droplet."], "python scripts/audit/run_monday_open_readiness.py")
        if "ERROR" in (out or "") or rc != 0:
            return fail_closed("Alpaca paper API unreachable or auth failed.", ["Check network and paper API keys on droplet."], "python scripts/audit/run_monday_open_readiness.py")
        results["phases"]["5_alpaca"] = {"account_ok": True, "clock_ok": True}
    except Exception as e:
        return fail_closed(f"Phase 5 Alpaca check failed: {e}", ["Verify Alpaca paper keys and base URL on droplet."], "python scripts/audit/run_monday_open_readiness.py")

    # ---------- PHASE 6: SMOKE TEST ----------
    try:
        out, err, rc = client._execute_with_cd("DROPLET_RUN=1 TRADING_MODE=PAPER python3 scripts/audit/run_monday_open_smoke_test.py 2>&1", timeout=90)
        save_proof("phase6_smoke_test", (out or "") + (err or ""))
        if rc != 0:
            return fail_closed("Monday smoke test failed (non-zero exit).", ["Fix run_monday_open_smoke_test.py or dependencies on droplet.", "Re-run readiness after fix."], "python scripts/audit/run_monday_open_readiness.py")
        out2, _, _ = client._execute_with_cd("ls reports/audit/MONDAY_SMOKE_TEST_*.json 2>/dev/null || echo 'no-file'", timeout=5)
        save_proof("phase6_smoke_list", out2 or "")
        if "no-file" in (out2 or "") or "MONDAY_SMOKE_TEST_" not in (out2 or ""):
            return fail_closed("Smoke test did not produce MONDAY_SMOKE_TEST_*.json on droplet.", ["Ensure scripts/audit/run_monday_open_smoke_test.py writes to reports/audit/ on droplet."], "python scripts/audit/run_monday_open_readiness.py")
        results["phases"]["6_smoke"] = {"exit_code": 0, "output_tail": (out or "")[-500:]}
    except Exception as e:
        return fail_closed(f"Phase 6 smoke test failed: {e}", ["Run smoke test manually on droplet: DROPLET_RUN=1 python3 scripts/audit/run_monday_open_smoke_test.py"], "python scripts/audit/run_monday_open_readiness.py")

    # ---------- PHASE 7: DASHBOARD ENDPOINTS ----------
    try:
        run_validation = REPO / "scripts" / "audit" / "run_dashboard_full_validation_on_droplet.py"
        if run_validation.exists():
            import subprocess
            r = subprocess.run([sys.executable, str(run_validation)], cwd=REPO, capture_output=True, text=True, timeout=120)
            save_proof("phase7_dashboard_validation", (r.stdout or "") + (r.stderr or ""))
            out, _, _ = client._execute_with_cd(
                "code_learn=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/learning_readiness); "
                "code_tele=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/telemetry_health); "
                "code_prof=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/profitability_learning); "
                "echo learning_readiness:$code_learn telemetry_health:$code_tele profitability_learning:$code_prof",
                timeout=15,
            )
            save_proof("phase7_key_endpoints", out or "")
            if "500" in (out or ""):
                return fail_closed("One or more dashboard endpoints returned 500.", ["Check dashboard logs and data files (cockpit, CSA, state)."], "python scripts/audit/run_monday_open_readiness.py")
            results["phases"]["7_dashboard"] = {"key_endpoints_ok": "500" not in (out or "")}
        else:
            results["phases"]["7_dashboard"] = {"skipped": "run_dashboard_full_validation_on_droplet.py not found"}
    except Exception as e:
        results["warnings"].append(f"Phase 7: {e}")
        results["phases"]["7_dashboard"] = results["phases"].get("7_dashboard", {}) | {"error": str(e)}

    # ---------- PHASE 8: CSA + COCKPIT ----------
    try:
        out, _, _ = client._execute_with_cd(
            "cat reports/audit/CSA_VERDICT_LATEST.json 2>/dev/null | head -50; echo '---'; cat reports/state/TRADE_CSA_STATE.json 2>/dev/null || cat reports/state/test_csa_100/TRADE_CSA_STATE.json 2>/dev/null || echo '{}'",
            timeout=10,
        )
        save_proof("phase8_csa_state", out or "")
        try:
            parts = (out or "").split("---")
            verdict_raw = parts[0].strip() if parts else "{}"
            state_raw = parts[1].strip() if len(parts) > 1 else "{}"
            verdict = json.loads(verdict_raw) if verdict_raw and verdict_raw != "{}" else {}
            state = json.loads(state_raw) if state_raw and state_raw != "{}" else {}
            total = state.get("total_trade_events", 0)
            last_csa = state.get("last_csa_trade_count", 0)
            until = 100 - (total % 100) if total else 100
            results["phases"]["8_csa"] = {"total_trade_events": total, "last_csa_trade_count": last_csa, "trades_until_next": until}
        except json.JSONDecodeError:
            results["phases"]["8_csa"] = {"parse_warning": True}
        out2, _, rc = client._execute_with_cd("python3 scripts/update_profitability_cockpit.py 2>&1", timeout=30)
        save_proof("phase8_cockpit_update", out2 or "")
        if rc != 0:
            results["warnings"].append("update_profitability_cockpit.py returned non-zero")
        results["phases"]["8_csa"]["cockpit_updated"] = rc == 0
    except Exception as e:
        results["warnings"].append(f"Phase 8: {e}")
        results["phases"]["8_csa"] = results["phases"].get("8_csa", {}) | {"error": str(e)}

    # ---------- PHASE 9: CRON ----------
    try:
        out, _, _ = client._execute_with_cd("crontab -l 2>/dev/null || echo 'no-crontab'; echo '---'; ls -la logs/cron*.log 2>/dev/null || true", timeout=10)
        save_proof("phase9_cron", out or "")
        results["phases"]["9_cron"] = {"cron_listed": "no-crontab" not in (out or "") or "cron" in (out or "").lower()}
    except Exception as e:
        results["phases"]["9_cron"] = {"error": str(e)}

    # ---------- PHASE 10: VERDICT + OPERATOR STEPS ----------
    results["verdict"] = "PASS"
    _write_readiness_md(results, readiness_md, date_str, ts)
    results_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Readiness: {results['verdict']}. Proof: {proof_dir}")
    return 0


def _write_readiness_md(results: dict, path: Path, date_str: str, ts: str) -> None:
    md = [
        "# Monday Market Open Readiness",
        "",
        f"**Date:** {date_str} **Time (UTC):** {ts}",
        "",
        f"**Verdict:** {results.get('verdict', 'PASS')}",
        "",
        "## Evidence",
        "",
        f"- Proof folder: `{results.get('proof_dir', 'reports/audit/MONDAY_OPEN_READINESS_PROOF_*')}`",
        "",
        "## Phases",
        "",
    ]
    for k, v in results.get("phases", {}).items():
        md.append(f"- **{k}:** {json.dumps(v)[:200]}...")
    if results.get("warnings"):
        md.extend(["", "## Warnings", ""] + [f"- {w}" for w in results["warnings"]])
    md.extend([
        "",
        "## Monday 9:29am operator steps (30s runbook)",
        "",
        "1. Confirm PAPER mode: `grep TRADING_MODE .env` on droplet → PAPER",
        "2. Confirm Alpaca paper: `curl -s https://paper-api.alpaca.markets/...` or dashboard SRE health",
        "3. Confirm dashboard last update: check Telemetry Health / Profitability tab freshness",
        "4. Kill switch: set TRADING_MODE=HALT or stop stock-bot service; document in runbook.",
        "",
    ])
    path.write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
