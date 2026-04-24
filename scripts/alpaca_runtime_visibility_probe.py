#!/usr/bin/env python3
"""
ALPACA RUNTIME ATTACHMENT + DATA VISIBILITY PROBE (droplet/Linux only).

Writes exactly one file: reports/ALPACA_RUNTIME_VISIBILITY_<TS>.md
Does not modify strategy, trading state, or logs.
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
from typing import Any, Dict, List, Optional, Tuple

TS = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", "").strip()
    if r:
        return Path(r).resolve()
    p = Path(__file__).resolve().parents[1]
    return p


def _sh(cmd: str, timeout: int = 30) -> Tuple[str, str, int]:
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


def _read_cmdline(pid: int) -> List[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        return [x.decode("utf-8", errors="replace") for x in raw.split(b"\0") if x]
    except OSError:
        return []


def _read_proc_exe(pid: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/exe")
    except OSError:
        return ""


def _read_proc_cwd(pid: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return ""


def _read_environ_dict(pid: int) -> Dict[str, str]:
    out: Dict[str, str] = {}
    try:
        raw = Path(f"/proc/{pid}/environ").read_bytes()
    except OSError:
        return out
    for chunk in raw.split(b"\0"):
        if b"=" not in chunk:
            continue
        k, _, v = chunk.partition(b"=")
        try:
            out[k.decode("utf-8", errors="replace")] = v.decode("utf-8", errors="replace")
        except Exception:
            pass
    return out


def _environ_key_presence(env: Dict[str, str], prefixes: Tuple[str, ...]) -> List[str]:
    return sorted({k for k in env.keys() if any(k.upper().startswith(p.upper()) for p in prefixes)})


def _systemd_unit_for_pid(pid: int) -> str:
    cg = Path(f"/proc/{pid}/cgroup")
    if not cg.exists():
        return ""
    try:
        text = cg.read_text(errors="replace")
    except OSError:
        return ""
    for line in text.splitlines():
        # e.g. 0::/system.slice/stock-bot.service
        m = re.search(r"/([^/]+\.service)$", line.strip())
        if m:
            return m.group(1)
    return ""


def _systemctl_show(unit: str) -> Dict[str, str]:
    out, _, rc = _sh(f"systemctl show '{unit}' --no-pager 2>/dev/null", timeout=15)
    d: Dict[str, str] = {}
    if rc != 0:
        return d
    for line in out.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        d[k.strip()] = v.strip()
    return d


def _find_candidate_pids() -> List[int]:
    me = os.getpid()
    out, _, _ = _sh("pgrep -af python 2>/dev/null || true", timeout=15)
    pids: List[int] = []
    for line in out.splitlines():
        line_l = line.lower()
        if "alpaca_runtime_visibility_probe" in line_l:
            continue
        if "grep" in line_l:
            continue
        if "main.py" in line_l or "trading" in line_l or "stock-bot" in line_l:
            parts = line.split(None, 1)
            if parts and parts[0].isdigit():
                cand = int(parts[0])
                if cand != me:
                    pids.append(cand)
    # dedupe preserve order
    seen = set()
    uniq = []
    for p in pids:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def _pick_live_pid() -> Tuple[Optional[int], str]:
    """Prefer main.py; else first python in /root/stock-bot."""
    for pid in _find_candidate_pids():
        cmd = " ".join(_read_cmdline(pid)).lower()
        if "main.py" in cmd:
            return pid, "pgrep: cmdline contains main.py"
    out, _, _ = _sh("pgrep -af 'python.*main.py' 2>/dev/null || true", timeout=10)
    for line in out.splitlines():
        m = re.match(r"^(\d+)\s", line)
        if m and "grep" not in line.lower() and int(m.group(1)) != os.getpid():
            return int(m.group(1)), "pgrep -af python.*main.py"
    # fallback: running service with stock in name
    sout, _, _ = _sh(
        "systemctl list-units --type=service --state=running --no-pager 2>/dev/null | "
        "grep -iE 'stock|trade|bot|alpaca' || true",
        timeout=15,
    )
    for line in sout.splitlines():
        parts = line.split()
        if not parts:
            continue
        unit = parts[0]
        if not unit.endswith(".service"):
            continue
        show = _systemctl_show(unit)
        mp = show.get("MainPID", "0")
        if mp.isdigit() and int(mp) > 1:
            return int(mp), f"systemd running unit {unit} MainPID"
    return None, "no candidate found"


def _real(p: str) -> str:
    try:
        return str(Path(p).resolve())
    except Exception:
        return p


def _probe_inner_source() -> str:
    return r"""
import json, os, sys, time
from pathlib import Path
from datetime import datetime, timezone

def tail_jsonl(path, n=10):
    p = Path(path)
    if not p.exists():
        return {"error": "missing", "path": str(p)}
    lines = []
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                if ln.strip():
                    lines.append(ln.strip())
        lines = lines[-n:]
    except OSError as e:
        return {"error": str(e), "path": str(p)}
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except Exception:
            out.append({"raw": ln[:200]})
    return {"path": str(p), "count": len(out), "rows": out}

def main():
    tr = os.environ.get("TRADING_BOT_ROOT", "").strip()
    root = Path(tr).resolve() if tr else Path.cwd().resolve()
    now = time.time()
    t48 = now - 48 * 3600
    sc_path = root / "logs" / "signal_context.jsonl"
    exit_48h = 0
    if sc_path.exists():
        try:
            with open(sc_path, "r", encoding="utf-8", errors="replace") as f:
                for ln in f:
                    if not ln.strip():
                        continue
                    try:
                        r = json.loads(ln)
                    except Exception:
                        continue
                    if str(r.get("decision", "")).lower() != "exit":
                        continue
                    ts = r.get("ts")
                    if isinstance(ts, (int, float)) and float(ts) >= t48:
                        exit_48h += 1
                        continue
                    tss = r.get("timestamp")
                    if tss:
                        try:
                            from datetime import datetime as dt
                            s = str(tss).replace("Z", "+00:00")
                            d = dt.fromisoformat(s)
                            if d.timestamp() >= t48:
                                exit_48h += 1
                        except Exception:
                            pass
        except OSError:
            pass
    orders = tail_jsonl(root / "logs" / "orders.jsonl", 10)
    def _last_ts(path: Path):
        if not path.exists():
            return None
        try:
            last = ""
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for ln in f:
                    if ln.strip():
                        last = ln.strip()
            if not last:
                return None
            r = json.loads(last)
            return r.get("timestamp") or r.get("ts")
        except Exception:
            return "parse_error"

    uw_recent = _last_ts(root / "logs" / "uw_daemon.jsonl")
    if uw_recent is None:
        uw_recent = _last_ts(root / "logs" / "uw_errors.jsonl")
    mods = []
    for mod in ("alpaca_trade_api", "config.registry", "uw_composite_v2"):
        try:
            __import__(mod)
            mods.append(mod + ":OK")
        except Exception as e:
            mods.append(mod + ":FAIL " + str(e)[:80])
    print(json.dumps({
        "sys_executable": sys.executable,
        "sys_prefix": sys.prefix,
        "cwd": str(root),
        "orders_tail": orders,
        "signal_context_exit_48h": exit_48h,
        "uw_daemon_last_ts": uw_recent,
        "imports": mods,
    }, default=str))
main()
"""


def main() -> int:
    if not Path("/proc").is_dir():
        print("This probe must run on Linux (droplet).", file=sys.stderr)
        return 2

    root = _root()
    rep = root / "reports" / f"ALPACA_RUNTIME_VISIBILITY_{TS}.md"
    rep.parent.mkdir(parents=True, exist_ok=True)

    # --- Cursor / invoker identity (how this script was started, e.g. SSH) ---
    cursor_py = _real(sys.executable)
    cursor_cwd = _real(str(Path.cwd()))
    cursor_uid = os.getuid()
    cursor_gid = os.getgid()
    cursor_keys = _environ_key_presence(dict(os.environ), ("APCA_", "ALPACA_", "UW_"))
    cursor_apca = _environ_key_presence(dict(os.environ), ("APCA_", "ALPACA_"))

    lines: List[str] = [
        f"# ALPACA Runtime Visibility — `{TS}`",
        "",
        "## Phase 0 — Live bot runtime identification (SRE)",
        "",
    ]

    pid, how = _pick_live_pid()
    phase0_stop = pid is None
    if phase0_stop:
        lines.append("**STOP:** Live trading runtime could not be identified (no `main.py` process, no matching systemd unit with MainPID).")
        lines.extend(["", "## Phase 1–3", "Skipped due to Phase 0 STOP.", ""])
        rep.write_text("\n".join(lines), encoding="utf-8")
        print("verdict: B")
        print("live_bot_python: UNKNOWN")
        print("cursor_probe_python:", cursor_py)
        print("UW_visible: NO")
        print("execution_events_visible: NO")
        print("report:", rep)
        return 2

    assert pid is not None
    cmdline = _read_cmdline(pid)
    live_exe = _read_proc_exe(pid)
    live_cwd = _read_proc_cwd(pid)
    live_env = _read_environ_dict(pid)
    live_uid = None
    live_gid = None
    try:
        st = os.stat(f"/proc/{pid}")
        live_uid, live_gid = st.st_uid, st.st_gid
    except OSError:
        pass

    unit = _systemd_unit_for_pid(pid)
    svc_meta: Dict[str, str] = {}
    if unit:
        svc_meta = _systemctl_show(unit)

    lines.append(f"- **How selected:** {how}")
    lines.append(f"- **PID:** `{pid}`")
    lines.append(f"- **cmdline:** `{' '.join(cmdline)[:500]}`")
    if unit:
        lines.append(f"- **systemd unit (from cgroup):** `{unit}`")
        for key in (
            "User",
            "Group",
            "WorkingDirectory",
            "EnvironmentFile",
            "EnvironmentFiles",
            "Environment",
            "ExecStart",
            "FragmentPath",
        ):
            if key in svc_meta:
                val = svc_meta[key]
                if key == "Environment" and val:
                    # show variable NAMES only
                    names = []
                    for part in val.split():
                        if part.startswith('"'):
                            part = part.strip('"')
                        if "=" in part:
                            names.append(part.split("=", 1)[0])
                    lines.append(f"- **{key}:** `{', '.join(names[:40])}{' …' if len(names) > 40 else ''}`")
                else:
                    lines.append(f"- **{key}:** `{val[:800]}{'…' if len(val) > 800 else ''}`")
    else:
        lines.append("- **systemd unit:** not detected from cgroup (process may be tmux/cron/manual).")
        ppid = "?"
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
            ppid = stat.split()[3]
        except OSError:
            pass
        lines.append(f"- **Parent PID (stat):** `{ppid}`")
        po, _, _ = _sh(f"ps -o ppid=,cmd= -p {pid} 2>/dev/null; ps -o cmd= -p {ppid} 2>/dev/null || true", timeout=5)
        if po.strip():
            lines.append(f"- **ps parent context:**\n```\n{po.strip()[:1200]}\n```")

    lines.extend(["", "## Phase 1 — Live runtime identity (SRE)", ""])
    lines.append(f"- **python executable (`/proc/{pid}/exe`):** `{live_exe}`")
    lines.append(f"- **cwd (`/proc/{pid}/cwd`):** `{live_cwd}`")
    lines.append(f"- **UID/GID:** `{live_uid}` / `{live_gid}`")
    pres_apca = _environ_key_presence(live_env, ("APCA_", "ALPACA_"))
    pres_uw = _environ_key_presence(live_env, ("UW_",))
    lines.append(f"- **APCA_/ALPACA_ keys present (names only):** {pres_apca or '*(none)*'}")
    lines.append(f"- **UW_ keys present (names only):** {pres_uw or '*(none)*'}")

    sc = root / "logs" / "signal_context.jsonl"
    od = root / "logs" / "orders.jsonl"
    uw = root / "logs" / "uw_daemon.jsonl"
    for label, pth in (
        ("signal_context.jsonl", sc),
        ("orders.jsonl", od),
        ("uw_daemon.jsonl", uw),
    ):
        if pth.exists():
            lines.append(f"- **`{label}`:** exists, size **{pth.stat().st_size}** bytes")
        else:
            lines.append(f"- **`{label}`:** missing")

    # Phase 2: subprocess with live python + live env + live cwd
    py_for_probe = _resolve_probe_python(live_exe, cmdline)

    probe_json: Dict[str, Any] = {}
    probe_err = ""
    merged_env = {**os.environ, **live_env}
    merged_env.setdefault("TRADING_BOT_ROOT", str(root))

    try:
        p = subprocess.run(
            [py_for_probe, "-c", _probe_inner_source()],
            cwd=live_cwd or str(root),
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        probe_err = (p.stderr or "")[:2000]
        if p.stdout.strip():
            probe_json = json.loads(p.stdout.strip())
    except Exception as e:
        probe_err = str(e)
        probe_json = {"error": str(e)}

    lines.extend(["", "## Phase 2 — Probe in live-matched context (SRE)", ""])
    lines.append(f"- **Probe python:** `{py_for_probe}`")
    lines.append(f"- **Probe cwd:** `{live_cwd or str(root)}`")
    lines.append(f"- **Env merge:** live `/proc/{pid}/environ` merged over probe parent (keys only logged above).")
    lines.append("```json")
    lines.append(json.dumps(probe_json, indent=2, default=str)[:12000])
    lines.append("```")
    if probe_err.strip():
        lines.append(f"- **stderr:**\n```\n{probe_err[:2000]}\n```")

    uw_vis = False
    ex_vis = False
    if isinstance(probe_json, dict):
        imps = probe_json.get("imports") or []
        uw_mod = any("uw_composite_v2:OK" in x for x in imps)
        uwt = probe_json.get("uw_daemon_last_ts")
        uw_ts_ok = uwt is not None and uwt not in ("parse_error", "")
        # Mission: module import AND evidence of UW activity (daemon timestamp).
        uw_vis = bool(uw_mod and uw_ts_ok)
        ot = probe_json.get("orders_tail") or {}
        if ot.get("rows"):
            ex_vis = True
        if probe_json.get("signal_context_exit_48h", 0) > 0:
            ex_vis = True

    # Phase 3 verdict — compare *live bot* vs *Cursor invoker* (SSH session that started this script)
    live_py_path = live_exe or py_for_probe
    same_py = _real(live_py_path) == _real(cursor_py)
    same_cwd = _real(live_cwd) == _real(cursor_cwd)
    same_user = live_uid is not None and live_uid == cursor_uid
    set_apca_bot = set(pres_apca)
    set_apca_cur = set(cursor_apca)
    apca_align = (not set_apca_bot) or (set_apca_bot <= set_apca_cur)

    verdict_a = same_py and same_cwd and same_user and apca_align

    lines.extend(["", "## Phase 3 — Diff & verdict (CSA)", ""])
    lines.append("| Field | Live bot | Cursor invoker (this script) | Match |")
    lines.append("|-------|----------|--------------------------------|-------|")
    lines.append(f"| python | `{live_py_path}` | `{cursor_py}` | {'YES' if same_py else 'NO'} |")
    lines.append(f"| cwd | `{live_cwd}` | `{cursor_cwd}` | {'YES' if same_cwd else 'NO'} |")
    lines.append(f"| uid | `{live_uid}` | `{cursor_uid}` | {'YES' if same_user else 'NO'} |")
    lines.append(
        f"| APCA/ALPACA key names | {len(set_apca_bot)} keys | {len(set_apca_cur)} keys | "
        f"{'YES' if apca_align else 'NO'} |"
    )
    lines.append("")
    if verdict_a:
        lines.append("### Verdict: **A) CURSOR IS ATTACHED TO LIVE RUNTIME — DATA SHOULD BE VISIBLE**")
    else:
        lines.append("### Verdict: **B) CURSOR IS NOT ATTACHED — FIX REQUIRED**")
        lines.append("")
        lines.append("**Mismatches:**")
        if not same_py:
            lines.append("- Python interpreter differs — run Cursor/SSH commands using the bot venv interpreter (see `ExecStart` / `/proc/PID/exe`).")
        if not same_cwd:
            lines.append("- Working directory differs — `cd` to the bot `WorkingDirectory` before running probes.")
        if not same_user:
            lines.append("- User differs — use `sudo -u <service User>` or `runuser` so UID matches the service.")
        if not apca_align:
            lines.append("- APCA/ALPACA env key set differs — `set -a && source <EnvironmentFile> && set +a` in the same shell as probe, or use `systemd-run` with the unit's environment file.")
        lines.append("")
        lines.append("**Single fix (typical):** run probes exactly as the unit does, e.g. "
                    "`cd <WorkingDirectory> && set -a && source <EnvironmentFile> && set +a && <venv>/python ...` "
                    "or inspect `ExecStart` and copy that prefix.")

    lines.append("")
    lines.append("---")
    lines.append("*No other conclusions per mission scope.*")
    lines.append("")

    rep.write_text("\n".join(lines), encoding="utf-8")

    v = "A" if verdict_a else "B"
    print(f"verdict: {v}")
    print("live_bot_python:", live_py_path)
    print("cursor_probe_python:", cursor_py)
    print("UW_visible:", "YES" if uw_vis else "NO")
    print("execution_events_visible:", "YES" if ex_vis else "NO")
    print("report:", rep)
    return 0 if verdict_a else 1


def _resolve_probe_python(live_exe: str, cmdline: List[str]) -> str:
    if live_exe and Path(live_exe).exists() and "python" in os.path.basename(live_exe).lower():
        return live_exe
    for a in cmdline:
        bn = os.path.basename(a).lower()
        if "python" in bn and Path(a).exists():
            return a
    w = shutil.which("python3")
    return w or sys.executable


if __name__ == "__main__":
    raise SystemExit(main())
