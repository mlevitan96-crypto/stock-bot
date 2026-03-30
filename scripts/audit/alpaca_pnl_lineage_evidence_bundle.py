#!/usr/bin/env python3
"""
Emit full PnL lineage evidence pack (droplet or local repo root).

Phases 0,3,5–8 artifacts under reports/daily/<ET>/evidence/.
Requires docs/pnl_audit/* and scripts/audit/alpaca_pnl_lineage_map_check.py.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
from typing import Any, Dict, Tuple

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))


def _load_map_check():
    p = REPO / "scripts" / "audit" / "alpaca_pnl_lineage_map_check.py"
    name = "_alpaca_pnl_lineage_map_check_dyn"
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _et_date() -> str:
    try:
        r = subprocess.run(
            ["bash", "-lc", "TZ=America/New_York date +%Y-%m-%d"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _sh(cmd: str, timeout: int = 60) -> Tuple[str, str, int]:
    r = subprocess.run(
        ["bash", "-lc", cmd],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return r.stdout or "", r.stderr or "", r.returncode


def _evidence_dir() -> Path:
    d = REPO / "reports" / "daily" / _et_date() / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def phase0_context(ev: Path) -> None:
    gh, _, _ = _sh("git rev-parse HEAD", 15)
    du, _, _ = _sh("date -u", 10)
    et = _et_date()
    en, _, _ = _sh("systemctl is-enabled stock-bot 2>&1", 10)
    ac, _, _ = _sh("systemctl is-active stock-bot 2>&1", 10)
    clock: Dict[str, Any] = {}
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(REPO / ".env")
        import alpaca_trade_api as tradeapi  # type: ignore

        from main import Config

        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version="v2")
        c = api.get_clock()
        clock = {
            "is_open": bool(getattr(c, "is_open", False)),
            "next_open": str(getattr(c, "next_open", "") or ""),
            "next_close": str(getattr(c, "next_close", "") or ""),
        }
    except Exception as e:
        clock = {"error": str(e)[:400]}
    body = [
        "# ALPACA PnL LINEAGE — Phase 0 context\n\n",
        f"- ET evidence date: `{et}`\n",
        f"- `git rev-parse HEAD`: `{gh.strip()}`\n",
        f"- `date -u`: `{du.strip()}`\n",
        f"- `systemctl is-enabled stock-bot`: `{en.strip()}`\n",
        f"- `systemctl is-active stock-bot`: `{ac.strip()}`\n\n",
        "## Alpaca clock\n\n",
        "```json\n",
        json.dumps(clock, indent=2),
        "\n```\n",
    ]
    (ev / "ALPACA_PNL_LINEAGE_CONTEXT.md").write_text("".join(body), encoding="utf-8")


def phase3_sre(ev: Path) -> None:
    mc = _load_map_check()
    run_check = mc.run_check

    matrix = REPO / "docs" / "pnl_audit" / "LINEAGE_MATRIX.json"
    data = json.loads(matrix.read_text(encoding="utf-8"))
    rows, meta = run_check(matrix, REPO)

    svc_user, _, _ = _sh("systemctl show stock-bot -p User --value 2>/dev/null | head -1", 10)
    svc_user = (svc_user or "").strip() or "unknown"

    broker_sample: Dict[str, Any] = {}
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(REPO / ".env")
        import alpaca_trade_api as tradeapi  # type: ignore

        from main import Config

        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version="v2")
        o = api.list_orders(status="all", limit=3, nested=True)
        if o:
            x = o[0]
            raw = getattr(x, "_raw", None)
            if isinstance(raw, dict):
                broker_sample = {k: raw.get(k) for k in list(raw.keys())[:25]}
            else:
                broker_sample = {"id": getattr(x, "id", None), "status": getattr(x, "status", None)}
    except Exception as e:
        broker_sample = {"error": str(e)[:300]}

    ping_out, _, ping_rc = _sh("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/ping 2>/dev/null || echo curl_fail", 15)

    lines = [
        "# ALPACA PnL LINEAGE — Droplet verification (SRE)\n\n",
        f"- Service user (systemctl): `{svc_user}`\n",
        f"- Map check summary: `{meta.get('summary')}`\n",
        f"- Dashboard `/api/ping` HTTP: `{ping_out.strip()}` (rc context: curl exit embedded)\n\n",
        "## Broker REST sample (first order keys subset)\n\n",
        "```json\n",
        json.dumps(broker_sample, indent=2, default=str),
        "\n```\n\n",
        "## Per-field resolution (persistence + emitter)\n\n",
        "| field | overall | persistence note | emitter note |\n",
        "|-------|---------|------------------|-------------|\n",
    ]
    by_name = {r.field_name: r for r in rows}
    for f in data.get("fields", []):
        name = f.get("field_name", "?")
        r = by_name.get(name)
        if not r:
            continue
        lines.append(
            f"| `{name}` | **{r.overall}** | {r.persistence_status}: {r.persistence_detail[:80]} | {r.emitter_status}: {r.emitter_detail[:80]} |\n"
        )

    lines.append("\n## File surfaces (mtime age sec, writable)\n\n")
    seen = set()
    for f in data.get("fields", []):
        pl = f.get("persistence_location", "")
        for part in pl.split("|"):
            first = part.strip().split()[0] if part.strip() else ""
            if first.startswith(("logs/", "state/", "data/")) and "*" not in first:
                p = REPO / first
                if first in seen:
                    continue
                seen.add(first)
                exists = p.is_file()
                age = ""
                if exists:
                    age = f"{time.time() - p.stat().st_mtime:.0f}"
                w = False
                try:
                    if p.is_file():
                        w = os.access(p, os.W_OK)
                    elif p.parent.is_dir():
                        w = os.access(p.parent, os.W_OK)
                except Exception:
                    pass
                lines.append(f"- `{first}` exists={exists} age_s={age or 'n/a'} writable={w}\n")

    (ev / "ALPACA_PNL_LINEAGE_DROPLET_VERIFICATION.md").write_text("".join(lines), encoding="utf-8")


def copy_adversarial_and_playbook(ev: Path) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    adv_src = REPO / "docs" / "pnl_audit" / "ADVERSARIAL_FINDINGS.md"
    adv_dst = ev / "ALPACA_PNL_LINEAGE_ADVERSARIAL_FINDINGS.md"
    adv_dst.write_text(
        f"# Adversarial findings (evidence copy)\n\n- Copied at UTC `{ts}` from `docs/pnl_audit/ADVERSARIAL_FINDINGS.md`.\n\n---\n\n"
        + adv_src.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    pb_src = REPO / "docs" / "pnl_audit" / "FIELD_ADDITION_PLAYBOOK.md"
    pb_dst = ev / "ALPACA_PNL_FIELD_ADDITION_PLAYBOOK_EVIDENCE.md"
    pb_dst.write_text(
        f"# Field addition playbook (evidence copy)\n\n- Copied at UTC `{ts}`.\n\n---\n\n" + pb_src.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def memory_bank_excerpt(ev: Path) -> None:
    mb = REPO / "MEMORY_BANK.md"
    text = mb.read_text(encoding="utf-8", errors="replace")
    marker = "## 1."
    idx = text.find("## 1.")
    snippet = text[idx : idx + 1200] if idx >= 0 else "(could not find section 1)"
    body = [
        "# ALPACA PNL MEMORY BANK UPDATE (evidence)\n\n",
        "## Inserted governance (see MEMORY_BANK.md for full file)\n\n",
        "- Canonical docs: `docs/pnl_audit/REQUIRED_FIELDS.md`, `LINEAGE_MATRIX.md`, `LINEAGE_MATRIX.json`, `FIELD_ADDITION_PLAYBOOK.md`, `ADVERSARIAL_FINDINGS.md`.\n",
        "- **LINEAGE_MATRIX.json** is the machine contract; any telemetry change must update it.\n",
        "- **Broker vs local** sources are explicit per matrix row (`source_of_truth`, `persistence_location`).\n",
        "- Map check: `python3 scripts/audit/alpaca_pnl_lineage_map_check.py --write-evidence`\n",
        "- Full evidence bundle: `python3 scripts/audit/alpaca_pnl_lineage_evidence_bundle.py`\n\n",
        "## Prior MEMORY_BANK excerpt (first `## 1.` block, truncated)\n\n",
        "```markdown\n",
        snippet[:2000],
        "\n```\n",
    ]
    (ev / "ALPACA_PNL_MEMORY_BANK_UPDATE.md").write_text("".join(body), encoding="utf-8")


def final_verdict(ev: Path) -> None:
    mc = _load_map_check()
    _, meta = mc.run_check(REPO / "docs" / "pnl_audit" / "LINEAGE_MATRIX.json", REPO)
    s = meta.get("summary", {})
    lines = [
        "# ALPACA PnL LINEAGE — FINAL VERDICT\n\n",
        f"- Required fields documented: **docs/pnl_audit/REQUIRED_FIELDS.md** (+ evidence copy).\n",
        f"- Lineage matrix rows: **{meta.get('field_count')}** (`LINEAGE_MATRIX.json`).\n",
        f"- Map check: RESOLVED={s.get('RESOLVED')} MOVED={s.get('MOVED')} MISSING={s.get('MISSING')}.\n\n",
        "## Completeness\n\n",
        "- **Lineage map:** all matrix rows classified (see `ALPACA_PNL_LINEAGE_MAP_CHECK.md`).\n",
        "- **Droplet verification:** see `ALPACA_PNL_LINEAGE_DROPLET_VERIFICATION.md` (files, broker sample, dashboard ping).\n\n",
        "## Adversarial residual risk\n\n",
        "- Top risks: service inactive → no new telemetry; local `order_id` sparse → use broker REST join; paper fees implicit zero.\n",
        "- **Acceptable for next open** if `stock-bot` is started and Alpaca keys valid (verify context + SRE doc).\n\n",
        "## Rerun commands\n\n",
        "```bash\n",
        "cd /root/stock-bot\n",
        "python3 scripts/audit/alpaca_pnl_lineage_map_check.py --write-evidence\n",
        "python3 scripts/audit/alpaca_forward_collection_readiness.py\n",
        "python3 scripts/audit/alpaca_pnl_lineage_evidence_bundle.py\n",
        "```\n",
    ]
    (ev / "ALPACA_PNL_LINEAGE_FINAL_VERDICT.md").write_text("".join(lines), encoding="utf-8")


def main() -> int:
    ev = _evidence_dir()
    phase0_context(ev)
    shutil.copy2(REPO / "docs" / "pnl_audit" / "REQUIRED_FIELDS.md", ev / "ALPACA_PNL_REQUIRED_FIELDS_EVIDENCE.md")
    shutil.copy2(REPO / "docs" / "pnl_audit" / "LINEAGE_MATRIX.md", ev / "ALPACA_PNL_LINEAGE_MATRIX.md")
    shutil.copy2(REPO / "docs" / "pnl_audit" / "LINEAGE_MATRIX.json", ev / "ALPACA_PNL_LINEAGE_MATRIX.json")

    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "audit" / "alpaca_pnl_lineage_map_check.py"), "--write-evidence", "--evidence-dir", str(ev)],
        cwd=str(REPO),
        check=False,
    )

    phase3_sre(ev)
    copy_adversarial_and_playbook(ev)
    memory_bank_excerpt(ev)
    final_verdict(ev)
    print(json.dumps({"evidence_dir": str(ev)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
