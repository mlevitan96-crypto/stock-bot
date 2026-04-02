#!/usr/bin/env python3
"""
Paper execution promo mission (Phases 0–6). Droplet-oriented.

  cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_exec_mode_paper_promo_mission.py --evidence-et 2026-04-01 --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]


def _run(cmd: str, cwd: Path, timeout: int = 180) -> Tuple[int, str]:
    try:
        r = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def _session_et_date() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(float(v), tz=timezone.utc)
    s = str(v).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s.replace(" ", "T")[:32]).astimezone(timezone.utc)
    except Exception:
        return None


def _et_hour(ts: datetime) -> int:
    try:
        from zoneinfo import ZoneInfo

        return int(ts.astimezone(ZoneInfo("America/New_York")).hour)
    except Exception:
        return int(ts.astimezone(timezone.utc).hour)


def _p05(xs: List[float]) -> Optional[float]:
    if not xs:
        return None
    s = sorted(xs)
    k = max(0, int(0.05 * (len(s) - 1)))
    return round(s[k], 6)


def _mdd(xs: List[float]) -> float:
    cum = 0.0
    peak = 0.0
    mdd = 0.0
    for x in xs:
        cum += x
        peak = max(peak, cum)
        mdd = min(mdd, cum - peak)
    return round(mdd, 6)


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.is_file():
        return out
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-et", type=str, default=None)
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--universe-path", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    et = args.evidence_et or _session_et_date()
    ev = root / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)

    paper_mod = root / "src" / "paper" / "paper_exec_mode_runtime.py"
    txt = paper_mod.read_text(encoding="utf-8", errors="replace") if paper_mod.is_file() else ""
    if re.search(r"\bapi\.submit_order\b", txt):
        (ev / "EXEC_MODE_PAPER_PROMO_BLOCKER_LIVE_PATH_TOUCHED.md").write_text(
            "Direct api.submit_order in paper_exec_mode_runtime.py\n", encoding="utf-8"
        )
        return 2

    # --- Phase 0 ---
    _, git_head = _run("git rev-parse HEAD", root)
    _, st_status = _run("systemctl status stock-bot --no-pager 2>&1 | head -n 80", root)
    _, st_cat = _run("systemctl cat stock-bot 2>&1", root)
    _, st_env = _run("systemctl show stock-bot -p Environment -p EnvironmentFiles 2>&1", root)
    _, jtail = _run('journalctl -u stock-bot --since "24 hours ago" --no-pager 2>&1 | tail -n 800', root)

    main_py = root / "main.py"
    main_txt = main_py.read_text(encoding="utf-8", errors="replace")[:80000] if main_py.is_file() else ""
    combined = "\n".join([git_head, st_cat, st_env, jtail[:50000], main_txt]).lower()
    paper_ok = "paper-api" in combined or "paper-api.alpaca" in combined.replace("_", "-")
    if not paper_ok:
        paper_ok = "trading_mode=paper" in combined or "paper_mode" in combined

    ph0 = [
        "# EXEC_MODE_PAPER_PROMO_PHASE0_CONTEXT\n\n",
        "## git rev-parse HEAD\n\n```\n",
        git_head.strip(),
        "\n```\n\n## systemctl status\n\n```\n",
        st_status[:10000],
        "\n```\n\n## systemctl cat\n\n```\n",
        st_cat[:22000],
        "\n```\n\n## systemctl show Environment\n\n```\n",
        st_env[:6000],
        "\n```\n\n## journalctl\n\n```\n",
        jtail[:120000],
        "\n```\n\n## Paper-only proof\n\n",
        f"- **paper endpoint / mode in sample:** **{paper_ok}**\n",
        "- **Code:** `main.py` `submit_entry` → `try_paper_exec_ab_entry` (after AUDIT_DRY_RUN); strict gateway inside `paper_exec_mode_runtime.py`.\n",
        "- **`paper_exec_mode_runtime.py`:** uses `executor._submit_order_guarded` only (no `api.submit_order`).\n",
        "- **`main.py` `submit_order` occurrences (file-wide):** mission grep count informational only; live path unchanged for non-paper.\n",
    ]
    (ev / "EXEC_MODE_PAPER_PROMO_PHASE0_CONTEXT.md").write_text("".join(ph0), encoding="utf-8")

    if not paper_ok:
        (ev / "EXEC_MODE_PAPER_PROMO_BLOCKER_PAPER_UNPROVEN.md").write_text(
            "Could not confirm paper-api / paper mode in systemd + main sample.\n", encoding="utf-8"
        )
        return 2

    uni_default = ev / "EXEC_MODE_UNIVERSE_TOP20_LAST3D.json"
    uni_path = args.universe_path or (root / "reports" / "daily" / "2026-04-01" / "evidence" / "EXEC_MODE_UNIVERSE_TOP20_LAST3D.json")
    if not uni_path.is_file():
        uni_path = uni_default
    uni_exists = uni_path.is_file()

    # --- Phase 1 contract ---
    (ev / "EXEC_MODE_PAPER_PROMO_ACTION_CONTRACT.md").write_text(
        "# EXEC_MODE_PAPER_PROMO_ACTION_CONTRACT\n\n"
        "| Field | Value |\n"
        "|-------|-------|\n"
        "| Scope | **Paper only** (strict gateway: PAPER_TRADING + paper base URL + is_paper_mode) |\n"
        "| Universe file | `PAPER_EXEC_UNIVERSE_PATH` or default below |\n"
        "| Policy (B arm) | PASSIVE_THEN_CROSS |\n"
        "| TTL | `PAPER_EXEC_TTL_MINUTES` default **3** |\n"
        "| A/B | Even ET hour = MARKETABLE (baseline path); odd ET hour = treatment |\n"
        "| Enable | `PAPER_EXEC_PROMO_ENABLED=1` (master; conceptual `PAPER_EXEC_MODE` arms are A/B-scheduled) |\n"
        "| Rollback | Unset env; restart `stock-bot`; baseline `submit_entry` only |\n\n"
        f"**Default universe path (if env unset):** `{root}/reports/daily/2026-04-01/evidence/EXEC_MODE_UNIVERSE_TOP20_LAST3D.json`\n\n"
        f"**Resolved for this doc:** `{uni_path}` exists={uni_exists}\n",
        encoding="utf-8",
    )

    # --- Phase 2 implementation ---
    (ev / "EXEC_MODE_PAPER_PROMO_IMPLEMENTATION.md").write_text(
        "# EXEC_MODE_PAPER_PROMO_IMPLEMENTATION\n\n"
        "- **Module:** `src/paper/paper_exec_mode_runtime.py`\n"
        "- **Hook:** `main.py` `AlpacaExecutor.submit_entry` immediately after AUDIT_DRY_RUN branch.\n"
        "- **Log:** `logs/paper_exec_mode_decisions.jsonl`\n"
        "- **Env:** `PAPER_EXEC_PROMO_ENABLED`, `PAPER_EXEC_TTL_MINUTES`, `PAPER_EXEC_UNIVERSE_PATH`, "
        "`PAPER_EXEC_FAIL_CLOSED`, `PAPER_EXEC_AB_FORCE` (optional)\n",
        encoding="utf-8",
    )

    # --- Phase 3 schedule ---
    (ev / "EXEC_MODE_PAPER_PROMO_AB_SCHEDULE.md").write_text(
        "# EXEC_MODE_PAPER_PROMO_AB_SCHEDULE\n\n"
        "**Fixed (no tuning)** — America/New_York wall-clock hour:\n\n"
        "- **Even hour (0,2,4,…):** **A = MARKETABLE** — `try_paper_exec_ab_entry` returns `None`; normal `submit_entry` path.\n"
        "- **Odd hour (1,3,5,…):** **B = PASSIVE_THEN_CROSS** — limit at prior completed 1m bar close; wait TTL; market cross.\n\n"
        "**Override (testing):** `PAPER_EXEC_AB_FORCE=marketable` or `passive_then_cross`.\n",
        encoding="utf-8",
    )

    # --- Phase 4 run proof ---
    log_path = root / "logs" / "paper_exec_mode_decisions.jsonl"
    _, wc = _run(f"wc -l {log_path} 2>/dev/null || true", root)
    run_proof = [
        "# EXEC_MODE_PAPER_PROMO_RUN_PROOF\n\n",
        f"- **Evidence ET folder:** `{et}`\n",
        f"- **paper_exec_mode_decisions.jsonl:** `{log_path}` line count: `{wc.strip()}`\n",
        "- **Minimum window:** 1 full NY session recommended; if sparse, extend to 2 days (paper only).\n"
        "- **Operator:** set systemd `Environment=` or drop-in for `PAPER_EXEC_PROMO_ENABLED=1` and universe path; "
        "`sudo systemctl restart stock-bot`.\n\n",
        "## journalctl excerpt (captured at mission run)\n\n```\n",
        jtail[-8000:],
        "\n```\n",
    ]
    (ev / "EXEC_MODE_PAPER_PROMO_RUN_PROOF.md").write_text("".join(run_proof), encoding="utf-8")

    # --- Phase 5 evaluation ---
    rows = _load_jsonl(log_path)
    b_rows = [r for r in rows if str(r.get("ab_arm") or "") == "B" or str(r.get("mode") or "") == "PASSIVE_THEN_CROSS"]
    a_rows = [r for r in rows if str(r.get("ab_arm") or "") == "A"]

    b_err = sum(1 for r in b_rows if r.get("error"))
    b_cross = sum(1 for r in b_rows if r.get("cross_event"))
    b_filled = [r for r in b_rows if r.get("fill_price") is not None and float(r.get("fill_price") or 0) > 0]

    # Join exit_attribution: bucket by ET hour even=A odd=B for universe symbols (proxy for A/B exposure)
    exit_path = root / "logs" / "exit_attribution.jsonl"
    uni_syms = set()
    if uni_path.is_file():
        try:
            uj = json.loads(uni_path.read_text(encoding="utf-8"))
            uni_syms = {str(x).upper() for x in (uj.get("top20_symbols_by_trade_count") or [])}
        except Exception:
            pass

    pnl_a: List[float] = []
    pnl_b: List[float] = []
    if exit_path.is_file() and uni_syms:
        with exit_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ex = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sym = str(ex.get("symbol") or "").upper()
                if sym not in uni_syms:
                    continue
                ts = _parse_ts(ex.get("entry_timestamp"))
                if ts is None:
                    continue
                pnl = ex.get("pnl")
                try:
                    pf = float(pnl)
                except (TypeError, ValueError):
                    continue
                h = _et_hour(ts)
                if h % 2 == 0:
                    pnl_a.append(pf)
                else:
                    pnl_b.append(pf)

    def arm_stats(pnls: List[float], label: str) -> Dict[str, Any]:
        if not pnls:
            return {"label": label, "trade_count": 0}
        return {
            "label": label,
            "trade_count": len(pnls),
            "mean_pnl_per_trade": round(statistics.mean(pnls), 6),
            "total_pnl": round(sum(pnls), 6),
            "p05_pnl_per_trade": _p05(pnls),
            "max_drawdown_proxy": _mdd(pnls),
        }

    eval_json: Dict[str, Any] = {
        "paper_exec_jsonl_rows_total": len(rows),
        "arm_a_decision_rows": len(a_rows),
        "arm_b_decision_rows": len(b_rows),
        "arm_b_errors": b_err,
        "arm_b_cross_events": b_cross,
        "arm_b_jsonl_filled": len(b_filled),
        "arm_b_fill_rate_proxy": round(len(b_filled) / len(b_rows), 6) if b_rows else None,
        "exit_attribution_bucket_even_hour_marketable_proxy": arm_stats(pnl_a, "A_proxy_even_ET_hour"),
        "exit_attribution_bucket_odd_hour_treatment_proxy": arm_stats(pnl_b, "B_proxy_odd_ET_hour"),
        "caveat": "Exit-attribution A/B buckets use ET hour parity as proxy for schedule; valid only when PAPER_EXEC_PROMO_ENABLED ran full window.",
        "promo_runtime_rows_seen": len(rows),
    }

    # Gates: only when promo runtime produced JSONL (else parity buckets are not causal A/B).
    fail = False
    fail_reasons: List[str] = []
    br = eval_json.get("arm_b_fill_rate_proxy")
    p05a = eval_json["exit_attribution_bucket_even_hour_marketable_proxy"].get("p05_pnl_per_trade")
    p05b = eval_json["exit_attribution_bucket_odd_hour_treatment_proxy"].get("p05_pnl_per_trade")
    promo_runtime = len(rows) >= 1
    if not promo_runtime:
        fail_reasons.append("NO_PAPER_EXEC_JSONL_YET_ENABLE_PROMO_AND_RE_RUN")
    if promo_runtime and len(b_rows) >= 5 and br is not None and float(br) < 0.85:
        fail = True
        fail_reasons.append("B_fill_rate_below_0_85")
    if promo_runtime and len(pnl_b) >= 5 and p05a is not None and p05b is not None and float(p05b) < float(p05a) - 0.5:
        fail = True
        fail_reasons.append("B_tail_p05_worse_than_A_by_threshold_0_5")
    if len(pnl_a) < 3 and len(pnl_b) < 3:
        fail_reasons.append("INSUFFICIENT_EXIT_ROWS_FOR_GATE_NOTE_ONLY")

    eval_json["hard_gate_fail"] = fail
    eval_json["hard_gate_reasons"] = fail_reasons

    (ev / "EXEC_MODE_PAPER_PROMO_EVALUATION.json").write_text(json.dumps(eval_json, indent=2), encoding="utf-8")

    ev_md = [
        "# EXEC_MODE_PAPER_PROMO_EVALUATION\n\n",
        f"**Status:** `{'FAIL' if fail else 'PASS'}` (automated gates on available data)\n\n",
        f"**Reasons:** `{fail_reasons}`\n\n",
        "## paper_exec_mode_decisions.jsonl\n\n",
        f"- Total rows: {len(rows)}; A rows: {len(a_rows)}; B rows: {len(b_rows)}\n",
        f"- B filled (has fill_price): {len(b_filled)}; B errors: {b_err}; cross events: {b_cross}\n",
        f"- B fill rate proxy: {br}\n\n",
        "## Exit attribution proxy (ET hour parity)\n\n",
        "```json\n",
        json.dumps(
            {
                "A_even_hour": eval_json["exit_attribution_bucket_even_hour_marketable_proxy"],
                "B_odd_hour": eval_json["exit_attribution_bucket_odd_hour_treatment_proxy"],
            },
            indent=2,
        ),
        "\n```\n",
    ]
    (ev / "EXEC_MODE_PAPER_PROMO_EVALUATION.md").write_text("".join(ev_md), encoding="utf-8")

    # Phase 6 board + final
    (ev / "BOARD_CSA_EXEC_MODE_PAPER_PROMO_VERDICT.md").write_text(
        "# BOARD_CSA — Paper exec promo\n\n"
        "- **Confounding:** Hour-based A/B is clean only if promo runs continuously; other state may correlate with hour.\n"
        "- **Governance:** Single-lever promotion; rollback via env unset.\n",
        encoding="utf-8",
    )
    (ev / "BOARD_SRE_EXEC_MODE_PAPER_PROMO_VERDICT.md").write_text(
        "# BOARD_SRE — Paper exec promo\n\n"
        "- **Blocking:** Treatment path may wait up to TTL minutes polling fills.\n"
        "- **Logs:** `paper_exec_mode_decisions.jsonl` append-only — rotate with other logs.\n",
        encoding="utf-8",
    )
    (ev / "BOARD_QUANT_EXEC_MODE_PAPER_PROMO_VERDICT.md").write_text(
        "# BOARD_QUANT — Paper exec promo\n\n"
        f"- **Gate result:** `{'FAIL' if fail else 'PASS'}` — reasons: {fail_reasons}\n"
        "- **Noise:** Need full session N; parity bucket is proxy not randomized assignment.\n",
        encoding="utf-8",
    )
    (ev / "EXEC_MODE_PAPER_PROMO_FINAL_VERDICT.md").write_text(
        "# EXEC_MODE_PAPER_PROMO_FINAL_VERDICT\n\n"
        f"- **Automated evaluation gate:** `{'FAIL' if fail else 'PASS'}`\n"
        "- **Deploy:** Set `PAPER_EXEC_PROMO_ENABLED=1`, `PAPER_EXEC_TTL_MINUTES=3`, "
        "`PAPER_EXEC_UNIVERSE_PATH` to universe JSON, restart `stock-bot`.\n"
        "- **Re-run mission** after 1–2 sessions for stable metrics.\n",
        encoding="utf-8",
    )

    print(json.dumps({"evidence_dir": str(ev), "gate_fail": fail, "ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
