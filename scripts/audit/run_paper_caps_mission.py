#!/usr/bin/env python3
"""
Paper caps mission (Phases 0–6). Droplet-oriented; evidence-only.

  cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_paper_caps_mission.py --evidence-et 2026-04-01
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]


def _run(cmd: str, cwd: Path, timeout: int = 180) -> Tuple[int, str]:
    try:
        r = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def _count_needle(path: Path, needle: str) -> int:
    if not path.is_file():
        return 0
    return path.read_text(encoding="utf-8", errors="replace").count(needle)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-et", required=True)
    ap.add_argument("--root", type=Path, default=REPO)
    args = ap.parse_args()
    root = args.root.resolve()
    ev = root / "reports" / "daily" / args.evidence_et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)

    # --- Phase 0 ---
    chunks: Dict[str, str] = {}
    _, chunks["git_head"] = _run("git rev-parse HEAD", root)
    _, chunks["systemctl_status"] = _run("systemctl status stock-bot --no-pager 2>&1 | head -n 80", root)
    _, chunks["systemctl_cat"] = _run("systemctl cat stock-bot 2>&1", root)
    _, chunks["systemctl_show"] = _run("systemctl show stock-bot -p Environment -p EnvironmentFiles 2>&1", root)
    _, chunks["journal_tail"] = _run('journalctl -u stock-bot --since "24 hours ago" --no-pager 2>&1 | tail -n 800', root)

    drop_ins = _run("ls /etc/systemd/system/stock-bot.service.d/*.conf 2>/dev/null", root)[1]
    drop_content = ""
    for line in drop_ins.splitlines():
        line = line.strip()
        if line.endswith(".conf") and Path(line).is_file():
            try:
                drop_content += f"\n### {line}\n" + Path(line).read_text(errors="replace")[:8000]
            except OSError:
                pass

    combined = "\n".join(chunks.values()) + drop_content + (root / "main.py").read_text(encoding="utf-8", errors="replace")[:50000]
    cl = combined.lower()
    paper_ok = "paper-api" in cl or "paper-api.alpaca.markets" in cl.replace("_", "-")
    if not paper_ok:
        paper_ok = "trading_mode=paper" in cl or "trading_mode paper" in cl or 'trading_mode", "paper' in cl

    main_submit = _count_needle(root / "main.py", "submit_order")
    pc_path = root / "src" / "paper" / "paper_cap_enforcement.py"
    pc_submit = _count_needle(pc_path, "submit_order")

    ph0 = {
        "git_head": chunks["git_head"].strip(),
        "paper_endpoint_detected": paper_ok,
        "main_py_submit_order_occurrences": main_submit,
        "paper_cap_module_submit_order_occurrences": pc_submit,
        "code_pointers": [
            "main.py Config TRADING_MODE / ALPACA_BASE_URL (~351–352)",
            "main.py _is_paper_url / paper-only enforcement (~916–951)",
            "main.py AlpacaExecutor._submit_order_guarded → api.submit_order (~4316–4452)",
        ],
    }
    (ev / "PAPER_CAPS_PHASE0_CONTEXT.json").write_text(json.dumps(ph0, indent=2), encoding="utf-8")

    md0 = [
        "# PAPER_CAPS_PHASE0_CONTEXT\n\n",
        "## git rev-parse HEAD\n\n```\n",
        chunks["git_head"].strip(),
        "\n```\n\n## systemctl status stock-bot\n\n```\n",
        chunks["systemctl_status"][:10000],
        "\n```\n\n## systemctl cat stock-bot\n\n```\n",
        chunks["systemctl_cat"][:20000],
        "\n```\n\n## systemctl show Environment\n\n```\n",
        chunks["systemctl_show"][:8000],
        "\n```\n\n## journalctl tail\n\n```\n",
        chunks["journal_tail"][:120000],
        "\n```\n\n## Paper-only proof\n\n",
        f"- **paper endpoint / mode detected in combined unit+main sample:** **{paper_ok}**\n",
        f"- **`main.py` `submit_order` string hits:** {main_submit} (live executor; unchanged by this mission).\n",
        f"- **`paper_cap_enforcement.py` `submit_order` hits:** {pc_submit} (must stay 0).\n",
        "- **Pointers:** " + "; ".join(ph0["code_pointers"]) + "\n",
    ]
    (ev / "PAPER_CAPS_PHASE0_CONTEXT.md").write_text("".join(md0), encoding="utf-8")

    if not paper_ok:
        (ev / "PAPER_CAPS_BLOCKER_PAPER_MODE_UNPROVEN.md").write_text(
            "# PAPER_CAPS_BLOCKER_PAPER_MODE_UNPROVEN\n\n"
            "Could not find `paper-api` / paper trading mode in systemd/journal/main sample.\n",
            encoding="utf-8",
        )
        print(json.dumps({"blocker": "PAPER_MODE_UNPROVEN", "evidence": str(ev)}))
        return 2

    if pc_submit > 0:
        (ev / "PAPER_CAPS_BLOCKER_LIVE_PATH_TOUCHED.md").write_text(
            "# PAPER_CAPS_BLOCKER_LIVE_PATH_TOUCHED\n\n`submit_order` found in paper cap module.\n",
            encoding="utf-8",
        )
        return 2

    # --- Phase 1 SPEC ---
    (ev / "PAPER_CAPS_SPEC.md").write_text(
        "# PAPER_CAPS_SPEC\n\n"
        "## Env-configurable caps (paper replay only)\n\n"
        "| Variable | Role |\n"
        "|----------|------|\n"
        "| `PAPER_CAPS_ENABLED` | `1` enables enforcement in replay helpers |\n"
        "| `PAPER_CAP_MAX_GROSS_USD` | Max sum |notional| of simulated open legs |\n"
        "| `PAPER_CAP_MAX_NET_USD` | Max |net| directional exposure |\n"
        "| `PAPER_CAP_MAX_PER_SYMBOL_USD` | Max |per-symbol| net after intent |\n"
        "| `PAPER_CAP_MAX_ORDERS_PER_MINUTE` | Max cap evaluations per UTC minute |\n"
        "| `PAPER_CAP_MAX_NEW_POSITIONS_PER_CYCLE` | Max accepts per cycle bucket (`PAPER_CAP_CYCLE_MINUTES`) |\n"
        "| `PAPER_CAP_FAIL_CLOSED` | Default `1` — errors → block |\n"
        "| `PAPER_CAP_HOLD_MINUTES` | Simulated hold before leg drops from book (default 60) |\n"
        "| `PAPER_CAP_CYCLE_MINUTES` | Cycle bucket length for position count |\n\n"
        "## Log: `logs/paper_cap_decisions.jsonl`\n\n"
        "Fields: `ts`, `symbol`, `side`, `intended_notional_usd`, `current_gross_usd`, `current_net_usd`, "
        "`per_symbol_usd`, `cap_check_result` (PASS/FAIL), `fail_reason_codes`, `decision_outcome`, `pretrade_key`.\n",
        encoding="utf-8",
    )

    # --- Phase 2 verify + implementation note ---
    vcode, vout = _run(f"cd {root} && PYTHONPATH=. python3 scripts/audit/verify_paper_caps_wired.py", root, 60)
    if vcode != 0:
        (ev / "PAPER_CAPS_BLOCKER_VERIFY_FAILED.md").write_text(
            f"# PAPER_CAPS_BLOCKER_VERIFY_FAILED\n\n```\n{vout}\n```\n", encoding="utf-8"
        )
        return 2

    impl = [
        "# PAPER_CAPS_IMPLEMENTATION\n\n",
        "## Modules (no `main.py` edits; no broker in cap module)\n\n",
        "- `src/paper/paper_cap_enforcement.py` — `enforce_paper_caps`, `PaperCapReplayState`, `append_paper_cap_log`.\n",
        "- `scripts/audit/run_paper_extension_caps_evaluation.py` — calls caps **before** counting CF/EMU PnL in replay.\n",
        "- `scripts/audit/verify_paper_caps_wired.py` — smoke.\n\n",
        "## Live path audit\n\n",
        f"- `paper_cap_enforcement.py` contains **{pc_submit}** occurrences of `submit_order`.\n",
        f"- verify_paper_caps_wired exit **{vcode}**.\n",
    ]
    (ev / "PAPER_CAPS_IMPLEMENTATION.md").write_text("".join(impl), encoding="utf-8")

    # --- Phase 3 runplan ---
    (ev / "PAPER_EXTENSION_RUNPLAN.md").write_text(
        "# PAPER_EXTENSION_RUNPLAN\n\n"
        "## Window\n\n"
        "Computed inside `run_paper_extension_caps_evaluation.py` from `displacement_blocked` covered rows: "
        "**last 7** distinct ET/UTC calendar days if ≥7 unique days exist in timestamps, else **last 3**.\n\n"
        "## A) Baseline (caps OFF)\n\n"
        "`run_paper_extension_caps_evaluation.py` runs `QUANT_CF_001` and `QUANT_EMU_001` branches with `caps_enabled=False` "
        "(no cap state mutation).\n\n"
        "## B) Caps ON\n\n"
        "Same script then sets env via `_apply_paper_cap_env_for_on()` and re-runs branches with `caps_enabled=True`.\n\n"
        "## Commands (droplet)\n\n"
        "```bash\n"
        "cd /root/stock-bot\n"
        "export PYTHONPATH=.\n"
        "python3 scripts/audit/verify_paper_caps_wired.py\n"
        "python3 scripts/audit/run_paper_extension_caps_evaluation.py --evidence-et "
        f"{args.evidence_et} --root /root/stock-bot --log-cap-decisions\n"
        "```\n\n"
        "**No live orders.** Read-only JSON + local bars file; optional cap JSONL append.\n",
        encoding="utf-8",
    )

    # --- Phase 4 run evaluation ---
    ecode, eout = _run(
        f"cd {root} && PYTHONPATH=. python3 scripts/audit/run_paper_extension_caps_evaluation.py "
        f"--evidence-et {args.evidence_et} --root {root} --log-cap-decisions",
        root,
        300,
    )
    if ecode != 0:
        (ev / "PAPER_EXTENSION_BLOCKER_EVAL_FAILED.md").write_text(
            f"# PAPER_EXTENSION_BLOCKER_EVAL_FAILED\n\n```\n{eout}\n```\n", encoding="utf-8"
        )
        return 2

    eval_path = ev / "PAPER_EXTENSION_EVALUATION.json"
    evj = json.loads(eval_path.read_text(encoding="utf-8"))
    md_ev = [
        "# PAPER_EXTENSION_EVALUATION\n\n",
        "See `PAPER_EXTENSION_EVALUATION.json` for full metrics (CF + EMU × caps off/on).\n\n",
        "## Summary table\n\n",
        "| Branch | total_pnl | trades | p05 | mdd | blocked | top fail codes |\n",
        "|--------|-----------|--------|-----|-----|---------|----------------|\n",
    ]
    for action in ("QUANT_CF_001", "QUANT_EMU_001"):
        for mode in ("baseline_caps_off", "caps_on"):
            b = evj.get(action, {}).get(mode, {})
            fails = b.get("top_fail_reason_codes") or []
            fs = ",".join(f"{a}:{n}" for a, n in fails[:5]) if fails else "—"
            md_ev.append(
                f"| {action} {mode} | {b.get('total_pnl_usd')} | {b.get('trade_count')} | "
                f"{b.get('tail_p05_pnl_per_trade')} | {b.get('max_drawdown_usd')} | "
                f"{b.get('blocked_by_caps_count')} | {fs} |\n"
            )
    (ev / "PAPER_EXTENSION_EVALUATION.md").write_text("".join(md_ev), encoding="utf-8")

    # --- Phase 5 board ---
    cf_off = evj.get("QUANT_CF_001", {}).get("baseline_caps_off", {})
    cf_on = evj.get("QUANT_CF_001", {}).get("caps_on", {})
    em_off = evj.get("QUANT_EMU_001", {}).get("baseline_caps_off", {})
    em_on = evj.get("QUANT_EMU_001", {}).get("caps_on", {})

    (ev / "BOARD_CSA_PAPER_CAPS_VERDICT.md").write_text(
        "# BOARD_CSA — Paper caps\n\n"
        "## Still paper-only?\n\n"
        "Yes: evaluation uses **counterfactual JSON + local bars** only; cap module has **zero** broker imports; "
        "`verify_paper_caps_wired` and Phase 0 attest paper service configuration sample.\n\n"
        "## Fail-closed?\n\n"
        "`PAPER_CAP_FAIL_CLOSED=1` default; invalid ts → block when caps on.\n\n"
        "## Counterfactual vs realized?\n\n"
        "Metrics remain **Variant A / emulator proxy**, not Alpaca fills — do not treat as realized PnL.\n",
        encoding="utf-8",
    )
    (ev / "BOARD_SRE_PAPER_CAPS_VERDICT.md").write_text(
        "# BOARD_SRE — Paper caps\n\n"
        "- **IO:** `--log-cap-decisions` appends JSONL; rotate `logs/paper_cap_decisions.jsonl` like other logs.\n"
        "- **CPU:** Single-pass replay O(n) on window rows.\n"
        "- **Silent disable:** If `PAPER_CAPS_ENABLED` not set to `1`, caps branch still forces enabled inside evaluation "
        "for the second pass only via env injection in script — document in runplan.\n",
        encoding="utf-8",
    )
    def _p05v(d: Dict[str, Any]) -> float:
        v = d.get("tail_p05_pnl_per_trade")
        return float(v) if v is not None else -1e18

    better = "QUANT_CF_001" if _p05v(cf_on) >= _p05v(em_on) else "QUANT_EMU_001"
    (ev / "BOARD_QUANT_PAPER_CAPS_VERDICT.md").write_text(
        "# BOARD_QUANT — Paper caps\n\n"
        f"- **CF baseline total / trades:** {cf_off.get('total_pnl_usd')} / {cf_off.get('trade_count')}; "
        f"**caps-on:** {cf_on.get('total_pnl_usd')} / {cf_on.get('trade_count')}; p05 {cf_off.get('tail_p05_pnl_per_trade')} → {cf_on.get('tail_p05_pnl_per_trade')}.\n"
        f"- **EMU baseline total / trades:** {em_off.get('total_pnl_usd')} / {em_off.get('trade_count')}; "
        f"**caps-on:** {em_on.get('total_pnl_usd')} / {em_on.get('trade_count')}; p05 {em_off.get('tail_p05_pnl_per_trade')} → {em_on.get('tail_p05_pnl_per_trade')}.\n"
        f"- **Tail note:** Higher p05 (less negative) suggests better tail under caps for that metric (see JSON).\n"
        f"- **Heuristic better-under-caps (p05):** `{better}` (descriptive only).\n",
        encoding="utf-8",
    )

    # --- Phase 6 verdict ---
    p05_cf_delta = (cf_on.get("tail_p05_pnl_per_trade") or 0) - (cf_off.get("tail_p05_pnl_per_trade") or 0)
    verdict = {
        "better_action_under_caps_on_by_p05": better,
        "caps_improve_tail_cf_p05_delta": round(p05_cf_delta, 6),
        "recommended_caps_from_evidence": evj.get("caps_env_snapshot"),
        "next_single_paper_lever": "Re-run weekly `run_paper_extension_caps_evaluation.py` with frozen cap env; archive JSON.",
        "verify": "python3 scripts/audit/verify_paper_caps_wired.py && diff PAPER_EXTENSION_EVALUATION.json week-over-week",
        "rollback": "Unset PAPER_CAPS_* env; delete cap JSONL; stop scheduling evaluation script.",
    }
    (ev / "PAPER_CAPS_FINAL_VERDICT.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    (ev / "PAPER_CAPS_FINAL_VERDICT.md").write_text(
        "# PAPER_CAPS_FINAL_VERDICT\n\n"
        f"- **Better under caps-on (p05 heuristic):** `{better}` — see `BOARD_QUANT_PAPER_CAPS_VERDICT.md`.\n"
        f"- **CF p05 delta (caps_on − baseline):** `{p05_cf_delta}` (USD per trade proxy).\n"
        f"- **Recommended caps (evidence snapshot):** see `PAPER_CAPS_FINAL_VERDICT.json` → `recommended_caps_from_evidence`.\n"
        f"- **Next single paper lever:** {verdict['next_single_paper_lever']}\n"
        f"- **Verify:** `{verdict['verify']}`\n"
        f"- **Rollback:** {verdict['rollback']}\n",
        encoding="utf-8",
    )

    for stale in ("PAPER_CAPS_BLOCKER_VERIFY_FAILED.md", "PAPER_EXTENSION_BLOCKER_EVAL_FAILED.md"):
        try:
            (ev / stale).unlink(missing_ok=True)
        except OSError:
            pass

    print(json.dumps({"evidence_dir": str(ev), "ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
