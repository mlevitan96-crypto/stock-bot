#!/usr/bin/env python3
"""
Full Telemetry Extract (date-scoped, read-only)
=============================================

Goal:
- Produce a single, comprehensive telemetry bundle for a given UTC date.
- Additive and v1-safe: reads logs/state/reports; writes ONLY under telemetry/YYYY-MM-DD/.

Outputs:
telemetry/YYYY-MM-DD/
  - FULL_TELEMETRY_YYYY-MM-DD.md
  - telemetry_manifest.json
  - state/ (copied state artifacts)
  - logs/  (copied log artifacts; full or tailed depending on size)
  - reports/ (copied report artifacts)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _side_from_direction(direction: str) -> str:
    d = str(direction or "").lower()
    if d in ("bearish", "short", "sell"):
        return "short"
    return "long"


def _utc_day_from_ts(ts: Any) -> Optional[str]:
    if ts is None:
        return None
    s = str(ts).strip()
    if not s:
        return None
    # Fast-path for ISO-like strings
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s[:10] if len(s) >= 10 else None


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        s = str(ts or "").replace("Z", "+00:00")
        if "T" not in s and " " in s:
            s = s.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(_read_text(path))
    except Exception:
        return None


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    for ln in _read_text(path).splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                yield obj
        except Exception:
            continue


def _compute_pnl_usd_pct(entry_price: float, exit_price: float, qty: float, side: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        e = float(entry_price)
        x = float(exit_price)
        q = float(qty)
        if e <= 0 or x <= 0 or q <= 0:
            return None, None
        pnl = q * (e - x) if str(side) == "short" else q * (x - e)
        pct = pnl / (q * e) if (q * e) > 0 else None
        return float(pnl), (float(pct) if pct is not None else None)
    except Exception:
        return None, None


def _basic_stats(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {}
    xs = sorted(float(x) for x in values)
    n = len(xs)
    mean = sum(xs) / float(n) if n else 0.0
    med = xs[n // 2] if (n % 2 == 1) else (xs[n // 2 - 1] + xs[n // 2]) / 2.0

    def pct(p: float) -> float:
        if n == 1:
            return xs[0]
        # nearest-rank
        i = int(round((p / 100.0) * (n - 1)))
        i = max(0, min(n - 1, i))
        return xs[i]

    return {
        "n": n,
        "min": xs[0],
        "p25": pct(25),
        "p50": pct(50),
        "p75": pct(75),
        "max": xs[-1],
        "mean": mean,
        "median": med,
    }


@dataclass(frozen=True)
class CopiedFile:
    kind: str  # state/logs/reports/generated
    source: str
    dest: str
    bytes: int
    sha256: str
    truncated: bool = False
    note: str = ""


def _copy_file_bytes(dst: Path, data: bytes) -> CopiedFile:
    _ensure_dir(dst.parent)
    dst.write_bytes(data)
    return CopiedFile(
        kind="generated",
        source="",
        dest=str(dst.as_posix()),
        bytes=len(data),
        sha256=_sha256_bytes(data),
    )


def _copy_from_repo(
    *,
    rel_src: str,
    dst_root: Path,
    kind: str,
    max_log_bytes: int,
    tail_lines: int,
) -> Optional[CopiedFile]:
    src = ROOT / rel_src
    if not src.exists() or not src.is_file():
        return None

    # Destination mirrors structure under telemetry bundle.
    dst = dst_root / rel_src
    _ensure_dir(dst.parent)

    truncated = False
    note = ""
    data: bytes

    try:
        if kind == "logs":
            size = src.stat().st_size
            if size > int(max_log_bytes):
                # Tail by lines in a UTF-8-safe-ish way: decode replace then re-encode.
                text = _read_text(src)
                lines = text.splitlines()[-int(tail_lines) :]
                text2 = "\n".join(lines) + ("\n" if lines else "")
                data = text2.encode("utf-8", errors="replace")
                truncated = True
                note = f"tailed_last_lines={int(tail_lines)} original_bytes={size}"
            else:
                data = src.read_bytes()
        else:
            data = src.read_bytes()
    except Exception:
        return None

    dst.write_bytes(data)
    return CopiedFile(
        kind=str(kind),
        source=str(src.as_posix()),
        dest=str(dst.as_posix()),
        bytes=len(data),
        sha256=_sha256_bytes(data),
        truncated=truncated,
        note=note,
    )


def _git_head_short() -> str:
    # Avoid shelling out; best-effort read .git/HEAD (works for normal checkout).
    try:
        head = (ROOT / ".git" / "HEAD").read_text(encoding="utf-8", errors="replace").strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[-1].strip()
            ref_path = ROOT / ".git" / ref
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8", errors="replace").strip()[:12]
        return head[:12]
    except Exception:
        return ""


def _universe_rank(universe_doc: Any, symbol: str) -> Tuple[Optional[int], Optional[float]]:
    try:
        if not isinstance(universe_doc, dict):
            return None, None
        rows = universe_doc.get("symbols")
        if not isinstance(rows, list):
            return None, None
        sym = str(symbol).upper()
        for idx, r in enumerate(rows):
            if isinstance(r, dict) and str(r.get("symbol", "")).upper() == sym:
                return int(idx + 1), _safe_float(r.get("score"))
    except Exception:
        pass
    return None, None


def _summarize_health(day: str) -> Dict[str, Any]:
    intel_health = _read_json(ROOT / "state" / "intel_health_state.json")
    daemon_health = _read_json(ROOT / "state" / "uw_daemon_health_state.json")
    out: Dict[str, Any] = {
        "intel_health": {},
        "daemon_health": {},
    }
    if isinstance(intel_health, dict):
        checks = intel_health.get("checks") if isinstance(intel_health.get("checks"), list) else []
        status_counts = Counter()
        for c in checks:
            if isinstance(c, dict):
                status_counts[str(c.get("status", "unknown"))] += 1
        out["intel_health"] = {
            "ts": (intel_health.get("_meta") or {}).get("ts") if isinstance(intel_health.get("_meta"), dict) else intel_health.get("ts"),
            "status_counts": dict(status_counts),
            "check_count": len(checks),
        }
    if isinstance(daemon_health, dict):
        out["daemon_health"] = {
            "timestamp": daemon_health.get("timestamp"),
            "status": daemon_health.get("status"),
            "pid_ok": daemon_health.get("pid_ok"),
            "lock_ok": daemon_health.get("lock_ok"),
            "poll_fresh": daemon_health.get("poll_fresh"),
            "crash_loop": daemon_health.get("crash_loop"),
            "endpoint_errors": daemon_health.get("endpoint_errors"),
        }
    return out


def _extract_shadow_telemetry(day: str) -> Dict[str, Any]:
    """
    Build v2 shadow trade/exits telemetry for the given UTC day from:
    - logs/shadow_trades.jsonl
    - logs/exit_attribution.jsonl
    - state/daily_universe_v2.json (rank at entry)
    - state/regime_state.json (session regime)
    """
    shadow_path = ROOT / "logs" / "shadow_trades.jsonl"
    exit_attr_path = ROOT / "logs" / "exit_attribution.jsonl"
    universe_v2 = _read_json(ROOT / "state" / "daily_universe_v2.json")
    regime = _read_json(ROOT / "state" / "regime_state.json")

    trades_today: List[Dict[str, Any]] = []
    entries_by_trade: Dict[str, Dict[str, Any]] = {}
    exits_by_trade: Dict[str, Dict[str, Any]] = {}

    for rec in _iter_jsonl(shadow_path):
        ts = rec.get("ts") or rec.get("timestamp")
        if _utc_day_from_ts(ts) != day:
            continue
        trades_today.append(rec)
        et = str(rec.get("event_type", "") or "")
        if et == "shadow_entry_opened":
            tid = str(rec.get("trade_id") or "") or f"{rec.get('symbol','')}-{rec.get('entry_ts','')}"
            entries_by_trade[tid] = rec
        elif et == "shadow_exit":
            tid = str(rec.get("trade_id") or "") or f"{rec.get('symbol','')}-{rec.get('entry_ts','')}"
            exits_by_trade[tid] = rec

    # Exit attribution (today) – keyed by (symbol, entry_timestamp) best-effort.
    exit_attrib_today: List[Dict[str, Any]] = []
    exit_attrib_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for rec in _iter_jsonl(exit_attr_path):
        ts = rec.get("timestamp") or rec.get("ts")
        if _utc_day_from_ts(ts) != day:
            continue
        exit_attrib_today.append(rec)
        sym = str(rec.get("symbol", "") or "").upper()
        ent = str(rec.get("entry_timestamp", "") or "")
        if sym and ent:
            exit_attrib_by_key[(sym, ent)] = rec

    # Compute realized trades (requires entry + exit)
    realized: List[Dict[str, Any]] = []
    for tid, ent in entries_by_trade.items():
        ex = exits_by_trade.get(tid)
        if not isinstance(ex, dict):
            continue
        sym = str(ent.get("symbol", "") or ex.get("symbol", "")).upper()
        side = str(ent.get("side") or _side_from_direction(str(ent.get("direction", ""))))
        entry_price = _safe_float(ent.get("entry_price"))
        exit_price = _safe_float(ex.get("exit_price"))
        qty = _safe_float(ex.get("qty") or ent.get("qty"))

        pnl_usd = _safe_float(ex.get("pnl"))
        pnl_pct = _safe_float(ex.get("pnl_pct"))
        if pnl_usd is None and entry_price is not None and exit_price is not None and (qty or 0) > 0:
            pnl_usd, pnl_pct = _compute_pnl_usd_pct(entry_price, exit_price, float(qty or 0), side)

        entry_ts = str(ent.get("entry_ts") or ent.get("ts") or ent.get("timestamp") or "")
        exit_ts = str(ex.get("exit_ts") or ex.get("ts") or ex.get("timestamp") or "")
        tmin = None
        dt0 = _parse_iso(entry_ts)
        dt1 = _parse_iso(exit_ts)
        if dt0 and dt1:
            tmin = (dt1 - dt0).total_seconds() / 60.0

        intel_ent = ent.get("intel_snapshot") if isinstance(ent.get("intel_snapshot"), dict) else {}
        intel_ex = ex.get("intel_snapshot") if isinstance(ex.get("intel_snapshot"), dict) else {}
        sec_ent = ""
        reg_ent = ""
        sec_ex = ""
        reg_ex = ""
        try:
            sec_ent = str(((intel_ent.get("v2_uw_sector_profile") or {}) if isinstance(intel_ent.get("v2_uw_sector_profile"), dict) else {}).get("sector", "UNKNOWN"))
            reg_ent = str(((intel_ent.get("v2_uw_regime_profile") or {}) if isinstance(intel_ent.get("v2_uw_regime_profile"), dict) else {}).get("regime_label", ""))
            sec_ex = str(((intel_ex.get("v2_uw_sector_profile") or {}) if isinstance(intel_ex.get("v2_uw_sector_profile"), dict) else {}).get("sector", "UNKNOWN"))
            reg_ex = str(((intel_ex.get("v2_uw_regime_profile") or {}) if isinstance(intel_ex.get("v2_uw_regime_profile"), dict) else {}).get("regime_label", ""))
        except Exception:
            pass

        entry_rank, entry_u_score = _universe_rank(universe_v2, sym)
        exit_reason = str(ex.get("v2_exit_reason", "") or "")
        repl = ex.get("replacement_candidate")

        # Score evolution:
        entry_v2_score = _safe_float(ent.get("v2_score"))
        exit_v2_score = _safe_float(ex.get("v2_score"))
        v2_exit_score = _safe_float(ex.get("v2_exit_score"))

        # Pull richer attribution if present (deterioration, exit comps, time_in_trade)
        # shadow_executor emits entry_ts on "shadow_entry_opened" matching exit_attribution.entry_timestamp.
        attrib_key = (sym, str(ent.get("entry_ts") or ""))
        attrib = exit_attrib_by_key.get(attrib_key)

        realized.append(
            {
                "trade_id": tid,
                "symbol": sym,
                "side": side,
                "direction": ent.get("direction"),
                "entry_ts": entry_ts,
                "exit_ts": exit_ts,
                "time_in_trade_minutes": tmin,
                "qty": qty,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl_usd": pnl_usd,
                "pnl_pct": pnl_pct,
                "exit_reason": exit_reason,
                "replacement_candidate": repl,
                "entry_v1_score": _safe_float(ent.get("v1_score")),
                "entry_v2_score": entry_v2_score,
                "exit_v2_score": exit_v2_score,
                "v2_exit_score": v2_exit_score,
                "exit_attribution": attrib,
                "entry_universe_rank_v2": entry_rank,
                "entry_universe_score_v2": entry_u_score,
                "entry_sector": sec_ent or "UNKNOWN",
                "entry_regime": reg_ent or "",
                "exit_sector": sec_ex or "UNKNOWN",
                "exit_regime": reg_ex or "",
            }
        )

    # Aggregate PnL breakdowns
    pnl_total = 0.0
    pnl_by_symbol: Dict[str, float] = defaultdict(float)
    pnl_by_sector: Dict[str, float] = defaultdict(float)
    pnl_by_regime: Dict[str, float] = defaultdict(float)
    pnl_by_exit_reason: Dict[str, float] = defaultdict(float)
    for r in realized:
        p = float(r.get("pnl_usd") or 0.0)
        pnl_total += p
        pnl_by_symbol[str(r.get("symbol", ""))] += p
        pnl_by_sector[str(r.get("entry_sector", "UNKNOWN") or "UNKNOWN")] += p
        pnl_by_regime[str(r.get("entry_regime", "") or "")] += p
        pnl_by_exit_reason[str(r.get("exit_reason", "") or "")] += p

    # Simple entry intelligence: UW feature usage counts from shadow candidates
    feat_counts = Counter()
    candidates = [r for r in trades_today if str(r.get("event_type", "")) == "shadow_trade_candidate"]
    for r in candidates:
        snap = r.get("uw_attribution_snapshot") if isinstance(r.get("uw_attribution_snapshot"), dict) else {}
        adj = snap.get("v2_uw_adjustments") if isinstance(snap.get("v2_uw_adjustments"), dict) else {}
        for k, v in adj.items():
            if k == "total":
                continue
            try:
                if abs(float(v)) > 1e-6:
                    feat_counts[k] += 1
            except Exception:
                continue

    replacement_events = [r for r in realized if r.get("replacement_candidate")]
    exit_reasons = Counter([str(r.get("exit_reason", "") or "") for r in realized])

    return {
        "counts": {
            "shadow_log_records_today": len(trades_today),
            "shadow_trade_candidates_today": len(candidates),
            "shadow_entries_opened_today": len(entries_by_trade),
            "shadow_exits_today": len(exits_by_trade),
            "realized_closed_trades": len(realized),
            "exit_attribution_records_today": len(exit_attrib_today),
            "replacement_events": len(replacement_events),
        },
        "regime_session": (regime.get("regime_label") if isinstance(regime, dict) else ""),
        "pnl_total_usd": round(pnl_total, 6),
        "pnl_by_symbol": dict(sorted(pnl_by_symbol.items(), key=lambda kv: kv[1], reverse=True)),
        "pnl_by_sector": dict(sorted(pnl_by_sector.items(), key=lambda kv: kv[1], reverse=True)),
        "pnl_by_regime": dict(sorted(pnl_by_regime.items(), key=lambda kv: kv[1], reverse=True)),
        "pnl_by_exit_reason": dict(sorted(pnl_by_exit_reason.items(), key=lambda kv: kv[1], reverse=True)),
        "exit_reasons_distribution": dict(exit_reasons),
        "uw_feature_usage_counts": dict(feat_counts),
        "realized_trades": realized,
    }


def _render_master_md(
    *,
    day: str,
    source_meta: Dict[str, Any],
    health: Dict[str, Any],
    shadow: Dict[str, Any],
    universe: Dict[str, Any],
    intel: Dict[str, Any],
    tails: Dict[str, str],
    copied_files: List[CopiedFile],
    missing: Dict[str, List[str]],
) -> str:
    lines: List[str] = []
    lines.append(f"# FULL TELEMETRY — {day}")
    lines.append("")
    lines.append("## 1. Overview")
    lines.append(f"- Generated at (UTC): **{source_meta.get('generated_at_utc','')}**")
    lines.append(f"- Data source: **{source_meta.get('data_source','unknown')}**")
    gh = source_meta.get("git_head", "")
    if gh:
        lines.append(f"- Git head: **{gh}**")
    lines.append("")
    lines.append("### Status snapshot")
    v1_live_present = bool(universe.get("v1_live_log_present"))
    lines.append(f"- v1 status: **{'present' if v1_live_present else 'unknown / no live log found'}**")
    lines.append(f"- v2 status: **shadow-only telemetry**")
    dh = health.get("daemon_health") or {}
    ih = health.get("intel_health") or {}
    if dh:
        lines.append(f"- Daemon health: **{dh.get('status','unknown')}** (pid_ok={dh.get('pid_ok')} lock_ok={dh.get('lock_ok')} poll_fresh={dh.get('poll_fresh')})")
    if ih:
        lines.append(f"- Intel health checks: **{ih.get('status_counts',{})}** (n={ih.get('check_count',0)})")
    lines.append("")

    lines.append("## 2. v2 Shadow Trading Summary")
    c = shadow.get("counts") or {}
    lines.append(f"- Entries (opened): **{c.get('shadow_entries_opened_today',0)}**")
    lines.append(f"- Exits: **{c.get('shadow_exits_today',0)}**")
    lines.append(f"- Closed trades (realized): **{c.get('realized_closed_trades',0)}**")
    lines.append(f"- Total PnL (USD): **{shadow.get('pnl_total_usd',0.0)}**")
    lines.append(f"- Replacement events: **{c.get('replacement_events',0)}**")
    lines.append(f"- Exit reasons distribution: **{shadow.get('exit_reasons_distribution',{})}**")
    lines.append("")

    # Best/Worst trades (realized)
    realized = shadow.get("realized_trades") if isinstance(shadow.get("realized_trades"), list) else []
    realized_sorted = sorted(realized, key=lambda r: float((r or {}).get("pnl_usd") or 0.0), reverse=True)
    best = realized_sorted[:5]
    worst = list(reversed(realized_sorted[-5:])) if realized_sorted else []
    lines.append("### Best trades (by realized PnL, USD)")
    if not best:
        lines.append("- None (no realized exits today).")
    else:
        for r in best:
            lines.append(
                f"- **{r.get('symbol')}** pnl_usd={round(float(r.get('pnl_usd') or 0.0),2)} "
                f"pnl_pct={r.get('pnl_pct')} reason={r.get('exit_reason')} tmin={r.get('time_in_trade_minutes')}"
            )
    lines.append("")
    lines.append("### Worst trades (by realized PnL, USD)")
    if not worst:
        lines.append("- None (no realized exits today).")
    else:
        for r in worst:
            lines.append(
                f"- **{r.get('symbol')}** pnl_usd={round(float(r.get('pnl_usd') or 0.0),2)} "
                f"pnl_pct={r.get('pnl_pct')} reason={r.get('exit_reason')} tmin={r.get('time_in_trade_minutes')}"
            )
    lines.append("")

    # Replacement events
    repl = [r for r in realized if (r or {}).get("replacement_candidate")]
    lines.append("### Replacement logic events")
    if not repl:
        lines.append("- None.")
    else:
        for r in repl[:20]:
            lines.append(f"- **{r.get('symbol')}** → replacement_candidate={r.get('replacement_candidate')}")
    lines.append("")

    lines.append("## 3. Entry Intelligence")
    lines.append(f"- UW feature usage (non-zero adjustments counts): **{shadow.get('uw_feature_usage_counts',{})}**")
    # Sector / regime alignment at entry (best-effort)
    entry_sector = Counter([str((r or {}).get("entry_sector") or "UNKNOWN") for r in realized])
    entry_regime = Counter([str((r or {}).get("entry_regime") or "") for r in realized])
    lines.append(f"- Entry sector distribution (closed trades): **{dict(entry_sector)}**")
    lines.append(f"- Entry regime distribution (closed trades): **{dict(entry_regime)}**")
    # Universe rank at entry (v2)
    ranks = [float(r.get("entry_universe_rank_v2")) for r in realized if r.get("entry_universe_rank_v2") is not None]
    if ranks:
        lines.append(f"- Universe v2 rank stats at entry: **{_basic_stats(ranks)}**")
    lines.append("")

    lines.append("## 4. Exit Intelligence")
    exit_scores = [float(r.get("v2_exit_score")) for r in realized if r.get("v2_exit_score") is not None]
    det = []
    for r in realized:
        ev = r.get("entry_v2_score")
        xv = r.get("exit_v2_score")
        if ev is not None and xv is not None:
            try:
                det.append(float(ev) - float(xv))
            except Exception:
                pass
    lines.append(f"- Exit score stats (v2_exit_score): **{_basic_stats(exit_scores)}**")
    lines.append(f"- Score deterioration stats (entry_v2_score - exit_v2_score): **{_basic_stats(det)}**")
    lines.append(f"- Exit reasons distribution: **{shadow.get('exit_reasons_distribution',{})}**")
    lines.append("")

    lines.append("## 5. PnL Analysis")
    lines.append("### PnL by symbol (USD)")
    for k, v in list((shadow.get("pnl_by_symbol") or {}).items())[:25]:
        lines.append(f"- **{k}**: {round(float(v), 2)}")
    lines.append("")
    lines.append("### PnL by sector (USD)")
    for k, v in list((shadow.get("pnl_by_sector") or {}).items())[:25]:
        lines.append(f"- **{k or 'UNKNOWN'}**: {round(float(v), 2)}")
    lines.append("")
    lines.append("### PnL by regime (USD)")
    for k, v in list((shadow.get("pnl_by_regime") or {}).items())[:25]:
        lines.append(f"- **{k or 'UNKNOWN'}**: {round(float(v), 2)}")
    lines.append("")
    lines.append("### PnL by exit reason (USD)")
    for k, v in list((shadow.get("pnl_by_exit_reason") or {}).items())[:25]:
        lines.append(f"- **{k or 'UNKNOWN'}**: {round(float(v), 2)}")
    lines.append("")

    lines.append("## 6. Attribution")
    lines.append("- Entry attribution tail (`logs/uw_attribution.jsonl`):")
    lines.append("")
    lines.append("```")
    lines.append((tails.get("uw_attribution_tail") or "").strip() or "(missing)")
    lines.append("```")
    lines.append("")
    lines.append("- Exit attribution tail (`logs/exit_attribution.jsonl`):")
    lines.append("")
    lines.append("```")
    lines.append((tails.get("exit_attribution_tail") or "").strip() or "(missing)")
    lines.append("```")
    lines.append("")

    lines.append("## 7. Health & Reliability")
    lines.append(f"- Daemon health summary: `{health.get('daemon_health',{})}`")
    lines.append(f"- Intel health summary: `{health.get('intel_health',{})}`")
    lines.append("- System events tail (`logs/system_events.jsonl`):")
    lines.append("")
    lines.append("```")
    lines.append((tails.get("system_events_tail") or "").strip() or "(missing)")
    lines.append("```")
    lines.append("")

    lines.append("## 8. Promotion Readiness Notes")
    pnl_total = float(shadow.get("pnl_total_usd") or 0.0)
    daemon_ok = str((health.get("daemon_health") or {}).get("status", "")).lower() == "healthy"
    intel_ok = "ok" in (health.get("intel_health") or {}).get("status_counts", {})
    reasons_ready: List[str] = []
    reasons_not: List[str] = []
    if c.get("realized_closed_trades", 0) and pnl_total > 0:
        reasons_ready.append(f"Positive realized PnL today: {round(pnl_total,2)} USD (shadow)")
    if daemon_ok and intel_ok:
        reasons_ready.append("Daemon + intel health look OK (best-effort)")
    if not c.get("realized_closed_trades", 0):
        reasons_not.append("No realized shadow exits today (cannot validate exit quality/PnL)")
    if pnl_total < 0:
        reasons_not.append(f"Negative realized PnL today: {round(pnl_total,2)} USD (shadow)")
    if not daemon_ok:
        reasons_not.append("Daemon health not healthy (quota/data freshness risk)")
    if not intel_ok:
        reasons_not.append("Intel health not clean (missing/stale intel risk)")
    lines.append("- Reasons v2 looks ready:")
    if reasons_ready:
        for r in reasons_ready:
            lines.append(f"  - {r}")
    else:
        lines.append("  - (none detected automatically)")
    lines.append("- Reasons v2 is not ready:")
    if reasons_not:
        for r in reasons_not:
            lines.append(f"  - {r}")
    else:
        lines.append("  - (none detected automatically)")
    lines.append("- Questions to investigate:")
    lines.append("  - Are there consistent divergences between v1_score vs v2_score on high-quality symbols today?")
    lines.append("  - Do replacement exits improve realized outcomes vs holding?")
    lines.append("")

    lines.append("## Universe & Intel snapshots (best-effort)")
    lines.append(f"- Universe v1: n={universe.get('daily_universe_count')} (file present={universe.get('daily_universe_present')})")
    lines.append(f"- Universe v2: n={universe.get('daily_universe_v2_count')} (file present={universe.get('daily_universe_v2_present')})")
    lines.append(f"- Regime state: {intel.get('regime_label','')}, conf={intel.get('regime_confidence')}")
    lines.append("")

    lines.append("## Bundle contents (high-level)")
    lines.append(f"- Copied files: **{len([x for x in copied_files if x.kind in ('state','logs','reports')])}**")
    trunc = [x for x in copied_files if x.truncated]
    lines.append(f"- Truncated (tailed) logs: **{len(trunc)}**")
    if trunc:
        for x in trunc[:15]:
            lines.append(f"  - {x.dest} ({x.note})")
    lines.append("")

    lines.append("## Missing artifacts (best-effort)")
    for bucket, items in missing.items():
        if not items:
            continue
        lines.append(f"- **{bucket}**:")
        for x in items:
            lines.append(f"  - {x}")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--output-root", default="telemetry", help="Output root directory (default: telemetry/)")
    ap.add_argument("--max-log-bytes", type=int, default=2_000_000, help="Max bytes before log is tailed (default: 2,000,000)")
    ap.add_argument("--tail-lines", type=int, default=5000, help="Tail lines when log exceeds max-log-bytes (default: 5000)")
    args = ap.parse_args()

    day = (args.date.strip() or _today_utc()).strip()
    out_root = ROOT / str(args.output_root)
    out_dir = out_root / day
    _ensure_dir(out_dir)

    # Create bundle subfolders (explicit structure)
    _ensure_dir(out_dir / "state")
    _ensure_dir(out_dir / "logs")
    _ensure_dir(out_dir / "reports")

    copied: List[CopiedFile] = []
    missing: Dict[str, List[str]] = {"state": [], "logs": [], "reports": []}

    # Required state artifacts (best-effort)
    state_targets = [
        "state/shadow_v2_positions.json",
        "state/daily_universe.json",
        "state/daily_universe_v2.json",
        "state/premarket_intel.json",
        "state/postmarket_intel.json",
        "state/premarket_exit_intel.json",
        "state/postmarket_exit_intel.json",
        "state/regime_state.json",
        "state/intel_health_state.json",
        "state/uw_daemon_health_state.json",
        "state/uw_usage_state.json",
        "state/uw_intel_pnl_summary.json",
        "state/exit_intel_pnl_summary.json",
        # optional but useful context (additive)
        "state/market_context_v2.json",
        "state/regime_posture_state.json",
        "state/symbol_risk_features.json",
        "state/score_telemetry.json",
    ]
    for rel in state_targets:
        r = _copy_from_repo(rel_src=rel, dst_root=out_dir, kind="state", max_log_bytes=args.max_log_bytes, tail_lines=args.tail_lines)
        if r is None:
            missing["state"].append(rel)
        else:
            copied.append(r)

    # Logs (best-effort; tailed if large)
    log_targets = [
        # v1 live (optional)
        "logs/live_trades.jsonl",
        "logs/shadow_trades.jsonl",
        "logs/exit_attribution.jsonl",
        "logs/shadow.jsonl",
        "logs/uw_attribution.jsonl",
        "logs/system_events.jsonl",
        # general system tails (helpful for "all system events / all logs tails")
        "logs/run.jsonl",
        "logs/run_once.jsonl",
        "logs/worker.jsonl",
        "logs/worker_error.jsonl",
        "logs/scoring_flow.jsonl",
        "logs/scoring_pipeline.jsonl",
        "logs/scoring.jsonl",
        "logs/gate.jsonl",
        "logs/orders.jsonl",
        "logs/exit.jsonl",
    ]
    for rel in log_targets:
        r = _copy_from_repo(rel_src=rel, dst_root=out_dir, kind="logs", max_log_bytes=args.max_log_bytes, tail_lines=args.tail_lines)
        if r is None:
            missing["logs"].append(rel)
        else:
            copied.append(r)

    # Reports (date-scoped)
    report_targets = [
        f"reports/SHADOW_DAY_SUMMARY_{day}.md",
        f"reports/EXIT_DAY_SUMMARY_{day}.md",
        f"reports/EXIT_INTEL_PNL_{day}.md",
        f"reports/UW_INTEL_PNL_{day}.md",
        f"reports/V2_TUNING_SUGGESTIONS_{day}.md",
        f"reports/INTEL_DASHBOARD_{day}.md",
    ]
    for rel in report_targets:
        r = _copy_from_repo(rel_src=rel, dst_root=out_dir, kind="reports", max_log_bytes=args.max_log_bytes, tail_lines=args.tail_lines)
        if r is None:
            missing["reports"].append(rel)
        else:
            copied.append(r)

    # Compute telemetry sections
    health = _summarize_health(day)
    shadow = _extract_shadow_telemetry(day)
    daily_universe = _read_json(ROOT / "state" / "daily_universe.json")
    daily_universe_v2 = _read_json(ROOT / "state" / "daily_universe_v2.json")
    regime_state = _read_json(ROOT / "state" / "regime_state.json")

    universe_summary: Dict[str, Any] = {
        "daily_universe_present": isinstance(daily_universe, dict),
        "daily_universe_v2_present": isinstance(daily_universe_v2, dict),
        "daily_universe_count": (len(daily_universe.get("symbols")) if isinstance(daily_universe, dict) and isinstance(daily_universe.get("symbols"), list) else None),
        "daily_universe_v2_count": (len(daily_universe_v2.get("symbols")) if isinstance(daily_universe_v2, dict) and isinstance(daily_universe_v2.get("symbols"), list) else None),
        "v1_live_log_present": (ROOT / "logs" / "live_trades.jsonl").exists(),
    }
    intel_summary: Dict[str, Any] = {}
    if isinstance(regime_state, dict):
        intel_summary["regime_label"] = regime_state.get("regime_label")
        intel_summary["regime_confidence"] = regime_state.get("regime_confidence")

    # Small tails for report embedding (use originals)
    def _tail_text(path: Path, n: int = 20) -> str:
        t = _read_text(path).splitlines()
        return "\n".join(t[-n:]) + ("\n" if t else "")

    tails = {
        "uw_attribution_tail": _tail_text(ROOT / "logs" / "uw_attribution.jsonl", n=12) if (ROOT / "logs" / "uw_attribution.jsonl").exists() else "",
        "exit_attribution_tail": _tail_text(ROOT / "logs" / "exit_attribution.jsonl", n=12) if (ROOT / "logs" / "exit_attribution.jsonl").exists() else "",
        "system_events_tail": _tail_text(ROOT / "logs" / "system_events.jsonl", n=25) if (ROOT / "logs" / "system_events.jsonl").exists() else "",
    }

    source_meta = {
        "generated_at_utc": _now_iso(),
        "data_source": os.environ.get("TELEMETRY_DATA_SOURCE", "local"),
        "host": platform.node(),
        "platform": platform.platform(),
        "git_head": _git_head_short(),
        "date": day,
    }

    master = _render_master_md(
        day=day,
        source_meta=source_meta,
        health=health,
        shadow=shadow,
        universe=universe_summary,
        intel=intel_summary,
        tails=tails,
        copied_files=copied,
        missing=missing,
    )
    master_path = out_dir / f"FULL_TELEMETRY_{day}.md"
    copied.append(_copy_file_bytes(master_path, master.encode("utf-8", errors="replace")))

    # Manifest
    manifest = {
        "_meta": source_meta,
        "bundle_dir": str(out_dir.as_posix()),
        "copied_files": [cf.__dict__ for cf in copied if cf.kind != "generated" or cf.dest.endswith(".md")],
        "computed": {
            "shadow": shadow,
            "health": health,
        },
        "missing": missing,
    }
    man_path = out_dir / "telemetry_manifest.json"
    man_bytes = (json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8")
    man_path.write_bytes(man_bytes)

    # Add manifest to copied list (for completeness)
    copied.append(
        CopiedFile(
            kind="generated",
            source="",
            dest=str(man_path.as_posix()),
            bytes=len(man_bytes),
            sha256=_sha256_bytes(man_bytes),
        )
    )

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

