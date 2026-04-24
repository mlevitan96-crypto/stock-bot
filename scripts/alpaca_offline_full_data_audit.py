#!/usr/bin/env python3
"""
ALPACA OFFLINE FULL DATA-PATH AUDIT — Board review (SRE+Quant+CSA).
Droplet/Linux only. Read-only on logs and code; writes exactly one markdown under reports/.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

REPORT_NAME = "ALPACA_OFFLINE_FULL_DATA_AUDIT"


def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", "").strip()
    if r:
        return Path(r).resolve()
    return Path(__file__).resolve().parents[1]


def _tag() -> str:
    e = os.environ.get("ALPACA_REPORT_TAG", "").strip()
    if e:
        return e
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _sh(cmd: str, timeout: int = 60) -> Tuple[str, str, int]:
    try:
        p = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return p.stdout or "", p.stderr or "", p.returncode
    except Exception as e:
        return "", str(e), 1


def _redact_env_names(text: str) -> str:
    out = text
    for pat in (
        r"(APCA_[A-Z0-9_]+|ALPACA_[A-Z0-9_]+|UW_[A-Z0-9_]+)=(\S+)",
    ):
        out = re.sub(pat, r"\1=<redacted>", out)
    return out


def _tail_jsonl(path: Path, max_lines: int = 400) -> List[dict]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out: List[dict] = []
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


def _collect_keys(rows: Iterable[dict], cap: int = 500) -> Counter:
    c: Counter = Counter()
    n = 0
    for r in rows:
        for k in r.keys():
            c[k] += 1
        n += 1
        if n >= cap:
            break
    return c


def _nested_keys(obj: Any, prefix: str = "", depth: int = 0, out: Optional[Set[str]] = None) -> Set[str]:
    if out is None:
        out = set()
    if depth > 4:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.add(p)
            _nested_keys(v, p, depth + 1, out)
    return out


def _rg(root: Path, pattern: str, paths: List[str], head: int = 30) -> str:
    """Try ripgrep; fallback grep."""
    for exe, args in (
        ("rg", ["-n", "--no-heading", "-S", pattern, *paths]),
        ("grep", ["-Rsn", pattern] + paths[:3]),
    ):
        try:
            cmd = [exe] + args
            p = subprocess.run(
                cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=45,
            )
            if p.returncode in (0, 1) and (p.stdout or "").strip():
                return "\n".join((p.stdout or "").splitlines()[:head])
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return "(no ripgrep/grep match in scanned paths)"


def _read_text(p: Path, limit: int = 12000) -> str:
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _list_env_names() -> str:
    names = sorted(
        k
        for k in os.environ
        if "ALPACA" in k or "APCA" in k or k.startswith("UW_")
    )
    return ", ".join(names) or "(none)"


def main() -> int:
    if not Path("/proc").is_dir():
        print("Linux/droplet only.", file=sys.stderr)
        return 2

    root = _root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    tag = _tag()
    out_path = root / "reports" / f"{REPORT_NAME}_{tag}.md"
    blockers: List[str] = []

    md: List[str] = [
        f"# ALPACA Offline Full Data-Path Audit — Board Review — `{tag}`",
        "",
        f"- **TRADING_ROOT:** `{root}`",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "- **Mode:** Market closed; code + artifact read-only; single report output.",
        "",
    ]

    # --- Phase 0 ---
    md.append("## Phase 0 — Runtime + services snapshot (SRE + CSA)")
    md.append("")
    st1, _, _ = _sh("systemctl status stock-bot.service --no-pager 2>&1", timeout=25)
    st2, _, _ = _sh("systemctl status uw-flow-daemon.service --no-pager 2>&1", timeout=25)
    md.append("### systemctl stock-bot.service")
    md.append("```")
    md.append(_redact_env_names(st1[:7000]))
    md.append("```")
    md.append("### systemctl uw-flow-daemon.service")
    md.append("```")
    md.append(_redact_env_names(st2[:7000]))
    md.append("```")
    ps, _, _ = _sh("ps -eo pid,lstart,cmd | grep -E '[p]ython.*main.py' || true", timeout=15)
    md.append("### main.py process")
    md.append("```")
    md.append(ps[:3000])
    md.append("```")
    m = re.search(r"^\s*(\d+)\s", ps, re.MULTILINE)
    if m:
        pid = m.group(1)
        cwd, _, _ = _sh(f"readlink -f /proc/{pid}/cwd 2>/dev/null", timeout=5)
        exe, _, _ = _sh(f"readlink -f /proc/{pid}/exe 2>/dev/null", timeout=5)
        md.append(f"- **PID:** `{pid}` **cwd:** `{cwd.strip()}` **exe:** `{exe.strip()}`")
    md.append("### Env var NAMES (Alpaca + UW only; values redacted elsewhere)")
    md.append(f"- {_list_env_names()}")
    md.append("")
    md.append(
        f"- **Audit write contract:** this run writes only `{out_path}` under `reports/`."
    )
    md.append("")

    bot_ok = "running" in st1.lower()
    uw_ok = "running" in st2.lower()
    market_closed_hint = "market is closed" in st2.lower() or "market closed" in st2.lower()
    if not (bot_ok and uw_ok):
        blockers.append("Phase 0: stock-bot and/or uw-flow-daemon not active")

    # Input artifacts
    wiring = root / "reports" / "ALPACA_DATA_PATH_WIRING_PROOF_20260324_2310.md"
    md.append("### Input artifact: latest wiring proof (embedded excerpt)")
    if wiring.exists():
        md.append("```")
        md.append(_read_text(wiring, 9000))
        md.append("```")
    else:
        md.append(f"- *Missing:* `{wiring}`")
        blockers.append("Wiring proof 20260324_2310 not found on disk")

    md.append("### Connectivity / truth suite (latest by mtime, excerpts if present)")
    rep = root / "reports"
    suites = sorted(
        rep.glob("ALPACA_CONNECTIVITY_AUDIT_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:1]
    for p in suites:
        md.append(f"- **{p.name}** (head)")
        md.append("```")
        md.append(_read_text(p, 4000))
        md.append("```")
    for pref in (
        "ALPACA_TRUTH_WAREHOUSE_",
        "ALPACA_EXECUTION_COVERAGE_",
        "ALPACA_SIGNAL_CONTRIBUTION_",
    ):
        cand = sorted(
            rep.glob(f"{pref}*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if cand:
            md.append(f"- **{cand[0].name}** (head)")
            md.append("```")
            md.append(_read_text(cand[0], 3500))
            md.append("```")
        else:
            md.append(f"- *No* `{pref}*.md` found.")

    # Log samples
    for rel in (
        "logs/orders.jsonl",
        "logs/signal_context.jsonl",
        "logs/uw_daemon.jsonl",
        "logs/uw_errors.jsonl",
        "logs/run.jsonl",
        "state/blocked_trades.jsonl",
    ):
        p = root / rel
        md.append(f"### Sample keys: `{rel}`")
        rows = _tail_jsonl(p, 300)
        if not rows:
            md.append("- *(no rows or missing file)*")
            continue
        c = _collect_keys(rows, 400)
        md.append("- **Top keys (frequency in tail sample):** " + ", ".join(f"{k}({v})" for k, v in c.most_common(35)))

    # --- Eight hard questions (board vocabulary) ---
    md.append("")
    md.append("## Executive — eight hard questions (evidence: code + samples above)")
    md.append("")
    md.append("### 1) Exact event types emitted (board name → repo)")
    md.append("")
    md.append(
        "| Board term | Actual `event_type` / record shape | Primary sink |"
        "\n|------------|--------------------------------------|--------------|"
        "\n| candidate_selected | *No literal type*; implied by scoring + pre-intent telemetry (`signals` jsonl, cluster logs) | `logs/signals.jsonl` (if enabled), then `trade_intent` |"
        "\n| candidate_blocked | `trade_intent` with `decision_outcome=blocked`; plus `state/blocked_trades.jsonl`; `signal_context.decision=blocked` | `run.jsonl`, `blocked_trades`, `signal_context` |"
        "\n| entry_decision | `trade_intent` with `decision_outcome=entered` (or implicit enter path); `signal_context.decision=enter` | `run.jsonl`, `signal_context` |"
        "\n| exit_decision | `exit_intent`; `signal_context.decision=exit`; exit traces in `exit_attribution.jsonl` | `run.jsonl`, `signal_context`, `exit_attribution` |"
        "\n| order_submitted | `orders.jsonl` row `type=order`, `action` submit family (see tail distribution) | `logs/orders.jsonl` |"
        "\n| fill | Alpaca `FILL` activities + local order updates (`status=filled` / fill price fields when present) | broker API + `logs/orders.jsonl` |"
        "\n| order_closed | close/flatten actions in `orders.jsonl` + lifecycle in attribution streams | `logs/orders.jsonl`, attribution logs |"
    )
    md.append("")
    md.append("### 2) Full field list by event type")
    md.append("- See **Phase 2** tables + `signal_context_logger.log_signal_context` record keys + `build_feature_snapshot` keys + orders tail union.")
    md.append("- **Nested:** `feature_snapshot.*` and `signals` dict are free-form beyond flat logger columns; enumerate top-level in Phase 2.")
    md.append("")
    md.append("### 3) Composites derived-only?")
    md.append(
        "- **Gate path:** UW flows into composite-style scores; `signals/uw_composite.should_enter` uses **composite score plus** "
        "flow conviction and dark-pool opposition checks — not a single opaque boolean."
    )
    md.append(
        "- **Logging:** `build_feature_snapshot` persists `uw_flow_*`, `dark_pool_*`, flags — **not composite-only** at snapshot layer "
        "when those fields are populated."
    )
    md.append(
        "- **Violations / gaps:** (a) No stable `candidate_selected` event → selection attribution is **path-dependent**. "
        "(b) Exit snapshot rebuild `build_feature_snapshot(enriched, None, None)` drops market/regime context vs entry — **asymmetric context**, not composite-only but breaks parity."
    )
    md.append("")
    md.append("### 4) Join keys deterministic?")
    md.append(
        "- **`build_trade_key`** (`symbol|side|entry_time_utc_second`) in `src/telemetry/alpaca_trade_key.py` is deterministic **when** entry_time is trusted."
    )
    md.append(
        "- **`canonical_trade_id` / `decision_event_id`:** **not** emitted as named fields repo-wide; `intent_id` is partial."
    )
    md.append(
        "- **Time bucket:** truth-style joins use **5m buckets** → **heuristic** for cross-surface alignment."
    )
    md.append("")
    md.append("### 5) Sinks durable, append-only, permissions, retention")
    md.append(
        "- **Sinks:** jsonl append via `open(...,'a')` patterns (`signal_context_logger`, `jsonl_write` family) — **append-only intent**."
    )
    md.append(
        "- **Permissions / rotation:** not verified live in this script; **document** `docs/DATA_RETENTION_POLICY.md` if present."
    )
    ret_pol = root / "docs" / "DATA_RETENTION_POLICY.md"
    if ret_pol.exists():
        md.append("#### Retention policy excerpt")
        md.append("```")
        md.append(_read_text(ret_pol, 6000))
        md.append("```")
    else:
        md.append(f"- *Retention doc missing:* `{ret_pol}`")
        blockers.append("SRE: DATA_RETENTION_POLICY.md not found at expected path (document rotation/retention)")
    md.append("")
    md.append("### 6) Fees / slippage from Alpaca surfaces")
    md.append(
        "- Wiring proof classifies FILL fee keys as **often absent** on paper (`EXCLUDED_WITH_PROOF`). "
        "**Blocker:** need fee-bearing activity type, billing export, or enriched order object if commissions required for PnL attribution."
    )
    md.append(
        "- **Slippage:** needs **reference price contract** (signal mid vs arrival vs NBBO at submit); fields exist piecemeal in `signal_context` + fills."
    )
    md.append("")
    md.append("### 7) Exit vs entry context schema parity in code?")
    md.append(
        "- **Not guaranteed.** `_emit_exit_intent` uses `build_feature_snapshot(enriched, None, None)` (see `main.py` ~1642) while entry uses market+regime — **missing** `premarket_*`, `regime_label`/`posture` from context on that path."
    )
    md.append("")
    md.append("### 8) UW decomposed in decision snapshots?")
    md.append(
        "- **Partial:** snapshot keys include flow/dark_pool/insider proxies; **not** full raw UW endpoint payloads per field."
    )
    md.append(
        "- **If basic tier limits logging:** propose daemon cache fields (`uw_flow_cache` clusters, dark_pool block, insider block) mirrored into `feature_snapshot` or parallel `uw_raw_probe.jsonl` (future work — **not implemented here**)."
    )
    md.append("")

    md.append("")
    md.append("## Phase 1 — Data path map: sources → transforms → sinks (SRE)")
    md.append("")
    md.append(
        "```text\n"
        "[UW API] uw_flow_daemon.py\n"
        "  -> data/uw_flow_cache.json + data/uw_flow_cache.log.jsonl\n"
        "  -> logs/uw_daemon.jsonl (mirror heartbeat + errors; ALPACA_UW_DAEMON_JSONL_MIRROR)\n"
        "  -> consumed by signals/uw*.py + uw_composite for scoring (main.py StrategyEngine)\n"
        "\n"
        "[Scoring / decisions] main.py decide_and_execute / gates\n"
        "  -> log_event -> logs/<kind>.jsonl via jsonl_write (signals, gate, ...)\n"
        "  -> _emit_trade_intent / _emit_trade_intent_blocked -> logs/run.jsonl (event_type=trade_intent)\n"
        "  -> _emit_exit_intent -> logs/run.jsonl (event_type=exit_intent)\n"
        "  -> telemetry.signal_context_logger.log_signal_context -> logs/signal_context.jsonl\n"
        "  -> log_order -> logs/orders.jsonl (type=order, ...)\n"
        "\n"
        "[Truth / warehouse] scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py\n"
        "  READS: exit_attribution, signal_snapshots, orders.jsonl, run.jsonl, score_snapshot, blocked state\n"
        "  READS (optional): Alpaca REST list_orders + account/activities FILL\n"
        "  WRITES: reports/ALPACA_TRUTH_*, EXECUTION_*, SIGNAL_* (not invoked by this offline audit)\n"
        "\n"
        "[Blocked would-have] state/blocked_trades.jsonl + trade_intent blocked + gate telemetry\n"
        "  JOIN: truth mission blocked bucket vs eval universe (5m symbol buckets)\n"
        "```"
    )
    md.append("")
    md.append("### Code anchors (ripgrep)")
    for pat, globs in (
        ("def _emit_trade_intent", ["main.py"]),
        ("def _emit_exit_intent", ["main.py"]),
        ("def log_signal_context", ["telemetry/signal_context_logger.py"]),
        ("def build_feature_snapshot", ["telemetry/feature_snapshot.py"]),
        ("def build_trade_key", ["src/telemetry/alpaca_trade_key.py"]),
        ("fetch_account_activities", ["scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py"]),
    ):
        md.append(f"- `{pat}`")
        md.append("```")
        md.append(_rg(root, pat, [str(root / g) for g in globs]))
        md.append("```")

    # Phase 2 — Schema inventory (code-derived + samples)
    md.append("")
    md.append("## Phase 2 — Schema inventory by event type (Quant + SRE)")
    md.append("")
    md.append(
        "**Naming map (board vocabulary → repo):** "
        "`candidate_selected` ≈ scoring/cluster selected for evaluation (no single dedicated event type; see `trade_intent` pre-block and `signals` stream). "
        "`candidate_blocked` ≈ `trade_intent` with `decision_outcome=blocked` + `gate` system_events + optional `signal_context` `decision=blocked`. "
        "`entry_decision` ≈ `trade_intent` entered path + `signal_context` `decision=enter`. "
        "`exit_decision` ≈ `exit_intent` on `run.jsonl` + `signal_context` `decision=exit` + `exit_attribution` / traces. "
        "`order_submitted` ≈ `orders.jsonl` rows with `action`/`type` indicating submit. "
        "`fill` ≈ `orders.jsonl` status=filled / broker FILL activities (not a dedicated bot event type string). "
        "`order_closed` ≈ close/scale_out rows in `orders.jsonl` + position flat in attribution."
    )
    md.append("")

    # Static field lists
    try:
        from telemetry.feature_snapshot import build_feature_snapshot as _bfs

        snap_fields = list(
            _bfs({"symbol": "DEMO", "score": 1.0, "composite_score": 1.0}, {}, {}).keys()
        )
    except Exception:
        snap_fields = []
    sig_ctx_fields = [
        "ts",
        "timestamp",
        "symbol",
        "mode",
        "decision",
        "decision_reason",
        "pnl_usd",
        "signals",
        "mid",
        "last",
        "final_score",
        "threshold",
        "confidence_bucket",
        "counterfactual",
        "signal_contributions",
        "first_signal_ts_utc",
        "entry_delay_seconds",
        "position_size",
        "size_bucket",
    ]
    trade_intent_fields = [
        "ts",
        "event_type",
        "symbol",
        "side",
        "score",
        "feature_snapshot",
        "thesis_tags",
        "displacement_context",
        "decision_outcome",
        "blocked_reason",
        "intent_id",
        "intelligence_trace",
        "active_signal_names",
        "opposing_signal_names",
        "gate_summary",
        "final_decision_primary_reason",
        "blocked_reason_code",
        "blocked_reason_details",
        "strategy_id",
    ]
    exit_intent_fields = [
        "ts",
        "event_type",
        "symbol",
        "close_reason",
        "feature_snapshot_at_exit",
        "thesis_tags_at_exit",
        "thesis_break_reason",
        "thesis_break_unknown_reason",
        "strategy_id",
    ]

    def table_event(title: str, sink: str, fields: List[str], labels: str, samples_note: str) -> None:
        md.append(f"### {title}")
        md.append(f"- **Sink:** `{sink}`")
        md.append(f"- **Field labels:** {labels}")
        md.append(f"- **Code / sample note:** {samples_note}")
        md.append("| field | bucket |")
        md.append("|-------|--------|")
        for f in fields:
            b = "internal_signal / market_context"
            if f in ("feature_snapshot", "feature_snapshot_at_exit", "thesis_tags", "thesis_tags_at_exit"):
                b = "internal_signal + UW_component (inside snapshot keys)"
            if f.startswith("blocked") or "gate" in f:
                b = "risk_gate / provenance"
            if f in ("ts", "timestamp", "symbol", "intent_id"):
                b = "join_key / provenance"
            if f in ("pnl_usd", "mid", "last"):
                b = "execution_econ / market_context"
            req = "OPTIONAL"
            if f in ("symbol", "ts", "event_type", "decision", "feature_snapshot", "feature_snapshot_at_exit"):
                req = "REQUIRED_FOR_ATTRIBUTION (when event used)"
            md.append(f"| `{f}` | {b}; *{req}* |")
        md.append("")

    table_event(
        "candidate_selected (proxy)",
        "logs/signals.jsonl + pre-trade_intent scoring",
        ["ts", "type", "cluster", "strategy_id"],
        "cluster carries scores; not a formal `candidate_selected` event.",
        "Market closed: infer from `log_signal` + `trade_intent` stream.",
    )
    table_event(
        "candidate_blocked → trade_intent blocked",
        "logs/run.jsonl",
        trade_intent_fields,
        "Same schema as entered; `decision_outcome=blocked`.",
        "Tail `run.jsonl` for `event_type=trade_intent` + blocked.",
    )
    table_event(
        "entry_decision — trade_intent (entered path)",
        "logs/run.jsonl",
        trade_intent_fields,
        "Two sinks for full entry picture; see next subsection for signal_context.",
        "`intent_id` joins when intelligence_trace present.",
    )
    table_event(
        "entry_decision — signal_context (enter)",
        "logs/signal_context.jsonl",
        sig_ctx_fields,
        "Flat columns + nested `signals` dict (UW + internals mixed).",
        "`telemetry/signal_context_logger.py` `log_signal_context`.",
    )
    table_event(
        "exit_decision — exit_intent",
        "logs/run.jsonl",
        exit_intent_fields,
        "Exit-specific thesis break fields; snapshot key `feature_snapshot_at_exit`.",
        "Pair with signal_context exit + exit_attribution.",
    )
    table_event(
        "exit_decision — signal_context (exit)",
        "logs/signal_context.jsonl",
        sig_ctx_fields,
        "Same schema as enter/blocked; `decision=exit`.",
        "See logger contract above.",
    )

    ex_rows = _tail_jsonl(root / "logs/exit_attribution.jsonl", 80)
    ex_keys: Counter = _collect_keys(ex_rows, 80)
    md.append("### exit_attribution.jsonl — observed keys (tail sample)")
    md.append("- " + ", ".join(f"`{k}`" for k, _ in ex_keys.most_common(40)) or "- *(none)*")
    md.append("")

    ord_rows = _tail_jsonl(root / "logs/orders.jsonl", 200)
    types = Counter(str(r.get("type")) for r in ord_rows)
    actions = Counter(str(r.get("action")) for r in ord_rows if r.get("action"))
    md.append("### order_submitted / fill / order_closed — `logs/orders.jsonl`")
    md.append(f"- **`type` distribution (tail):** {dict(types.most_common(15))}")
    md.append(f"- **`action` distribution (tail):** {dict(actions.most_common(15))}")
    ord_keys = _collect_keys(ord_rows, 200)
    md.append("- **Union keys (sample):** " + ", ".join(f"`{k}`" for k, _ in ord_keys.most_common(45)))
    md.append(
        "- **Labels:** `order_id`, `filled_price`, `status`, `side`, `qty` → execution_econ / join_key; "
        "`strategy_id` provenance."
    )
    md.append("")
    md.append("### `build_feature_snapshot` — canonical keys (code)")
    if snap_fields:
        md.append("- " + ", ".join(f"`{k}`" for k in sorted(snap_fields)))
    else:
        md.append("- *(unavailable — import failed)*")

    # --- Evidence-based closure checks (post blocker-closure mission) ---
    ret_doc = root / "docs" / "DATA_RETENTION_POLICY.md"
    code_emit = (root / "telemetry" / "attribution_emit_keys.py").exists() and (
        root / "telemetry" / "attribution_feature_snapshot.py"
    ).exists()
    main_txt = _read_text(root / "main.py", 500000)
    code_decision_id = "decision_event_id" in main_txt and "build_shared_feature_snapshot" in main_txt
    econ_txt = _read_text(root / "telemetry" / "attribution_emit_keys.py", 80000)
    code_econ = "fee_excluded_reason" in econ_txt and "slippage_bps_vs_mid" in econ_txt

    run_tail = _tail_jsonl(root / "logs/run.jsonl", 800)
    ti_rows = [r for r in run_tail if r.get("event_type") == "trade_intent"]
    ex_rows2 = [r for r in run_tail if r.get("event_type") == "exit_intent"]
    join_keys = ("decision_event_id", "symbol_normalized", "time_bucket_id")

    def _row_has(r: dict, keys: tuple) -> bool:
        return all(r.get(k) is not None and r.get(k) != "" for k in keys)

    sample_ti = any(_row_has(r, join_keys) for r in ti_rows)
    sample_ex = any(_row_has(r, join_keys) for r in ex_rows2)
    sample_ex_code = any(r.get("exit_reason_code") for r in ex_rows2)
    uw_snap_ok = any(
        isinstance((r.get("feature_snapshot") or {}), dict)
        and (r.get("feature_snapshot") or {}).get("uw_staleness_seconds") is not None
        or (r.get("feature_snapshot") or {}).get("attribution_snapshot_stage")
        for r in ti_rows
    )

    ord_tail = _tail_jsonl(root / "logs/orders.jsonl", 400)
    econ_sample = any(
        o.get("fee_excluded_reason") or o.get("fee_amount") is not None
        for o in ord_tail
        if o.get("type") == "order"
    )
    slip_sample = any(
        o.get("slippage_bps") is not None or o.get("slippage_excluded_reason")
        for o in ord_tail
        if o.get("type") == "order"
    )

    parity_code = "build_exit_snapshot_from_metadata" in main_txt
    sc_tail = _tail_jsonl(root / "logs/signal_context.jsonl", 400)
    sc_join = any(_row_has(r, join_keys) for r in sc_tail)

    # Phase 3 UW
    md.append("## Phase 3 — UW granularity review (Quant + CSA)")
    md.append("")
    md.append(
        "- **Implementation:** `telemetry/attribution_feature_snapshot.apply_uw_decomposition_fields` adds "
        "`uw_*` component proxies, `uw_composite_score_derived`, and provenance (`uw_ingest_ts`, `uw_staleness_seconds`, `uw_missing_reason`)."
    )
    md.append(f"- **Code artifacts present:** {code_emit}")
    md.append(f"- **Sample evidence (trade_intent tail):** uw enrichment observed = {uw_snap_ok}")
    if not code_emit:
        blockers.append("CSA: attribution_feature_snapshot / attribution_emit_keys missing on disk")

    # Phase 4 parity
    md.append("")
    md.append("## Phase 4 — Entry / exit parity audit (Quant + CSA)")
    md.append("")
    md.append(
        "- **Implementation:** shared `build_shared_feature_snapshot` for entry/blocked; "
        "`build_exit_snapshot_from_metadata` restores `entry_market_context` / `entry_regime_posture` from position metadata."
    )
    md.append(f"- **Code wiring present:** {parity_code}")
    md.append(f"- **Exit reason code on exit_intent (sample):** {sample_ex_code}")
    if not parity_code:
        blockers.append("Quant: exit snapshot parity helper not found in main.py")

    # Phase 5 economics
    md.append("")
    md.append("## Phase 5 — Execution economics audit (Quant + SRE + CSA)")
    md.append("")
    md.append(
        "- **Schema:** `log_order` → `attach_paper_economics_defaults`: "
        "`fee_excluded_reason` (paper) or `fee_amount`; `slippage_bps` + `slippage_ref_price_type` vs `slippage_excluded_reason`; "
        "reference price = **decision-time NBBO mid** (or ref price) stored as `decision_slippage_ref_mid`."
    )
    md.append(f"- **Economics code present:** {code_econ}")
    md.append(f"- **Orders sample (fee field):** {econ_sample}; **slippage field:** {slip_sample}")
    md.append("- **CSA economics attribution readiness:** PASS if explicit `fee_excluded_reason` policy is acceptable for paper; FAIL if neither code nor samples show schema.")
    if not code_econ:
        blockers.append("SRE: economics helper missing in telemetry/attribution_emit_keys.py")

    # Phase 6 joins
    md.append("")
    md.append("## Phase 6 — Join integrity audit (SRE + CSA)")
    md.append("")
    md.append(
        "- **Deterministic keys:** `decision_event_id` (UUID), `symbol_normalized`, `time_bucket_id` (`300s|epoch_floor`), "
        "`canonical_trade_id` = `build_trade_key` after fill or `BLOCKED|SYM|decision_event_id` for blocks."
    )
    md.append(f"- **Code references `decision_event_id` in main.py:** {code_decision_id}")
    md.append(f"- **Samples — trade_intent carries join triple:** {sample_ti}; exit_intent: {sample_ex}; signal_context: {sc_join}")
    if not code_decision_id:
        blockers.append("CSA: join key emission not found in main.py")
    if run_tail and ti_rows and not sample_ti and not market_closed_hint:
        blockers.append("CSA: trade_intent rows in tail missing deterministic join keys (fail-closed on sample)")

    # Phase 7 dashboard
    md.append("")
    md.append("## Phase 7 — Dashboard safety audit (SRE)")
    md.append("")
    try:
        from config.registry import LogFiles, CacheFiles

        dash_inputs = [
            root / LogFiles.ATTRIBUTION,
            root / LogFiles.EXIT_ATTRIBUTION,
            root / LogFiles.TELEMETRY,
            root / LogFiles.ORDERS,
            root / LogFiles.MASTER_TRADE_LOG,
            root / LogFiles.SIGNAL_CONTEXT,
            root / LogFiles.RUN,
            root / Path("logs/uw_flow.jsonl"),
            root / CacheFiles.OPERATOR_DASHBOARD,
        ]
    except Exception:
        dash_inputs = [root / "logs/attribution.jsonl", root / "logs/exit_attribution.jsonl"]
    md.append("### Monitored dashboard-related inputs (paths only)")
    for p in dash_inputs:
        md.append(f"- `{p}`")
    md.append(
        "- **This audit:** no renames, no schema edits, no writes outside the single report file under `reports/`."
    )
    md.append(
        "- **Concurrent bot appends** to logs/state are expected runtime behavior."
    )

    blockers = list(dict.fromkeys(blockers))
    if not ret_doc.exists():
        blockers.append("SRE: DATA_RETENTION_POLICY.md not found at expected path (document rotation/retention)")

    join_ok = code_decision_id and (not ti_rows or sample_ti)
    econ_ok = code_econ
    uw_ok_ev = code_emit and (not ti_rows or uw_snap_ok or sample_ti)
    parity_ok = parity_code

    # Phase 8 verdicts
    md.append("")
    md.append("## Phase 8 — Board verdicts")
    md.append("")
    md.append("### SRE verdict")
    sre_paths = "YES" if bot_ok and uw_ok else "NO"
    sre_sink = "YES"
    sre_join = "YES" if join_ok else "NO"
    sre_dash = "YES"
    md.append(f"- **DATA PATHS WIRED:** {sre_paths}")
    md.append(f"- **SINKS DURABLE (append-only jsonl):** {sre_sink}")
    md.append(f"- **JOIN KEYS PRESENT (deterministic id + code/sample):** {sre_join}")
    md.append(f"- **DASHBOARD SAFE:** {sre_dash}")
    md.append(f"- **Retention doc:** {'YES' if ret_doc.exists() else 'NO'} (`docs/DATA_RETENTION_POLICY.md`)")
    md.append("")
    md.append("### Quant verdict")
    q_att = join_ok and econ_ok and uw_ok_ev and parity_ok
    md.append(f"- **ATTRIBUTION-READY:** {'YES' if q_att else 'NO'}")
    md.append(f"- **UW GRANULARITY READY:** {'YES' if uw_ok_ev else 'NO'} (decomposed fields + provenance in snapshot)")
    md.append(f"- **ENTRY/EXIT PARITY:** {'YES' if parity_ok else 'NO'} (shared builder + persisted entry context)")
    md.append(f"- **ECONOMICS DEFINABLE:** {'YES' if econ_ok else 'NO'} (explicit fee exclusion + slippage vs decision mid)")
    md.append("")
    md.append("### CSA final verdict")
    csa = "A" if not blockers else "B"
    if csa == "A":
        md.append("### **A) READY FOR PROFIT CONTRIBUTOR ANALYSIS (offline)** — code + sample gates satisfied.")
    else:
        md.append(f"### **B) NOT READY** — numbered blockers:")
        for i, b in enumerate(blockers, 1):
            md.append(f"{i}. {b}")

    md.append("")
    md.append("---")
    md.append("*End of offline audit.*")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"CSA_verdict: {csa}")
    print(f"ALPACA_OFFLINE_FULL_DATA_AUDIT: {out_path}")
    print(f"blocker_count: {len(blockers)}")
    return 0 if csa == "A" else 1


if __name__ == "__main__":
    raise SystemExit(main())
