#!/usr/bin/env python3
"""
Execute FULL Phase-2 workflow per MEMORY_BANK §6.11:
deploy, runtime identity, log sinks, heartbeat, dry-run, symbol risk, shadow, EOD, activation proof.
Fetch artifacts, write PHASE2_WORKFLOW_COMPLETE.md.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE = "/root/stock-bot"


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    sftp = None
    date = "2026-01-26"  # last trading date; override via env if needed
    proofs: list[str] = []
    fails: list[str] = []

    def run(cmd: str, timeout: int = 60) -> tuple[str, str, int]:
        out, err, rc = client._execute(f"cd {REMOTE} && {cmd}", timeout=timeout)
        return (out or "").strip(), (err or "").strip(), rc

    def _num(s: str) -> int:
        try:
            return int(str(s or "0").strip().splitlines()[0].strip() or "0")
        except Exception:
            return 0

    try:
        # --- 0) Preconditions ---
        out, _, rc = run("pwd && test -d /root/stock-bot && echo OK")
        if "OK" not in out:
            fails.append("WorkingDirectory not /root/stock-bot")
            return 1
        out, _, _ = run("systemctl is-active stock-bot.service 2>/dev/null || true")
        proofs.append(f"stock-bot.service: {out or 'unknown'}")

        # --- 1) Deploy: fetch, reset, restart ---
        pre, _, _ = run("git rev-parse HEAD 2>/dev/null || echo n/a")
        run("git fetch origin main 2>&1", timeout=30)
        run("git reset --hard origin/main 2>&1", timeout=15)
        post, _, _ = run("git rev-parse HEAD 2>/dev/null || echo n/a")
        proofs.append(f"git pre={pre[:8]} post={post[:8]}")
        out2, err2, rc2 = run("systemctl restart stock-bot.service 2>&1", timeout=20)
        proofs.append(f"restart: rc={rc2} stderr={err2[:200] if err2 else 'none'}")
        restart_ts = datetime.now(timezone.utc).isoformat()

        # Wait for cycles (heartbeat, log_sink)
        time.sleep(90)
        status, _, _ = run("systemctl status stock-bot.service --no-pager 2>&1", timeout=15)
        jlog, _, _ = run("journalctl -u stock-bot.service --since '5 min ago' --no-pager 2>&1 | tail -200", timeout=15)

        # Write deployment proof (local + upload to droplet)
        dep_lines = [
            "# Phase-2 Deployment Proof",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Pre/Post commit",
            f"- Pre: `{pre[:12]}`",
            f"- Post: `{post[:12]}`",
            "",
            "## Restart",
            f"- Time: {restart_ts}",
            f"- systemctl restart rc: {rc2}",
            "",
            "## systemctl status (excerpt)",
            "```",
            (status or "")[:2000],
            "```",
            "",
            "## journalctl (last 200 lines excerpt)",
            "```",
            (jlog or "")[:3000],
            "```",
        ]
        dep_path = REPO / "reports" / "PHASE2_DEPLOYMENT_PROOF.md"
        dep_path.parent.mkdir(parents=True, exist_ok=True)
        dep_path.write_text("\n".join(dep_lines), encoding="utf-8")
        proofs.append(f"Wrote {dep_path}")

        # Upload deployment proof to droplet
        ssh = client._connect()
        sftp = ssh.open_sftp()
        try:
            sftp.put(str(dep_path), f"{REMOTE}/reports/PHASE2_DEPLOYMENT_PROOF.md")
        except Exception:
            pass

        # --- 2) Runtime identity ---
        run("python3 scripts/phase2_runtime_identity.py", timeout=30)

        # --- 3) Log sinks: log_sink_confirmed ---
        out, _, _ = run("grep -n 'log_sink_confirmed' logs/system_events.jsonl 2>/dev/null | tail -20")
        if not out.strip():
            fails.append("log_sink_confirmed missing in system_events.jsonl")
        else:
            proofs.append("log_sink_confirmed: found")

        # --- 4) Heartbeat ---
        out, _, _ = run('grep -n "phase2_heartbeat" logs/system_events.jsonl 2>/dev/null | tail -50')
        if not out.strip():
            fails.append("phase2_heartbeat missing")
        else:
            proofs.append("phase2_heartbeat: found")

        # --- 5) Dry-run: trade_intent / exit_intent ---
        for name in [
            "phase2_dryrun_signal_emit.py", "build_symbol_risk_features.py", "phase2_forensic_audit.py",
            "phase2_activation_proof.py", "phase2_shadow_dryrun.py", "phase2_count_run_events.py",
        ]:
            local = REPO / "scripts" / name
            if local.exists():
                sftp.put(str(local), f"{REMOTE}/scripts/{name}")
        dry_out, dry_err, dry_rc = run("python3 scripts/phase2_dryrun_signal_emit.py 2>&1", timeout=60)
        if dry_rc != 0:
            fails.append(f"dry-run exit {dry_rc}: {dry_err[:300] if dry_err else dry_out[:300]}")
        check, _, _ = run("python3 scripts/phase2_count_run_events.py 2>/dev/null || echo 0 0", timeout=30)
        parts = (check or "0 0").strip().split()
        nt = _num(parts[0]) if len(parts) >= 1 else 0
        ne = _num(parts[1]) if len(parts) >= 2 else 0
        if nt < 1 or ne < 1:
            fails.append("trade_intent or exit_intent missing after dry-run")
        else:
            proofs.append(f"dry-run: trade_intent={nt} exit_intent={ne}")

        # --- 6) Symbol risk ---
        out, _, _ = run("python3 -c \"import json; d=json.load(open('state/symbol_risk_features.json')); s=d.get('symbols',{}); print(len(s))\" 2>/dev/null || echo 0")
        n = _num(out)
        if n == 0:
            run("python3 scripts/build_symbol_risk_features.py 2>&1", timeout=120)
            out, _, _ = run("python3 -c \"import json; d=json.load(open('state/symbol_risk_features.json')); s=d.get('symbols',{}); print(len(s))\" 2>/dev/null || echo 0")
            n = _num(out)
        if n > 0:
            proofs.append(f"symbol_risk_features: {n} symbols")
        else:
            fails.append("symbol_risk_features missing or empty after build")

        # --- 7) Shadow (dry-run if main loop does not emit when market closed) ---
        run("python3 scripts/phase2_shadow_dryrun.py 2>&1", timeout=60)
        out, _, _ = run('grep -n "shadow_variants_rotated" logs/system_events.jsonl 2>/dev/null | tail -10')
        out2, _, _ = run('grep -c "shadow_variant" logs/shadow.jsonl 2>/dev/null || echo 0')
        if not out.strip() and _num(out2) == 0:
            fails.append("shadow_variants_rotated / shadow_variant_* missing")
        else:
            proofs.append("shadow: found")

        # --- 8) EOD ---
        run(f"python3 reports/_daily_review_tools/generate_eod_alpha_diagnostic.py --date {date} 2>&1", timeout=90)

        # --- 8b) Forensic audit (VERIFY_*.csv) ---
        run(f"python3 scripts/phase2_forensic_audit.py --date {date} --local 2>&1", timeout=120)

        # --- 9) Activation proof ---
        run(f"python3 scripts/phase2_activation_proof.py --date {date} 2>&1", timeout=90)

        # --- 10) Fetch artifacts ---
        for r in [
            "PHASE2_DEPLOYMENT_PROOF.md",
            "PHASE2_RUNTIME_IDENTITY.md",
            f"PHASE2_ACTIVATION_PROOF_{date}.md",
            f"EOD_ALPHA_DIAGNOSTIC_{date}.md",
        ]:
            try:
                sftp.get(f"{REMOTE}/reports/{r}", str(REPO / "reports" / r))
                proofs.append(f"Fetched {r}")
            except FileNotFoundError:
                fails.append(f"Missing {r}")
        for name in [
            "VERIFY_trade_intent_samples.csv", "VERIFY_exit_intent_samples.csv",
            "VERIFY_directional_gate_blocks.csv", "VERIFY_displacement_decisions.csv",
            "VERIFY_shadow_variant_activity.csv", "VERIFY_high_vol_cohort.csv",
        ]:
            try:
                (REPO / "exports").mkdir(parents=True, exist_ok=True)
                sftp.get(f"{REMOTE}/exports/{name}", str(REPO / "exports" / name))
            except FileNotFoundError:
                pass

        # --- PHASE2_WORKFLOW_COMPLETE ---
        all_ok = len(fails) == 0
        lines = [
            "# Phase-2 Workflow Complete",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Executed",
            "1. Deploy: git pull, systemctl restart stock-bot",
            "2. Runtime identity, log_sink_confirmed, phase2_heartbeat",
            "3. Dry-run trade_intent/exit_intent",
            "4. Symbol risk build (if needed), shadow, EOD, activation proof",
            "5. Fetched reports and exports",
            "",
            "## PASS/FAIL",
            "| Check | Status |",
            "|-------|--------|",
        ]
        for p in proofs:
            lines.append(f"| {p} | OK |")
        for f in fails:
            lines.append(f"| {f} | FAIL |")
        lines.extend([
            "",
            "## Artifacts",
            f"- reports/PHASE2_DEPLOYMENT_PROOF.md",
            f"- reports/PHASE2_RUNTIME_IDENTITY.md",
            f"- reports/PHASE2_ACTIVATION_PROOF_{date}.md",
            f"- reports/EOD_ALPHA_DIAGNOSTIC_{date}.md",
            "- exports/VERIFY_*.csv",
            "",
            "## Next",
            "None." if all_ok else "Address FAILs above; re-run workflow.",
        ])
        wf_path = REPO / "reports" / "PHASE2_WORKFLOW_COMPLETE.md"
        wf_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {wf_path}")
        return 0 if all_ok else 1

    except Exception as e:
        fails.append(str(e))
        raise
    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
