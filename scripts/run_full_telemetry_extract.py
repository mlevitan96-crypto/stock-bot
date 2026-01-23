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


def _write_json(path: Path, obj: Any) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    b = (json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8", errors="replace")
    path.write_bytes(b)
    return b


def _clean_dir_files(p: Path) -> None:
    """
    Best-effort: remove files under p (non-recursive).
    Used only inside telemetry output folders to keep runs idempotent.
    """
    try:
        if not p.exists() or not p.is_dir():
            return
        for child in p.iterdir():
            try:
                if child.is_file():
                    child.unlink()
            except Exception:
                continue
    except Exception:
        return


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
                # Additive: preserve entry intel snapshot for downstream signal-family analytics.
                "entry_intel_snapshot": intel_ent,
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
    computed: Dict[str, Any],
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

    # Computed artifacts index
    desc = {
        "feature_equalizer_builder.json": "Equalizer-ready per-feature realized outcome summaries.",
        "long_short_analysis.json": "Long vs short expectancy stats from realized shadow exits.",
        "exit_intel_completeness.json": "Exit attribution completeness + missing-key counts.",
        "feature_value_curves.json": "Per-feature value curves (binned) vs realized PnL.",
        "regime_sector_feature_matrix.json": "Regime/Sector → per-feature realized PnL matrix.",
        "shadow_vs_live_parity.json": "Shadow vs live entry-time parity (score/price/time) + aggregates.",
        "entry_parity_details.json": "Full per-entry parity rows (v1 vs v2) with deltas + classification.",
        "score_distribution_curves.json": "Score histograms + delta histograms by feature family (long/short split).",
        "regime_timeline.json": "Hourly (UTC) regime/posture timeline (best-effort) + day summary.",
        "feature_family_summary.json": "Per-family parity deltas + realized EV contribution + stability.",
        "replacement_telemetry_expanded.json": "Replacement rates by feature/family + cause histogram + anomaly flag.",
        "live_vs_shadow_pnl.json": "Rolling (24h/48h/5d) live vs shadow PnL/expectancy/win-rate deltas + per-symbol table.",
        "signal_performance.json": "Per-signal (feature-family) win rate/expectancy/trade count + regime/side breakdowns.",
        "signal_weight_recommendations.json": "Advisory (read-only) signal weight delta suggestions derived from performance.",
    }
    computed_files = [
        x for x in copied_files if x.kind == "generated" and "/computed/" in str(x.dest) and str(x.dest).endswith(".json")
    ]
    lines.append("## 1b. Computed Artifacts Index")
    if not computed_files:
        lines.append("- None (computed artifacts missing).")
    else:
        for cf in sorted(computed_files, key=lambda c: str(c.dest)):
            name = str(cf.dest).split("/")[-1]
            lines.append(f"- `{name}` — {desc.get(name, 'Computed telemetry artifact.')}")
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

    # Long/short asymmetry summary (computed)
    ls = computed.get("long_short_analysis") if isinstance(computed.get("long_short_analysis"), dict) else {}
    if ls:
        lines.append("### Long vs short asymmetry (realized shadow exits)")
        for k in ("overall", "long", "short"):
            g = ls.get(k) if isinstance(ls.get(k), dict) else {}
            if not g:
                continue
            lines.append(
                f"- **{k}**: n={g.get('count')} win_rate={g.get('win_rate')} "
                f"avg_pnl_usd={g.get('avg_pnl_usd')} expectancy_usd={g.get('expectancy_usd')}"
            )
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
    excomp = computed.get("exit_intel_completeness") if isinstance(computed.get("exit_intel_completeness"), dict) else {}
    if excomp:
        cnts = excomp.get("counts") if isinstance(excomp.get("counts"), dict) else {}
        lines.append(
            f"- Exit intel completeness: complete_rate={cnts.get('complete_rate')} "
            f"(complete={cnts.get('complete_records')} / total={cnts.get('exit_attribution_records')})"
        )
    lines.append("")

    # Feature value curve highlights (computed)
    fvc = computed.get("feature_value_curves") if isinstance(computed.get("feature_value_curves"), dict) else {}
    if fvc and isinstance(fvc.get("features"), dict):
        lines.append("## 4b. Feature Value Curve Highlights")
        for feat, fb in list((fvc.get("features") or {}).items())[:50]:
            if not isinstance(fb, dict):
                continue
            bins = fb.get("overall") if isinstance(fb.get("overall"), list) else []
            if not bins:
                continue
            best = max(bins, key=lambda r: float((r or {}).get("avg_pnl_usd") or 0.0))
            worst = min(bins, key=lambda r: float((r or {}).get("avg_pnl_usd") or 0.0))
            # crude monotonicity: fraction of adjacent deltas matching overall slope
            ys = [float((r or {}).get("avg_pnl_usd") or 0.0) for r in bins]
            slope = ys[-1] - ys[0] if ys else 0.0
            good = 0
            tot = 0
            for i in range(1, len(ys)):
                dy = ys[i] - ys[i - 1]
                if dy == 0:
                    continue
                tot += 1
                if slope >= 0 and dy > 0:
                    good += 1
                if slope < 0 and dy < 0:
                    good += 1
            mono = (good / float(tot)) if tot else 0.0
            lines.append(
                f"- **{feat}** best[{best.get('x_lo')},{best.get('x_hi')}] avg_pnl_usd={best.get('avg_pnl_usd')} | "
                f"worst[{worst.get('x_lo')},{worst.get('x_hi')}] avg_pnl_usd={worst.get('avg_pnl_usd')} | monotonicity={round(mono,3)}"
            )
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

    # Feature equalizer summary (computed)
    feq = computed.get("feature_equalizer") if isinstance(computed.get("feature_equalizer"), dict) else {}
    if feq:
        feats = feq.get("features") if isinstance(feq.get("features"), dict) else {}
        lines.append("## 6b. Feature Equalizer Snapshot (shadow-only, realized)")
        if not feats:
            lines.append("- No feature-level stats available (no realized exits with attribution).")
        else:
            # Top 6 features by sample count
            ranked = sorted(feats.items(), key=lambda kv: int((kv[1] or {}).get("count") or 0), reverse=True)
            for name, st in ranked[:6]:
                lines.append(f"- **{name}**: n={st.get('count')} win_rate={st.get('win_rate')} avg_pnl_usd={st.get('avg_pnl_usd')}")
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

    # Regime/sector matrix highlights (computed)
    rsm = computed.get("regime_sector_feature_matrix") if isinstance(computed.get("regime_sector_feature_matrix"), dict) else {}
    if rsm and isinstance(rsm.get("matrix"), dict):
        lines.append("## Regime/Sector Matrix Highlights")
        best_cell = None
        worst_cell = None
        for reg, sectors in (rsm.get("matrix") or {}).items():
            if not isinstance(sectors, dict):
                continue
            for sec, cell in sectors.items():
                if not isinstance(cell, dict):
                    continue
                ccell = cell.get("_cell") if isinstance(cell.get("_cell"), dict) else {}
                key = (str(reg), str(sec))
                row = {"key": key, **ccell}
                if best_cell is None or float(row.get("total_pnl_usd") or 0.0) > float(best_cell.get("total_pnl_usd") or 0.0):
                    best_cell = row
                if worst_cell is None or float(row.get("total_pnl_usd") or 0.0) < float(worst_cell.get("total_pnl_usd") or 0.0):
                    worst_cell = row
        if best_cell:
            lines.append(f"- Strongest cell: **{best_cell.get('key')}** total_pnl_usd={best_cell.get('total_pnl_usd')} count={best_cell.get('count')}")
        if worst_cell:
            lines.append(f"- Weakest cell: **{worst_cell.get('key')}** total_pnl_usd={worst_cell.get('total_pnl_usd')} count={worst_cell.get('count')}")
        lines.append("")

    # Entry-time parity summary (computed)
    parity = computed.get("shadow_vs_live_parity") if isinstance(computed.get("shadow_vs_live_parity"), dict) else {}
    if parity:
        lines.append("## Entry-Time Parity Summary")
        notes = parity.get("notes") if isinstance(parity.get("notes"), dict) else {}
        agg = parity.get("aggregate_metrics") if isinstance(parity.get("aggregate_metrics"), dict) else {}
        lines.append(f"- Parity available: **{notes.get('parity_available')}**")
        lines.append(f"- Match rate (perfect|near): **{agg.get('match_rate')}** (pairs={agg.get('matched_pairs')})")
        lines.append(f"- Mean ts delta (s): **{agg.get('mean_entry_ts_delta_seconds')}**")
        lines.append(f"- Mean score delta (v2-v1): **{agg.get('mean_score_delta')}**")
        lines.append(f"- Mean price delta (USD): **{agg.get('mean_price_delta_usd')}**")
        # Top divergences (by abs score delta then abs price delta)
        try:
            rows = []
            ep = parity.get("entry_parity") if isinstance(parity.get("entry_parity"), dict) else {}
            if isinstance(ep.get("rows"), list):
                rows = [r for r in ep.get("rows") if isinstance(r, dict)]
            rows2 = sorted(
                rows,
                key=lambda r: (abs(float(r.get("score_delta") or 0.0)), abs(float(r.get("price_delta_usd") or 0.0))),
                reverse=True,
            )
            if rows2:
                lines.append("- Top divergences (by |score_delta|, |price_delta_usd|):")
                for r in rows2[:10]:
                    lines.append(
                        f"  - **{r.get('symbol')}** cls={r.get('classification')} "
                        f"ts_delta_s={r.get('entry_ts_delta_seconds')} score_delta={r.get('score_delta')} price_delta_usd={r.get('price_delta_usd')}"
                    )
        except Exception:
            pass
        lines.append("")

    # Score distribution summary (computed)
    sdc = computed.get("score_distribution_curves") if isinstance(computed.get("score_distribution_curves"), dict) else {}
    if sdc and isinstance(sdc.get("families"), dict):
        lines.append("## Score Distribution Summary")
        # report a couple of high-signal families
        for fam in ("flow", "darkpool", "alignment"):
            fam_block = (sdc.get("families") or {}).get(fam) if isinstance((sdc.get("families") or {}).get(fam), dict) else {}
            overall = fam_block.get("overall") if isinstance(fam_block.get("overall"), dict) else {}
            delta_hist = overall.get("score_delta_hist") if isinstance(overall.get("score_delta_hist"), dict) else {}
            lines.append(f"- **{fam}** delta_hist.n={delta_hist.get('n')} bins={len(delta_hist.get('counts') or [])}")
        lines.append("")

    # Replacement telemetry summary (computed)
    rte = computed.get("replacement_telemetry_expanded") if isinstance(computed.get("replacement_telemetry_expanded"), dict) else {}
    if rte:
        lines.append("## Replacement Telemetry Summary")
        cnts = rte.get("counts") if isinstance(rte.get("counts"), dict) else {}
        lines.append(f"- Replacement rate: **{cnts.get('replacement_rate')}** (repl={cnts.get('replacement_trades')} / total={cnts.get('realized_trades')})")
        lines.append(f"- Replacement anomaly detected: **{rte.get('replacement_anomaly_detected')}**")
        # top replaced features (by rate, denom>=3)
        pf = rte.get("per_feature_replacement_rate") if isinstance(rte.get("per_feature_replacement_rate"), dict) else {}
        ranked = sorted(
            [(k, v) for k, v in pf.items() if isinstance(v, dict)],
            key=lambda kv: float((kv[1] or {}).get("replacement_rate") or 0.0),
            reverse=True,
        )
        if ranked:
            lines.append("- Top replaced features:")
            for k, v in ranked[:10]:
                lines.append(f"  - **{k}** rate={v.get('replacement_rate')} denom={v.get('denom')} numer={v.get('numer')}")
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
    _ensure_dir(out_dir / "computed")
    _clean_dir_files(out_dir / "computed")

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
        "logs/attribution.jsonl",
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

    # Additional computed telemetry artifacts (equalizer-ready)
    # NOTE: imports happen here (after sys.path injection) to avoid ModuleNotFoundError
    # when executing this script directly.
    from telemetry.exit_intel_completeness import build_exit_intel_completeness  # type: ignore
    from telemetry.feature_equalizer_builder import build_feature_equalizer  # type: ignore
    from telemetry.feature_value_curves import build_feature_value_curves  # type: ignore
    from telemetry.feature_family_summary import build_feature_family_summary  # type: ignore
    from telemetry.long_short_analysis import build_long_short_analysis  # type: ignore
    from telemetry.live_vs_shadow_pnl import build_live_vs_shadow_pnl  # type: ignore
    from telemetry.regime_sector_feature_matrix import build_regime_sector_feature_matrix  # type: ignore
    from telemetry.regime_timeline import build_regime_timeline  # type: ignore
    from telemetry.replacement_telemetry_expanded import build_replacement_telemetry_expanded  # type: ignore
    from telemetry.score_distribution_curves import build_score_distribution_curves  # type: ignore
    from telemetry.shadow_vs_live_parity import build_shadow_vs_live_parity  # type: ignore
    from telemetry.signal_performance import build_signal_performance  # type: ignore
    from telemetry.signal_weight_recommendations import build_signal_weight_recommendations  # type: ignore

    exit_attrib_today: List[Dict[str, Any]] = []
    for rec in _iter_jsonl(ROOT / "logs" / "exit_attribution.jsonl"):
        ts = rec.get("timestamp") or rec.get("ts")
        if _utc_day_from_ts(ts) == day:
            exit_attrib_today.append(rec)

    # v1 attribution log (best-effort parity input)
    v1_attrib_path = ROOT / "logs" / "attribution.jsonl"
    computed: Dict[str, Any] = {}
    try:
        computed["feature_equalizer"] = build_feature_equalizer(day=day, realized_trades=shadow.get("realized_trades") or [])
    except Exception as e:
        computed["feature_equalizer"] = {"error": str(e)}
    try:
        computed["long_short_analysis"] = build_long_short_analysis(day=day, realized_trades=shadow.get("realized_trades") or [])
    except Exception as e:
        computed["long_short_analysis"] = {"error": str(e)}
    try:
        computed["exit_intel_completeness"] = build_exit_intel_completeness(day=day, exit_attrib_recs=exit_attrib_today)
    except Exception as e:
        computed["exit_intel_completeness"] = {"error": str(e)}
    try:
        computed["feature_value_curves"] = build_feature_value_curves(day=day, realized_trades=shadow.get("realized_trades") or [])
    except Exception as e:
        computed["feature_value_curves"] = {"error": str(e)}
    try:
        computed["regime_sector_feature_matrix"] = build_regime_sector_feature_matrix(day=day, realized_trades=shadow.get("realized_trades") or [])
    except Exception as e:
        computed["regime_sector_feature_matrix"] = {"error": str(e)}
    try:
        computed["shadow_vs_live_parity"] = build_shadow_vs_live_parity(
            day=day,
            v1_attribution_log_path=str(v1_attrib_path),
            shadow_trades_log_path=str(ROOT / "logs" / "shadow_trades.jsonl"),
        )
    except Exception as e:
        computed["shadow_vs_live_parity"] = {"error": str(e)}

    # Derived from parity rows (separate required artifact)
    parity_rows: List[Dict[str, Any]] = []
    try:
        parity_doc = computed.get("shadow_vs_live_parity")
        if isinstance(parity_doc, dict):
            ep = parity_doc.get("entry_parity") if isinstance(parity_doc.get("entry_parity"), dict) else {}
            rows = ep.get("rows") if isinstance(ep.get("rows"), list) else []
            parity_rows = [r for r in rows if isinstance(r, dict)]
        computed["entry_parity_details"] = {
            "_meta": {"date": str(day), "kind": "entry_parity_details", "version": "2026-01-22_v1"},
            "rows": parity_rows,
        }
    except Exception as e:
        computed["entry_parity_details"] = {"error": str(e), "rows": []}

    try:
        computed["score_distribution_curves"] = build_score_distribution_curves(day=day, entry_parity_rows=parity_rows)
    except Exception as e:
        computed["score_distribution_curves"] = {"error": str(e)}

    try:
        computed["regime_timeline"] = build_regime_timeline(
            day=day,
            v1_attribution_log_path=str(v1_attrib_path),
            shadow_trades_log_path=str(ROOT / "logs" / "shadow_trades.jsonl"),
            regime_state=regime_state if isinstance(regime_state, dict) else None,
            posture_state=_read_json(ROOT / "state" / "regime_posture_state.json") if (ROOT / "state" / "regime_posture_state.json").exists() else None,
            market_context=_read_json(ROOT / "state" / "market_context_v2.json") if (ROOT / "state" / "market_context_v2.json").exists() else None,
        )
    except Exception as e:
        computed["regime_timeline"] = {"error": str(e)}

    try:
        computed["feature_family_summary"] = build_feature_family_summary(
            day=day,
            entry_parity_rows=parity_rows,
            realized_trades=shadow.get("realized_trades") or [],
        )
    except Exception as e:
        computed["feature_family_summary"] = {"error": str(e)}

    try:
        computed["replacement_telemetry_expanded"] = build_replacement_telemetry_expanded(
            day=day, realized_trades=shadow.get("realized_trades") or []
        )
    except Exception as e:
        computed["replacement_telemetry_expanded"] = {"error": str(e)}

    # Live vs shadow PnL (rolling windows, UTC)
    try:
        computed["live_vs_shadow_pnl"] = build_live_vs_shadow_pnl(
            attribution_log_path=str(ROOT / "logs" / "attribution.jsonl"),
            shadow_exit_attribution_log_path=str(ROOT / "logs" / "exit_attribution.jsonl"),
        )
    except Exception as e:
        computed["live_vs_shadow_pnl"] = {"error": str(e), "as_of_ts": _now_iso(), "windows": {}, "per_symbol": []}

    # Per-signal performance + advisory recommendations (shadow realized trades)
    try:
        computed["signal_performance"] = build_signal_performance(realized_trades=shadow.get("realized_trades") or [])
    except Exception as e:
        computed["signal_performance"] = {"error": str(e), "as_of_ts": _now_iso(), "signals": []}
    try:
        sp = computed.get("signal_performance") if isinstance(computed.get("signal_performance"), dict) else {}
        computed["signal_weight_recommendations"] = build_signal_weight_recommendations(signal_performance=sp)
    except Exception as e:
        computed["signal_weight_recommendations"] = {"error": str(e), "as_of_ts": _now_iso(), "recommendations": []}

    # Persist computed artifacts into bundle folder
    computed_files: Dict[str, str] = {}
    filename_map = {
        "feature_equalizer": "feature_equalizer_builder.json",
        "long_short_analysis": "long_short_analysis.json",
        "exit_intel_completeness": "exit_intel_completeness.json",
        "feature_value_curves": "feature_value_curves.json",
        "regime_sector_feature_matrix": "regime_sector_feature_matrix.json",
        "shadow_vs_live_parity": "shadow_vs_live_parity.json",
        "entry_parity_details": "entry_parity_details.json",
        "score_distribution_curves": "score_distribution_curves.json",
        "regime_timeline": "regime_timeline.json",
        "feature_family_summary": "feature_family_summary.json",
        "replacement_telemetry_expanded": "replacement_telemetry_expanded.json",
        "live_vs_shadow_pnl": "live_vs_shadow_pnl.json",
        "signal_performance": "signal_performance.json",
        "signal_weight_recommendations": "signal_weight_recommendations.json",
    }
    for name, obj in computed.items():
        fp = out_dir / "computed" / filename_map.get(name, f"{name}.json")
        _write_json(fp, obj)
        copied.append(CopiedFile(kind="generated", source="", dest=str(fp.as_posix()), bytes=fp.stat().st_size, sha256=_sha256_file(fp)))
        computed_files[name] = str(fp.as_posix())

    master = _render_master_md(
        day=day,
        source_meta=source_meta,
        health=health,
        shadow=shadow,
        computed=computed,
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
        "copied_files": [cf.__dict__ for cf in copied],
        "computed": {
            "shadow": shadow,
            "health": health,
            "feature_equalizer": computed.get("feature_equalizer"),
            "long_short_analysis": computed.get("long_short_analysis"),
            "exit_intel_completeness": computed.get("exit_intel_completeness"),
            "feature_value_curves": computed.get("feature_value_curves"),
            "regime_sector_feature_matrix": computed.get("regime_sector_feature_matrix"),
            "shadow_vs_live_parity": computed.get("shadow_vs_live_parity"),
            "entry_parity_details": computed.get("entry_parity_details"),
            "score_distribution_curves": computed.get("score_distribution_curves"),
            "regime_timeline": computed.get("regime_timeline"),
            "feature_family_summary": computed.get("feature_family_summary"),
            "replacement_telemetry_expanded": computed.get("replacement_telemetry_expanded"),
            "live_vs_shadow_pnl": computed.get("live_vs_shadow_pnl"),
            "signal_performance": computed.get("signal_performance"),
            "signal_weight_recommendations": computed.get("signal_weight_recommendations"),
            "computed_files": computed_files,
        },
        "missing": missing,
    }
    man_path = out_dir / "telemetry_manifest.json"
    man_bytes = _write_json(man_path, manifest)

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

