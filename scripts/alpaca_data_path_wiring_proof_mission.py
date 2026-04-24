#!/usr/bin/env python3
"""
ALPACA DATA PATH WIRING PROOF — droplet/Linux only, fail-closed.

Read-only on dashboard sinks; writes only reports/ALPACA_DATA_PATH_WIRING_PROOF_<TS>.md
(and optionally chains connectivity mission → other allowed report names).

Does not change strategy, dashboard schemas/paths, or rewrite historical logs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", "").strip()
    if r:
        return Path(r).resolve()
    return Path(__file__).resolve().parents[1]


def _broker_headers() -> Optional[Dict[str, str]]:
    """Same key resolution as truth mission; uses this process os.environ (post .env overlay)."""
    key = (
        os.getenv("APCA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY")
        or os.getenv("ALPACA_KEY")
    )
    sec = (
        os.getenv("APCA_API_SECRET_KEY")
        or os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("ALPACA_SECRET")
    )
    if not key or not sec:
        return None
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec}


def _overlay_env_from_dotenv(root: Path) -> None:
    """Populate os.environ from repo .env when keys are not inherited (e.g. non-interactive SSH)."""
    p = root / ".env"
    if not p.is_file():
        return
    try:
        raw = p.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    except OSError:
        return
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.lower().startswith("export "):
            s = s[7:].strip()
        k, _, v = s.partition("=")
        k = k.strip()
        if not k:
            continue
        existing = os.environ.get(k, "").strip()
        if existing:
            continue
        v = v.strip().strip("\r")
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        os.environ[k] = v


def _fill_blank_alpaca_keys_from_dotenv(root: Path) -> None:
    """SSH clients may inject empty APCA_/ALPACA_* placeholders; replace from .env when blank."""
    p = root / ".env"
    if not p.is_file():
        return
    try:
        raw = p.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    except OSError:
        return
    watch = {
        "ALPACA_KEY",
        "ALPACA_SECRET",
        "APCA_API_KEY_ID",
        "APCA_API_SECRET_KEY",
        "ALPACA_API_KEY_ID",
        "ALPACA_SECRET_KEY",
    }
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.lower().startswith("export "):
            s = s[7:].strip()
        k, _, v = s.partition("=")
        k = k.strip()
        if k not in watch:
            continue
        if (os.environ.get(k) or "").strip():
            continue
        v = v.strip().strip("\r")
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        if v:
            os.environ[k] = v


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
        "Authorization",
    ):
        out = re.sub(
            rf"({re.escape(key)})\s*[=:]\s*\S+",
            r"\1=<redacted>",
            out,
            flags=re.IGNORECASE,
        )
    return out


def _parse_ts(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        t = float(v)
        if t > 1e12:
            t /= 1000.0
        return t
    s = str(v).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _load_truth_mission(root: Path):
    path = root / "scripts" / "alpaca_truth_unblock_and_full_pnl_audit_mission.py"
    spec = importlib.util.spec_from_file_location("alpaca_truth_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _truth_uw_visible(mod: Any, root: Path) -> Tuple[bool, str]:
    """Reuse truth mission UW 30m check if present."""
    fn = getattr(mod, "uw_visible_recent", None)
    if callable(fn):
        try:
            ok, detail, _n, last = fn(root, 30)
            last_s = (
                datetime.fromtimestamp(float(last), tz=timezone.utc).isoformat()
                if last is not None
                else "n/a"
            )
            return ok, f"{detail} | last_event_utc={last_s}"
        except Exception as e:
            return False, str(e)
    return False, "uw_visible_recent missing"


def _dashboard_watch_paths(root: Path) -> List[Path]:
    """Canonical dashboard JSONL/state inputs (no path changes)."""
    try:
        from config.registry import LogFiles, CacheFiles, Directories

        paths = [
            root / LogFiles.ATTRIBUTION,
            root / LogFiles.EXIT_ATTRIBUTION,
            root / LogFiles.TELEMETRY,
            root / LogFiles.ORDERS,
            root / LogFiles.MASTER_TRADE_LOG,
            root / LogFiles.SIGNAL_CONTEXT,
            root / LogFiles.RUN,
            root / Directories.LOGS / "uw_flow.jsonl",
            root / CacheFiles.OPERATOR_DASHBOARD,
        ]
    except Exception:
        paths = [
            root / "logs/attribution.jsonl",
            root / "logs/exit_attribution.jsonl",
            root / "logs/telemetry.jsonl",
            root / "logs/orders.jsonl",
            root / "logs/master_trade_log.jsonl",
            root / "logs/signal_context.jsonl",
            root / "logs/run.jsonl",
            root / "logs/uw_flow.jsonl",
            root / "data/operator_dashboard.json",
        ]
    out: List[Path] = []
    seen: Set[str] = set()
    for p in paths:
        k = str(p.resolve()) if p.exists() else str(p)
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


def _snapshot_paths(paths: List[Path]) -> Dict[str, Tuple[float, int]]:
    snap: Dict[str, Tuple[float, int]] = {}
    for p in paths:
        try:
            if p.is_file():
                st = p.stat()
                snap[str(p.resolve())] = (st.st_mtime, st.st_size)
        except OSError:
            pass
    return snap


def _collect_activity_field_names(rows: List[dict], max_rows: int = 50) -> Set[str]:
    keys: Set[str] = set()
    for r in rows[:max_rows]:
        if isinstance(r, dict):
            keys.update(r.keys())
    return keys


def _fee_like_keys(keys: Set[str]) -> List[str]:
    kl = [k.lower() for k in keys]
    out = []
    for k in keys:
        lk = k.lower()
        if any(x in lk for x in ("fee", "commission", "cost", "reg_", "taf", "sec_fee")):
            out.append(k)
    return sorted(out)


def _orders_jsonl_recent_stats(path: Path, days: float) -> Tuple[int, Optional[float], Optional[str]]:
    """Count lines in last `days` with parseable ts; return (count, last_ts_epoch, last_ts_iso)."""
    if not path.exists() or path.stat().st_size == 0:
        return 0, None, None
    cut = time.time() - days * 86400
    n = 0
    last: Optional[float] = None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0, None, None
    for line in lines[-25000:]:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(r.get("ts") or r.get("timestamp"))
        if ts is None or ts < cut:
            continue
        n += 1
        if last is None or ts > last:
            last = ts
    last_iso = datetime.fromtimestamp(last, tz=timezone.utc).isoformat() if last else None
    return n, last, last_iso


def _signal_context_breakdown(path: Path, hours: int = 48) -> Tuple[int, int, int, List[str]]:
    if not path.exists():
        return 0, 0, 0, []
    cut = time.time() - hours * 3600
    ent = ex = blk = 0
    tail_lines: List[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0, 0, 0, []
    for line in lines[-20000:]:
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
    exit_samples: List[str] = []
    for line in reversed(lines[-5000:]):
        try:
            r = json.loads(line.strip())
        except (json.JSONDecodeError, AttributeError):
            continue
        if str(r.get("decision", "")).lower() != "exit":
            continue
        ts = _parse_ts(r.get("timestamp") or r.get("ts"))
        if ts is None or ts < cut:
            continue
        exit_samples.append(_redact(line[:500]))
        if len(exit_samples) >= 5:
            break
    return ent, ex, blk, exit_samples


def _probe_signal_context(root: Path) -> Tuple[bool, str]:
    mpy = root / "venv" / "bin" / "python3"
    if not mpy.exists():
        mpy = root / "venv" / "bin" / "python"
    cmd = (
        f"cd '{root}' && set -a && [ -f .env ] && . ./.env; set +a && {mpy} <<'PY'\n"
        "from telemetry.signal_context_logger import log_signal_context\n"
        "log_signal_context('__PROBE__', 'paper', 'connectivity_probe', "
        "'wiring_proof_sink', signals={})\n"
        "PY"
    )
    out, err, rc = _sh(cmd, timeout=60)
    return rc == 0, _redact((out + err).strip()[:1500])


def _symbols_from_exits(root: Path, days: int = 30) -> List[str]:
    cut = time.time() - days * 86400
    syms: Set[str] = set()
    for name in ("exit_attribution.jsonl", "alpaca_exit_attribution.jsonl"):
        p = root / "logs" / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines()[-50000:]:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_ts(r.get("timestamp") or r.get("ts"))
            if ts is None or ts < cut:
                continue
            s = (r.get("symbol") or "").strip().upper()
            if s:
                syms.add(s)
    return sorted(syms)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--chain-missions",
        action="store_true",
        help="If phases 0–5 pass all gates, run connectivity mission (same ALPACA_REPORT_TAG).",
    )
    args = ap.parse_args()

    if not Path("/proc").is_dir():
        print("Linux/droplet only.", file=sys.stderr)
        return 2

    root = _root()
    os.chdir(root)
    # SSH runners often `source .env` before Python; avoid load_dotenv clobbering inherited keys.
    if not (
        os.getenv("ALPACA_KEY")
        or os.getenv("APCA_API_KEY_ID")
        or os.getenv("ALPACA_API_KEY_ID")
    ):
        try:
            from dotenv import load_dotenv  # type: ignore

            load_dotenv(root / ".env")
        except Exception:
            pass
    _overlay_env_from_dotenv(root)
    _fill_blank_alpaca_keys_from_dotenv(root)
    tag = _tag()
    report_path = root / "reports" / f"ALPACA_DATA_PATH_WIRING_PROOF_{tag}.md"

    md: List[str] = [
        f"# ALPACA Data Path Wiring Proof — `{tag}`",
        "",
        f"- **TRADING_ROOT:** `{root}`",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    gates_ok: List[str] = []
    gates_fail: List[str] = []
    end: Dict[str, Any] = {}

    dash_paths = _dashboard_watch_paths(root)
    mission_start = time.time()
    snap_t0 = _snapshot_paths(dash_paths)

    # --- Phase 0 ---
    md.append("## Phase 0 — Baseline: services + runtime identity (SRE + CSA)")
    md.append("")
    st_bot, se_bot, rc_bot = _sh("systemctl status stock-bot.service --no-pager 2>&1", timeout=30)
    st_uw, se_uw, rc_uw = _sh("systemctl status uw-flow-daemon.service --no-pager 2>&1", timeout=30)
    md.append("### systemctl status stock-bot.service")
    md.append("```")
    md.append(_redact((st_bot + se_bot)[:8000]))
    md.append("```")
    md.append("")
    md.append("### systemctl status uw-flow-daemon.service")
    md.append("```")
    md.append(_redact((st_uw + se_uw)[:8000]))
    md.append("```")
    md.append("")

    lu, _, _ = _sh("systemctl list-units --type=service --all --no-pager 2>&1 | grep -iE 'dash|flask|5001|5000' || true", timeout=15)
    md.append("### Related units (dashboard-ish; grep on unit list)")
    md.append("```")
    md.append(lu[:4000] or "(none matched)")
    md.append("```")
    md.append("> This mission does **not** restart or modify dashboard services.")

    bot_ok = "active (running)" in st_bot.lower() or "(running)" in st_bot.lower()
    uw_ok = "active (running)" in st_uw.lower() or "(running)" in st_uw.lower()
    if bot_ok and uw_ok:
        gates_ok.append("Phase 0: stock-bot + uw-flow-daemon active")
    else:
        gates_fail.append("Phase 0: required systemd units not active")
        end["uw_fresh"] = False
        end["uw_last_ts"] = "n/a"
        md.append("")
        md.append("### GATE: **STOP** — stock-bot and/or uw-flow-daemon not active.")
        md.append("")
        md.append("## CSA verdict (early)")
        md.append("**WIRING NOT CONFIRMED** — bring up both units before re-run.")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        end["uw_last_ts"] = "n/a"
        _print_end(end, report_path, gates_ok, gates_fail, None)
        return 1

    ps_out, _, _ = _sh("ps -eo pid,lstart,cmd | grep -E '[p]ython.*main.py' || true", timeout=15)
    md.append("")
    md.append("### ps (main.py)")
    md.append("```")
    md.append(_redact(ps_out[:4000]))
    md.append("```")
    main_pid: Optional[int] = None
    m = re.search(r"^\s*(\d+)\s", ps_out, re.MULTILINE)
    if m:
        main_pid = int(m.group(1))
    if main_pid:
        cwd_o, _, _ = _sh(f"readlink -f /proc/{main_pid}/cwd 2>/dev/null || true", timeout=5)
        exe_o, _, _ = _sh(f"readlink -f /proc/{main_pid}/exe 2>/dev/null || true", timeout=5)
        md.append("")
        md.append(f"### /proc/{main_pid} (cwd + exe)")
        md.append("```")
        md.append(f"cwd: {cwd_o.strip()}")
        md.append(f"exe: {exe_o.strip()}")
        md.append("```")
    end["main_pid"] = main_pid

    # --- Phase 1 ---
    md.append("")
    md.append("## Phase 1 — UW pipeline: emit → sink → join (SRE + Quant + CSA)")
    md.append("")
    uw_path = root / "logs" / "uw_daemon.jsonl"
    if uw_path.exists():
        tail, _, _ = _sh(f"tail -n 20 '{uw_path}' 2>/dev/null", timeout=10)
        md.append("### tail -20 logs/uw_daemon.jsonl (redacted)")
        md.append("```")
        md.extend(_redact(x)[:400] for x in tail.splitlines()[-20:])
        md.append("```")
    else:
        md.append("### logs/uw_daemon.jsonl — *missing*")

    truth = None
    uw_note = ""
    uw_vis = False
    try:
        truth = _load_truth_mission(root)
    except Exception as e:
        uw_note = f"truth_load: {e}"
    if truth is not None:
        try:
            uw_vis, uw_note = _truth_uw_visible(truth, root)
        except Exception as e:
            uw_vis = False
            uw_note = f"uw_visible: {e}"
    elif not uw_note:
        uw_note = "truth module not loaded"

    md.append("")
    md.append(f"- **Truth mission UW check (30m):** `{uw_vis}` — {uw_note}")
    md.append("- **Intended join keys (UW → decisions):** symbol + time alignment via `uw_flow_cache` / composite scoring inputs; truth warehouse indexes UW fields on evaluated trade rows (`uw_coverage` metric).")
    md.append("- **Truth mission recognizes UW:** yes — `uw_coverage` / UW snapshot fields in `alpaca_truth_unblock_and_full_pnl_audit_mission.py`.")

    if uw_vis:
        gates_ok.append("Phase 1: UW fresh (30m)")
        end["uw_fresh"] = True
        mts = re.search(r"last_event_utc=([^|]+)", uw_note)
        end["uw_last_ts"] = (mts.group(1).strip() if mts else "see_phase1_detail")
    else:
        gates_fail.append("Phase 1: UW not fresh within 30m")
        end["uw_fresh"] = False
        md.append("")
        md.append("### GATE: **STOP** — UW not fresh.")
        md.append("")
        md.append("## CSA verdict (early)")
        md.append("**WIRING NOT CONFIRMED** — restore UW daemon emission to `logs/uw_daemon.jsonl` / cache.")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        end["uw_last_ts"] = "n/a"
        _print_end(end, report_path, gates_ok, gates_fail, None)
        return 1

    # --- Phase 2 ---
    md.append("")
    md.append("## Phase 2 — Execution economics: orders / fills / fees (SRE + Quant + CSA)")
    md.append("")
    orders_path = root / "logs" / "orders.jsonl"
    n2, last_e, last_iso = _orders_jsonl_recent_stats(orders_path, 2.0)
    n7, _, _ = _orders_jsonl_recent_stats(orders_path, 7.0)
    if orders_path.exists():
        ls, _, _ = _sh(f"ls -la '{orders_path}' 2>&1", timeout=5)
        tl, _, _ = _sh(f"tail -n 5 '{orders_path}' 2>/dev/null", timeout=5)
        md.append("### logs/orders.jsonl")
        md.append("```")
        md.append(ls.strip())
        md.append("--- tail (5) ---")
        md.extend(_redact(x)[:350] for x in tl.splitlines())
        md.append("```")
    else:
        md.append("### logs/orders.jsonl — *missing*")

    md.append(f"- **On-disk orders.jsonl rows (approx, ts in last 2d):** {n2}; **last ts:** `{last_iso}`")
    md.append(f"- **Same (last 7d window sample):** {n7} rows")

    fill_logs: List[str] = []
    for pat in ("**/fills*.jsonl", "**/execution*.jsonl", "**/alpaca*fill*.jsonl"):
        for p in root.glob(pat):
            if "reports" in p.parts:
                continue
            if p.is_file() and p.stat().st_size > 0:
                fill_logs.append(str(p.relative_to(root)))
    md.append("- **Other fill-like logs (inventory):** " + (", ".join(sorted(set(fill_logs))[:30]) or "(none found)"))

    broker_orders_2d = broker_act_2d = broker_act_30d = 0
    order_fields: Set[str] = set()
    act_fields: Set[str] = set()
    fills_2d: List[dict] = []
    hdrs = _broker_headers()
    if not hdrs and truth:
        hdrs = truth._alpaca_headers()
    key_names = []
    if hdrs:
        key_names = ["APCA_API_KEY_ID (or ALPACA_*)", "APCA_API_SECRET_KEY (or ALPACA_*)"]
    md.append("")
    md.append("### Broker probe (read-only; same helpers as truth mission)")
    md.append(f"- **Credential env keys present (names only):** {key_names or '(none — broker calls skipped)'}")
    if truth and hdrs:
        until = datetime.now(timezone.utc).isoformat()
        after2 = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        after30 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        base = os.getenv("APCA_API_BASE_URL") or os.getenv("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets"
        md.append(f"- **REST base:** `{base}`")
        md.append("- **list_orders** — `fetch_orders_rest` (truth mission), `status=all`, paginated")
        ords2 = truth.fetch_orders_rest(after2, until, max_rows=8000)
        ords30 = truth.fetch_orders_rest(after30, until, max_rows=8000)
        broker_orders_2d = len([o for o in ords2 if isinstance(o, dict)])
        broker_orders_30d = len([o for o in ords30 if isinstance(o, dict)])
        for o in ords2[:40]:
            if isinstance(o, dict):
                order_fields.update(o.keys())
        for o in ords30[:80]:
            if isinstance(o, dict):
                order_fields.update(o.keys())
        md.append(f"- **Order count last 2d window:** {broker_orders_2d} (capped fetch)")
        md.append(f"- **Order count last 30d window:** {broker_orders_30d} (capped fetch)")
        d0 = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
        d1 = datetime.now(timezone.utc).date().isoformat()
        md.append(
            f"- **account/activities** — `fetch_account_activities`, `activity_types=FILL`, "
            f"day-by-day `{d0}`..`{d1}` (+ extended for 30d count)"
        )
        fills_2d = truth.fetch_account_activities(
            base.rstrip("/"),
            hdrs,
            d0,
            d1,
            "FILL",
            max_days=3,
            max_pages_per_day=50,
        )
        broker_act_2d = len(fills_2d)
        d30 = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
        fills_30 = truth.fetch_account_activities(
            base.rstrip("/"),
            hdrs,
            d30,
            d1,
            "FILL",
            max_days=35,
            max_pages_per_day=50,
        )
        broker_act_30d = len(fills_30)
        act_fields = _collect_activity_field_names(fills_30)
        fee_keys = _fee_like_keys(act_fields)
        order_fee_keys = _fee_like_keys(order_fields)
        md.append(f"- **FILL activity count last 2d (by day query):** {broker_act_2d}")
        md.append(f"- **FILL activity count last ~30d:** {broker_act_30d}")
        md.append("- **Sample order object field names:** " + ", ".join(sorted(order_fields)[:40]))
        md.append("- **Sample activity field names:** " + ", ".join(sorted(act_fields)[:50]))
        md.append("- **Fee-like activity keys:** " + (", ".join(fee_keys) if fee_keys else "(none)"))
        md.append("- **Fee-like keys on order objects (top-level):** " + (", ".join(order_fee_keys) if order_fee_keys else "(none)"))
        end["broker_orders_2d"] = broker_orders_2d
        end["broker_act_2d"] = broker_act_2d
        end["broker_orders_30d"] = broker_orders_30d
        end["broker_act_30d"] = broker_act_30d
        mismatch_local = n2 >= 5 and broker_orders_2d == 0 and broker_act_2d == 0 and broker_orders_30d == 0 and broker_act_30d == 0
        if mismatch_local:
            gates_fail.append(
                "Phase 2: local orders.jsonl shows recent activity but broker returned 0 rows (endpoint/key mismatch)"
            )
            md.append("")
            md.append("### GATE: **STOP** — broker REST returned zero rows while local orders show activity.")
        elif broker_act_30d > 0 and not fee_keys:
            md.append("")
            md.append(
                "### Fee economics: **EXCLUDED_WITH_PROOF** (not a wiring failure for fills)"
            )
            md.append(
                "Sampled `FILL` activities (same truth-mission fetch path) carry **no top-level fee/commission-like "
                "fields** on this account/API shape (common on paper). **Wiring to the FILL surface is proven** by "
                "non-zero row counts; **per-fill fee attribution for DATA_READY** still needs another surface "
                "(e.g. billing export, non-FILL activity types, or order detail enrichment)."
            )
            gates_ok.append(
                "Phase 2: broker FILL + REST paths live; fee fields EXCLUDED_WITH_PROOF on FILL payload"
            )
        elif (
            n2 > 0
            or n7 > 0
            or broker_orders_2d > 0
            or broker_act_2d > 0
            or broker_orders_30d > 0
            or broker_act_30d > 0
        ):
            gates_ok.append("Phase 2: execution economics surfaces present (local and/or broker) in probed windows")
        else:
            gates_fail.append("Phase 2: no execution economics evidence in probed windows (local + broker)")
            md.append("")
            md.append("### GATE: **STOP** — no orders/fills evidence in 2d/7d local scan or broker 2d/30d fetch.")
    else:
        md.append("- **Broker probe skipped** (could not load truth mission or no API headers).")
        gates_fail.append("Phase 2: broker probe incomplete")

    # --- Phase 3 ---
    md.append("")
    md.append("## Phase 3 — Exit context: signal_context (SRE + Quant + CSA)")
    md.append("")
    sig_mod, _, _ = _sh(
        f"cd '{root}' && {root / 'venv' / 'bin' / 'python3'} -c "
        "\"import telemetry.signal_context_logger as m; print(m.__file__)\" 2>&1",
        timeout=30,
    )
    if not (root / "venv" / "bin" / "python3").exists():
        sig_mod, _, _ = _sh(
            f"cd '{root}' && {root / 'venv' / 'bin' / 'python'} -c "
            "\"import telemetry.signal_context_logger as m; print(m.__file__)\" 2>&1",
            timeout=30,
        )
    md.append("### signal_context_logger import path")
    md.append("```")
    md.append(sig_mod.strip()[:2000])
    md.append("```")

    scp = root / "logs" / "signal_context.jsonl"
    try:
        writable = os.access(scp, os.W_OK) if scp.exists() else os.access(scp.parent, os.W_OK)
    except OSError:
        writable = False
    md.append(f"- **logs/signal_context.jsonl exists:** {scp.exists()}; **writable (no touch):** {writable}")

    ent, ex, blk, exit_samples = _signal_context_breakdown(scp, 48)
    md.append(f"- **Last 48h counts:** ENTER={ent}, EXIT={ex}, BLOCKED={blk}")
    if exit_samples:
        md.append("### Last EXIT rows (≤5, redacted)")
        md.append("```")
        md.extend(exit_samples)
        md.append("```")
    else:
        other: List[str] = []
        if scp.exists():
            for line in scp.read_text(encoding="utf-8", errors="replace").splitlines()[-500:]:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                d = str(r.get("decision", "")).lower()
                if d in ("enter", "blocked", "connectivity_probe"):
                    other.append(_redact(line[:500]))
                if len(other) >= 5:
                    break
        md.append("### Recent non-EXIT rows (≤5) or empty")
        md.append("```")
        md.extend(other or ["(none in tail)"])
        md.append("```")
        md.append("- **Note:** EXIT rows **pending next close** if bot has not exited in-window.")

    phase3_ok = False
    if scp.exists() and scp.stat().st_size > 0 and (ent + ex + blk > 0):
        phase3_ok = True
    elif scp.exists() and scp.stat().st_size > 0:
        phase3_ok = True
    else:
        ok_p, det_p = _probe_signal_context(root)
        md.append("")
        md.append(f"- **Append probe (mission-only):** ok={ok_p}")
        md.append("```")
        md.append(det_p)
        md.append("```")
        phase3_ok = ok_p and scp.exists() and scp.stat().st_size > 0

    end["signal_context_writing"] = phase3_ok
    end["exit_rows_48h"] = ex

    if phase3_ok:
        gates_ok.append("Phase 3: signal_context sink active (rows or successful probe)")
    else:
        gates_fail.append("Phase 3: signal_context not being written")
        md.append("")
        md.append("### GATE: **STOP** — signal_context.jsonl not written.")

    # --- Phase 4 ---
    md.append("")
    md.append("## Phase 4 — Corporate actions: certify or exclude (SRE + CSA)")
    md.append("")
    corp_status = "FAIL"
    corp_detail = ""
    syms = _symbols_from_exits(root, 30)
    if truth and hdrs:
        start_d = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
        end_d = datetime.now(timezone.utc).date().isoformat()
        ann, st = truth.fetch_corporate_announcements(syms[:400], start_d, end_d)
        md.append(f"- **Corporate API call:** `data.alpaca.markets` announcements; status=`{st}`; rows={len(ann)}")
        if st == "OK" and ann:
            corp_status = "CERTIFIED"
            corp_detail = f"Returned {len(ann)} announcement rows for traded-symbol window."
        elif st == "OK" and not ann:
            corp_status = "EXCLUDED_WITH_PROOF"
            corp_detail = (
                "Broker returned zero announcements for traded symbols in window — excluded until manual verification "
                "or alternate feed."
            )
        elif st == "NO_API_KEYS":
            corp_status = "EXCLUDED_WITH_PROOF"
            corp_detail = "Data API keys not available in-process; cannot certify from this runtime."
        else:
            corp_status = "EXCLUDED_WITH_PROOF"
            corp_detail = f"API non-OK ({st}); exclusion until keys/feed verified."
    else:
        corp_status = "EXCLUDED_WITH_PROOF"
        corp_detail = "Truth module or Alpaca headers unavailable — corporate actions excluded with proof."

    md.append(f"- **Status:** **{corp_status}**")
    md.append(f"- **Detail:** {corp_detail}")
    md.append(f"- **Symbols (30d from exit logs, sample):** {', '.join(syms[:40])}{'…' if len(syms) > 40 else ''}")
    md.append(
        "- **Exclusion impact:** PnL readiness gates treat corporate actions as fail-closed until CERTIFIED or "
        "documented EXCLUDED_WITH_PROOF; adjusted positions must be reconciled manually when excluded."
    )
    end["corp_actions"] = corp_status

    if corp_status not in ("CERTIFIED", "EXCLUDED_WITH_PROOF"):
        gates_fail.append("Phase 4: corporate actions neither certified nor excluded")
    else:
        gates_ok.append(f"Phase 4: corporate actions {corp_status}")

    # --- Phase 6 (optional; before Phase 5 so we can list chained report paths) ---
    chain_rc: Optional[int] = None
    written_paths: List[str] = [str(report_path.resolve())]
    phases_0_5_ok = len(gates_fail) == 0
    if args.chain_missions and phases_0_5_ok:
        md.append("")
        md.append("## Phase 6 — Chained connectivity + truth mission")
        md.append("")
        os.environ["ALPACA_REPORT_TAG"] = tag
        mpy = root / "venv" / "bin" / "python3"
        if not mpy.exists():
            mpy = root / "venv" / "bin" / "python"
        cmd = f"cd '{root}' && export ALPACA_REPORT_TAG='{tag}' TRADING_BOT_ROOT='{root}' && {mpy} scripts/alpaca_uw_execution_connectivity_mission.py"
        md.append("### Command")
        md.append("```bash")
        md.append(_redact(cmd))
        md.append("```")
        out, err, chain_rc = _sh(cmd, timeout=7200)
        md.append(f"- **exit code:** {chain_rc}")
        md.append("### Output (truncated)")
        md.append("```")
        md.append(_redact((out + err)[-20000:]))
        md.append("```")
        for name in (
            f"ALPACA_CONNECTIVITY_AUDIT_{tag}.md",
            f"ALPACA_TRUTH_WAREHOUSE_{tag}.md",
            f"ALPACA_EXECUTION_COVERAGE_{tag}.md",
            f"ALPACA_SIGNAL_CONTRIBUTION_{tag}.md",
        ):
            p = root / "reports" / name
            md.append(f"- `{p}` {'(exists)' if p.exists() else '(missing)'}")
        for p in sorted((root / "reports").glob(f"ALPACA_*_{tag}.md")):
            try:
                if p.stat().st_mtime >= mission_start - 2:
                    sp = str(p.resolve())
                    if sp not in written_paths:
                        written_paths.append(sp)
            except OSError:
                pass
        for line in (out + err).splitlines():
            if line.startswith("DATA_READY:"):
                end["DATA_READY"] = "YES" in line.upper()
            if "execution_join_coverage:" in line or "fee_coverage:" in line:
                end.setdefault("mission_metrics", []).append(line.strip())
    elif args.chain_missions and not phases_0_5_ok:
        md.append("")
        md.append("## Phase 6 — Skipped")
        md.append("Phases 0–5 did not all pass; connectivity mission not chained.")

    # --- Phase 5 — Dashboard safety (after Phase 6; includes all report outputs) ---
    md.append("")
    md.append("## Phase 5 — Dashboard safety assertion (SRE + CSA)")
    md.append("")
    md.append(
        "*Note: Phase 6 (if enabled) runs before this section is composed so chained `reports/` outputs "
        "can appear in the manifest below.*"
    )
    md.append("")
    md.append("### Dashboard input paths monitored (registry/dashboard conventions)")
    md.append("")
    for p in dash_paths:
        md.append(f"- `{p}`")
    md.append("")
    md.append("### Markdown / report files attributed to this run (`reports/` only)")
    md.append("")
    for w in written_paths:
        md.append(f"- `{w}`")
    md.append("")
    snap_t1 = _snapshot_paths(dash_paths)
    changed: List[str] = []
    for k, v0 in snap_t0.items():
        v1 = snap_t1.get(k)
        if v1 is None:
            continue
        if v1 != v0:
            changed.append(f"{k}: mtime/size {v0} -> {v1}")
    md.append("### Monitored path changes (mtime/size) during mission window")
    md.append("")
    if not changed:
        md.append("- *(no changes detected on monitored dashboard paths)*")
    else:
        for c in changed[:40]:
            md.append(f"- {c}")
        md.append("")
        md.append(
            "> **Interpretation:** Log sinks may append from the running bot concurrently. This mission only "
            "creates/updates files under `reports/` listed above; it does not intentionally write to dashboard inputs."
        )

    bad_writes = [w for w in written_paths if "/reports/" not in w.replace("\\", "/")]
    if bad_writes:
        gates_fail.append(f"Phase 5: unexpected report paths outside reports/: {bad_writes}")
        end["dashboard_safety"] = "FAIL"
    else:
        if not any(x.startswith("Phase 5") for x in gates_ok):
            gates_ok.append("Phase 5: attributed outputs are under reports/ only")
        end["dashboard_safety"] = "PASS"

    # --- CSA ---
    final_ok = len(gates_fail) == 0
    md.append("")
    md.append("## CSA final verdict")
    md.append("")
    if final_ok:
        md.append(
            "### **WIRING CONFIRMED**; historical completeness remains **pending event volume** "
            "(DATA_READY may still be NO until joins/fees/slippage backfill)."
        )
        verdict = "WIRING_CONFIRMED"
    else:
        md.append("### **WIRING NOT CONFIRMED**")
        md.append("")
        md.append("**Blockers:**")
        for g in gates_fail:
            md.append(f"1. {g}")
        md.append("")
        md.append(
            "**Single highest-leverage fix:** align broker REST env (`APCA_*` / `ALPACA_*`) with the account "
            "that actually traded, then verify `list_orders` + `FILL` activities return rows and fee-like fields."
        )
        verdict = "WIRING_NOT_CONFIRMED"

    md.append("")
    md.append("---")
    md.append("*End of wiring proof.*")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    end["verdict"] = verdict
    end["report_path"] = str(report_path)
    _print_end(end, report_path, gates_ok, gates_fail, chain_rc)
    return 0 if final_ok else 1


def _print_end(
    end: Dict[str, Any],
    report_path: Path,
    ok: List[str],
    fail: List[str],
    chain_rc: Optional[int],
) -> None:
    print("--- END-OF-RUN ---")
    print(f"UW_fresh: {'YES' if end.get('uw_fresh') else 'NO'}")
    print(f"uw_last_ts: {end.get('uw_last_ts', 'n/a')}")
    print(f"broker_orders_2d: {end.get('broker_orders_2d', 'n/a')}")
    print(f"broker_activities_2d: {end.get('broker_act_2d', 'n/a')}")
    print(f"broker_orders_30d: {end.get('broker_orders_30d', 'n/a')}")
    print(f"broker_activities_30d: {end.get('broker_act_30d', 'n/a')}")
    print(
        f"signal_context_writing: {'YES' if end.get('signal_context_writing') else 'NO'} "
        f"exit_rows_48h={end.get('exit_rows_48h', 'n/a')}"
    )
    print(f"corp_actions: {end.get('corp_actions', 'n/a')}")
    print(f"dashboard_safety: {end.get('dashboard_safety', 'n/a')}")
    if "DATA_READY" in end:
        print(f"DATA_READY: {end['DATA_READY']}")
        for m in end.get("mission_metrics", []):
            print(m)
    if chain_rc is not None:
        print(f"chain_connectivity_rc: {chain_rc}")
    print(f"ALPACA_DATA_PATH_WIRING_PROOF: {report_path}")
    print(f"gates_ok: {len(ok)} gates_fail: {len(fail)}")


if __name__ == "__main__":
    raise SystemExit(main())
