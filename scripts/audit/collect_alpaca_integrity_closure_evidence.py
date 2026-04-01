#!/usr/bin/env python3
"""
Run on developer machine with droplet_config.json / SSH — captures Phase 0 baseline from /root/stock-bot.
Writes under reports/daily/<ET_DATE>/evidence/ (ET_DATE from remote TZ=America/New_York).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402


def main() -> int:
    c = DropletClient()
    et = c.execute_command(
        "TZ=America/New_York date +%Y-%m-%d",
        timeout=30,
    )
    et_date = (et.get("stdout") or "").strip() or "unknown"
    ev = REPO / "reports" / "daily" / et_date / "evidence"
    ev.mkdir(parents=True, exist_ok=True)

    def run(name: str, cmd: str, timeout: int = 120) -> str:
        r = c.execute_command(cmd, timeout=timeout)
        out = f"### {name} (exit {r.get('exit_code')})\n\n```\n"
        out += (r.get("stdout") or "") + (r.get("stderr") or "")
        out += "\n```\n\n"
        return out

    chunks = []
    chunks.append("# ALPACA_INTEGRITY_CLOSURE_CONTEXT (Phase 0 — droplet capture)\n\n")
    chunks.append(
        run(
            "git_pull",
            "find /root/stock-bot/reports/daily -name 'ALPACA_STRICT_GATE_SNAPSHOT_DEDUP_VERIFY_*.json' "
            "-exec mv -t /tmp {} + 2>/dev/null; true; cd /root/stock-bot && git pull origin main 2>&1",
            120,
        )
    )
    chunks.append(
        run(
            "git_head_utc_et",
            "cd /root/stock-bot && git rev-parse HEAD && date -u && TZ=America/New_York date +%Y-%m-%d",
            30,
        )
    )
    chunks.append(
        run(
            "stock_bot_status",
            "systemctl status stock-bot --no-pager -l 2>&1 | head -100",
            60,
        )
    )
    chunks.append(run("ps_stock_bot", "ps aux | grep stock-bot | grep -v grep", 30))
    chunks.append(
        run(
            "journal_stock_bot",
            "journalctl -u stock-bot --since '36 hours ago' --no-pager 2>&1 | tail -n 800",
            180,
        )
    )
    chunks.append(
        run(
            "state_ls",
            "ls -lah /root/stock-bot/state/ 2>&1 | sed -n '1,200p'",
            30,
        )
    )
    chunks.append(
        run(
            "timers",
            "systemctl list-timers --all --no-pager 2>&1 | sed -n '1,200p'",
            60,
        )
    )
    chunks.append(run("crontab", "crontab -l 2>&1 || true", 30))
    chunks.append(
        run(
            "cron_grep",
            "grep -r stock-bot /etc/cron.d/ /etc/cron.daily/ 2>/dev/null | head -40 || true",
            30,
        )
    )
    chunks.append(
        run(
            "deploy_systemd_copy",
            "cp -f /root/stock-bot/deploy/systemd/alpaca-postclose-deepdive.service /etc/systemd/system/ && "
            "cp -f /root/stock-bot/deploy/systemd/telegram-failure-detector.service /etc/systemd/system/ && "
            "systemctl daemon-reload 2>&1 && echo OK",
            60,
        )
    )
    chunks.append(
        run(
            "systemd_cat_postclose",
            "systemctl cat alpaca-postclose-deepdive.service 2>&1 | head -40",
            30,
        )
    )
    chunks.append(
        run(
            "systemd_cat_failure_det",
            "systemctl cat telegram-failure-detector.service 2>&1 | head -40",
            30,
        )
    )

    strict_path = f"/root/stock-bot/reports/daily/{et_date}/evidence/ALPACA_STRICT_BASELINE.json"
    chunks.append(
        run(
            "strict_export",
            f"mkdir -p /root/stock-bot/reports/daily/{et_date}/evidence && "
            f"cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/export_strict_quant_edge_review_cohort.py "
            f"--root /root/stock-bot --out-json {strict_path} 2>&1",
            120,
        )
    )

    chunks.append(
        run(
            "warehouse_tail",
            "cd /root/stock-bot && PYTHONPATH=. timeout 300 python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py "
            "--root /root/stock-bot --days 30 --max-compute 2>&1 | tail -n 100",
            360,
        )
    )

    cov_head = c.execute_command(
        f"head -n 80 $(ls -t /root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md 2>/dev/null | head -1) 2>/dev/null || "
        f"head -n 80 $(find /root/stock-bot/reports/daily -name 'ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md' -printf '%T@ %p\\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)",
        timeout=60,
    )
    chunks.append(
        "### coverage_file_head (exit %s)\n\n```\n"
        % cov_head.get("exit_code")
        + (cov_head.get("stdout") or "")
        + (cov_head.get("stderr") or "")
        + "\n```\n\n"
    )

    parse_out = c.execute_command(
        "cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/parse_coverage_smoke_check.py --root /root/stock-bot 2>&1",
        timeout=60,
    )
    (ev / "ALPACA_COVERAGE_PARSE_BASELINE.json").write_text(
        parse_out.get("stdout") or "{}", encoding="utf-8"
    )
    chunks.append(
        "### parse_coverage_smoke_check\n\n```\n"
        + (parse_out.get("stdout") or "")
        + (parse_out.get("stderr") or "")
        + "\n```\n\n"
    )

    integ = c.execute_command(
        "cd /root/stock-bot && PYTHONPATH=. python3 scripts/run_alpaca_telegram_integrity_cycle.py "
        "--dry-run --skip-warehouse --no-self-heal 2>&1",
        timeout=120,
    )
    (ev / "ALPACA_INTEGRITY_CYCLE_DRYRUN_POSTFIX.json").write_text(
        integ.get("stdout") or "{}", encoding="utf-8"
    )
    chunks.append(
        "### integrity_cycle_dry_run\n\n```\n"
        + (integ.get("stdout") or "")[:12000]
        + (integ.get("stderr") or "")
        + "\n```\n\n"
    )

    arm = c.execute_command("cat /root/stock-bot/state/alpaca_milestone_integrity_arm.json 2>&1", 30)
    chunks.append(
        "### alpaca_milestone_integrity_arm.json\n\n```\n"
        + (arm.get("stdout") or "")
        + "\n```\n\n"
    )

    ms250 = c.execute_command("cat /root/stock-bot/state/alpaca_milestone_250_state.json 2>&1", 30)
    chunks.append(
        "### alpaca_milestone_250_state.json\n\n```\n"
        + (ms250.get("stdout") or "")
        + "\n```\n\n"
    )

    rg = c.execute_command(
        "cd /root/stock-bot && rg -l 'send_governance_telegram' deploy/systemd scripts/governance 2>/dev/null | head -20",
        60,
    )
    chunks.append(
        "### rg_send_governance_telegram_sample\n\n```\n"
        + (rg.get("stdout") or "")
        + "\n```\n\n"
    )

    tail_ev = c.execute_command(
        "tail -n 120 /root/stock-bot/logs/system_events.jsonl 2>/dev/null | rg ERROR || echo 'no_ERROR_in_tail'",
        60,
    )
    chunks.append(
        "### system_events_tail_grep_ERROR\n\n```\n"
        + (tail_ev.get("stdout") or "")
        + (tail_ev.get("stderr") or "")
        + "\n```\n\n"
    )

    ctx_path = ev / "ALPACA_INTEGRITY_CLOSURE_CONTEXT.md"
    ctx_path.write_text("".join(chunks), encoding="utf-8")

    r3 = c.execute_command(f"test -f {strict_path} && cat {strict_path}", 30)
    if r3.get("exit_code") == 0 and (r3.get("stdout") or "").strip().startswith("{"):
        (ev / "ALPACA_STRICT_BASELINE.json").write_text(r3.get("stdout") or "{}", encoding="utf-8")

    cov_md = c.execute_command(
        f"ls -t /root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md 2>/dev/null | head -1",
        30,
    )
    cov_p = (cov_md.get("stdout") or "").strip()
    if not cov_p:
        cov_md2 = c.execute_command(
            "find /root/stock-bot/reports/daily -name 'ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md' -printf '%T@ %p\\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-",
            30,
        )
        cov_p = (cov_md2.get("stdout") or "").strip()
    if cov_p:
        r4 = c.execute_command(f"head -n 120 '{cov_p}'", 30)
        (ev / "ALPACA_COVERAGE_BASELINE.md").write_text(
            f"<!-- source: {cov_p} -->\n\n```\n" + (r4.get("stdout") or "") + "\n```\n",
            encoding="utf-8",
        )

    print(json.dumps({"evidence_dir": str(ev), "et_date": et_date}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
