#!/usr/bin/env python3
"""
Fetch governance loop activity from droplet for the last 48 hours and write a report.
Output: reports/audit/GOVERNANCE_48H_REPORT_<date>.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.governance.droplet_authority import add_droplet_authority_args, require_droplet_authority


def _parse_cycle_ts(name: str) -> datetime | None:
    """Parse equity_governance_YYYYMMDDTHHMMSSZ -> datetime UTC."""
    m = re.match(r"equity_governance_(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z", name)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)), int(m.group(5)), int(m.group(6)), tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def _parse_log_ts(line: str) -> datetime | None:
    """Parse [YYYY-MM-DDTHH:MM:SSZ] from log line."""
    m = re.match(r"\[(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z\]", line)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)), int(m.group(5)), int(m.group(6)), tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch governance 48h activity from droplet and write report")
    add_droplet_authority_args(ap)
    args = ap.parse_args()
    require_droplet_authority("run_governance_48h_report_on_droplet", args, REPO)

    from droplet_client import DropletClient

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=48)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    report_date = now.strftime("%Y-%m-%d")

    out_dir = REPO / "reports" / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md = out_dir / f"GOVERNANCE_48H_REPORT_{report_date}.md"

    with DropletClient() as c:
        # 1) Loop process running?
        pgrep_out, _, _ = c._execute(
            "pgrep -af 'run_equity_governance_loop|CURSOR_DROPLET_EQUITY_GOVERNANCE' || true",
            timeout=10,
        )
        process_running = bool((pgrep_out or "").strip())

        # 2) State file
        state_out, _, _ = c._execute(
            "cat /root/stock-bot/state/equity_governance_loop_state.json 2>/dev/null || echo '{}'",
            timeout=10,
        )
        try:
            state = json.loads((state_out or "{}").strip()) if state_out else {}
        except Exception:
            state = {}

        # 3) List all equity_governance dirs (names only for timestamp parsing)
        list_out, _, _ = c._execute(
            "ls -1 /root/stock-bot/reports/equity_governance/ 2>/dev/null | grep '^equity_governance_'",
            timeout=10,
        )
        all_dirs = [n.strip() for n in (list_out or "").splitlines() if n.strip()]
        cycle_times = [(n, _parse_cycle_ts(n)) for n in all_dirs]
        cycle_times = [(n, t) for n, t in cycle_times if t is not None]
        cycle_times.sort(key=lambda x: x[1], reverse=True)
        last_48h_dirs = [n for n, t in cycle_times if t >= cutoff]
        last_48h_dirs.sort(key=lambda n: _parse_cycle_ts(n) or now, reverse=True)

        # 4) For each cycle in last 48h: decision, overlay, summary
        cycles_48h = []
        for dname in last_48h_dirs:
            dpath = f"/root/stock-bot/reports/equity_governance/{dname}"
            dec_out, _, _ = c._execute(f"cat {dpath}/lock_or_revert_decision.json 2>/dev/null", timeout=5)
            ov_out, _, _ = c._execute(f"cat {dpath}/overlay_config.json 2>/dev/null", timeout=5)
            sum_out, _, _ = c._execute(f"cat {dpath}/GOVERNANCE_FINAL_SUMMARY.txt 2>/dev/null", timeout=5)
            try:
                decision = json.loads((dec_out or "{}").strip()) if dec_out else {}
            except Exception:
                decision = {}
            try:
                overlay = json.loads((ov_out or "{}").strip()) if ov_out else {}
            except Exception:
                overlay = {}
            summary_txt = (sum_out or "").strip() if sum_out else ""
            ts = _parse_cycle_ts(dname)
            cycles_48h.append({
                "dir": dname,
                "ts": ts,
                "decision": decision,
                "overlay": overlay,
                "summary_txt": summary_txt,
            })

        # 5) Autopilot log: last 3000 lines then filter by 48h
        log_out, _, _ = c._execute(
            "tail -3000 /tmp/equity_governance_autopilot.log 2>/dev/null || echo ''",
            timeout=15,
        )
        log_lines = (log_out or "").splitlines()
        log_48h = []
        for line in log_lines:
            t = _parse_log_ts(line)
            if t and t >= cutoff:
                log_48h.append((t, line))

        log_48h.sort(key=lambda x: x[0])

    # Build report
    lines = [
        "# Governance Loop — Last 48 Hours Report",
        "",
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"**Window:** {cutoff.strftime('%Y-%m-%d %H:%M')} UTC → {now.strftime('%Y-%m-%d %H:%M')} UTC",
        "",
        "---",
        "",
        "## 1. Process status",
        "",
    ]
    if process_running:
        lines.append("- **Governance loop process:** Running")
    else:
        lines.append("- **Governance loop process:** Not running (or not detected)")

    lines.extend([
        "",
        "## 2. Loop state (current)",
        "",
        "```json",
        json.dumps(state, indent=2),
        "```",
        "",
        "## 3. Cycles in last 48 hours",
        "",
    ])

    if not cycles_48h:
        lines.append("No governance cycles completed in the last 48 hours.")
        lines.append("")
        lines.append("(Cycles are created when the autopilot runs and reaches A5 compare; if the loop is in A4 waiting for ≥100 closed trades, no new cycle dir will appear until that gate is met.)")
    else:
        lines.append(f"| Cycle (dir) | Time (UTC) | Decision | Lever | Baseline exp | Candidate exp |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for c in cycles_48h:
            dec = c["decision"]
            ov = c["overlay"]
            d = dec.get("decision", "")
            lev = ov.get("lever", "")
            ch = ov.get("change") or {}
            min_sc = ch.get("min_exec_score")
            lever_desc = f"entry(min_exec_score={min_sc})" if min_sc is not None else (lev or "—")
            base = dec.get("baseline") or {}
            cand = dec.get("candidate") or {}
            base_exp = base.get("expectancy_per_trade")
            cand_exp = cand.get("expectancy_per_trade")
            ts_str = c["ts"].strftime("%Y-%m-%d %H:%M") if c["ts"] else "—"
            lines.append(f"| {c['dir']} | {ts_str} | {d} | {lever_desc} | {base_exp} | {cand_exp} |")
        lines.append("")
        for c in cycles_48h:
            lines.append(f"### {c['dir']}")
            lines.append("")
            lines.append("**Decision:**")
            lines.append("```json")
            lines.append(json.dumps(c["decision"], indent=2))
            lines.append("```")
            if c["summary_txt"]:
                lines.append("**Summary:**")
                lines.append("```")
                lines.append(c["summary_txt"])
                lines.append("```")
            lines.append("")

    lines.extend([
        "## 4. Log activity (last 48h)",
        "",
    ])
    if not log_48h:
        lines.append("No log lines in the last 48 hours (or log empty/unreadable).")
    else:
        lines.append(f"Total log lines in window: **{len(log_48h)}**")
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Log excerpt (first 100 lines)</summary>")
        lines.append("")
        lines.append("```")
        for _, line in log_48h[:100]:
            lines.append(line)
        lines.append("```")
        lines.append("</details>")
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Log excerpt (last 100 lines)</summary>")
        lines.append("")
        lines.append("```")
        for _, line in log_48h[-100:]:
            lines.append(line)
        lines.append("```")
        lines.append("</details>")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report produced by `scripts/governance/run_governance_48h_report_on_droplet.py`*")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written: {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
