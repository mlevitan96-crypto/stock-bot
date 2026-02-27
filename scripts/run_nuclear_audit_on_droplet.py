#!/usr/bin/env python3
"""
Nuclear audit on DROPLET: entries + data + wiring.
Runs all checks via DropletClient in project_dir (e.g. /root/stock-bot).
Writes report bundle to reports/nuclear_audit/<YYYYMMDD>/ (00_summary.md .. 09_verdict.md).
Ends with PASS/FAIL verdict, top 5 blockers, exact next actions.
NO TUNING. NO STRATEGY CHANGES. AUDIT ONLY.

Requires: droplet_config.json (or DROPLET_* env), DropletClient.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE_TAG = datetime.now(timezone.utc).strftime("%Y%m%d")
AUDIT_DIR = REPO / "reports" / "nuclear_audit" / DATE_TAG


def _run(c, command: str, timeout: int = 60) -> tuple[str, str, int]:
    return c._execute_with_cd(command, timeout=timeout)


def _cat(c, remote_path: str, timeout: int = 15) -> str:
    out, _, _ = _run(c, f"cat {remote_path} 2>/dev/null || true", timeout=timeout)
    return out or ""


def _run_audit(client) -> dict:
    """Run all checklist steps; return dict of section -> {out, err, rc, content}."""
    r = {}
    # A) Runtime health
    out_tmux, err, rc = _run(client, "tmux ls 2>/dev/null || echo 'NO_TMUX'", timeout=10)
    r["tmux_ls"] = {"out": out_tmux, "err": err, "rc": rc}
    out_pane, err2, _ = _run(client, "tmux capture-pane -pt stock_bot_paper_run -S -200 2>/dev/null || echo 'NO_PANE'", timeout=10)
    r["tmux_pane"] = {"out": out_pane, "err": err2}
    out_state, _, _ = _run(client, "cat state/live_paper_run_state.json 2>/dev/null || echo '{}'", timeout=10)
    r["state_json"] = {"out": out_state}
    # B) Git + drift
    out_rev, _, rc_rev = _run(client, "git rev-parse HEAD 2>/dev/null", timeout=10)
    out_status, _, _ = _run(client, "git status --short 2>/dev/null", timeout=10)
    out_log, _, _ = _run(client, "git log -20 --oneline 2>/dev/null", timeout=10)
    r["git"] = {"rev": out_rev, "status": out_status, "log": out_log, "rc": rc_rev}
    critical_files = "main.py config/ policy_variants.py board/eod/start_live_paper_run.py"
    out_diff, _, _ = _run(client, f"git diff --name-only HEAD 2>/dev/null; git diff --name-only --cached 2>/dev/null", timeout=10)
    r["git_diff"] = {"out": out_diff}
    # C) Config + env
    env_pattern = "PAPER|TRADING|LIVE|MIN_EXEC_SCORE|MAX_CONCURRENT_POSITIONS|MAX_NEW_POSITIONS_PER_CYCLE|COOLDOWN|MINUTES|GOVERNED_TUNING_CONFIG|DISABLE|LOG_LEVEL"
    out_env, _, _ = _run(client, f"env | grep -E '^({env_pattern})' 2>/dev/null || true", timeout=5)
    _caps_cmd = """python3 -c '
import json, os, sys
sys.path.insert(0, ".")
try:
    from policy_variants import get_live_safety_caps, is_live
    caps = get_live_safety_caps() if is_live() else {}
    print("caps:", json.dumps(caps))
except Exception as e:
    print("error:", e)
' 2>/dev/null"""
    out_caps, _, _ = _run(client, _caps_cmd, timeout=15)
    _config_cmd = """python3 -c '
import os, sys
sys.path.insert(0, ".")
try:
    from main import Config
    print("MIN_EXEC_SCORE:", getattr(Config, "MIN_EXEC_SCORE", "N/A"))
    print("MAX_CONCURRENT_POSITIONS:", getattr(Config, "MAX_CONCURRENT_POSITIONS", "N/A"))
    print("COOLDOWN_MINUTES_PER_TICKER:", getattr(Config, "COOLDOWN_MINUTES_PER_TICKER", "N/A"))
except Exception as e:
    print("error:", e)
' 2>/dev/null"""
    out_config, _, _ = _run(client, _config_cmd, timeout=15)
    r["config"] = {"env": out_env, "caps": out_caps, "config": out_config}
    # D) Data freshness
    out_date, _, _ = _run(client, "date 2>/dev/null; date +%Z 2>/dev/null", timeout=5)
    out_data, _, _ = _run(client, "ls -la data/*.json 2>/dev/null | head -20; ls -la state/*.json 2>/dev/null | head -10", timeout=10)
    out_cache, _, _ = _run(client, "find . -maxdepth 3 -type f -name '*.json' -mmin -60 2>/dev/null | head -30", timeout=10)
    r["data_freshness"] = {"date": out_date, "data_ls": out_data, "recent_cache": out_cache}
    # E) Entry pipeline evidence (logs)
    out_gate, _, _ = _run(client, "tail -n 800 logs/gate.jsonl 2>/dev/null || true", timeout=15)
    out_run, _, _ = _run(client, "tail -n 300 logs/run.jsonl 2>/dev/null || true", timeout=15)
    r["entry_logs"] = {"gate": out_gate, "run": out_run}
    # F) Positions + capacity
    out_pos_state, _, _ = _run(client, "cat state/*.json 2>/dev/null | head -500", timeout=10)
    _pos_cmd = """python3 -c '
import sys
sys.path.insert(0, ".")
try:
    from main import get_api
    api = get_api()
    pos = api.list_positions() if api else []
    print("count:", len(pos))
    for p in (pos or [])[:20]:
        print(getattr(p, "symbol", p), getattr(p, "qty", ""))
except Exception as e:
    print("error:", e)
' 2>/dev/null"""
    out_pos_api, _, _ = _run(client, _pos_cmd, timeout=20)
    r["positions"] = {"state": out_pos_state, "api": out_pos_api}
    # G) Logs + attribution flow
    out_attr_tail, _, _ = _run(client, "tail -n 3 logs/attribution.jsonl 2>/dev/null || echo 'NO_FILE'", timeout=5)
    out_attr_wc, _, _ = _run(client, "wc -l logs/attribution.jsonl 2>/dev/null || echo '0'", timeout=5)
    out_exit_tail, _, _ = _run(client, "tail -n 3 logs/exit_attribution.jsonl 2>/dev/null || echo 'NO_FILE'", timeout=5)
    out_exit_wc, _, _ = _run(client, "wc -l logs/exit_attribution.jsonl 2>/dev/null || echo '0'", timeout=5)
    out_attr_ts, _, _ = _run(client, "tail -n 1 logs/attribution.jsonl 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"ts\",\"\")[:19])' 2>/dev/null || echo 'N/A'", timeout=5)
    out_exit_ts, _, _ = _run(client, "tail -n 1 logs/exit_attribution.jsonl 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); t=d.get(\"ts\",d.get(\"timestamp\",\"\")); print(t[:19] if isinstance(t,str) else \"N/A\")' 2>/dev/null || echo 'N/A'", timeout=5)
    r["attribution"] = {"attr_tail": out_attr_tail, "attr_wc": out_attr_wc, "exit_tail": out_exit_tail, "exit_wc": out_exit_wc, "attr_ts": out_attr_ts, "exit_ts": out_exit_ts}
    # H) Recent errors
    out_err, _, _ = _run(client, "grep -h -E 'ERROR|Traceback|Exception' logs/*.log logs/*.jsonl 2>/dev/null | tail -100 || true", timeout=15)
    out_err_recent, _, _ = _run(client, "grep -h -E 'ERROR|Traceback' logs/run.jsonl logs/worker_debug.log 2>/dev/null | tail -30 || true", timeout=10)
    r["errors"] = {"all": out_err, "recent": out_err_recent}
    return r


def _parse_gate_logs(gate_text: str) -> dict:
    """Parse gate.jsonl for cycle_summary and rejection reasons. Return candidate_count, selected_count, gate_counts, rejection_reasons."""
    result = {"cycle_summaries": [], "gate_counts_agg": Counter(), "rejection_reasons": Counter(), "candidate_count": None, "selected_count": None}
    for line in gate_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = d.get("msg") or d.get("message") or ""
        if msg == "cycle_summary":
            considered = d.get("considered", 0)
            orders = d.get("orders", 0)
            result["cycle_summaries"].append({"considered": considered, "orders": orders, "gate_counts": d.get("gate_counts") or {}})
            if result["candidate_count"] is None and considered is not None:
                result["candidate_count"] = considered
            if result["selected_count"] is None and orders is not None:
                result["selected_count"] = orders
            for k, v in (d.get("gate_counts") or {}).items():
                if isinstance(v, (int, float)):
                    result["gate_counts_agg"][k] += int(v)
        else:
            if msg and msg != "cycle_summary":
                result["rejection_reasons"][msg] += 1
    return result


def _write_reports(data: dict, out_dir: Path) -> None:
    """Write 00_summary.md through 09_verdict.md."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # 01 Runtime health
    t = data["tmux_ls"]["out"] or ""
    pane = (data["tmux_pane"]["out"] or "")[:4000]
    state_raw = data["state_json"]["out"] or "{}"
    state_ok = "stock_bot_paper_run" in t
    try:
        state_obj = json.loads(state_raw) if state_raw.strip() else {}
        gov = (state_obj.get("details") or {}).get("governed_tuning_config") or state_obj.get("governed_tuning_config") or ""
        overlay_ok = (gov == "" or gov is None)
    except Exception:
        overlay_ok = False
    lines_01 = [
        "# 01 Runtime health",
        "",
        "## tmux ls",
        "```", t.strip(), "```",
        "",
        "## tmux capture-pane (stock_bot_paper_run, last 200 lines)",
        "```", pane, "```",
        "",
        "## state/live_paper_run_state.json",
        "```", state_raw[:3000], "```",
        "",
        "## Checks",
        f"- Tmux session present: **{state_ok}**",
        f"- No GOVERNED_TUNING_CONFIG / no overlay in state: **{overlay_ok}**",
    ]
    (out_dir / "01_runtime_health.md").write_text("\n".join(lines_01), encoding="utf-8")

    # 02 Git + drift
    rev = (data["git"]["rev"] or "").strip()
    status = (data["git"]["status"] or "").strip()
    log = (data["git"]["log"] or "").strip()
    diff = (data["git_diff"]["out"] or "").strip()
    lines_02 = [
        "# 02 Git and drift",
        "",
        "## git rev-parse HEAD",
        rev or "N/A",
        "",
        "## git status --short",
        "```", status[:2000], "```",
        "",
        "## git log -20 --oneline",
        "```", log, "```",
        "",
        "## Local modifications (git diff name-only)",
        "```", diff[:1500], "```",
    ]
    (out_dir / "02_git_and_drift.md").write_text("\n".join(lines_02), encoding="utf-8")

    # 03 Config + env
    env = (data["config"]["env"] or "").strip()
    caps = (data["config"]["caps"] or "").strip()
    cfg = (data["config"]["config"] or "").strip()
    lines_03 = [
        "# 03 Config and env",
        "",
        "## Relevant env vars",
        "```", env or "none captured", "```",
        "",
        "## Live safety caps (policy_variants)",
        "```", caps, "```",
        "",
        "## Key config (Config)",
        "```", cfg, "```",
        "",
        "## Disable entries check",
        "Look for DISABLE_ENTRIES, MAX_CONCURRENT_POSITIONS=0, MIN_EXEC_SCORE very high, or paper=false.",
    ]
    (out_dir / "03_config_and_env.md").write_text("\n".join(lines_03), encoding="utf-8")

    # 04 Data freshness
    date_out = (data["data_freshness"]["date"] or "").strip()
    data_ls = (data["data_freshness"]["data_ls"] or "").strip()
    cache = (data["data_freshness"]["recent_cache"] or "").strip()
    lines_04 = [
        "# 04 Data freshness",
        "",
        "## System date / timezone",
        "```", date_out, "```",
        "",
        "## data/ and state/ (ls -la)",
        "```", data_ls, "```",
        "",
        "## Files modified in last 60 min",
        "```", cache, "```",
    ]
    (out_dir / "04_data_freshness.md").write_text("\n".join(lines_04), encoding="utf-8")

    # 05 Entry pipeline evidence
    gate_text = data["entry_logs"].get("gate") or ""
    entry_parsed = _parse_gate_logs(gate_text)
    summaries = entry_parsed["cycle_summaries"]
    gate_counts = dict(entry_parsed["gate_counts_agg"].most_common(20))
    rejection = dict(entry_parsed["rejection_reasons"].most_common(15))
    candidate_count = entry_parsed["candidate_count"]
    selected_count = entry_parsed["selected_count"]
    if candidate_count is None and summaries:
        candidate_count = summaries[-1].get("considered", 0) if summaries else 0
    if selected_count is None and summaries:
        selected_count = summaries[-1].get("orders", 0) if summaries else 0
    lines_05 = [
        "# 05 Entry pipeline evidence",
        "",
        "## From logs/gate.jsonl (parsed)",
        "",
        f"- **candidate_count (considered last cycle):** {candidate_count}",
        f"- **selected_count (orders last cycle):** {selected_count}",
        "",
        "## Last cycle_summary entries (up to 5)",
        "```",
        json.dumps(summaries[-5:] if len(summaries) > 5 else summaries, indent=2),
        "```",
        "",
        "## Aggregated gate_counts (top 20)",
        "```", json.dumps(gate_counts, indent=2), "```",
        "",
        "## Top rejection reasons (msg != cycle_summary)",
        "```", json.dumps(rejection, indent=2), "```",
    ]
    (out_dir / "05_entry_pipeline_evidence.md").write_text("\n".join(lines_05), encoding="utf-8")

    # 06 Positions + capacity
    pos_state = (data["positions"]["state"] or "").strip()
    pos_api = (data["positions"]["api"] or "").strip()
    lines_06 = [
        "# 06 Positions and capacity",
        "",
        "## state/*.json (positions from state)",
        "```", pos_state[:2500], "```",
        "",
        "## API list_positions (paper)",
        "```", pos_api, "```",
    ]
    (out_dir / "06_positions_and_capacity.md").write_text("\n".join(lines_06), encoding="utf-8")

    # 07 Logs and attribution flow
    attr_ts = (data["attribution"].get("attr_ts") or "").strip()
    exit_ts = (data["attribution"].get("exit_ts") or "").strip()
    attr_wc = (data["attribution"].get("attr_wc") or "").strip()
    exit_wc = (data["attribution"].get("exit_wc") or "").strip()
    attr_tail = (data["attribution"].get("attr_tail") or "").strip()
    exit_tail = (data["attribution"].get("exit_tail") or "").strip()
    lines_07 = [
        "# 07 Logs and attribution flow",
        "",
        "## attribution.jsonl",
        f"- Line count: {attr_wc}",
        f"- Last record ts: {attr_ts}",
        "Last 3 lines (sample):",
        "```", attr_tail[:1500], "```",
        "",
        "## exit_attribution.jsonl",
        f"- Line count: {exit_wc}",
        f"- Last record ts: {exit_ts}",
        "Last 3 lines (sample):",
        "```", exit_tail[:1500], "```",
        "",
        "## Join keys",
        "Expect trade_id (or equivalent) on both sides for join.",
    ]
    (out_dir / "07_logs_and_attribution_flow.md").write_text("\n".join(lines_07), encoding="utf-8")

    # 08 Recent errors
    err_all = (data["errors"].get("all") or "").strip()
    err_recent = (data["errors"].get("recent") or "").strip()
    lines_08 = [
        "# 08 Recent errors",
        "",
        "## Last 100 ERROR/Traceback/Exception (logs)",
        "```", err_all[:4000], "```",
        "",
        "## Last 30 from run.jsonl / worker_debug.log",
        "```", err_recent[:2000], "```",
    ]
    (out_dir / "08_recent_errors.md").write_text("\n".join(lines_08), encoding="utf-8")

    # Verdict
    blockers = []
    if not state_ok:
        blockers.append("Paper process not running (tmux session stock_bot_paper_run missing)")
    if not overlay_ok:
        blockers.append("State has GOVERNED_TUNING_CONFIG/overlay (expected clean paper run)")
    if "DISABLE" in (env or "").upper() and "ENTRY" in (env or "").upper():
        blockers.append("Config/env suggests entries disabled")
    if attr_ts == "N/A" or (attr_wc and attr_wc.strip().startswith("0 ")):
        blockers.append("attribution.jsonl empty or not recently appended")
    if exit_ts == "N/A" or (exit_wc and exit_wc.strip().startswith("0 ")):
        blockers.append("exit_attribution.jsonl empty or not recently appended")
    if candidate_count is not None and candidate_count == 0 and not gate_counts and not rejection:
        blockers.append("Entry pipeline produced 0 candidates with no clear gate/rejection evidence")
    if err_recent and ("Traceback" in err_recent or "Exception:" in err_recent):
        blockers.append("Recent exceptions in logs (check 08_recent_errors.md)")
    # Capacity: MAX_CONCURRENT_POSITIONS or caps
    if "MAX_CONCURRENT_POSITIONS" in (cfg or "") and " 0" in (cfg or ""):
        blockers.append("MAX_CONCURRENT_POSITIONS is 0")
    if "max_new_positions_per_cycle" in (caps or "").lower() and "0" in caps:
        blockers.append("max_new_positions_per_cycle may be 0")

    verdict = "FAIL" if blockers else "PASS"
    if verdict == "PASS":
        if candidate_count == 0 and (gate_counts or rejection):
            reason = "0 candidates with clear gating (no_clusters or gate_counts/rejection reasons)"
        elif candidate_count and candidate_count > 0 and (selected_count or 0) == 0:
            reason = "Candidates exist but selected_count=0 (gates blocking; see gate_counts)"
        else:
            reason = "Runtime healthy; data and attribution flowing; entry pipeline has evidence."
    else:
        reason = "; ".join(blockers[:3]) if blockers else "Unknown"

    top5 = (blockers + ["(none)"] * 5)[:5]
    next_actions = []
    if "Paper process not running" in str(blockers):
        next_actions.append("Start paper run: board/eod/start_live_paper_run.py --date $(date +%Y-%m-%d) (proof: 01_runtime_health.md)")
    if "GOVERNED_TUNING_CONFIG" in str(blockers):
        next_actions.append("Restart paper with no overlay; confirm state has no governed_tuning_config (proof: 01_runtime_health.md)")
    if "attribution" in str(blockers).lower():
        next_actions.append("Verify logging path and disk space; confirm main loop writes to logs/attribution.jsonl and exit_attribution (proof: 07_logs_and_attribution_flow.md)")
    if "0 candidates" in str(blockers) or "Entry pipeline" in str(blockers):
        next_actions.append("Inspect gate_counts and rejection reasons in 05_entry_pipeline_evidence.md; fix config or data if score/threshold/caps block all entries")
    if "exceptions" in str(blockers).lower() or "Traceback" in str(blockers):
        next_actions.append("Fix repeated exceptions (proof: 08_recent_errors.md); restart paper after fix")
    if "MAX_CONCURRENT_POSITIONS" in str(blockers) or "max_new_positions" in str(blockers):
        next_actions.append("Set MAX_CONCURRENT_POSITIONS and max_new_positions_per_cycle to allow entries (proof: 03_config_and_env.md)")
    next_actions = (next_actions + ["Re-run nuclear audit after fixes."])[:5]

    lines_09 = [
        "# 09 Verdict",
        "",
        f"## Verdict: **{verdict}**",
        "",
        "## Why no open trades? (single best explanation)",
        reason,
        "",
        "## Top 5 blockers",
        *[f"{i+1}. {b}" for i, b in enumerate(top5)],
        "",
        "## Exact next actions (max 5)",
        *[f"{i+1}. {a}" for i, a in enumerate(next_actions)],
    ]
    (out_dir / "09_verdict.md").write_text("\n".join(lines_09), encoding="utf-8")

    # 00 Summary
    lines_00 = [
        "# 00 Summary",
        "",
        f"**Date:** {DATE_TAG}",
        f"**Verdict:** {verdict}",
        "",
        "## One-line explanation",
        reason,
        "",
        "## Blocker count",
        str(len(blockers)),
        "",
        "## Report sections",
        "1. 01_runtime_health.md",
        "2. 02_git_and_drift.md",
        "3. 03_config_and_env.md",
        "4. 04_data_freshness.md",
        "5. 05_entry_pipeline_evidence.md",
        "6. 06_positions_and_capacity.md",
        "7. 07_logs_and_attribution_flow.md",
        "8. 08_recent_errors.md",
        "9. 09_verdict.md",
    ]
    (out_dir / "00_summary.md").write_text("\n".join(lines_00), encoding="utf-8")

    return {"verdict": verdict, "reason": reason, "blockers": blockers, "next_actions": next_actions}


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: {e}. Need droplet_config.json and DropletClient.", file=sys.stderr)
        return 1

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Running nuclear audit on droplet; report bundle: {AUDIT_DIR}")

    with DropletClient() as c:
        data = _run_audit(c)
    result = _write_reports(data, AUDIT_DIR)

    print("\n=== NUCLEAR AUDIT RESULT ===")
    print(f"Verdict: {result['verdict']}")
    print(f"Why no open trades: {result['reason']}")
    print("Top 5 blockers:", result.get("blockers", [])[:5])
    print("Next actions:", result.get("next_actions", [])[:5])
    print(f"\nReport bundle: {AUDIT_DIR}")

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
