#!/usr/bin/env python3
"""
Run data-integrity verification on droplet: pull, run audits, check intel/readiness, fetch report.
Writes reports/audit/DATA_INTEGRITY_DROPLET_VERIFICATION.md locally.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Data-integrity verification on droplet")
    ap.add_argument("--expected-commit", type=str, default="", help="If set, report when droplet HEAD does not match this deploy commit")
    ap.add_argument("--since-ts", type=str, default="", help="If set, only count exit_attribution records with timestamp >= this ISO ts for embed check (windowed verification)")
    args = ap.parse_args()
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found. Install paramiko and configure droplet_config.json.", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"
    verdict = "FAIL"
    out_lines = [
        "# Data Integrity — Droplet Verification",
        "",
        f"**Run time (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Git pull",
        "",
        "```",
    ]

    with DropletClient() as c:
        # Use project_dir from client if set
        proj = getattr(c, "project_dir", proj).replace("~", "/root")

        pull_out, pull_err, pull_rc = c._execute_with_cd("git stash push -u -m 'pre-data-integrity-verify' 2>/dev/null || true; git pull origin main 2>&1", timeout=90)
        out_lines.append((pull_out or "").strip()[-2000:])
        out_lines.append("```")
        out_lines.append("")

        rev_out, _, _ = c._execute_with_cd("git rev-parse HEAD 2>/dev/null || echo 'unknown'")
        droplet_commit = (rev_out or "").strip()
        out_lines.append(f"**Commit after pull:** `{droplet_commit}`")
        if getattr(args, "expected_commit", ""):
            exp = args.expected_commit.strip()[:40]
            match = droplet_commit.startswith(exp) or exp in droplet_commit
            out_lines.append(f"**Expected deploy commit:** `{exp}` — **match:** " + ("Yes" if match else "No"))
        out_lines.append("")

        # Always ensure dirs exist; upload required audit scripts (retry each so one failure does not stop rest)
        c._execute(f"mkdir -p {proj}/scripts/audit {proj}/src/contracts {proj}/reports/audit")
        uploads = [
            (REPO / "scripts" / "audit" / "telemetry_contract_audit.py", f"{proj}/scripts/audit/telemetry_contract_audit.py"),
            (REPO / "scripts" / "audit" / "build_telemetry_io_map.py", f"{proj}/scripts/audit/build_telemetry_io_map.py"),
            (REPO / "scripts" / "audit" / "telemetry_integrity_gate.py", f"{proj}/scripts/audit/telemetry_integrity_gate.py"),
            (REPO / "src" / "contracts" / "telemetry_schemas.py", f"{proj}/src/contracts/telemetry_schemas.py"),
            (REPO / "scripts" / "ensure_telemetry_paths.py", f"{proj}/scripts/ensure_telemetry_paths.py"),
            (REPO / "scripts" / "audit_direction_intel_wiring.py", f"{proj}/scripts/audit_direction_intel_wiring.py"),
        ]
        for local, remote in uploads:
            if local.exists():
                try:
                    c.put_file(local, remote)
                except Exception as ex:
                    out_lines.append(f"Upload warning: {local.name} -> {ex}")

        # Run audits
        out_lines.append("## 2. ensure_telemetry_paths.py")
        out_lines.append("")
        out_lines.append("```")
        e_out, e_err, e_rc = c._execute_with_cd("python3 scripts/ensure_telemetry_paths.py 2>&1", timeout=15)
        out_lines.append((e_out or e_err or "").strip())
        out_lines.append("```")
        out_lines.append("")

        out_lines.append("## 3. telemetry_contract_audit.py (last 50 records)")
        out_lines.append("")
        out_lines.append("```")
        t_out, t_err, t_rc = c._execute_with_cd("python3 scripts/audit/telemetry_contract_audit.py --base-dir . --n 50 2>&1", timeout=30)
        out_lines.append((t_out or t_err or "").strip()[:3000])
        out_lines.append("```")
        out_lines.append("")

        out_lines.append("## 4. audit_direction_intel_wiring.py")
        out_lines.append("")
        out_lines.append("```")
        a_out, a_err, a_rc = c._execute_with_cd(
            f"python3 scripts/audit_direction_intel_wiring.py --base-dir . --out reports/audit/DIRECTION_INTEL_WIRING_AUDIT.md 2>&1",
            timeout=60,
        )
        out_lines.append((a_out or a_err or "").strip()[:2500])
        out_lines.append("```")
        out_lines.append("")

        # Checks: intel_snapshot_entry, direction_readiness, exit_attribution direction_intel_embed
        out_lines.append("## 5. File and readiness checks")
        out_lines.append("")

        ls_out, _, _ = c._execute_with_cd("ls -la logs/intel_snapshot_entry.jsonl 2>&1 || echo 'FILE_MISSING'")
        out_lines.append("- **logs/intel_snapshot_entry.jsonl:** " + (ls_out or "").strip().replace("\n", " "))

        wc_out, _, _ = c._execute_with_cd("wc -l logs/intel_snapshot_entry.jsonl 2>/dev/null || echo '0'")
        out_lines.append("- **Line count:** " + (wc_out or "0").strip())

        exit_intel_ex, _, _ = c._execute_with_cd("test -f logs/intel_snapshot_exit.jsonl && echo EXISTS || echo MISSING")
        dir_ev_ex, _, _ = c._execute_with_cd("test -f logs/direction_event.jsonl && echo EXISTS || echo MISSING")
        exit_ev_ex, _, _ = c._execute_with_cd("test -f logs/exit_event.jsonl && echo EXISTS || echo MISSING")
        out_lines.append("- **logs/intel_snapshot_exit.jsonl:** " + (exit_intel_ex or "").strip())
        out_lines.append("- **logs/direction_event.jsonl:** " + (dir_ev_ex or "").strip())
        out_lines.append("- **logs/exit_event.jsonl:** " + (exit_ev_ex or "").strip())

        read_out, _, _ = c._execute_with_cd("cat state/direction_readiness.json 2>/dev/null || echo '{}'")
        out_lines.append("- **state/direction_readiness.json:**")
        out_lines.append("```")
        out_lines.append((read_out or "{}").strip()[:800])
        out_lines.append("```")

        since_ts = (getattr(args, "since_ts", "") or "").strip()[:19]
        if since_ts:
            embed_cmd = (
                "tail -n 100 logs/exit_attribution.jsonl 2>/dev/null | python3 -c \""
                "import sys, json\n"
                "since = '" + since_ts.replace("'", "'\"'\"'") + "'\n"
                "n=0\nm=0\n"
                "for line in sys.stdin:\n"
                "  try:\n"
                "    r=json.loads(line)\n"
                "    ts = (r.get('timestamp') or r.get('entry_timestamp') or '')[:19]\n"
                "    if since and ts < since: continue\n"
                "    n+=1\n"
                "    e=r.get('direction_intel_embed')\n"
                "    if isinstance(e, dict) and e.get('intel_snapshot_entry'): m+=1\n"
                "  except: pass\n"
                "print('last_100_exit_attribution', n, 'with_direction_intel_embed_entry', m)\n"
                "\" 2>&1"
            )
        else:
            embed_cmd = (
                "tail -n 100 logs/exit_attribution.jsonl 2>/dev/null | python3 -c \""
                "import sys, json\n"
                "n=0\nm=0\n"
                "for line in sys.stdin:\n"
                "  try:\n"
                "    r=json.loads(line)\n"
                "    n+=1\n"
                "    e=r.get('direction_intel_embed')\n"
                "    if isinstance(e, dict) and e.get('intel_snapshot_entry'): m+=1\n"
                "  except: pass\n"
                "print('last_100_exit_attribution', n, 'with_direction_intel_embed_entry', m)\n"
                "\" 2>&1"
            )
        embed_out, _, _ = c._execute_with_cd(embed_cmd)
        out_lines.append("")
        out_lines.append("- **Exit attribution (last 100):** " + (embed_out or "").strip())

        out_lines.append("")
        out_lines.append("## 6. Verdict")
        out_lines.append("")
        intel_exists = "FILE_MISSING" not in (ls_out or "")
        embed_str = (embed_out or "").strip()
        has_embed = "with_direction_intel_embed_entry" in embed_str
        try:
            parts = embed_str.split()
            embed_count = int(parts[-1]) if parts else 0
        except Exception:
            embed_count = 0
        has_embed = has_embed and embed_count > 0
        # Existence of other canonical logs (required after first close)
        intel_exit_exists = (exit_intel_ex or "").strip() == "EXISTS"
        direction_event_exists = (dir_ev_ex or "").strip() == "EXISTS"
        exit_event_exists = (exit_ev_ex or "").strip() == "EXISTS"
        telemetry_trades = 0
        try:
            import json as _j
            read_str = (read_out or "{}").strip()
            if read_str and read_str != "{}":
                _d = _j.loads(read_str)
                telemetry_trades = int(_d.get("telemetry_trades") or 0)
        except Exception:
            pass
        failing_gates = []
        if not intel_exists:
            failing_gates.append("logs/intel_snapshot_entry.jsonl must exist after at least one entry")
        if not intel_exit_exists:
            failing_gates.append("logs/intel_snapshot_exit.jsonl must exist after at least one close")
        if not direction_event_exists:
            failing_gates.append("logs/direction_event.jsonl must exist")
        if not exit_event_exists:
            failing_gates.append("logs/exit_event.jsonl must exist")
        if not has_embed:
            failing_gates.append("at least one exit_attribution record must have non-empty direction_intel_embed.intel_snapshot_entry")
        if telemetry_trades == 0 and (read_out or "").strip() and (read_out or "").strip() != "{}":
            failing_gates.append("state/direction_readiness.json must show telemetry_trades > 0 once capture is live")
        verdict = "PASS" if not failing_gates else "FAIL"
        out_lines.append(f"**VERDICT: {verdict}**")
        out_lines.append("")
        out_lines.append("- intel_snapshot_entry.jsonl exists: **" + ("Yes" if intel_exists else "No") + "**")
        out_lines.append("- intel_snapshot_exit.jsonl exists: **" + ("Yes" if intel_exit_exists else "No") + "**")
        out_lines.append("- direction_event.jsonl exists: **" + ("Yes" if direction_event_exists else "No") + "**")
        out_lines.append("- exit_event.jsonl exists: **" + ("Yes" if exit_event_exists else "No") + "**")
        out_lines.append("- At least one exit_attribution with direction_intel_embed.intel_snapshot_entry: **" + ("Yes" if has_embed else "No") + "**")
        out_lines.append("- direction_readiness telemetry_trades > 0: **" + ("Yes" if telemetry_trades > 0 else "No" if (read_out or "").strip() and (read_out or "").strip() != "{}" else "N/A") + "**")
        if failing_gates:
            out_lines.append("")
            out_lines.append("**Failing gates:**")
            for g in failing_gates:
                out_lines.append(f"- {g}")
        out_lines.append("")
        out_lines.append("*Generated by scripts/run_data_integrity_verification_on_droplet.py*")

    report = "\n".join(out_lines)
    dest = REPO / "reports" / "audit" / "DATA_INTEGRITY_DROPLET_VERIFICATION.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote: {dest}", file=sys.stderr)
    try:
        return 0 if verdict == "PASS" else 1
    except NameError:
        return 1


if __name__ == "__main__":
    sys.exit(main())
