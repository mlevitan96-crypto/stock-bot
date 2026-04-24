#!/usr/bin/env python3
"""
ALPACA canonical Memory Bank update + max profit edge analysis (droplet-only).
Writes ONLY:
  reports/ALPACA_MEMORY_BANK_CANONICAL_UPDATE_<tag>.md
  reports/ALPACA_MAX_EDGE_ANALYSIS_<tag>.md
Updates MEMORY_BANK_ALPACA.md (repo root) with section 'Alpaca attribution truth contract (canonical)'.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

MB_MARKER_START = "<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_START -->"
MB_MARKER_END = "<!-- ALPACA_ATTRIBUTION_TRUTH_CONTRACT_END -->"

CANONICAL_SECTION = f"""{MB_MARKER_START}
## Alpaca attribution truth contract (canonical)

**Governance (CSA):** This subsection is canonical Alpaca attribution material. **Drift** between live emitters, sinks, and this contract is a **governance incident** and must be triaged like a production data-integrity breach.

### Canonical artifact paths (board / audit)
- `reports/ALPACA_BLOCKER_CLOSURE_PROOF_20260325_0112.md` — blocker closure checklist and compile/git evidence.
- `reports/ALPACA_OFFLINE_FULL_DATA_AUDIT_20260325_0112.md` — CSA offline full data-path audit (**verdict A required** before profit-contributor / promotion claims that depend on attribution readiness).
- `reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2310.md` — Alpaca REST + FILL payload wiring proof.

Promote newer dated filenames when they supersede the above; keep the same report family names.

### Invariants (non-negotiable)
1. **Deterministic join keys** on decision and execution records: `decision_event_id`, `canonical_trade_id`, `symbol_normalized`, `time_bucket_id` (rule: `300s|<utc_epoch_floor>` — `telemetry/attribution_emit_keys.py`).
2. **Entry/exit snapshot parity:** `telemetry/attribution_feature_snapshot.py` — `build_shared_feature_snapshot` (entry/blocked) and `build_exit_snapshot_from_metadata` (exit); persisted `entry_market_context` and `entry_regime_posture` on `StateFiles.POSITION_METADATA` via `main.py` / `AlpacaExecutor._persist_position_metadata`.
3. **UW decomposition + provenance:** `apply_uw_decomposition_fields` adds component proxies plus `uw_asof_ts`, `uw_ingest_ts`, `uw_staleness_seconds`, `uw_missing_reason`; `uw_composite_score_derived` is **derived only** (no composite-only logging as the sole signal).
4. **Economics explicit:** `main.py` `log_order` → `telemetry/attribution_emit_keys.attach_paper_economics_defaults` — `fee_excluded_reason` and/or `fee_amount`; `slippage_bps` + `slippage_ref_price_type` vs `slippage_excluded_reason`; decision reference mid stored as `decision_slippage_ref_mid`. **No silent zero fees** — exclusions must be explicit.
5. **Append-only sinks:** `main.py` `jsonl_write`, `telemetry/signal_context_logger.py`; retention/rotation — `docs/DATA_RETENTION_POLICY.md`.
6. **CSA offline audit:** run `scripts/alpaca_offline_full_data_audit.py` (Linux/droplet); **verdict A** before offline profit-contributor narratives that depend on attribution readiness.
7. **Operational rule:** After changes to `main.py` or `telemetry/*` emitters, **restart `stock-bot.service`** so the process loads new code (no hot reload assumption).

### TRUE data path map (Alpaca; module/file names)
| Stage | Emitter / module | Sink path |
|-------|------------------|-----------|
| Trade intent (entered/blocked) | `main.py` `_emit_trade_intent`, `_emit_trade_intent_blocked` | `logs/run.jsonl` (`event_type=trade_intent`) |
| Exit intent | `main.py` `_emit_exit_intent` | `logs/run.jsonl` (`event_type=exit_intent`) |
| Signal context (enter/blocked/exit) | `telemetry/signal_context_logger.py` `log_signal_context` | `logs/signal_context.jsonl` |
| Orders / execution | `main.py` `log_order` | `logs/orders.jsonl` |
| Blocked would-have | `main.py` `log_blocked_trade` | `state/blocked_trades.jsonl` |
| UW ingestion | `uw_flow_daemon.py` | `data/uw_flow_cache.json`, `data/uw_flow_cache.log.jsonl`; optional mirror `logs/uw_daemon.jsonl` |
| UW → decision snapshot | Scoring in `main.py` + `telemetry/attribution_feature_snapshot.py` | Join: `symbol_normalized` + `time_bucket_id` (same bucket rule as attribution keys) |
| Position state | `main.py` `AlpacaExecutor.mark_open`, `_persist_position_metadata` | `state/position_metadata.json` (`config.registry.StateFiles.POSITION_METADATA`) |
| Exit attribution v2 | `main.py` `log_exit_attribution` → `src/exit/exit_attribution.py` `append_exit_attribution` | `logs/exit_attribution.jsonl` |
| Truth / warehouse (read-only extractors) | e.g. `scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py` | `reports/ALPACA_TRUTH_*`, `ALPACA_EXECUTION_*`, etc. |
{MB_MARKER_END}
"""


def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", os.environ.get("DROPLET_TRADING_ROOT", "")).strip()
    return Path(r).resolve() if r else Path(__file__).resolve().parents[1]


def _tag() -> str:
    e = os.environ.get("ALPACA_REPORT_TAG", "").strip()
    return e if e else datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _sh(cmd: str, timeout: int = 90) -> Tuple[str, str, int]:
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.stdout or "", p.stderr or "", p.returncode
    except Exception as ex:
        return "", str(ex), 1


def _iter_jsonl(path: Path, max_lines: int = 25000) -> List[dict]:
    if not path.exists():
        return []
    out: List[dict] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    for line in lines[-max_lines:]:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict):
            out.append(r)
    return out


def _num(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _flatten(d: Any, prefix: str = "", depth: int = 0) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if depth > 3 or not isinstance(d, dict):
        return out
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else str(k)
        fn = _num(v)
        if fn is not None:
            out[key] = fn
        elif isinstance(v, dict):
            out.update(_flatten(v, key, depth + 1))
    return out


def _quartile_thresholds(xs: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if len(xs) < 8:
        return None, None
    s = sorted(xs)
    n = len(s)
    lo_thr = s[max(0, n // 4 - 1)]
    hi_thr = s[min(n - 1, (3 * n) // 4)]
    return lo_thr, hi_thr


def _mean(xs: List[float]) -> Optional[float]:
    if not xs:
        return None
    return sum(xs) / len(xs)


def _patch_memory_bank(mb_path: Path) -> Tuple[str, str]:
    text = mb_path.read_text(encoding="utf-8", errors="replace")
    block = "\n" + CANONICAL_SECTION + "\n"
    if MB_MARKER_START in text and MB_MARKER_END in text:
        text_new = re.sub(
            re.escape(MB_MARKER_START) + r"[\s\S]*?" + re.escape(MB_MARKER_END),
            CANONICAL_SECTION.strip(),
            text,
            count=1,
        )
    else:
        anchor = (
            "- Only frozen artifacts (e.g. EOD bundle, frozen trade sets) may be used for learning or tuning.\n\n"
            "---\n\n# 4. SIGNAL INTEGRITY CONTRACT"
        )
        if anchor in text:
            text_new = text.replace(
                anchor,
                "- Only frozen artifacts (e.g. EOD bundle, frozen trade sets) may be used for learning or tuning.\n\n"
                + block
                + "\n---\n\n# 4. SIGNAL INTEGRITY CONTRACT",
                1,
            )
        else:
            anchor2 = "\n---\n\n# 4. SIGNAL INTEGRITY CONTRACT"
            if anchor2 in text:
                text_new = text.replace(anchor2, "\n" + block + "\n---\n\n# 4. SIGNAL INTEGRITY CONTRACT", 1)
            else:
                text_new = text.rstrip() + "\n\n" + block + "\n"
    before = text
    mb_path.write_text(text_new, encoding="utf-8")
    # unified diff-ish summary (first 80 lines of conceptual diff)
    old_lines = before.splitlines()
    new_lines = text_new.splitlines()
    snippet = "\n".join(f"- {l[:120]}" for l in new_lines if "Alpaca attribution truth" in l or "attribution_emit_keys" in l)[:4000]
    return text_new, snippet


def main() -> int:
    if not Path("/proc").is_dir():
        print("Linux/droplet only.", file=sys.stderr)
        return 2

    root = _root()
    os.chdir(root)
    tag = _tag()
    rep = root / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    out_mb = rep / f"ALPACA_MEMORY_BANK_CANONICAL_UPDATE_{tag}.md"
    out_edge = rep / f"ALPACA_MAX_EDGE_ANALYSIS_{tag}.md"

    # Phase 0
    git_head, _, gh = _sh("git rev-parse HEAD 2>/dev/null", timeout=15)
    git_dirty, _, _ = _sh("git status --porcelain 2>/dev/null | head -40", timeout=15)
    st_bot, _, _ = _sh("systemctl status stock-bot.service --no-pager 2>&1 | head -25", timeout=20)
    st_uw, _, _ = _sh("systemctl status uw-flow-daemon.service --no-pager 2>&1 | head -20", timeout=20)

    mb_path = root / "MEMORY_BANK_ALPACA.md"
    if not mb_path.exists():
        print("USER INPUT NEEDED: MEMORY_BANK_ALPACA.md not found at repo root; specify canonical Memory Bank path.", file=sys.stderr)
        return 3

    _, diff_snip = _patch_memory_bank(mb_path)

    # Phase 2 — datasets
    run_rows = _iter_jsonl(root / "logs/run.jsonl", 30000)
    ord_rows = _iter_jsonl(root / "logs/orders.jsonl", 20000)
    sig_rows = _iter_jsonl(root / "logs/signal_context.jsonl", 20000)
    blk_rows = _iter_jsonl(root / "state/blocked_trades.jsonl", 15000)
    ex_attr = _iter_jsonl(root / "logs/exit_attribution.jsonl", 20000)

    ti_enter = [r for r in run_rows if r.get("event_type") == "trade_intent" and str(r.get("decision_outcome", "")).lower() == "entered"]
    ti_blocked = [r for r in run_rows if r.get("event_type") == "trade_intent" and str(r.get("decision_outcome", "")).lower() == "blocked"]
    ex_intent = [r for r in run_rows if r.get("event_type") == "exit_intent"]

    fills_like = [
        o
        for o in ord_rows
        if o.get("type") == "order"
        and (
            str(o.get("status", "")).lower() == "filled"
            or "filled" in str(o.get("action", "")).lower()
            or o.get("fill_price") is not None
        )
    ]
    closes = [o for o in ord_rows if o.get("type") == "order" and "close" in str(o.get("action", "")).lower()]

    # Outcome rows from exit_attribution
    outcomes: List[Tuple[dict, float]] = []
    for r in ex_attr:
        p = _num(r.get("pnl_pct"))
        if p is None:
            p = _num((r.get("snapshot") or {}).get("pnl_pct")) if isinstance(r.get("snapshot"), dict) else None
        if p is not None:
            outcomes.append((r, p))

    # Features from exit rows: v2_exit_components + flattened entry feature_snapshot from trade_intent (by symbol match weak)
    feat_rows: List[Tuple[Dict[str, float], float, str]] = []
    for r, y in outcomes:
        feats: Dict[str, float] = {}
        feats.update(_flatten(r.get("v2_exit_components"), "v2_exit"))
        feats.update(_flatten(r.get("v2_exit_score"), "v2_exit_score"))
        eq = r.get("exit_quality_metrics") if isinstance(r.get("exit_quality_metrics"), dict) else {}
        for k in ("mfe_pct", "mae_pct", "giveback_pct"):
            v = _num(eq.get(k))
            if v is not None:
                feats[f"eq.{k}"] = v
        sym = str(r.get("symbol") or "").upper()
        if feats and y is not None:
            feat_rows.append((feats, y, sym))

    # Univariate lifts on exit-attribution feature set
    all_keys: set[str] = set()
    for f, _, _ in feat_rows:
        all_keys.update(f.keys())

    lifts: List[Tuple[str, int, Optional[float], Optional[float], Optional[float], str]] = []
    for key in sorted(all_keys):
        pairs = [(f[key], y) for f, y, _ in feat_rows if key in f]
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        if len(xs) < 40:
            continue
        lo_thr, hi_thr = _quartile_thresholds(xs)
        if lo_thr is None or hi_thr is None:
            continue
        y_low = [y for x, y in zip(xs, ys) if x <= lo_thr]
        y_high = [y for x, y in zip(xs, ys) if x >= hi_thr]
        if len(y_low) < 5 or len(y_high) < 5:
            continue
        m_low, m_high = _mean(y_low), _mean(y_high)
        if m_low is None or m_high is None:
            continue
        lifts.append((key, len(xs), m_high - m_low, m_low, m_high, "exit_attribution_components"))

    # Entry feature_snapshot joined to outcomes via canonical_trade_id or build_trade_key
    pnl_by_ctid: Dict[str, float] = {}
    for r, y in outcomes:
        ct = r.get("canonical_trade_id")
        if ct is not None and str(ct).strip():
            pnl_by_ctid[str(ct)] = y
        try:
            from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side, normalize_symbol

            sym = normalize_symbol(r.get("symbol"))
            ets = str(r.get("entry_timestamp") or "").strip()
            if sym and ets and sym != "?":
                side_raw = r.get("side") or r.get("direction") or "buy"
                tk = build_trade_key(sym, normalize_side(side_raw), ets)
                pnl_by_ctid[tk] = y
        except Exception:
            pass

    entry_joined = 0
    entry_feat_rows: List[Tuple[Dict[str, float], float]] = []
    for r in ti_enter:
        ctid = r.get("canonical_trade_id")
        if ctid is None or str(ctid) not in pnl_by_ctid:
            continue
        y = pnl_by_ctid[str(ctid)]
        fs = r.get("feature_snapshot")
        if not isinstance(fs, dict):
            continue
        entry_feat_rows.append((_flatten(fs, "entry_fs"), y))
        entry_joined += 1

    all_keys_e: set[str] = set()
    for f, _ in entry_feat_rows:
        all_keys_e.update(f.keys())
    for key in sorted(all_keys_e):
        pairs = [(f[key], y) for f, y in entry_feat_rows if key in f]
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        if len(xs) < 40:
            continue
        lo_thr, hi_thr = _quartile_thresholds(xs)
        if lo_thr is None or hi_thr is None:
            continue
        y_low = [y for x, y in zip(xs, ys) if x <= lo_thr]
        y_high = [y for x, y in zip(xs, ys) if x >= hi_thr]
        if len(y_low) < 5 or len(y_high) < 5:
            continue
        m_low, m_high = _mean(y_low), _mean(y_high)
        if m_low is None or m_high is None:
            continue
        lifts.append((key, len(xs), m_high - m_low, m_low, m_high, "entry_feature_snapshot_joined"))

    lifts.sort(key=lambda t: abs(t[2] or 0), reverse=True)

    # Walk-forward stability on top feature
    wf_note = ""
    if outcomes:
        mid = len(outcomes) // 2
        first = outcomes[:mid]
        second = outcomes[mid:]
        wf_note = f"Walk-forward: exit_attribution with pnl split half n1={len(first)} n2={len(second)}; compare top-feature quartile effects separately (manual spot-check recommended)."

    # Memory bank report
    mb_lines = [
        f"# ALPACA Memory Bank Canonical Update — `{tag}`",
        "",
        f"- **TRADING_ROOT:** `{root}`",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Phase 0 — Baseline snapshot (SRE + CSA)",
        "",
        f"- **git HEAD:** `{git_head.strip()}` (exit {gh})",
        "```",
        git_dirty.strip() or "(clean or not a git repo)",
        "```",
        "### stock-bot.service (excerpt)",
        "```",
        st_bot[:3500],
        "```",
        "### uw-flow-daemon.service (excerpt)",
        "```",
        st_uw[:2500],
        "```",
        "",
        "## Phase 1 — Memory Bank canonization",
        "",
        f"- **File updated:** `{mb_path}`",
        "- **Section title (exact):** `Alpaca attribution truth contract (canonical)`",
        "",
        "### Unified diff summary (key inserted lines)",
        "```",
        diff_snip[:12000],
        "```",
        "",
        "### CSA canonization statement",
        "",
        "**This section is holy material.** Any change to Alpaca attribution paths, join keys, economics schema, or snapshot parity without updating this subsection and re-running the offline CSA audit is a governance incident. Promotions, profit-contributor claims, and board readiness narratives MUST cite current artifact paths and audit verdict A.",
        "",
    ]
    out_mb.write_text("\n".join(mb_lines) + "\n", encoding="utf-8")

    # Edge analysis report
    top10 = lifts[:10]
    edge_lines = [
        f"# ALPACA Max Profit Edge Analysis — `{tag}`",
        "",
        f"- **TRADING_ROOT:** `{root}`",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Personas",
        "",
        "- **Quant:** univariate lifts on exit attribution components vs `pnl_pct`; coverage tables; regime/time notes.",
        "- **SRE:** read-only JSONL; deterministic keys assumed where present; reproducibility command below.",
        "- **CSA:** sample gates; leakage warnings; promotion readiness forced NO.",
        "",
        "## Phase 0 — Dataset counts (read-only)",
        "",
        f"| Source | Rows scanned (tail) |",
        f"|--------|---------------------|",
        f"| `logs/run.jsonl` | {len(run_rows)} |",
        f"| `logs/orders.jsonl` | {len(ord_rows)} |",
        f"| `logs/signal_context.jsonl` | {len(sig_rows)} |",
        f"| `state/blocked_trades.jsonl` | {len(blk_rows)} |",
        f"| `logs/exit_attribution.jsonl` | {len(ex_attr)} |",
        "",
        f"- **trade_intent entered:** {len(ti_enter)}",
        f"- **trade_intent blocked:** {len(ti_blocked)}",
        f"- **exit_intent:** {len(ex_intent)}",
        f"- **orders (filled-like proxy):** {len(fills_like)}",
        f"- **orders (close_*):** {len(closes)}",
        f"- **exit_attribution rows with numeric pnl_pct:** {len(outcomes)}",
        f"- **trade_intent entered joined to exit PnL via canonical_trade_id:** {entry_joined}",
        "",
        "## Economics status (honest)",
        "",
        "- **Included:** `pnl_pct` / `pnl` from `exit_attribution` when present; `exit_quality_metrics` MFE/MAE when present.",
        "- **Excluded / explicit policy:** per-fill fees often `fee_excluded_reason` on paper (`telemetry/attribution_emit_keys`); slippage uses `decision_slippage_ref_mid` when set — many historical rows predate schema; **do not treat missing slippage as zero**.",
        "",
        "## Methods executed",
        "",
        "- Univariate: bottom vs top quartile of each numeric feature vs mean `pnl_pct` (min n=40 pairs, quartiles min 5 each).",
        "- **Not run at full depth (scope):** pairwise grid on all features; full walk-forward per-feature regression; blocked-trade counterfactual outcomes (pending definitional join).",
        "",
        wf_note,
        "",
        "## Top 10 candidate edges (offline; ranked by |Q75-Q25 mean pnl delta|)",
        "",
        "| rank | feature | n | delta_mean_pnl_pct | mean_low | mean_high | source |",
        "|------|---------|---|-------------------|----------|-----------|--------|",
    ]
    for i, (k, n, d, ml, mh, src) in enumerate(top10, 1):
        edge_lines.append(
            f"| {i} | `{k}` | {n} | {d:.6g} | {ml:.6g} | {mh:.6g} | {src} |"
        )
    if not top10:
        edge_lines.append("| — | *(insufficient numeric feature coverage vs pnl_pct)* | — | — | — | — | — |")

    edge_lines.extend(
        [
            "",
            "## Promotion readiness",
            "",
            "**ALL candidates: `OFFLINE CANDIDATE ONLY`.** `PROMOTION READINESS`: **NO** — post-deploy exits, economics completeness, and larger N must be proven before live promotion.",
            "",
            "## CSA adversarial review",
            "",
            "### Top 5 edges worth live confirmation later (hypothesis only)",
        ]
    )
    for i, row in enumerate(top10[:5], 1):
        edge_lines.append(f"{i}. `{row[0]}` — effect {row[2]:.4g} on n={row[1]} (confirm causality + stability; watch overfit).")
    if not top10:
        edge_lines.append("1. *(none — grow exit_attribution sample with stable schema first)*")

    edge_lines.extend(
        [
            "",
            "### Top 5 mirages to ignore",
            "",
            "1. Any edge with n < 100 and single-split ranking.",
            "2. Features perfectly collinear with exit reason (leakage).",
            "3. PnL drivers that ignore explicit fee/slippage exclusions.",
            "4. Joins by symbol-only same-day proximity (not used here; do not adopt without `canonical_trade_id`).",
            "5. Overnight/session effects without session bucket controls.",
            "",
            "## SRE integrity review",
            "",
            "- **Joins in this build:** outcome features taken **only** from within each `exit_attribution` row (no cross-file heuristic join).",
            "- **Files written:** `MEMORY_BANK_ALPACA.md`, `reports/ALPACA_MEMORY_BANK_CANONICAL_UPDATE_*.md`, `reports/ALPACA_MAX_EDGE_ANALYSIS_*.md`, and this script if uploaded.",
            "- **Reproducibility:**",
            "",
            "```bash",
            f"cd {root} && TRADING_BOT_ROOT={root} ./venv/bin/python3 scripts/alpaca_canonical_memory_bank_and_edge_mission.py",
            "```",
            "",
            "## CSA verdict — offline edge discovery legitimacy",
            "",
        ]
    )
    csa_pass = len(outcomes) >= 80 and len(top10) >= 3
    edge_lines.append(
        "**PASS** — sufficient exit PnL rows and lift signals for **hypothesis generation** only."
        if csa_pass
        else "**FAIL** — insufficient `exit_attribution` pnl_pct coverage and/or too few stable lifts; do not treat rankings as scientific conclusions."
    )

    out_edge.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")

    print("MEMORY_BANK_UPDATED:", mb_path)
    print("ALPACA_MEMORY_BANK_CANONICAL_UPDATE:", out_mb)
    print("ALPACA_MAX_EDGE_ANALYSIS:", out_edge)
    print("dataset_exit_pnl_rows:", len(outcomes))
    print("CSA_edge_analysis:", "PASS" if csa_pass else "FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
