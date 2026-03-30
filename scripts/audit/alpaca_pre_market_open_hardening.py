#!/usr/bin/env python3
"""
Pre-market-open hardening: service, broker, dashboard, telemetry, lineage, forward readiness.

Run on droplet (repo root):
  python3 scripts/audit/alpaca_pre_market_open_hardening.py
  python3 scripts/audit/alpaca_pre_market_open_hardening.py --no-start   # verify only; do not start stock-bot

Writes: reports/daily/<ET-date>/evidence/ALPACA_PRE_MARKET_OPEN_HARDENING.md
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))


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


def _evidence_dir() -> Path:
    d = REPO / "reports" / "daily" / _et_date() / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sh(cmd: str, timeout: int = 120) -> Tuple[str, str, int]:
    r = subprocess.run(
        ["bash", "-lc", cmd],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return r.stdout or "", r.stderr or "", r.returncode


def _start_stock_bot() -> Tuple[str, int]:
    """Try systemctl start; on failure retry with sudo -n (droplet non-interactive)."""
    out, err, rc = _sh("systemctl start stock-bot 2>&1", 60)
    blob = (out + err).strip()
    if rc == 0:
        return blob, 0
    out2, err2, rc2 = _sh("sudo -n systemctl start stock-bot 2>&1", 60)
    return (blob + "\n" + (out2 + err2).strip()).strip(), rc2


def _section(title: str) -> List[str]:
    return [f"\n## {title}\n\n"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Pre-market-open hardening audit (droplet).")
    ap.add_argument(
        "--no-start",
        action="store_true",
        help="Do not run systemctl start; only report whether stock-bot is active.",
    )
    ap.add_argument(
        "--start-wait-sec",
        type=int,
        default=120,
        help="After systemctl start, poll is-active up to this many seconds (default 120).",
    )
    args = ap.parse_args()

    ev = _evidence_dir()
    out_path = ev / "ALPACA_PRE_MARKET_OPEN_HARDENING.md"
    lines: List[str] = [
        "# ALPACA PRE-MARKET OPEN — Hardening audit\n\n",
        f"- UTC generated: `{datetime.now(timezone.utc).isoformat()}`\n",
        f"- ET evidence date: `{_et_date()}`\n",
        f"- `--no-start`: **{args.no_start}**\n\n",
    ]

    critical_fail: List[str] = []
    warnings: List[str] = []

    # --- Context ---
    gh, _, _ = _sh("git rev-parse HEAD", 15)
    du, _, _ = _sh("date -u", 10)
    lines += _section("Context")
    lines.append(f"- `git rev-parse HEAD`: `{gh.strip()}`\n")
    lines.append(f"- `date -u`: `{du.strip()}`\n")

    # --- stock-bot service ---
    lines += _section("stock-bot (systemd)")
    en, _, _ = _sh("systemctl is-enabled stock-bot 2>&1", 15)
    ac0, _, _ = _sh("systemctl is-active stock-bot 2>&1", 15)
    lines.append(f"- `systemctl is-enabled stock-bot`: `{en.strip()}`\n")
    lines.append(f"- `systemctl is-active stock-bot` (initial): **`{ac0.strip()}`**\n")

    started_by_script = False
    if ac0.strip() != "active":
        if args.no_start:
            critical_fail.append("stock-bot inactive and --no-start set")
            lines.append("\n**FAIL:** Service not active; rerun without `--no-start` to start, or `sudo systemctl start stock-bot`.\n")
        else:
            lines.append("\nStarting `stock-bot` (ensure-active)…\n")
            se, rc = _start_stock_bot()
            lines.append(f"- `systemctl start` exit: **{rc}**\n")
            if se.strip():
                lines.append(f"```text\n{se.strip()[:2000]}\n```\n")
            started_by_script = True
            deadline = time.monotonic() + max(10, args.start_wait_sec)
            active = False
            while time.monotonic() < deadline:
                a, _, _ = _sh("systemctl is-active stock-bot 2>&1", 10)
                if a.strip() == "active":
                    active = True
                    break
                time.sleep(3)
            ac1, _, _ = _sh("systemctl is-active stock-bot 2>&1", 10)
            lines.append(f"- `systemctl is-active stock-bot` (after start/poll): **`{ac1.strip()}`**\n")
            if not active:
                critical_fail.append("stock-bot failed to reach active state")
                jo, _, _ = _sh("journalctl -u stock-bot -n 40 --no-pager 2>&1", 30)
                lines.append("\n### journalctl tail (stock-bot)\n\n```text\n")
                lines.append(jo[:8000] + "\n```\n")
            else:
                lines.append("- **OK:** stock-bot is **active**.\n")
    else:
        lines.append("- **OK:** stock-bot already **active**.\n")

    st, _, _ = _sh("systemctl show stock-bot -p Restart -p RestartUSec -p User --no-pager 2>&1", 15)
    lines.append("\n```text\n" + st.strip()[:2000] + "\n```\n")

    svc_active_final = _sh("systemctl is-active stock-bot 2>&1", 15)[0].strip() == "active"

    # --- Processes ---
    lines += _section("Trading processes (best-effort)")
    ps, _, _ = _sh("ps aux | grep -E 'deploy_supervisor|main\\.py' | grep -v grep | head -15", 10)
    lines.append("```text\n" + (ps.strip() or "(none)") + "\n```\n")
    if "main.py" not in ps and "deploy_supervisor" not in ps:
        if svc_active_final:
            warnings.append("systemd active but no main.py/deploy_supervisor in ps snapshot (may still be starting)")
        elif not critical_fail:
            warnings.append("No engine processes visible")

    # --- Environment file presence ---
    lines += _section("Environment")
    env_ok, _, _ = _sh("test -f .env && echo yes || echo no", 10)
    lines.append(f"- `.env` present: **`{env_ok.strip()}`**\n")
    if env_ok.strip() != "yes":
        critical_fail.append(".env missing")

    # --- Alpaca broker ---
    lines += _section("Alpaca broker (read-only)")
    broker: Dict[str, Any] = {}
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(REPO / ".env")
        import alpaca_trade_api as tradeapi  # type: ignore

        from main import Config

        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version="v2")
        clk = api.get_clock()
        broker["clock"] = {
            "is_open": bool(getattr(clk, "is_open", False)),
            "next_open": str(getattr(clk, "next_open", "") or ""),
            "next_close": str(getattr(clk, "next_close", "") or ""),
        }
        acct = api.get_account()
        broker["account"] = {
            "status": str(getattr(acct, "status", "") or ""),
            "equity": str(getattr(acct, "equity", "") or ""),
            "trading_blocked": getattr(acct, "trading_blocked", None),
        }
        lines.append("```json\n" + json.dumps(broker, indent=2) + "\n```\n")
    except Exception as e:
        critical_fail.append(f"alpaca_broker: {e!s}"[:200])
        lines.append(f"**FAIL:** `{e!s}`\n")

    # --- Dashboard HTTP ---
    lines += _section("Dashboard (localhost)")
    for path in ("/api/ping", "/api/telemetry_health", "/api/sre/health"):
        code, _, _ = _sh(
            f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 8 http://127.0.0.1:5000{path} 2>/dev/null || echo fail",
            15,
        )
        c = code.strip()
        lines.append(f"- `{path}` → **HTTP {c}**\n")
        if path == "/api/ping":
            if c != "200":
                critical_fail.append(f"dashboard_ping_not_200:{c}")
        elif c in ("000", "fail", ""):
            critical_fail.append(f"dashboard_unreachable:{path}")
        elif c not in ("200", "401", "403"):
            warnings.append(f"dashboard_unexpected_http:{path}={c}")

    # --- Canonical log sinks (Phase-2 parity + audit spine) ---
    lines += _section("Telemetry surfaces (writable / mtime)")
    log_paths = [
        "logs/run.jsonl",
        "logs/system_events.jsonl",
        "logs/shadow.jsonl",
        "logs/orders.jsonl",
        "logs/attribution.jsonl",
        "logs/exit_attribution.jsonl",
        "logs/positions.jsonl",
        "logs/signal_context.jsonl",
        "logs/pnl_reconciliation.jsonl",
        "state/position_metadata.json",
    ]
    for rel in log_paths:
        p = REPO / rel
        par = p.parent
        ok_w = False
        try:
            if p.is_file():
                ok_w = os.access(p, os.W_OK)
            elif par.is_dir():
                ok_w = os.access(par, os.W_OK)
                with open(p, "a", encoding="utf-8"):
                    pass
                ok_w = True
        except Exception as e:
            lines.append(f"- `{rel}`: **FAIL** `{e!s}`\n")
            critical_fail.append(f"writable:{rel}")
            continue
        age = ""
        if p.is_file():
            age = f"{time.time() - p.stat().st_mtime:.0f}s"
        lines.append(f"- `{rel}`: writable=**{ok_w}** mtime_age=**{age or 'n/a'}**\n")

    # --- Lineage map check ---
    lines += _section("PnL lineage map check")
    mc = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit" / "alpaca_pnl_lineage_map_check.py"),
            "--write-evidence",
            "--evidence-dir",
            str(ev),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=120,
    )
    lines.append("```text\n" + (mc.stdout or "").strip()[:4000] + "\n```\n")
    try:
        meta = json.loads((mc.stdout or "").strip() or "{}")
        miss = int(meta.get("summary", {}).get("MISSING", 0) or 0)
        if miss > 0:
            critical_fail.append(f"lineage_map_missing_rows:{miss}")
        if mc.returncode != 0:
            critical_fail.append("lineage_map_check_exit_nonzero")
    except Exception as e:
        warnings.append(f"lineage_map_json_parse:{e!s}")

    # --- Forward collection readiness (full pack) ---
    lines += _section("Forward collection readiness")
    fr = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "audit" / "alpaca_forward_collection_readiness.py")],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=900,
    )
    lines.append(f"- Subprocess exit: **{fr.returncode}**\n")
    lines.append("```text\n" + (fr.stdout or "").strip()[:6000] + "\n```\n")
    if fr.returncode != 0:
        critical_fail.append("forward_collection_readiness_failed")

    # --- Disk ---
    lines += _section("Disk / journal")
    df, _, _ = _sh("df -h / /root 2>/dev/null | tail -n +1", 15)
    lines.append("```text\n" + df.strip() + "\n```\n")
    ju, _, _ = _sh("journalctl --disk-usage 2>/dev/null | head -3 || true", 10)
    lines.append("```text\n" + ju.strip() + "\n```\n")

    # --- Verdict ---
    lines += _section("Verdict")
    if critical_fail:
        lines.append("### **FAIL — blockers**\n\n")
        for b in critical_fail:
            lines.append(f"- {b}\n")
        lines.append("\n")
    else:
        lines.append("### **PASS — hardened for market open (within stated limits)**\n\n")
        lines.append(
            "- stock-bot **active**, broker **reachable**, dashboard **responding**, "
            "canonical logs **writable**, lineage map **clean**, forward readiness **passed**.\n\n"
        )
    if warnings:
        lines.append("### Warnings\n\n")
        for w in warnings:
            lines.append(f"- {w}\n")
        lines.append("\n")

    lines.append("### Operator notes\n\n")
    lines.append(
        "- This script does **not** validate strategy thresholds or positions risk — only **integrity + liveness** for data collection.\n"
        "- If you intentionally keep the bot stopped, use `--no-start` and expect **FAIL** on service gate.\n"
        "- Re-run after deploy: `git pull && python3 scripts/audit/alpaca_pre_market_open_hardening.py`\n"
    )
    if started_by_script:
        lines.append("- **This run started `stock-bot`.** Confirm risk posture before market open.\n")

    out_path.write_text("".join(lines), encoding="utf-8")
    result = {
        "evidence": str(out_path),
        "critical_fail": critical_fail,
        "warnings": warnings,
        "pass": len(critical_fail) == 0,
        "started_stock_bot": started_by_script,
    }
    print(json.dumps(result, indent=2))
    return 0 if not critical_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
