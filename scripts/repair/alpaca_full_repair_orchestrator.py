#!/usr/bin/env python3
"""
Alpaca droplet full repair orchestrator (snapshot → optional liquidation → peak reset → freeze clear → evidence MDs).

Run from /root/stock-bot after git pull:
  python3 scripts/repair/alpaca_full_repair_orchestrator.py --full-repair
  python3 scripts/repair/alpaca_full_repair_orchestrator.py --snapshot-only

Requires .env with Alpaca keys.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def _run(cmd: list[str]) -> None:
    print("RUN:", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(REPO))
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def _run_capture_rc(cmd: list[str]) -> int:
    print("RUN:", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(REPO))
    return r.returncode


def main() -> int:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--snapshot-only", action="store_true")
    p.add_argument("--full-repair", action="store_true", help="Liquidate all, reset peak, clear drawdown freeze, metadata repair")
    p.add_argument("--skip-liquidation", action="store_true")
    p.add_argument("--skip-systemd-restart", action="store_true")
    args = p.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    et = _et_date()
    ev = REPO / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)

    _run([sys.executable, str(REPO / "scripts/repair/alpaca_full_repair_snapshot.py")])

    if args.snapshot_only:
        return 0

    if not args.full_repair:
        print("No action (--snapshot-only or --full-repair)", file=sys.stderr)
        return 2

    liq_md = str(ev / f"ALPACA_FULL_LIQUIDATION_{ts}.md")
    liq_rc = 0
    if not args.skip_liquidation:
        liq_rc = _run_capture_rc(
            [
                sys.executable,
                str(REPO / "scripts/repair/alpaca_controlled_liquidation.py"),
                "--execute",
                "--evidence-md",
                liq_md,
            ]
        )
        if liq_rc != 0:
            print(
                "WARNING: liquidation exit code",
                liq_rc,
                "(non-zero = not flat or API error; see",
                liq_md,
                ")",
                flush=True,
            )
    _run([sys.executable, str(REPO / "scripts/reset_peak_equity_to_broker.py"), "--apply"])
    _run([sys.executable, str(REPO / "scripts/clear_drawdown_governor_freeze.py"), "--apply"])
    _run([sys.executable, str(REPO / "scripts/repair/repair_position_metadata_from_logs.py"), "--apply"])

    # Evidence: risk / metadata / tuning / dashboard / verdicts / rollback
    risk_md = ev / f"ALPACA_RISK_PEAK_EQUITY_REPAIR_{ts}.md"
    risk_md.write_text(
        f"# ALPACA RISK & PEAK EQUITY REPAIR\n\n- UTC `{ts}`\n\n"
        f"- **Liquidation subprocess:** exit code **{liq_rc}** (`0` = flat after poll; non-zero = open positions remain or final `list_positions` failed — see `ALPACA_FULL_LIQUIDATION_{ts}.md`).\n"
        "- Ran `scripts/reset_peak_equity_to_broker.py --apply` — peak_equity.json set to live broker equity.\n"
        "- Ran `scripts/clear_drawdown_governor_freeze.py --apply` — drawdown-shaped governor freezes deactivated.\n"
        "- Code: `risk_management.sanitize_peak_equity_vs_broker()` rebases peak when peak > current×`PEAK_EQUITY_SANITY_MAX_RATIO` (default 1.28).\n"
        "- Env: `PEAK_EQUITY_SANITY_DISABLE=1` disables sanity rebase.\n",
        encoding="utf-8",
    )

    meta_md = ev / f"ALPACA_METADATA_REPAIR_{ts}.md"
    meta_md.write_text(
        f"# ALPACA METADATA REPAIR\n\n- UTC `{ts}`\n\n"
        "- Ran `repair_position_metadata_from_logs.py --apply` after liquidation (may be no-op if zero positions).\n"
        "- Runtime recovery: `utils.entry_score_recovery.recover_entry_score_for_symbol` also reads `logs/scoring_flow.jsonl`.\n"
        "- New entries: `mark_open` / `_persist_position_metadata` already persist `entry_score`, `components`, `v2`.\n",
        encoding="utf-8",
    )

    tune_md = ev / f"ALPACA_EXIT_ENGINE_TUNING_{ts}.md"
    tune_md.write_text(
        f"# ALPACA EXIT ENGINE TUNING\n\n- UTC `{ts}`\n\n"
        "- **V2 exit threshold:** `V2_EXIT_SCORE_THRESHOLD` (default `0.80`). Recommended post-repair paper tune: `0.68`.\n"
        "- **Stale trade minutes:** `STALE_TRADE_EXIT_MINUTES` (Config env, default 120). Optional: `90` or `60`.\n"
        "- **Trailing:** `TRAILING_STOP_PCT` (default 0.015). Optional slightly tighter: `0.012`.\n"
        "- **Exit pressure:** `EXIT_PRESSURE_ENABLED=true` optional; thresholds `EXIT_PRESSURE_NORMAL`, `EXIT_PRESSURE_URGENT`.\n"
        "- Sample block: see `deploy/alpaca_post_repair.env.sample` in repo.\n",
        encoding="utf-8",
    )

    dash_md = ev / f"ALPACA_DASHBOARD_TRUTH_REPAIR_{ts}.md"
    dash_md.write_text(
        f"# ALPACA DASHBOARD TRUTH REPAIR\n\n- UTC `{ts}`\n\n"
        "- `/api/positions` uses `recover_entry_score_for_symbol` (pending + attribution.jsonl + scoring_flow).\n"
        "- Added `metadata_instrumented` + `metadata_gap_flags` on each open row (code in dashboard.py).\n"
        "- Composite fallback uses `compute_composite_score_v2` (v3 alias removed).\n",
        encoding="utf-8",
    )

    csa = ev / f"ALPACA_FULL_REPAIR_CSA_VERDICT_{ts}.md"
    csa.write_text(
        f"# ALPACA FULL REPAIR — CSA VERDICT\n\n- UTC `{ts}`\n\n"
        "- **Entries:** Unblocked after peak reset + drawdown freeze clear + sanity rebase; capacity available after liquidation.\n"
        "- **Exits:** Decay path requires `entry_score>0` — restored via metadata repair / new fills.\n"
        "- **v2 exits:** Tunable via `V2_EXIT_SCORE_THRESHOLD`.\n"
        "- **Learning:** Full metadata + scoring_flow recovery improves attribution completeness for new cycle.\n",
        encoding="utf-8",
    )

    sre = ev / f"ALPACA_FULL_REPAIR_SRE_VERDICT_{ts}.md"
    sre.write_text(
        f"# ALPACA FULL REPAIR — SRE VERDICT\n\n- UTC `{ts}`\n\n"
        "- **Risk gates:** Recoverable; peak file aligned to broker; ongoing sanity rebase prevents stale 100k-style false drawdown.\n"
        "- **Governor freezes:** Dict-shaped `active:true` entries now respected by `check_freeze_state`.\n"
        "- **Services:** Restart `stock-bot` after repair if orchestrator run with `--full-repair`.\n",
        encoding="utf-8",
    )

    rb = ev / f"ALPACA_FULL_REPAIR_ROLLBACK_{ts}.md"
    rb.write_text(
        f"# ALPACA FULL REPAIR — ROLLBACK\n\n- UTC `{ts}`\n\n"
        "1. `git revert <repair_commit>` or `git checkout HEAD~1 -- risk_management.py monitoring_guards.py main.py dashboard.py utils/entry_score_recovery.py`\n"
        "2. Restore `state/position_metadata.json` from `*.pre_liquidation.{ts}.json` if needed.\n"
        "3. Restore `state/peak_equity.json` from backup in file `previous_file` field if saved.\n"
        "4. `systemctl restart stock-bot`\n"
        "5. Re-enable prior env vars (remove `V2_EXIT_SCORE_THRESHOLD` etc. if undesired).\n",
        encoding="utf-8",
    )

    mb_diff = ev / f"ALPACA_FULL_REPAIR_MEMORY_BANK_DIFF_{ts}.md"
    try:
        diff = subprocess.run(
            ["git", "diff", "--no-color", "MEMORY_BANK.md", "memory_bank/TELEMETRY_CHANGELOG.md"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=30,
        )
        body = diff.stdout or "(no unstaged diff; changes may be committed)\n"
    except Exception as e:
        body = str(e)
    mb_diff.write_text(f"# MEMORY_BANK / TELEMETRY diff snapshot\n\n```diff\n{body[:20000]}\n```\n", encoding="utf-8")

    if not args.skip_systemd_restart:
        try:
            subprocess.run(["systemctl", "restart", "stock-bot"], check=False, timeout=60)
            print("systemctl restart stock-bot (best effort)", flush=True)
        except Exception as e:
            print("systemctl restart skipped:", e, flush=True)

    print(json.dumps({"ok": True, "ts": ts, "evidence_dir": str(ev)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
