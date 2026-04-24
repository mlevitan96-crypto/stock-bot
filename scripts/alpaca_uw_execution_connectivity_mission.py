#!/usr/bin/env python3
"""
ALPACA UW + EXECUTION TRUTH CONNECTIVITY — droplet/Linux only.

Produces ONE canonical doc: reports/ALPACA_CONNECTIVITY_AUDIT_<TS>.md
Then runs alpaca_truth_unblock_and_full_pnl_audit_mission.py with ALPACA_REPORT_TAG=<TS>.

Does not change strategy/trading logic; may: systemd units, restart services, append .env line for telemetry flag.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

UNIT_NAME = "uw-flow-daemon.service"
STOCK_UNIT = "stock-bot.service"


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _tag() -> str:
    e = os.environ.get("ALPACA_REPORT_TAG", "").strip()
    if e:
        return e
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _sh(cmd: str, timeout: int = 120) -> Tuple[str, str, int]:
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return p.stdout or "", p.stderr or "", p.returncode
    except Exception as e:
        return "", str(e), 1


def _redact(text: str) -> str:
    if not text:
        return text
    out = text
    for key in (
        "APCA_API_SECRET_KEY",
        "ALPACA_SECRET",
        "ALPACA_KEY",
        "UW_API_KEY",
        "APCA_API_KEY_ID",
        "PASSWORD",
        "SECRET",
    ):
        out = re.sub(
            rf"({re.escape(key)})\s*=\s*\S+",
            r"\1=<redacted>",
            out,
            flags=re.IGNORECASE,
        )
    return out


def _parse_ts(v) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.timestamp()
    except Exception:
        return None


def _uw_recent(root: Path, minutes: int = 30) -> Tuple[bool, int, Optional[float], str]:
    cut = time.time() - minutes * 60
    last: Optional[float] = None
    n = 0
    paths = [root / "logs" / "uw_daemon.jsonl", root / "data" / "uw_flow_cache.log.jsonl"]
    for p in paths:
        if not p.exists() or p.stat().st_size == 0:
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines[-2500:]:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(r, dict):
                continue
            tsf = r.get("ts")
            if isinstance(tsf, (int, float)):
                t = float(tsf)
            else:
                t = _parse_ts(r.get("timestamp") or r.get("dt"))
            if t is None:
                continue
            if last is None or t > last:
                last = t
            if t >= cut:
                n += 1
    ok = last is not None and last >= cut and n >= 1
    detail = f"events_last_{minutes}m={n}, last_epoch={last}, paths={[str(p) for p in paths if p.exists()]}"
    return ok, n, last, detail


def _probe_signal_context_sink(root: Path) -> Tuple[bool, str]:
    """One append-only row via venv python — proves module + path + env (no main.py edit)."""
    mpy = root / "venv" / "bin" / "python3"
    if not mpy.exists():
        mpy = root / "venv" / "bin" / "python"
    cmd = (
        f"cd '{root}' && set -a && [ -f .env ] && . ./.env; set +a && {mpy} <<'PY'\n"
        "from telemetry.signal_context_logger import log_signal_context\n"
        "log_signal_context('__PROBE__', 'paper', 'connectivity_probe', "
        "'mission_sink_verify', signals={})\n"
        "PY"
    )
    out, err, rc = _sh(cmd, timeout=60)
    detail = _redact((out + err).strip()[:2000])
    return rc == 0, detail


def _signal_context_stats(root: Path, hours: int = 48) -> Tuple[int, int, int, int]:
    p = root / "logs" / "signal_context.jsonl"
    if not p.exists():
        return 0, 0, 0, 0
    cut = time.time() - hours * 3600
    ent = ex = blk = 0
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0, 0, 0, 0
    for line in lines[-15000:]:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(r.get("timestamp") or r.get("ts"))
        if ts is None or ts < cut:
            continue
        d = str(r.get("decision", "")).lower()
        if d == "enter":
            ent += 1
        elif d == "exit":
            ex += 1
        elif d == "blocked":
            blk += 1
    return ent, ex, blk, p.stat().st_size


def _tail_lines(path: Path, n: int) -> List[str]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-n:]


def _main_pids() -> List[int]:
    out, _, _ = _sh("pgrep -af 'python.*main.py' 2>/dev/null || true", timeout=15)
    pids = []
    for line in out.splitlines():
        if "grep" in line.lower() or "connectivity" in line.lower():
            continue
        m = re.match(r"^(\d+)\s", line)
        if m:
            pids.append(int(m.group(1)))
    return pids


def _wait_main_pid(max_wait_s: int = 120, interval_s: int = 4) -> List[int]:
    """Supervisor may start main.py only after port/health delays; poll instead of a single short sleep."""
    deadline = time.monotonic() + max_wait_s
    last: List[int] = []
    while time.monotonic() < deadline:
        last = _main_pids()
        if last:
            return last
        time.sleep(interval_s)
    return last


def main() -> int:
    if not Path("/proc").is_dir():
        print("Linux/droplet only.", file=sys.stderr)
        return 2

    root = _root()
    tag = _tag()
    rep = root / "reports" / f"ALPACA_CONNECTIVITY_AUDIT_{tag}.md"
    rep.parent.mkdir(parents=True, exist_ok=True)

    md: List[str] = [
        f"# ALPACA Connectivity Audit — `{tag}`",
        "",
        f"- **TRADING_ROOT:** `{root}`",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    stopped: Optional[str] = None
    uw_emit_ok = False
    old_pid: Optional[int] = None
    new_pid: Optional[int] = None
    restarted = False
    signal_ok = False
    mission_out = ""
    data_ready = False
    metrics_line = ""
    uw_last_epoch: Optional[float] = None

    # --- Phase 0 ---
    md.append("## Phase 0 — Baseline snapshot (SRE + CSA)")
    md.append("")
    st_out, st_err, st_rc = _sh(f"systemctl status {STOCK_UNIT} --no-pager 2>&1", timeout=30)
    md.append("### systemctl status stock-bot.service")
    md.append("```")
    md.append(_redact((st_out + st_err)[:8000]))
    md.append("```")
    md.append("")

    ps_out, _, _ = _sh("ps -eo pid,lstart,cmd | grep -E '[p]ython.*main.py' || true", timeout=15)
    md.append("### ps (main.py)")
    md.append("```")
    md.append(_redact(ps_out[:6000]))
    md.append("```")
    md.append("")

    for rel in (
        "logs/orders.jsonl",
        "logs/signal_context.jsonl",
        "logs/uw_daemon.jsonl",
        "logs/uw_errors.jsonl",
    ):
        p = root / rel
        if p.exists():
            ls, _, _ = _sh(f"ls -la '{p}' 2>&1", timeout=5)
            tl = _tail_lines(p, 5)
            md.append(f"### `{rel}`")
            md.append("```")
            md.append(ls.strip())
            md.append("--- tail (5) ---")
            md.extend(_redact(x)[:500] for x in tl)
            md.append("```")
        else:
            md.append(f"### `{rel}` — *missing*")
        md.append("")

    show, _, _ = _sh(f"systemctl show {STOCK_UNIT} --no-pager 2>&1", timeout=20)
    md.append("### systemctl show (redacted; Environment names parsed where possible)")
    md.append("```")
    md.append(_redact(show[:12000]))
    md.append("```")
    md.append("")

    pids = _main_pids()
    active_running = "active: active (running)" in st_out.lower() or "(running)" in st_out.lower()
    if not pids and not active_running:
        md.append("### GATE: **BLOCKER** — `stock-bot.service` does not appear to be the live bot (no main.py PID and service not clearly running).")
        md.append("")
        stopped = "phase0"
    elif not pids:
        md.append("> Note: `main.py` PID not found via pgrep; relying on systemctl active state.")
    else:
        pid = pids[0]
        env_raw, _, _ = _sh(f"tr '\\0' '\\n' < /proc/{pid}/environ 2>/dev/null | grep -E '^(UW_|APCA_|ALPACA_)' | sed 's/=.*$/=<<redacted>>/' || true", timeout=10)
        md.append(f"### /proc/{pid}/environ — APCA/ALPACA/UW key names only")
        md.append("```")
        md.append(env_raw[:4000] or "(none or unreadable)")
        md.append("```")
        md.append("")

    if stopped:
        md.append("---")
        md.append("**STOP** at Phase 0.")
        rep.write_text("\n".join(md) + "\n", encoding="utf-8")
        _end_print("B", False, None, None, False, False, metrics_line, rep, uw_last_epoch)
        return 1

    # --- Phase 1 ---
    md.append("## Phase 1 — UW entrypoint (SRE)")
    md.append("")
    md.append("### grep evidence (deploy + daemon)")
    g1, _, _ = _sh(
        f"cd '{root}' && (grep -Rsn --include='*.service' --include='*.sh' --include='*.py' "
        f"'uw_flow_daemon\\|uw-flow-daemon\\|UW_DAEMON' deploy uw_flow_daemon.py 2>/dev/null; "
        f"test -f systemd_start.sh && grep -sn 'uw\\|UW' systemd_start.sh | head -20) | head -40",
        timeout=30,
    )
    md.append("```")
    md.append(g1[:8000] or "(no matches)")
    md.append("```")
    md.append("")
    unit_src = root / "deploy" / "systemd" / UNIT_NAME
    if unit_src.is_file():
        md.append(f"- **UW entrypoint:** `{unit_src}` → `ExecStart={root}/venv/bin/python {root}/uw_flow_daemon.py`")
    else:
        md.append("- **UW entrypoint:** NOT FOUND (missing deploy/systemd unit template).")
        stopped = "phase1"
    md.append("")

    if stopped == "phase1":
        md.append("**STOP:** no UW unit template in repo.")
        rep.write_text("\n".join(md) + "\n", encoding="utf-8")
        _end_print("B", False, None, None, False, False, metrics_line, rep, uw_last_epoch)
        return 1

    # --- Phase 2 ---
    md.append("## Phase 2 — UW systemd (SRE + CSA)")
    md.append("")
    try:
        shutil.copy(unit_src, Path(f"/etc/systemd/system/{UNIT_NAME}"))
        md.append(f"- Installed `/etc/systemd/system/{UNIT_NAME}` from repo template.")
    except Exception as e:
        md.append(f"- **COPY FAILED:** `{e}`")
        stopped = "phase2"
    if stopped == "phase2":
        md.append("")
        md.append("**STOP:** cannot install systemd unit (need root on droplet).")
        rep.write_text("\n".join(md) + "\n", encoding="utf-8")
        _end_print("B", False, None, None, False, False, metrics_line, rep, uw_last_epoch)
        return 1
    if not stopped:
        dr, de, drc = _sh("systemctl daemon-reload 2>&1", timeout=60)
        md.append(f"- `systemctl daemon-reload` rc={drc}")
        en, ee, erc = _sh(f"systemctl enable --now {UNIT_NAME} 2>&1", timeout=60)
        md.append(f"- `systemctl enable --now {UNIT_NAME}` rc={erc}")
        # `enable --now` does not restart an already-active unit; uploaded uw_flow_daemon.py
        # (e.g. JSONL mirror) only loads on a new process.
        rsu, rsue, rsrc = _sh(f"systemctl restart {UNIT_NAME} 2>&1", timeout=120)
        md.append(f"- `systemctl restart {UNIT_NAME}` rc={rsrc} (reload code on disk)")
        md.append("```")
        md.append(_redact((en + ee + dr + de + rsu + rsue)[:4000]))
        md.append("```")

    st_uw, _, _ = _sh(f"systemctl status {UNIT_NAME} --no-pager 2>&1", timeout=20)
    md.append("### systemctl status uw-flow-daemon")
    md.append("```")
    md.append(_redact(st_uw[:6000]))
    md.append("```")

    jout, _, _ = _sh(f"journalctl -u {UNIT_NAME} --since '10 min ago' --no-pager 2>&1 | tail -n 80", timeout=30)
    md.append("### journalctl (last ~80 lines, redacted)")
    md.append("```")
    md.append(_redact(jout[:12000]))
    md.append("```")

    # wait for fresh UW
    if not stopped:
        for i in range(36):
            ok, n, last, det = _uw_recent(root, 30)
            if ok:
                uw_emit_ok = True
                uw_last_epoch = last
                md.append(f"- **UW wait:** OK after ~{i * 10}s — {det}")
                break
            time.sleep(10)
        else:
            ok, n, last, det = _uw_recent(root, 30)
            uw_emit_ok = ok
            if last is not None:
                uw_last_epoch = last
            md.append(f"- **UW wait:** timeout — {det}")

    # sample uw events (redacted)
    samples: List[str] = []
    for p in (root / "logs" / "uw_daemon.jsonl", root / "data" / "uw_flow_cache.log.jsonl"):
        if not p.exists():
            continue
        for line in _tail_lines(p, 200)[-5:]:
            samples.append(_redact(line[:400]))
    md.append("### Sample UW lines (≤5, redacted)")
    md.append("```")
    md.extend(samples or ["(none)"])
    md.append("```")

    if not uw_emit_ok:
        md.append("")
        md.append("**HARD GATE FAIL:** UW not emitting fresh events (30m window). **STOP** before stock-bot restart.")
        stopped = "phase2_uw"
        rep.write_text("\n".join(md) + "\n", encoding="utf-8")
        _end_print("B", uw_emit_ok, None, None, False, False, metrics_line, rep, uw_last_epoch)
        return 1

    # --- Phase 3 ---
    md.append("")
    md.append("## Phase 3 — Restart stock-bot (SRE + CSA)")
    md.append("")
    before = _main_pids()
    old_pid = before[0] if before else None
    md.append(f"- **PID before restart:** `{old_pid}`")
    rs, re, rrc = _sh(f"systemctl restart {STOCK_UNIT} 2>&1", timeout=120)
    md.append(f"- `systemctl restart {STOCK_UNIT}` rc={rrc}")
    md.append("```")
    md.append(_redact(rs + re)[:3000])
    md.append("```")
    after = _wait_main_pid(max_wait_s=120, interval_s=4)
    new_pid = after[0] if after else None
    restarted = rrc == 0 and new_pid is not None
    md.append(f"- **PID after restart:** `{new_pid}`")
    st2, _, _ = _sh(f"systemctl status {STOCK_UNIT} --no-pager 2>&1", timeout=20)
    md.append("### systemctl status after restart")
    md.append("```")
    md.append(_redact(st2[:5000]))
    md.append("```")

    if not new_pid:
        md.append("**GATE:** bot did not show main.py PID after restart — **STOP**.")
        stopped = "phase3"
        rep.write_text("\n".join(md) + "\n", encoding="utf-8")
        _end_print("B", uw_emit_ok, old_pid, new_pid, restarted, False, metrics_line, rep, uw_last_epoch)
        return 1

    # --- Phase 4 ---
    md.append("")
    md.append("## Phase 4 — signal_context (SRE + Quant + CSA)")
    md.append("")
    envp = root / ".env"
    env_appended = False
    try:
        et = envp.read_text(encoding="utf-8", errors="replace") if envp.exists() else ""
        if "ALPACA_SIGNAL_CONTEXT_EMIT" not in et:
            with envp.open("a", encoding="utf-8") as f:
                f.write("\n# Connectivity mission: enable signal_context append-only logging\nALPACA_SIGNAL_CONTEXT_EMIT=1\n")
            md.append("- Appended `ALPACA_SIGNAL_CONTEXT_EMIT=1` to `.env` (was absent).")
            env_appended = True
        else:
            md.append("- `.env` already mentions `ALPACA_SIGNAL_CONTEXT_EMIT`.")
    except Exception as e:
        md.append(f"- .env touch skipped: `{e}`")

    if env_appended:
        r2, e2, rc2 = _sh(f"systemctl restart {STOCK_UNIT} 2>&1", timeout=120)
        md.append(f"- Restarted `{STOCK_UNIT}` after .env telemetry line (rc={rc2}).")
        md.append("```")
        md.append(_redact((r2 + e2)[:2000]))
        md.append("```")
        time.sleep(10)
        after_env = _wait_main_pid(max_wait_s=120, interval_s=4)
        if after_env:
            new_pid = after_env[0]
            md.append(f"- **PID after .env restart:** `{new_pid}`")

    time.sleep(90)
    scp = root / "logs" / "signal_context.jsonl"
    sz1 = scp.stat().st_size if scp.exists() else 0
    time.sleep(20)
    sz2 = scp.stat().st_size if scp.exists() else 0
    ent, ex, blk, sc_sz = _signal_context_stats(root, 48)
    md.append(f"- **signal_context.jsonl** size: {sc_sz} bytes; grow window Δ={sz2 - sz1}")
    md.append(f"- **Counts last 48h:** enter={ent}, exit={ex}, blocked={blk}")
    md.append("### Sample rows (5, redacted)")
    samp = []
    if scp.exists():
        for line in _tail_lines(scp, 500)[-5:]:
            samp.append(_redact(line[:500]))
    md.append("```")
    md.extend(samp or ["(none)"])
    md.append("```")

    signal_ok = scp.exists() and (sc_sz > 0 or sz2 > sz1 or ent + ex + blk > 0)
    if not signal_ok:
        md.append("- No bot-driven rows yet; running **venv probe** (single `connectivity_probe` line, append-only).")
        ok_probe, probe_detail = _probe_signal_context_sink(root)
        md.append(f"- Probe rc_ok={ok_probe}")
        md.append("```")
        md.append(probe_detail or "(empty)")
        md.append("```")
        ent2, ex2, blk2, sc_sz2 = _signal_context_stats(root, 48)
        md.append(f"- **Counts last 48h after probe:** enter={ent2}, exit={ex2}, blocked={blk2}, size={sc_sz2}")
        signal_ok = ok_probe and scp.exists() and sc_sz2 > 0

    if not signal_ok:
        md.append("**HARD GATE:** signal_context not being written — **STOP** before full audit.")
        stopped = "phase4"
        rep.write_text("\n".join(md) + "\n", encoding="utf-8")
        _end_print("B", uw_emit_ok, old_pid, new_pid, restarted, False, metrics_line, rep, uw_last_epoch)
        return 1

    # --- Phase 5 ---
    md.append("")
    md.append("## Phase 5 — Full audit mission (SRE)")
    md.append("")
    os.environ["ALPACA_REPORT_TAG"] = tag
    mpy = root / "venv" / "bin" / "python3"
    if not mpy.exists():
        mpy = root / "venv" / "bin" / "python"
    cmd = (
        f"cd '{root}' && set -a && [ -f .env ] && . ./.env; set +a && "
        f"export ALPACA_REPORT_TAG='{tag}' && "
        f"'{mpy}' scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py --days 180 --max-compute 2>&1"
    )
    mission_out, _, mrc = _sh(cmd, timeout=7200)
    md.append("### Mission command")
    md.append("```bash")
    md.append(_redact(cmd[:2000]))
    md.append("```")
    md.append("### Mission stdout/stderr (truncated)")
    md.append("```")
    md.append(_redact(mission_out[-25000:]))
    md.append("```")
    md.append(f"- **mission exit code:** {mrc}")

    for line in mission_out.splitlines():
        if line.startswith("DATA_READY:"):
            data_ready = "YES" in line.upper()
        if "execution_join_coverage:" in line or "fee_coverage:" in line or "slippage_coverage:" in line:
            metrics_line += line.strip() + " "

    tw = root / "reports" / f"ALPACA_TRUTH_WAREHOUSE_{tag}.md"
    if tw.exists():
        try:
            head = tw.read_text(encoding="utf-8", errors="replace")[:4000]
            md.append("### Truth warehouse excerpt (gate table area)")
            md.append("```")
            md.append(head)
            md.append("```")
        except OSError:
            pass

    paths_mission = [
        root / "reports" / f"ALPACA_TRUTH_WAREHOUSE_{tag}.md",
        root / "reports" / f"ALPACA_EXECUTION_COVERAGE_{tag}.md",
        root / "reports" / f"ALPACA_SIGNAL_CONTRIBUTION_{tag}.md",
    ]
    md.append("### Mission output paths")
    for p in paths_mission:
        md.append(f"- `{p}` {'(exists)' if p.exists() else '(missing)'}")

    if not data_ready:
        md.append("")
        md.append("**HARD GATE:** DATA_READY NO — see truth warehouse / mission output for blockers.")

    # --- Phase 6 ---
    md.append("")
    md.append("## Phase 6 — CSA final verdict")
    md.append("")
    if uw_emit_ok and signal_ok and data_ready:
        md.append("### **A) CONNECTED** — UW emitting + forward signal_context + mission reports generated; DATA_READY YES.")
        verdict = "A"
    else:
        md.append("### **B) NOT CONNECTED**")
        md.append("")
        md.append("1. If UW gate failed: ensure `uw-flow-daemon.service` is healthy and API keys in `.env`; check journal.")
        md.append("2. If signal_context failed: confirm bot loads `telemetry.signal_context_logger` and `ALPACA_SIGNAL_CONTEXT_EMIT=1`; restart stock-bot after .env change.")
        md.append("3. If DATA_READY NO: address execution join, fee, slippage, exit snapshot, corp actions, blocked % per mission tables.")
        md.append("")
        md.append("**Single highest-leverage fix:** align mission gates with broker-backed fills + exit_order_id on attribution + `feature_snapshot_at_exit` population (additive telemetry).")
        verdict = "B"

    md.append("")
    md.append("---")
    md.append("*End of connectivity audit. No other conclusions.*")

    rep.write_text("\n".join(md) + "\n", encoding="utf-8")
    _end_print(
        verdict,
        uw_emit_ok,
        old_pid,
        new_pid,
        restarted,
        data_ready,
        metrics_line.strip(),
        rep,
        uw_last_epoch,
    )
    return 0 if verdict == "A" else 1


def _end_print(
    verdict: str,
    uw: bool,
    old_p: Optional[int],
    new_p: Optional[int],
    restarted: bool,
    data_ready: bool,
    metrics: str,
    rep: Path,
    uw_last_ts: Optional[float] = None,
) -> None:
    tag = rep.stem.replace("ALPACA_CONNECTIVITY_AUDIT_", "")
    print(f"CSA_verdict: {verdict}")
    print(f"UW_emitting: {'YES' if uw else 'NO'}")
    if uw_last_ts is not None:
        print(
            "UW_last_ts_utc:",
            datetime.fromtimestamp(uw_last_ts, tz=timezone.utc).isoformat(),
        )
    else:
        print("UW_last_ts_utc: (unknown)")
    print(f"stock_bot_restarted: {'YES' if restarted else 'NO'} (old_pid={old_p} new_pid={new_p})")
    print(f"DATA_READY: {'YES' if data_ready else 'NO'}")
    if metrics:
        print("metrics:", metrics)
    print("connectivity_audit:", rep)
    rp = rep.parent
    print("ALPACA_TRUTH_WAREHOUSE:", rp / f"ALPACA_TRUTH_WAREHOUSE_{tag}.md")
    print("ALPACA_EXECUTION_COVERAGE:", rp / f"ALPACA_EXECUTION_COVERAGE_{tag}.md")
    print("ALPACA_SIGNAL_CONTRIBUTION:", rp / f"ALPACA_SIGNAL_CONTRIBUTION_{tag}.md")


if __name__ == "__main__":
    raise SystemExit(main())
