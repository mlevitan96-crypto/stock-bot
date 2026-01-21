#!/usr/bin/env python3
"""
Post-Close Analysis Pack (additive, v1-safe)
===========================================

Creates a single dated bundle under:
  analysis_packs/YYYY-MM-DD/

Includes:
- Copies of key state files (best-effort)
- Copies of key reports (best-effort)
- Log tails (best-effort; fixed filenames)
- MASTER_SUMMARY_YYYY-MM-DD.md (human-facing)
- Optional archive: analysis_pack_YYYY-MM-DD.tar.gz

Notes:
- This script is observability-only; it never touches v1 trading logic.
- Safe-by-default: missing artifacts are recorded in the manifest and summary.
- `--mock` runs the orchestrated scripts in mock-safe mode where applicable.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _tail_text(path: Path, *, lines: int = 500) -> str:
    if not path.exists():
        return ""
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-int(lines) :]) + "\n"
    except Exception:
        return ""


def _tail_jsonl(path: Path, *, lines: int = 500) -> List[Dict[str, Any]]:
    raw = _tail_text(path, lines=lines)
    out: List[Dict[str, Any]] = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def _run(cmd: List[str], *, env: Optional[Dict[str, str]] = None, timeout: int = 900) -> Tuple[bool, str]:
    try:
        p = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + ("\n" + (p.stderr or "") if (p.stderr or "").strip() else "")
        return p.returncode == 0, out.strip()
    except Exception as e:
        return False, str(e)


def _copy_if_exists(src: Path, dst: Path) -> bool:
    try:
        if not src.exists():
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        return True
    except Exception:
        return False


def _summarize_universe(daily_v2: Dict[str, Any]) -> Dict[str, Any]:
    rows = daily_v2.get("symbols") if isinstance(daily_v2.get("symbols"), list) else []
    size = len(rows)
    # best-effort top symbols by score
    scored: List[Tuple[str, float, str]] = []
    for r in rows[:500]:
        if not isinstance(r, dict):
            continue
        s = str(r.get("symbol", "") or "").upper()
        if not s:
            continue
        try:
            sc = float(r.get("score", 0.0) or 0.0)
        except Exception:
            sc = 0.0
        sec = str(r.get("sector", "") or r.get("sector_label", "") or "")
        scored.append((s, sc, sec))
    scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)
    top_syms = [{"symbol": s, "score": round(sc, 4), "sector": sec} for s, sc, sec in scored_sorted[:10]]
    # top sectors
    sec_counts: Dict[str, int] = {}
    for _, _, sec in scored:
        if not sec:
            continue
        sec_counts[sec] = sec_counts.get(sec, 0) + 1
    top_secs = sorted(sec_counts.items(), key=lambda kv: kv[1], reverse=True)[:8]
    return {"universe_size": int(size), "top_sectors": top_secs, "top_symbols": top_syms}


def _count_trades_from_attribution(date: str) -> Tuple[int, List[str]]:
    """
    Best-effort v1 trade count via logs/attribution.jsonl.
    Returns (count, unique_symbols).
    """
    p = Path("logs/attribution.jsonl")
    if not p.exists():
        return 0, []
    syms: Dict[str, int] = {}
    cnt = 0
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()[-200000:]:
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        ts = str(rec.get("timestamp", "") or "")
        if ts[:10] != date:
            continue
        sym = str(rec.get("symbol", "") or rec.get("ticker", "") or "").upper()
        if sym:
            syms[sym] = syms.get(sym, 0) + 1
        cnt += 1
    return int(cnt), sorted(syms.keys())


def _count_shadow_activity(date: str) -> Dict[str, Any]:
    p = Path("logs/shadow_trades.jsonl")
    if not p.exists():
        return {"candidates": 0, "entries_opened": 0, "exits": 0, "symbols": []}
    candidates = 0
    entries = 0
    exits = 0
    syms: Dict[str, int] = {}
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()[-200000:]:
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        ts = str(rec.get("timestamp") or rec.get("ts") or "")
        if ts[:10] != date:
            continue
        et = str(rec.get("event_type", "") or "")
        sym = str(rec.get("symbol", "") or "").upper()
        if sym:
            syms[sym] = syms.get(sym, 0) + 1
        if et == "shadow_trade_candidate":
            candidates += 1
        elif et == "shadow_entry_opened":
            entries += 1
        elif et == "shadow_exit":
            exits += 1
    return {"candidates": int(candidates), "entries_opened": int(entries), "exits": int(exits), "symbols": sorted(syms.keys())}


def _pnl_snapshot_from_exit_summary(exit_pnl: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    counts = exit_pnl.get("counts") if isinstance(exit_pnl.get("counts"), dict) else {}
    out["exit_attributions"] = int(counts.get("exit_attributions", 0) or 0)
    out["overall"] = exit_pnl.get("overall") if isinstance(exit_pnl.get("overall"), dict) else {}
    out["by_exit_reason"] = exit_pnl.get("by_exit_reason") if isinstance(exit_pnl.get("by_exit_reason"), dict) else {}
    out["by_regime"] = exit_pnl.get("by_regime") if isinstance(exit_pnl.get("by_regime"), dict) else {}
    out["by_sector"] = exit_pnl.get("by_sector") if isinstance(exit_pnl.get("by_sector"), dict) else {}
    return out


def _write_master_summary(
    *,
    out_path: Path,
    date: str,
    pack_dir: Path,
    manifest: Dict[str, Any],
) -> None:
    daily_v2 = _read_json(pack_dir / "state" / "daily_universe_v2.json")
    regime = _read_json(pack_dir / "state" / "regime_state.json")
    uw_pnl = _read_json(pack_dir / "state" / "uw_intel_pnl_summary.json")
    exit_pnl = _read_json(pack_dir / "state" / "exit_intel_pnl_summary.json")
    daemon_health = _read_json(pack_dir / "state" / "uw_daemon_health_state.json")
    intel_health = _read_json(pack_dir / "state" / "intel_health_state.json")

    uni = _summarize_universe(daily_v2)
    v1_trade_count, v1_syms = _count_trades_from_attribution(date)
    v2_act = _count_shadow_activity(date)

    # Divergence (best-effort)
    v2_syms = set(v2_act.get("symbols") or [])
    v1_syms_set = set(v1_syms)
    v2_only = sorted(v2_syms - v1_syms_set)[:30]
    v1_only = sorted(v1_syms_set - v2_syms)[:30]

    # UW feature P&L highlights (best-effort)
    byf = uw_pnl.get("by_feature") if isinstance(uw_pnl.get("by_feature"), dict) else {}
    feat_rank: List[Tuple[str, float, int]] = []
    for k, r in byf.items():
        if not isinstance(r, dict):
            continue
        try:
            avg = float(r.get("avg_pnl_pct", 0.0) or 0.0)
        except Exception:
            avg = 0.0
        try:
            n = int(r.get("n", 0) or 0)
        except Exception:
            n = 0
        feat_rank.append((str(k), avg, n))
    feat_best = sorted(feat_rank, key=lambda x: x[1], reverse=True)[:6]
    feat_worst = sorted(feat_rank, key=lambda x: x[1])[:6]

    # Exit PnL snapshot
    pnl_snap = _pnl_snapshot_from_exit_summary(exit_pnl)

    # Health
    dh_status = str(daemon_health.get("status", "missing") or "missing")
    ih_ok = bool(intel_health.get("ok", False)) if isinstance(intel_health, dict) else False

    lines: List[str] = []
    lines.append(f"# MASTER SUMMARY — {date}")
    lines.append("")
    lines.append("## 2.1. Overview")
    lines.append(f"- Date (UTC): **{date}**")
    lines.append("- v1 status: **LIVE (sacred, unchanged)**")
    lines.append("- v2 status: **SHADOW-ONLY**")
    lines.append(f"- Daemon health: **{dh_status}**")
    lines.append(f"- Intel health: **{'OK' if ih_ok else 'NOT_OK/UNKNOWN'}**")
    lines.append("")

    lines.append("## 2.2. Universe & Regime Context")
    lines.append(f"- Universe v2 size: **{uni.get('universe_size', 0)}**")
    lines.append(f"- Top sectors: `{uni.get('top_sectors', [])}`")
    lines.append("- Top symbols by universe score (v2):")
    for r in uni.get("top_symbols", []) or []:
        if isinstance(r, dict):
            lines.append(f"  - **{r.get('symbol','')}** score={r.get('score')} sector={r.get('sector')}")
    if regime:
        lines.append(f"- Regime: **{regime.get('regime_label','NEUTRAL')}** (conf {regime.get('regime_confidence', 0.0)})")
        meta = regime.get("_meta") if isinstance(regime.get("_meta"), dict) else {}
        lines.append(f"- Regime engine version: `{meta.get('version','')}`")
    else:
        lines.append("- Regime state: missing")
    lines.append("")

    lines.append("## 2.3. v1 vs v2 Behavior Snapshot (best-effort)")
    lines.append(f"- v1 trade records (attribution.jsonl, best-effort): **{v1_trade_count}**")
    lines.append(f"- v2 shadow candidates: **{v2_act.get('candidates', 0)}** | entries_opened: **{v2_act.get('entries_opened', 0)}** | exits: **{v2_act.get('exits', 0)}**")
    lines.append(f"- Symbols v2 liked that v1 didn’t (up to 30): `{v2_only}`")
    lines.append(f"- Symbols v1 traded that v2 avoided (up to 30): `{v1_only}`")
    lines.append("")

    lines.append("## 2.4. v2 Entry Intelligence Summary (best-effort)")
    if feat_best:
        lines.append("- Best UW feature buckets by avg_pnl_pct:")
        for k, avg, n in feat_best:
            lines.append(f"  - **{k}**: avg_pnl_pct={round(avg, 6)} n={n}")
    if feat_worst:
        lines.append("- Worst UW feature buckets by avg_pnl_pct:")
        for k, avg, n in feat_worst:
            lines.append(f"  - **{k}**: avg_pnl_pct={round(avg, 6)} n={n}")
    lines.append(f"- See: `reports/SHADOW_DAY_SUMMARY_{date}.md` and `reports/UW_INTEL_PNL_{date}.md` (if present in pack).")
    lines.append("")

    lines.append("## 2.5. v2 Exit Intelligence Summary (best-effort)")
    by_reason = pnl_snap.get("by_exit_reason") if isinstance(pnl_snap.get("by_exit_reason"), dict) else {}
    if by_reason:
        lines.append("- Exit count / avg P&L by reason:")
        for k in sorted(by_reason.keys()):
            r = by_reason[k]
            if isinstance(r, dict):
                lines.append(f"  - **{k}**: n={r.get('n')} win_rate={r.get('win_rate')} avg_pnl={r.get('avg_pnl')}")
    else:
        lines.append("- Exit P&L by reason: unavailable (missing exit_intel_pnl_summary.json)")
    lines.append(f"- See: `reports/EXIT_DAY_SUMMARY_{date}.md` and `reports/EXIT_INTEL_PNL_{date}.md` (if present in pack).")
    lines.append("")

    lines.append("## 2.6. v2 Paper P&L Snapshot (best-effort)")
    overall = pnl_snap.get("overall") if isinstance(pnl_snap.get("overall"), dict) else {}
    if overall:
        lines.append(f"- Overall (from exit_intel_pnl_summary): `{overall}`")
    else:
        lines.append("- Overall: unavailable (needs exit attributions / exit intel pnl summary).")
    lines.append("")

    lines.append("## 2.7. Health & Reliability")
    if daemon_health:
        det = daemon_health.get("details") if isinstance(daemon_health.get("details"), dict) else {}
        lines.append(f"- Daemon status: **{daemon_health.get('status','unknown')}** | pid_ok={daemon_health.get('pid_ok')} | lock_ok={daemon_health.get('lock_ok')} | poll_fresh={daemon_health.get('poll_fresh')}")
        lines.append(f"- Restart storm detected: **{daemon_health.get('restart_storm_detected', False)}** (count={((det.get('restart_storm') or {}) if isinstance(det.get('restart_storm'), dict) else {}).get('count', 0)})")
        lines.append(f"- Endpoint errors: {det.get('endpoint_error_counts')}")
    else:
        lines.append("- Daemon health: missing")
    if intel_health:
        lines.append(f"- Intel health ok: **{intel_health.get('ok', False)}** (checks={len(intel_health.get('checks') or []) if isinstance(intel_health.get('checks'), list) else 0})")
    else:
        lines.append("- Intel health: missing")
    lines.append("- Recent system events: see `logs/system_events_tail.jsonl` in this pack.")
    lines.append("")

    lines.append("## 2.8. Promotion Readiness Notes (human-facing)")
    lines.append("### Reasons v2 looks ready")
    lines.append("- [ ] (fill in after reviewing pack)")
    lines.append("")
    lines.append("### Reasons v2 is not ready yet")
    lines.append("- [ ] (fill in after reviewing pack)")
    lines.append("")
    lines.append("### Questions to investigate before promotion")
    lines.append("- [ ] (fill in after reviewing pack)")
    lines.append("")

    # Append manifest quick view
    lines.append("## Appendix: Pack Manifest (what was captured)")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(manifest, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    ap.add_argument("--mock", action="store_true", help="Run orchestrated scripts in mock-safe mode where possible")
    ap.add_argument("--archive", action="store_true", help="Create analysis_pack_YYYY-MM-DD.tar.gz (recommended)")
    ap.add_argument("--lines", type=int, default=500, help="Tail size for log tails")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero if any required step fails")
    args = ap.parse_args()

    date = args.date.strip() or _today_utc()
    pack_dir = Path("analysis_packs") / date
    pack_state = pack_dir / "state"
    pack_logs = pack_dir / "logs"
    pack_reports = pack_dir / "reports"
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_state.mkdir(parents=True, exist_ok=True)
    pack_logs.mkdir(parents=True, exist_ok=True)
    pack_reports.mkdir(parents=True, exist_ok=True)

    # Environment: ensure UTF-8 output and allow mock mode
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if bool(args.mock):
        env["UW_MOCK"] = "1"

    steps: List[Tuple[str, List[str]]] = [
        ("run_shadow_day_summary", [env.get("PYTHON", "") or os.sys.executable, "scripts/run_shadow_day_summary.py", "--date", date]),
        ("run_exit_day_summary", [env.get("PYTHON", "") or os.sys.executable, "scripts/run_exit_day_summary.py", "--date", date]),
        ("run_exit_intel_pnl", [env.get("PYTHON", "") or os.sys.executable, "scripts/run_exit_intel_pnl.py", "--date", date]),
        ("run_daily_intel_pnl", [env.get("PYTHON", "") or os.sys.executable, "scripts/run_daily_intel_pnl.py", "--date", date]),
        ("run_intel_health_checks", [env.get("PYTHON", "") or os.sys.executable, "scripts/run_intel_health_checks.py", "--mock" if bool(args.mock) else "--nonfatal"]),
        ("run_daemon_health_check", [env.get("PYTHON", "") or os.sys.executable, "scripts/run_daemon_health_check.py", "--nonfatal"] + (["--mock"] if bool(args.mock) else [])),
        ("run_intel_dashboard", [env.get("PYTHON", "") or os.sys.executable, "reports/_dashboard/intel_dashboard_generator.py", "--date", date]),
        ("run_v2_tuning_suggestions", [env.get("PYTHON", "") or os.sys.executable, "-m", "src.intel.v2_tuning_helper"]),
    ]

    results: List[Dict[str, Any]] = []
    for name, cmd in steps:
        ok, out = _run(cmd, env=env, timeout=900)
        results.append({"step": name, "ok": bool(ok), "cmd": cmd, "output_tail": out[-1200:]})

    # Capture artifacts (best-effort)
    state_files = [
        "state/daily_universe.json",
        "state/daily_universe_v2.json",
        "state/premarket_intel.json",
        "state/postmarket_intel.json",
        "state/regime_state.json",
        "state/uw_intel_pnl_summary.json",
        "state/exit_intel_pnl_summary.json",
        "state/uw_daemon_health_state.json",
        "state/intel_health_state.json",
        "state/premarket_exit_intel.json",
        "state/postmarket_exit_intel.json",
        "state/shadow_v2_positions.json",
        "state/shadow_heartbeat.json",
    ]
    report_files = [
        f"reports/INTEL_DASHBOARD_{date}.md",
        f"reports/SHADOW_DAY_SUMMARY_{date}.md",
        f"reports/EXIT_DAY_SUMMARY_{date}.md",
        f"reports/UW_INTEL_PNL_{date}.md",
        f"reports/EXIT_INTEL_PNL_{date}.md",
        f"reports/V2_TUNING_SUGGESTIONS_{date}.md",
    ]
    log_tails = [
        ("logs/shadow_trades.jsonl", "shadow_trades_tail.jsonl"),
        ("logs/uw_attribution.jsonl", "uw_attribution_tail.jsonl"),
        ("logs/exit_attribution.jsonl", "exit_attribution_tail.jsonl"),
        ("logs/system_events.jsonl", "system_events_tail.jsonl"),
    ]

    captured: Dict[str, Any] = {"state": {}, "reports": {}, "log_tails": {}}
    for rel in state_files:
        src = Path(rel)
        dst = pack_state / src.name
        captured["state"][rel] = bool(_copy_if_exists(src, dst))
    for rel in report_files:
        src = Path(rel)
        dst = pack_reports / src.name
        captured["reports"][rel] = bool(_copy_if_exists(src, dst))
    for src_rel, out_name in log_tails:
        txt = _tail_text(Path(src_rel), lines=int(args.lines))
        (pack_logs / out_name).write_text(txt, encoding="utf-8")
        captured["log_tails"][src_rel] = {"file": str((pack_logs / out_name)), "lines": int(args.lines), "present": bool(txt.strip())}

    manifest: Dict[str, Any] = {
        "_meta": {"ts": _now_iso(), "version": "2026-01-21_postclose_pack_v1"},
        "date": date,
        "pack_dir": str(pack_dir),
        "steps": results,
        "captured": captured,
    }

    # Master summary
    master = pack_dir / f"MASTER_SUMMARY_{date}.md"
    _write_master_summary(out_path=master, date=date, pack_dir=pack_dir, manifest=manifest)
    (pack_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    # Optional archive
    if bool(args.archive):
        tar_path = pack_dir / f"analysis_pack_{date}.tar.gz"
        try:
            with tarfile.open(tar_path, "w:gz") as tf:
                # archive the contents of pack_dir (relative paths)
                for p in sorted(pack_dir.rglob("*")):
                    if p.is_file():
                        tf.add(p, arcname=str(p.relative_to(pack_dir)))
        except Exception:
            pass

    # Log completion (best-effort)
    try:
        from utils.system_events import log_system_event  # type: ignore

        ok_all = all(bool(r.get("ok")) for r in results)
        log_system_event(
            subsystem="postclose",
            event_type="postclose_analysis_pack_completed",
            severity=("INFO" if ok_all else "WARN"),
            details={"date": date, "pack_dir": str(pack_dir), "ok": bool(ok_all)},
        )
    except Exception:
        pass

    # Exit code policy
    ok_all = all(bool(r.get("ok")) for r in results)
    if bool(args.strict) and not ok_all:
        return 2

    print(str(pack_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

